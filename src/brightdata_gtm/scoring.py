"""Deterministic confidence fusion across signals.

The account-level confidence is computed, not guessed by the LLM. It blends:
- per-signal strength weighted by category importance (specificity + actionability proxy)
- coverage: how many distinct signal categories we actually collected

This keeps the score explainable and stable run-to-run.
"""
from __future__ import annotations

from .models import Signal

# Category weight ~ how actionable/specific that signal type is for GTM.
CATEGORY_WEIGHT = {
    "hiring": 0.9,    # concrete, account-specific, actionable
    "deep": 0.85,     # structured AI research (Deep Lookup)
    "funding": 0.8,   # strong timing trigger
    "pricing": 0.7,   # messaging/positioning
    "competitor": 0.65,
    "messaging": 0.6,
    "market": 0.55,
    "news": 0.5,      # noisiest
}
_TOTAL_CATEGORIES = 7  # hiring, funding, pricing/messaging, competitor, market, news, deep


def fuse_confidence(signals: list[Signal], weights: dict[str, float] | None = None) -> float:
    """Deterministic account confidence. `weights` overrides the per-category priority
    weights (Settings -> Signal priorities) so a user's priorities actually move the score;
    defaults to CATEGORY_WEIGHT."""
    if not signals:
        return 0.1
    w = weights or CATEGORY_WEIGHT
    weighted = [w.get(s.category, 0.5) * s.confidence for s in signals]
    strength = sum(weighted) / len(weighted)
    distinct = {("pricing" if s.category == "messaging" else s.category) for s in signals}
    coverage = min(1.0, len(distinct) / _TOTAL_CATEGORIES)
    score = 0.6 * strength + 0.4 * coverage
    return round(max(0.05, min(0.95, score)), 2)
