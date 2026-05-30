"""Pure (testable) helpers for watchlist batch runs: per-account status + table rows.

Kept out of the Streamlit app so the transform (ok / empty / failed) is unit-testable.
"""
from __future__ import annotations


def make_item(domain: str, intel_dump: dict | None = None, error: object | None = None) -> dict:
    """Wrap one watchlist result with an explicit status: ok | empty | failed."""
    if error is not None:
        return {"domain": domain, "status": "failed", "intel": None, "error": str(error)}
    signals = (intel_dump or {}).get("signals") or []
    return {
        "domain": domain,
        "status": "ok" if signals else "empty",
        "intel": intel_dump,
        "error": None,
    }


def summarize_row(item: dict) -> dict:
    """One display row for the watchlist table (safe for ok/empty/failed)."""
    intel = item.get("intel") or {}
    signals = intel.get("signals") or []
    top = signals[0].get("summary", "-")[:70] if signals else "-"
    return {
        "account": intel.get("company") or item.get("domain", "?"),
        "status": item.get("status", "unknown"),
        "confidence": f"{intel.get('confidence', 0):.0%}" if item.get("status") == "ok" else "-",
        "signals": len(signals),
        "top signal": top,
    }


def rankable(items: list[dict]) -> list[dict]:
    """Only successfully-validated, signal-bearing items are eligible for ranking / drill-in."""
    return [i for i in items if i.get("status") == "ok" and i.get("intel")]


def rank_and_rest(items: list[dict]) -> tuple[list[dict], list[dict]]:
    """Split into (ranked ok-items by confidence desc, the rest) using explicit status,
    not list membership, and a defensive confidence read."""
    ranked = sorted(rankable(items), key=lambda i: (i.get("intel") or {}).get("confidence", 0), reverse=True)
    others = [i for i in items if i.get("status") != "ok"]
    return ranked, others
