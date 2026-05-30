"""TriggerWare integration (optional, partner): event egress so a signal change or an
action-ready run can fire a downstream automation (alert, workflow, webhook).

Real client that POSTs a structured event to a configured TriggerWare endpoint. Enabled only
when TRIGGERWARE_API_KEY (+ a webhook/endpoint URL) is set; otherwise the run does nothing here.
Sits at the END of the loop (after the CRM action) so "what changed -> do something" is wired.
"""
from __future__ import annotations

import json

import requests


class TriggerWareError(RuntimeError):
    pass


class TriggerWareClient:
    def __init__(self, api_key: str, endpoint: str, timeout: int = 20):
        if not api_key or not endpoint:
            raise TriggerWareError("TriggerWare requires TRIGGERWARE_API_KEY and TRIGGERWARE_WEBHOOK_URL")
        self.endpoint = endpoint
        self.http = requests.Session()
        self.http.headers.update(
            {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        )
        self.timeout = timeout

    def fire(self, event: str, payload: dict, dry_run: bool = False) -> dict:
        """Emit an event. dry_run returns the planned body without sending."""
        body = {"event": event, "source": "markster-recon", "data": payload}
        if dry_run:
            return {"dry_run": True, "endpoint": self.endpoint, "body": body}
        try:
            r = self.http.post(self.endpoint, data=json.dumps(body), timeout=self.timeout)
        except requests.RequestException as e:
            raise TriggerWareError(f"post failed: {e}")
        return {"dry_run": False, "status_code": r.status_code, "ok": r.status_code < 400}


def account_event(intel_company: str, confidence: float, action_ready: bool, top_source: str) -> dict:
    """Build the standard 'account is actionable' event payload from a run."""
    return {
        "account": intel_company,
        "confidence": round(confidence, 2),
        "action_ready": action_ready,
        "top_source": top_source,
    }
