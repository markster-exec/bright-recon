"""Synthesis layer: narrative over collected signals.

Provenance integrity: the LLM only WRITES narrative (one-liner, why-now, action).
It never invents sources. The real Signals (with provenance) are kept as-is and
passed through to the AccountIntel. Works on Azure OpenAI or AI/ML API; falls back
to deterministic synthesis when no LLM is configured, so the pipeline runs anyway.
"""
from __future__ import annotations

import json

from .config import Settings
from .models import AccountIntel, Provenance, Signal
from .scoring import fuse_confidence


def synthesize(settings: Settings, company: str, signals: list[Signal], sources: list[Provenance]) -> AccountIntel:
    evidence = "\n".join(
        f"- [{s.category}] {s.summary} :: {s.evidence[:300]} (source: {s.provenance.source_url})" for s in signals
    )
    used = "fallback"
    try:
        if settings.provider == "azure" and settings.llm_ready:
            narrative = _azure(settings, company, evidence)
            used = "azure"
        elif settings.provider == "aimlapi" and settings.llm_ready:
            narrative = _aimlapi(settings, company, evidence)
            used = "aimlapi"
        elif settings.provider == "featherless" and settings.llm_ready:
            narrative = _featherless(settings, company, evidence)
            used = "featherless"
        else:
            narrative = _fallback(company, signals)
    except Exception:  # noqa: BLE001 - never fail the run on the narrative layer
        narrative = _fallback(company, signals)
        used = "fallback"

    # Account-level confidence is deterministic, not the LLM's guess.
    narrative["confidence"] = fuse_confidence(signals)
    return AccountIntel(company=company, signals=signals, sources=sources, llm_used=used, **narrative)


def _prompt(company: str, evidence: str) -> tuple[str, str]:
    system = (
        "You are a GTM account strategist. Using ONLY the signals provided (each cites a source), "
        "produce an enterprise-grade Account Action Plan. Return JSON exactly: "
        '{"one_liner": str, "the_read": str, "terrain": str, "routes": [str], '
        '"who_decides": [str], "evidence_gaps": [str], "next_actions": [str]}. '
        "Definitions: the_read = why this account, why now (2-3 sentences grounded in the signals). "
        "terrain = what the company is / its positioning, from the signals. "
        "routes = 2-4 concrete entry angles. "
        "who_decides = roles or named people who shape the buying decision (from hiring/people signals; "
        "if not in the signals, say 'unknown - verify'). "
        "evidence_gaps = what is NOT known from the signals and should be verified (be honest; never invent). "
        "next_actions = 2-4 concrete next moves a rep would take, most urgent first. "
        "Do not invent facts beyond the signals."
    )
    user = f"Company: {company}\n\nLive web signals:\n{evidence or '(no signals collected)'}"
    return system, user


def _azure(s: Settings, company: str, evidence: str) -> dict:
    from openai import AzureOpenAI

    client = AzureOpenAI(azure_endpoint=s.azure_endpoint, api_key=s.azure_key, api_version=s.azure_api_version)
    system, user = _prompt(company, evidence)
    base = dict(
        model=s.azure_deployment,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        response_format={"type": "json_object"},
    )
    try:
        r = client.chat.completions.create(temperature=0.2, **base)
    except Exception as e:  # gpt-5.x reasoning models reject non-default temperature
        if "temperature" in str(e).lower():
            r = client.chat.completions.create(**base)
        else:
            raise
    return _parse(r.choices[0].message.content or "")


def _aimlapi(s: Settings, company: str, evidence: str) -> dict:
    from openai import OpenAI

    client = OpenAI(api_key=s.aimlapi_key, base_url=s.aimlapi_base_url)
    system, user = _prompt(company, evidence)
    r = client.chat.completions.create(
        model=s.aimlapi_model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.2,
    )
    return _parse(r.choices[0].message.content or "")


def _featherless(s: Settings, company: str, evidence: str) -> dict:
    """Synthesis via Featherless AI (open-source model inference, OpenAI-compatible API).

    Same provenance contract as every other provider: the model only writes narrative;
    real Signals/sources are passed through untouched.
    """
    from openai import OpenAI

    client = OpenAI(api_key=s.featherless_key, base_url=s.featherless_base_url)
    system, user = _prompt(company, evidence)
    r = client.chat.completions.create(
        model=s.featherless_model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.2,
    )
    return _parse(r.choices[0].message.content or "")


def _parse(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
    start, end = text.find("{"), text.rfind("}")
    d = json.loads(text[start : end + 1])

    def _strlist(v) -> list[str]:
        if isinstance(v, list):
            return [str(x) for x in v if str(x).strip()]
        return [str(v)] if str(v).strip() else []

    return {
        "one_liner": str(d.get("one_liner", "")),
        "the_read": str(d.get("the_read", "")),
        "terrain": str(d.get("terrain", "")),
        "routes": _strlist(d.get("routes")),
        "who_decides": _strlist(d.get("who_decides")),
        "evidence_gaps": _strlist(d.get("evidence_gaps")),
        "next_actions": _strlist(d.get("next_actions")),
    }


def _fallback(company: str, signals: list[Signal]) -> dict:
    cats = sorted({s.category for s in signals})
    hiring = next((s for s in signals if s.category == "hiring"), None)
    read = hiring.summary if hiring else (signals[0].summary if signals else "No fresh signals found.")
    action = (
        "Open with a role-specific angle tied to the teams they are scaling."
        if hiring
        else f"Lead with the most recent public development about {company}."
    )
    return {
        "one_liner": f"{company}: {len(signals)} live signal(s) ({', '.join(cats) or 'none'}).",
        "the_read": read,
        "terrain": "",
        "routes": [],
        "who_decides": [],
        "evidence_gaps": ["LLM synthesis unavailable - raw signals only."] if signals else ["No signals collected."],
        "next_actions": [action],
    }
