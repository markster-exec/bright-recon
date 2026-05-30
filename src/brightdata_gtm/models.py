"""Typed output schema with per-signal provenance (Phase 1)."""
from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Provenance(BaseModel):
    """Where a datum came from. Attached to every signal and listed on the brief."""

    source_url: str
    captured_at: str
    method: str  # e.g. "brightdata:web_scraper:linkedin_jobs", "brightdata:web_unlocker:serp"
    provider: str = "bright_data"


class Signal(BaseModel):
    category: str  # hiring | news | pricing | funding | ...
    summary: str
    evidence: str = ""
    provenance: Provenance
    confidence: float = Field(0.5, ge=0.0, le=1.0)


class AccountIntel(BaseModel):
    """An enterprise-grade Account Action Plan, synthesized from sourced signals."""

    company: str
    one_liner: str = ""
    the_read: str = ""  # why this account, why now
    terrain: str = ""  # firmographics / positioning from the signals
    routes: list[str] = Field(default_factory=list)  # concrete entry angles
    who_decides: list[str] = Field(default_factory=list)  # roles/people who shape the decision
    evidence_gaps: list[str] = Field(default_factory=list)  # honest unknowns to verify
    next_actions: list[str] = Field(default_factory=list)  # most urgent first
    signals: list[Signal] = Field(default_factory=list)
    confidence: float = Field(0.5, ge=0.0, le=1.0)
    sources: list[Provenance] = Field(default_factory=list)
    generated_at: str = Field(default_factory=now_iso)
    llm_used: str = "fallback"  # azure | aimlapi | fallback

    @property
    def next_action(self) -> str:
        return self.next_actions[0] if self.next_actions else ""
