"""Cross-run account memory + change detection.

This is the "always-on" half of the product: Recon doesn't just take a one-shot
snapshot, it remembers what each account looked like last run and reports *what
changed* (confidence moved, a new signal category appeared, the lead story shifted).

Two backends, same interface:
- LocalMemory: a JSON file on disk. Always works, no account needed - so change
  detection is demonstrable out of the box.
- CogneeMemory: the Cognee cloud knowledge graph (partner). Same snapshots are
  mirrored to /api/v1/remember/entry and are queryable via /api/v1/recall. Enabled
  only when COGNEE_API_KEY is set AND the endpoint authenticates, so a bad/absent
  key silently degrades to local memory instead of breaking a run.

The diff itself (diff_snapshots) is pure and unit-tested.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

import requests

from .models import AccountIntel


def snapshot(intel: AccountIntel) -> dict:
    """The small, comparable fingerprint of one run (what we store and diff on)."""
    return {
        "generated_at": intel.generated_at,
        "confidence": round(intel.confidence, 2),
        "categories": sorted({s.category for s in intel.signals}),
        "signal_count": len(intel.signals),
        "one_liner": intel.one_liner,
        "top_headline": intel.signals[0].summary if intel.signals else "",
    }


def diff_snapshots(prev: dict | None, curr: dict) -> dict:
    """What changed between the previous run and this one. Pure / testable."""
    if not prev:
        return {
            "first_seen": True,
            "summary": "First time this account was scanned - no prior run to compare.",
            "confidence_delta": 0.0,
            "new_categories": curr["categories"],
            "dropped_categories": [],
            "headline_changed": False,
        }
    prev_cats, curr_cats = set(prev.get("categories", [])), set(curr.get("categories", []))
    new_cats = sorted(curr_cats - prev_cats)
    dropped = sorted(prev_cats - curr_cats)
    delta = round(curr["confidence"] - prev.get("confidence", 0.0), 2)
    headline_changed = curr.get("top_headline", "") != prev.get("top_headline", "")

    parts: list[str] = []
    if delta:
        parts.append(f"confidence {'+' if delta > 0 else ''}{delta:.2f}")
    if new_cats:
        parts.append(f"new signal(s): {', '.join(new_cats)}")
    if dropped:
        parts.append(f"signal(s) gone quiet: {', '.join(dropped)}")
    if headline_changed:
        parts.append("lead story changed")
    summary = "Since last run: " + ("; ".join(parts) if parts else "no material change.")
    return {
        "first_seen": False,
        "summary": summary,
        "confidence_delta": delta,
        "new_categories": new_cats,
        "dropped_categories": dropped,
        "headline_changed": headline_changed,
    }


class LocalMemory:
    """Snapshots persisted to a JSON file, keyed by domain/company."""

    def __init__(self, path: str | os.PathLike | None = None):
        self.path = Path(path or os.getenv("RECON_MEMORY_PATH", ".recon_memory.json"))

    def _load(self) -> dict:
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text())
        except (json.JSONDecodeError, OSError):
            return {}

    def prior(self, key: str) -> dict | None:
        runs = self._load().get(key.lower(), [])
        return runs[-1] if runs else None

    def remember(self, key: str, snap: dict) -> None:
        data = self._load()
        runs = data.setdefault(key.lower(), [])
        runs.append(snap)
        del runs[:-20]  # keep the last 20 runs per account
        try:
            self.path.write_text(json.dumps(data, indent=2))
        except OSError:
            pass


@dataclass
class CogneeMemory:
    """Mirror snapshots into the Cognee cloud knowledge graph (partner).

    Best-effort: any auth/network failure is swallowed so a run never breaks on the
    memory backend. `available()` reflects whether the endpoint actually accepts the key.
    """

    api_key: str
    base_url: str
    tenant_id: str = ""
    dataset: str = "markster_recon"
    timeout: int = 30

    def _headers(self) -> dict:
        h = {"X-Api-Key": self.api_key, "Content-Type": "application/json"}
        if self.tenant_id:
            h["X-Tenant-Id"] = self.tenant_id
        return h

    def available(self) -> bool:
        """True only if the key authenticates against an authd endpoint (not just /health)."""
        if not self.api_key:
            return False
        try:
            r = requests.get(
                f"{self.base_url}/api/v1/permissions/tenants/me", headers=self._headers(), timeout=self.timeout
            )
            return r.status_code < 400
        except requests.RequestException:
            return False

    def remember(self, key: str, snap: dict) -> bool:
        try:
            r = requests.post(
                f"{self.base_url}/api/v1/remember/entry",
                headers=self._headers(),
                json={"entry": f"Account {key}: {json.dumps(snap)}", "dataset_name": self.dataset},
                timeout=self.timeout,
            )
            return r.status_code < 400
        except requests.RequestException:
            return False

    def recall(self, query: str, top_k: int = 5) -> str | None:
        try:
            r = requests.post(
                f"{self.base_url}/api/v1/recall",
                headers=self._headers(),
                json={"query": query, "datasets": [self.dataset], "topK": top_k, "onlyContext": True},
                timeout=self.timeout,
            )
            if r.status_code < 400:
                return r.text
        except requests.RequestException:
            pass
        return None


def cognee_from_env() -> CogneeMemory | None:
    """Build a CogneeMemory from env, or None if unconfigured. Does not hit the network."""
    key = os.getenv("COGNEE_API_KEY", "").strip()
    base = os.getenv("COGNEE_BASE_URL", "").strip().rstrip("/")
    if not (key and base):
        return None
    return CogneeMemory(api_key=key, base_url=base, tenant_id=os.getenv("COGNEE_TENANT_ID", "").strip())


def remember_and_diff(intel: AccountIntel, key: str | None = None, local: LocalMemory | None = None) -> dict:
    """Compare this run against the prior one, persist it (local always; Cognee if live),
    and return the change report. `key` defaults to the company name."""
    key = (key or intel.company).strip()
    local = local or LocalMemory()
    snap = snapshot(intel)
    prev = local.prior(key)
    change = diff_snapshots(prev, snap)

    local.remember(key, snap)

    # Distinguish "not configured" from "configured but the endpoint rejected us", so the
    # silent fallback to local memory is operationally obvious (the CLI surfaces this).
    cog = cognee_from_env()
    if cog is None:
        change["cognee"] = "disabled"  # no COGNEE_API_KEY / COGNEE_BASE_URL set
    elif not cog.available():
        change["cognee"] = "unavailable"  # configured, but auth/network failed at the endpoint
        change["cognee_endpoint"] = cog.base_url
    else:
        change["cognee"] = "stored" if cog.remember(key, snap) else "error"
        change["cognee_endpoint"] = cog.base_url
    return change
