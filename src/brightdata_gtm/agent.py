"""Orchestration (Phase 1): collect live Bright Data signals -> one sourced AccountIntel."""
from __future__ import annotations

import re
from collections import Counter

from .brightdata import BrightDataClient, BrightDataError
from .config import Settings
from .models import AccountIntel, Provenance, Signal

_FUNDING_KW = ("raised", "raises", "series ", "seed round", "funding round", "investment", "investor", "valuation", "acqui")


def _ground_who_decides(who_decides: list[str], signals: list[Signal]) -> list[str]:
    """Honesty guard: flag any proposed person-name that does not actually appear in a
    collected signal, so the LLM cannot smuggle in an unsourced (hallucinated) name."""
    blob = " ".join(f"{s.summary} {s.evidence}" for s in signals).lower()
    out: list[str] = []
    for w in who_decides:
        m = re.search(r"\b([A-Z][a-z]+(?: [A-Z][a-z]+)+)\b", w)  # a Capitalized full name
        if m and m.group(1).lower() not in blob:
            out.append(f"{w} [name not found in sources - verify]")
        else:
            out.append(w)
    return out


def _domain_of(company: str) -> str | None:
    """Return a plain registered domain (exactly sld.tld) safe to fetch, else None.

    Strict by design (SSRF guard): rejects subdomains, paths, IPs, and internal/metadata hosts.
    """
    c = company.strip().lower().split("//")[-1].split("/")[0]
    # exactly two labels, letter TLD -> rejects subdomains (foo.bar.com), IPs, and path inputs
    if not re.fullmatch(r"[a-z0-9-]+\.[a-z]{2,}", c):
        return None
    if c.endswith(".local") or c.endswith(".internal") or "metadata" in c:
        return None
    return c


def _brand(company: str) -> str:
    """Brand for search queries. Only derive from a validated plain domain
    ('stripe.com' -> 'Stripe'); otherwise use the caller's text verbatim so we never
    mangle a name or point a subdomain at the wrong company."""
    d = _domain_of(company)
    if d:
        return d.split(".")[0].capitalize()
    return company.strip()


_PRICING_HINT = ("pric", "/mo", "per month", "per user", "per seat", "free", "tier", "plan", "$", "billed")


def _looks_like_pricing(text: str) -> bool:
    """Heuristic: real pricing pages mention pricing concepts. Rejects 404/cookie/coming-soon shells."""
    t = text.lower()
    return sum(1 for k in _PRICING_HINT if k in t) >= 2


def _summarize_jobs(company: str, jobs: list[dict]) -> tuple[str, str]:
    """Turn raw job postings into structured hiring intelligence (the tutorial's value):
    hiring velocity, department expansion, seniority mix, locations."""
    n = len(jobs)
    funcs = Counter(j.get("job_function") or j.get("job_department") for j in jobs if (j.get("job_function") or j.get("job_department")))
    seniority = Counter(j.get("job_seniority_level") for j in jobs if j.get("job_seniority_level"))
    locs = Counter(j.get("job_location") for j in jobs if j.get("job_location"))
    titles = [j.get("job_title") for j in jobs if j.get("job_title")][:12]

    dep = ", ".join(f"{k} ({v})" for k, v in funcs.most_common(6)) or "n/a"
    sen = ", ".join(f"{k} ({v})" for k, v in seniority.most_common(5)) or "n/a"
    loc = ", ".join(f"{k} ({v})" for k, v in locs.most_common(4)) or "n/a"

    summary = f"{n} live job postings for {company}; departments expanding: {dep}"
    evidence = (
        f"hiring velocity: {n} open roles. department mix: {dep}. seniority mix: {sen}. "
        f"top locations: {loc}. sample roles: {'; '.join(titles)}"
    )
    return summary, evidence


def research_account(
    company: str,
    location: str = "United States",
    settings: Settings | None = None,
    include_jobs: bool = True,
    deep: bool = False,
    verbose: bool = False,
) -> AccountIntel:
    settings = settings or Settings.load()
    bd = BrightDataClient(settings)
    brand = _brand(company)
    domain = _domain_of(company)

    signals: list[Signal] = []
    sources: list[Provenance] = []

    # Hiring signal: LinkedIn jobs via Web Scraper API (the organizer-blessed pattern).
    if include_jobs:
        try:
            if verbose:
                print(f"[bright data] linkedin jobs discover_new for {brand} ...")
            jobs, prov = bd.linkedin_jobs(brand, location)
            sources.append(prov)
            if jobs:
                summary, evidence = _summarize_jobs(brand, jobs)
                signals.append(
                    Signal(category="hiring", summary=summary, evidence=evidence, provenance=prov, confidence=0.72)
                )
        except BrightDataError as e:
            if verbose:
                print(f"[bright data] jobs unavailable: {e}")

    # Market signal: recent news via Google News RSS through Web Unlocker (clean, parsed).
    try:
        if verbose:
            print(f"[bright data] google news rss via web_unlocker for {brand} ...")
        items, prov = bd.news(f'"{brand}"')
        sources.append(prov)
        if items:
            headlines = " | ".join(f"{i['title']} ({i['pubDate'][:16]})" for i in items)
            signals.append(
                Signal(
                    category="news",
                    summary=f"{len(items)} recent news items for {brand}: {items[0]['title']}",
                    evidence=headlines,
                    provenance=prov,
                    confidence=0.55,
                )
            )
    except BrightDataError as e:
        if verbose:
            print(f"[bright data] news failed: {e}")

    # Funding signal: funding-focused news via Web Unlocker (Google News RSS).
    try:
        if verbose:
            print(f"[bright data] funding news for {brand} ...")
        fitems, fprov = bd.news(f'"{brand}" funding round investment')
        fund = [i for i in fitems if any(k in i["title"].lower() for k in _FUNDING_KW)]
        if fund:
            sources.append(fprov)
            signals.append(
                Signal(
                    category="funding",
                    summary=f"{len(fund)} funding/investment news item(s): {fund[0]['title']}",
                    evidence=" | ".join(i["title"] for i in fund[:5]),
                    provenance=fprov,
                    confidence=0.5,
                )
            )
    except BrightDataError as e:
        if verbose:
            print(f"[bright data] funding news failed: {e}")

    # Competitor signal: Discover API (AI-ranked URL discovery, token-only).
    try:
        if verbose:
            print(f"[bright data] discover competitors for {brand} ...")
        results, dprov = bd.discover(f"{brand} competitors alternatives", num_results=6)
        if results:
            sources.append(dprov)
            titles = " | ".join(r.get("title", "") for r in results[:5] if r.get("title"))
            signals.append(
                Signal(
                    category="competitor",
                    summary=f"{len(results)} competitor/alternative sources discovered for {brand}",
                    evidence=titles,
                    provenance=dprov,
                    confidence=0.5,
                )
            )
    except BrightDataError as e:
        if verbose:
            print(f"[bright data] discover failed: {e}")

    # Market signal: SERP API structured results (needs a SERP zone; skipped gracefully otherwise).
    try:
        if verbose:
            print(f"[bright data] serp api for {brand} ...")
        organic, sprov = bd.serp(f"{brand} news pricing 2026")
        if organic:
            sources.append(sprov)
            snips = " | ".join(o.get("title", "") for o in organic[:5] if o.get("title"))
            signals.append(
                Signal(
                    category="market",
                    summary=f"{len(organic)} structured SERP results for {brand}",
                    evidence=snips,
                    provenance=sprov,
                    confidence=0.5,
                )
            )
    except BrightDataError as e:
        if verbose:
            print(f"[bright data] serp skipped: {e}")

    # Pricing/messaging signal: web_unlocker /pricing -> Browser API render (JS SPAs) -> homepage.
    if domain:
        chosen: tuple | None = None
        try:
            if verbose:
                print(f"[bright data] web_unlocker /pricing https://{domain}/pricing ...")
            page = bd.fetch_text(f"https://{domain}/pricing")
            if page.content and len(page.content) > 200 and _looks_like_pricing(page.content):
                chosen = (page, "pricing", "pricing", 0.6)
        except BrightDataError as e:
            if verbose:
                print(f"[bright data] /pricing failed: {e}")

        if chosen is None and settings.browser_ready:
            try:
                if verbose:
                    print(f"[bright data] BROWSER API render https://{domain}/pricing ...")
                page = bd.fetch_rendered(f"https://{domain}/pricing")
                if page.content and len(page.content) > 200 and _looks_like_pricing(page.content):
                    chosen = (page, "pricing", "pricing (JS-rendered)", 0.65)
            except Exception as e:  # noqa: BLE001 - playwright/network errors, keep run alive
                if verbose:
                    print(f"[bright data] browser render failed: {e}")

        if chosen is None:
            try:
                page = bd.fetch_text(f"https://{domain}/")
                if page.content and len(page.content) > 200:
                    chosen = (page, "messaging", "homepage", 0.45)
            except BrightDataError as e:
                if verbose:
                    print(f"[bright data] homepage failed: {e}")

        if chosen is not None:
            page, cat, label, conf = chosen
            sources.append(page.provenance)
            signals.append(
                Signal(
                    category=cat,
                    summary=f"Live {label} snapshot from {page.provenance.source_url}",
                    evidence=page.content[:1800],
                    provenance=page.provenance,
                    confidence=conf,
                )
            )

    # Optional deep structured research via Deep Lookup API (async; --deep).
    if deep:
        try:
            if verbose:
                print(f"[bright data] deep lookup (funding) for {brand} ...")
            rows, cols, dlprov = bd.deep_lookup(f"Find all funding rounds for {brand} in the last 3 years")
            if rows and isinstance(rows[0], dict):
                sources.append(dlprov)
                top = "; ".join(
                    f"{c.get('name')}={rows[0].get(c.get('name'), '')}" for c in cols[:4] if isinstance(c, dict)
                )
                signals.append(
                    Signal(
                        category="deep",
                        summary=f"Deep Lookup structured research: {len(rows)} row(s) on {brand} funding",
                        evidence=top,
                        provenance=dlprov,
                        confidence=0.7,
                    )
                )
        except BrightDataError as e:
            if verbose:
                print(f"[bright data] deep lookup failed: {e}")

    if verbose:
        print(f"[synthesis] {len(signals)} signal(s); provider={settings.provider} ready={settings.llm_ready}")
    from .llm import synthesize

    intel = synthesize(settings, brand, signals, sources)
    intel.who_decides = _ground_who_decides(intel.who_decides, signals)  # honesty guard
    return intel
