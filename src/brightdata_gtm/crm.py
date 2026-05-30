"""Build a CRM-ready action package from an Account Action Plan.

Pure function, no auth, no network: it renders exactly what would be written to a
CRM (company properties + a sourced note + an urgent task). This is the
judge-testable preview of the "structured/integrable output into CRM" pillar; the
live HubSpot push (hubspot.py) writes this same package.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from pydantic import BaseModel, Field

from .models import AccountIntel


class CrmTask(BaseModel):
    subject: str
    body: str
    priority: str  # HIGH | MEDIUM | LOW
    due_date: str  # YYYY-MM-DD


class CrmActionPackage(BaseModel):
    company: str
    properties: dict[str, str] = Field(default_factory=dict)
    note_markdown: str = ""
    task: CrmTask
    action_ready: bool = True  # False = thin/low-confidence run, do not treat as approved action
    caveat: str = ""


def _priority(conf: float) -> str:
    if conf >= 0.6:
        return "HIGH"
    if conf >= 0.35:
        return "MEDIUM"
    return "LOW"


def _suggested_due(generated_at: str) -> str:
    """Suggested due date = run date + 1 day. Derived from the run timestamp (not wall-clock
    'now') so the preview is clearly a suggestion tied to this run, not a committed action."""
    try:
        base = datetime.fromisoformat(generated_at)
    except ValueError:
        base = datetime.now(timezone.utc)
    return (base + timedelta(days=1)).date().isoformat()


def _category_signal(intel: AccountIntel, *categories: str) -> str:
    """The summary of the highest-confidence signal in any of the given categories (else '')."""
    matches = [s for s in intel.signals if s.category in categories]
    if not matches:
        return ""
    best = max(matches, key=lambda s: s.confidence)
    return best.summary[:600]


def _top_source(intel: AccountIntel) -> str:
    """Source URL of the highest-confidence signal (the strongest evidence link)."""
    if not intel.signals:
        return ""
    return max(intel.signals, key=lambda s: s.confidence).provenance.source_url


def gtm_properties(intel: AccountIntel) -> dict[str, str]:
    """Map an AccountIntel onto the 13 `gtm_*` company properties that exist in the
    HubSpot portal (property group "GTM Intelligence"). Only real properties are
    emitted, with portal-correct types: gtm_confidence / gtm_signal_count are numbers,
    gtm_generated_at is a date (YYYY-MM-DD). See docs/hubspot-crm-setup.md."""
    return {
        "gtm_one_liner": intel.one_liner[:250],
        "gtm_why_now": intel.the_read[:600],
        "gtm_recommended_action": (intel.next_action or "")[:600],
        "gtm_confidence": f"{intel.confidence:.2f}",
        "gtm_signal_count": str(len(intel.signals)),
        "gtm_hiring_signal": _category_signal(intel, "hiring"),
        "gtm_funding_signal": _category_signal(intel, "funding", "deep"),
        "gtm_pricing_signal": _category_signal(intel, "pricing", "messaging"),
        "gtm_news_signal": _category_signal(intel, "news", "market", "competitor"),
        "gtm_top_source_url": _top_source(intel)[:250],
        "gtm_llm_used": intel.llm_used,
        "gtm_generated_at": intel.generated_at[:10],
        "gtm_source": "brightdata-gtm-agent",
    }


def build_action_package(intel: AccountIntel) -> CrmActionPackage:
    conf = intel.confidence
    next_action = intel.next_action or "Review the collected signals and pick the sharpest opening."

    # Gate: a thin / low-confidence / fallback run must not look operationally ready.
    signal_count = len(intel.signals)
    action_ready = conf >= 0.5 and intel.llm_used != "fallback" and signal_count >= 2
    caveat = (
        ""
        if action_ready
        else (
            f"LOW-CONFIDENCE PREVIEW - NOT an approved action. {signal_count} signal(s), "
            f"{conf:.0%} confidence, llm={intel.llm_used}. Verify the evidence gaps before any outreach."
        )
    )

    # Mirror the AccountIntel onto the real HubSpot "GTM Intelligence" property group.
    properties = gtm_properties(intel)

    lines = [
        f"# Markster Recon - Account Action Plan: {intel.company}",
        f"Confidence {conf:.0%} (coverage x signal strength) | generated {intel.generated_at}",
        "",
    ]
    if caveat:
        lines += [f"> {caveat}", ""]
    lines += [f"**The read:** {intel.the_read}", ""]
    if intel.terrain:
        lines += [f"**Terrain:** {intel.terrain}", ""]
    if intel.routes:
        lines.append("**Routes to enter:**")
        lines += [f"- {r}" for r in intel.routes]
        lines.append("")
    if intel.who_decides:
        lines.append("**Who shapes the decision:**")
        lines += [f"- {w}" for w in intel.who_decides]
        lines.append("")
    lines.append("**Live signals (each links to its source):**")
    for s in intel.signals:
        lines.append(f"- [{s.category}] {s.summary} -> {s.provenance.source_url}")
    if intel.evidence_gaps:
        lines += ["", "**Evidence gaps (verify before acting):**"]
        lines += [f"- {g}" for g in intel.evidence_gaps]
    lines += ["", "**Next actions:**"]
    lines += [f"{i}. {a}" for i, a in enumerate(intel.next_actions, 1)]
    note_markdown = "\n".join(lines)

    body = (
        f"Auto-generated by Markster Recon ({conf:.0%} confidence). "
        "Full sourced plan is in the linked note. Every signal links to its live web source. "
        "Due date is a suggestion (run date + 1 day) until the action is actually pushed."
    )
    if action_ready:
        subject = f"Recon: {next_action[:80]}"
        priority = _priority(conf)
    else:
        subject = f"Recon (review only): {intel.company} - low confidence, verify before acting"
        priority = "LOW"
        body = f"{caveat} {body}"

    task = CrmTask(subject=subject, body=body, priority=priority, due_date=_suggested_due(intel.generated_at))
    return CrmActionPackage(
        company=intel.company,
        properties=properties,
        note_markdown=note_markdown,
        task=task,
        action_ready=action_ready,
        caveat=caveat,
    )
