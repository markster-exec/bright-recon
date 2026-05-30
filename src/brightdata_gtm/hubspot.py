"""Live agentic CRM push: write a CRM action package to HubSpot.

Finds the company by domain, then creates a sourced Note + an urgent Task associated
to it (the actions an AI agent / rep acts on), and best-effort updates company
properties. Defaults to dry_run so a write only happens when explicitly requested.
"""
from __future__ import annotations

from datetime import datetime, timezone

import requests

from .config import Settings
from .crm import CrmActionPackage

BASE = "https://api.hubapi.com"


class HubSpotError(RuntimeError):
    pass


def _now_ms() -> str:
    return str(int(datetime.now(timezone.utc).timestamp() * 1000))


class HubSpotClient:
    def __init__(self, settings: Settings, timeout: int = 30, token: str | None = None):
        tok = token or settings.hubspot_token  # token override = judge BYO-token (push to their own HubSpot)
        if not tok:
            raise HubSpotError("No HubSpot token (set HUBSPOT_ACCESS_TOKEN or pass a token)")
        self.http = requests.Session()
        self.http.headers.update({"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
        self.timeout = timeout

    def find_company(self, domain: str) -> dict | None:
        body = {
            "filterGroups": [{"filters": [{"propertyName": "domain", "operator": "EQ", "value": domain}]}],
            "properties": ["name", "domain"],
            "limit": 1,
        }
        r = self.http.post(f"{BASE}/crm/v3/objects/companies/search", json=body, timeout=self.timeout)
        if r.status_code >= 400:
            raise HubSpotError(f"company search {r.status_code}: {r.text[:200]}")
        results = r.json().get("results", [])
        return results[0] if results else None

    def create_company(self, domain: str, name: str) -> str:
        r = self.http.post(
            f"{BASE}/crm/v3/objects/companies",
            json={"properties": {"name": name, "domain": domain}},
            timeout=self.timeout,
        )
        if r.status_code >= 400:
            raise HubSpotError(f"company create {r.status_code}: {r.text[:200]}")
        return r.json()["id"]

    def _create(self, obj: str, properties: dict) -> str:
        r = self.http.post(f"{BASE}/crm/v3/objects/{obj}", json={"properties": properties}, timeout=self.timeout)
        if r.status_code >= 400:
            raise HubSpotError(f"{obj} create {r.status_code}: {r.text[:200]}")
        return r.json()["id"]

    def _associate(self, from_obj: str, from_id: str, to_obj: str, to_id: str) -> None:
        # v4 default association - no typeId needed
        r = self.http.put(
            f"{BASE}/crm/v4/objects/{from_obj}/{from_id}/associations/default/{to_obj}/{to_id}", timeout=self.timeout
        )
        if r.status_code >= 400:
            raise HubSpotError(f"associate {from_obj}->{to_obj} {r.status_code}: {r.text[:200]}")

    def push(self, pkg: CrmActionPackage, domain: str, dry_run: bool = True, create_if_missing: bool = False) -> dict:
        """Write the package to HubSpot. dry_run=True returns the planned payloads without writing."""
        note_props = {"hs_note_body": pkg.note_markdown, "hs_timestamp": _now_ms()}
        task_props = {
            "hs_task_subject": pkg.task.subject,
            "hs_task_body": pkg.task.body,
            "hs_task_status": "NOT_STARTED",
            "hs_task_priority": pkg.task.priority,
            "hs_timestamp": _now_ms(),
        }
        result: dict = {
            "dry_run": dry_run,
            "company": pkg.company,
            "domain": domain,
            "action_ready": pkg.action_ready,
            "note_payload": note_props,
            "task_payload": task_props,
        }
        if dry_run:
            return result

        company = self.find_company(domain) if domain else None
        if company:
            cid = company["id"]
            result["company_name"] = company.get("properties", {}).get("name")
        elif create_if_missing and domain:
            cid = self.create_company(domain, pkg.company)
            result["company_created"] = True
            result["company_name"] = pkg.company
        else:
            result["error"] = f"company not found in HubSpot by domain '{domain}' (set create_if_missing)"
            return result
        result["company_id"] = cid

        # best-effort property update (custom recon_* props may not exist on the portal)
        try:
            pr = self.http.patch(
                f"{BASE}/crm/v3/objects/companies/{cid}", json={"properties": pkg.properties}, timeout=self.timeout
            )
            result["properties_updated"] = pr.status_code < 400
        except Exception:  # noqa: BLE001
            result["properties_updated"] = False

        note_id = self._create("notes", note_props)
        self._associate("notes", note_id, "companies", cid)
        result["note_id"] = note_id

        task_id = self._create("tasks", task_props)
        self._associate("tasks", task_id, "companies", cid)
        result["task_id"] = task_id
        return result
