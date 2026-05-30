"""Markster Recon - branded Streamlit app: live web -> Account Action Plan -> agentic CRM."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from brightdata_gtm.agent import research_account  # noqa: E402
from brightdata_gtm.config import Settings  # noqa: E402
from brightdata_gtm.crm import build_action_package  # noqa: E402
from brightdata_gtm.models import AccountIntel  # noqa: E402
from brightdata_gtm.scoring import CATEGORY_WEIGHT, fuse_confidence  # noqa: E402
from brightdata_gtm import ui  # noqa: E402

st.set_page_config(page_title="Markster Recon", page_icon="🛰️", layout="wide")
st.markdown(ui.BRAND_CSS, unsafe_allow_html=True)
st.markdown(ui.header_html(), unsafe_allow_html=True)

ALL_STAGES = {"provenance", "confidence", "synthesis", "crm", "agent"}
DEFAULT_TARGET_LIST = ["linear.app", "notion.so", "webflow.com", "vercel.com", "salesforce.com", "nvidia.com"]
SHOWCASE = {}
_sc = Path(__file__).parent / "examples" / "showcase.json"
if _sc.exists():
    try:
        SHOWCASE = json.loads(_sc.read_text())
    except json.JSONDecodeError:
        SHOWCASE = {}

st.session_state.setdefault("target_list", list(DEFAULT_TARGET_LIST))
st.session_state.setdefault("weights", dict(CATEGORY_WEIGHT))


@st.cache_data(show_spinner=False, ttl=3600)
def run_recon(company: str, location: str, include_jobs: bool, deep: bool, provider: str = "azure") -> dict:
    """Cached so repeated/stage runs are instant. `provider` is in the cache key so switching
    LLM (Azure / AI/ML API / Featherless) re-runs synthesis instead of serving a stale plan."""
    os.environ["LLM_PROVIDER"] = provider
    intel = research_account(company, location=location, settings=Settings.load(), include_jobs=include_jobs, deep=deep)
    return intel.model_dump()


def _section(label: str) -> None:
    st.markdown(f'<div class="mr-section">{label}</div>', unsafe_allow_html=True)


def render_plan(intel: AccountIntel, domain_or_company: str, sample: bool = False) -> None:
    # Re-score with the user's Signal priorities (Settings) so they actually move the number.
    intel.confidence = fuse_confidence(intel.signals, st.session_state["weights"])
    if sample:
        st.markdown('<span class="mr-badge">Cached sample</span> &nbsp; '
                    '<span style="color:#9aa0aa;font-size:.8rem;">pre-run for instant load; use Run Recon (live) for a fresh pull</span>',
                    unsafe_allow_html=True)
    fired = ui.products_fired([s.provenance.method for s in intel.signals] + [p.method for p in intel.sources])
    st.markdown(ui.loop_html(fired=fired, lit_stages=ALL_STAGES), unsafe_allow_html=True)

    left, right = st.columns([3, 1])
    with left:
        st.markdown(f'<div class="mr-card"><div class="mr-oneliner">{intel.one_liner}</div></div>', unsafe_allow_html=True)
    with right:
        st.markdown(f'<div class="mr-card">{ui.confidence_html(intel.confidence)}</div>', unsafe_allow_html=True)

    from brightdata_gtm.pdf import build_account_pdf

    st.download_button("Download Account Action Plan (PDF)", data=build_account_pdf(intel),
                       file_name=f"recon-{intel.company.lower().replace(' ', '-')}.pdf",
                       mime="application/pdf", key=f"pdf_{intel.company}")

    _section("The read &mdash; why this account, why now")
    st.markdown(f'<div class="mr-card">{intel.the_read or "&mdash;"}</div>', unsafe_allow_html=True)
    if intel.terrain:
        _section("Terrain")
        st.markdown(f'<div class="mr-card">{intel.terrain}</div>', unsafe_allow_html=True)

    cols = st.columns(2)
    if intel.routes:
        with cols[0]:
            _section("Routes to enter")
            st.markdown('<div class="mr-card">' + "".join(f"&bull; {r}<br>" for r in intel.routes) + "</div>",
                        unsafe_allow_html=True)
    if intel.who_decides:
        with cols[1]:
            _section("Who shapes the decision")
            st.markdown('<div class="mr-card">' + "".join(f"&bull; {w}<br>" for w in intel.who_decides) + "</div>",
                        unsafe_allow_html=True)

    _section(f"Live signals &mdash; {len(intel.signals)} collected, each links to its source")
    for s in intel.signals:
        st.markdown(
            ui.signal_card_html(s.category, s.summary, s.confidence, s.provenance.source_url, s.provenance.method),
            unsafe_allow_html=True,
        )
    with st.expander(f"Collection activity log ({len(intel.sources)} Bright Data calls)"):
        st.markdown(ui.activity_html([p.model_dump() for p in intel.sources]), unsafe_allow_html=True)

    if intel.evidence_gaps:
        _section("Evidence gaps &mdash; verify before acting")
        st.markdown('<div class="mr-card">' + "".join(f"&bull; {g}<br>" for g in intel.evidence_gaps) + "</div>",
                    unsafe_allow_html=True)

    _section("Next actions &mdash; most urgent first")
    st.markdown('<div class="mr-card">' + "".join(f"{i}. {a}<br>" for i, a in enumerate(intel.next_actions, 1)) + "</div>",
                unsafe_allow_html=True)
    _render_crm(intel, domain_or_company)


def _render_crm(intel: AccountIntel, domain_or_company: str) -> None:
    _section("Agentic CRM action &mdash; what Recon writes to your CRM")
    st.caption("A sourced note + an urgent task + structured account fields. Judge-testable, no login. "
               "A thin/low-confidence run is gated to review-only. Live connector: HubSpot.")
    pkg = build_action_package(intel)
    st.markdown(
        ui.crm_card_html(intel.company, pkg.task.priority, pkg.task.subject, pkg.task.due_date, pkg.properties, pkg.caveat),
        unsafe_allow_html=True,
    )
    with st.expander("Sourced note that lands on the company timeline"):
        st.markdown(pkg.note_markdown)

    settings = Settings.load()
    byo = st.text_input("Push to your own CRM: paste a HubSpot private-app token (optional)", type="password",
                        key=f"byo_{intel.company}",
                        help="Blank = configured demo CRM (only when enabled). Paste your token to push to YOUR HubSpot.")
    can_markster = settings.push_enabled and settings.hubspot_ready
    if not (byo or can_markster):
        st.caption("Live push disabled here (preview only). Set RECON_ENABLE_PUSH=1 locally, or paste your token.")
    if st.button("Push to CRM (live)", disabled=not (byo or can_markster), key=f"push_{intel.company}"):
        from brightdata_gtm.hubspot import HubSpotClient, HubSpotError

        try:
            res = HubSpotClient(settings, token=byo or None).push(
                pkg, domain_or_company.strip().lower(), dry_run=False, create_if_missing=True)
            if res.get("error"):
                st.error(res["error"])
            else:
                st.success(f"Pushed to {res.get('company_name')}: note {res.get('note_id')}, task {res.get('task_id')}")
        except HubSpotError as e:
            st.error(str(e))


# ---- sidebar: global run controls ----
with st.sidebar:
    st.markdown('<div class="mr-eyebrow">Run controls</div>', unsafe_allow_html=True)
    location = st.text_input("Location (hiring signal)", value="United States")
    include_jobs = st.checkbox("Include LinkedIn jobs", value=True, help="Slower; uses the Web Scraper dataset.")
    deep = st.checkbox("Deep Lookup (funding)", value=False)
    _cfg = Settings.load()
    _labels = {"azure": "Azure OpenAI (GPT-5.5)", "aimlapi": "AI/ML API", "featherless": "Featherless (open-source)"}
    provider = st.selectbox("LLM provider", ["azure", "aimlapi", "featherless"],
                            format_func=lambda p: f"{_labels[p]}{'' if _cfg.provider_ready(p) else ' (not configured)'}")
    st.caption(f"OK - {_labels[provider]} ready" if _cfg.provider_ready(provider)
               else f"{_labels[provider]} not configured; deterministic fallback.")

tab_accounts, tab_lists, tab_settings = st.tabs(["  Accounts  ", "  Target Lists  ", "  Settings  "])

# ---- ACCOUNTS ----
with tab_accounts:
    st.markdown(ui.loop_html(), unsafe_allow_html=True)

    run_col, sample_col = st.columns([1.25, 1], gap="large")
    with run_col:
        _section("Run an account")
        company = st.text_input("Company name or domain", placeholder="stripe.com  /  Anthropic",
                                label_visibility="collapsed")
        run_live = st.button("Run Recon (live)", type="primary")
        st.caption("Pulls live signals via 6 Bright Data products, then synthesizes the plan.")
    with sample_col:
        _section("Instant samples")
        chosen_sample = None
        for dom in ["salesforce.com", "vercel.com", "nvidia.com"]:
            has = dom in SHOWCASE
            if st.button(dom if has else f"{dom} (live)", key=f"ex_{dom}", use_container_width=True):
                chosen_sample = dom
        st.caption("Real pre-run results - open instantly.")

    st.markdown('<div class="mr-divider"></div>', unsafe_allow_html=True)
    st.markdown(ui.value_preview_html(), unsafe_allow_html=True)

    if chosen_sample and chosen_sample in SHOWCASE:
        render_plan(AccountIntel.model_validate(SHOWCASE[chosen_sample]), chosen_sample, sample=True)
    elif chosen_sample or (run_live and company):
        target = chosen_sample or company
        with st.spinner(f"Pulling live signals via Bright Data for {target}..."):
            intel = AccountIntel.model_validate(run_recon(target, location, include_jobs, deep, provider))
        render_plan(intel, target)

# ---- TARGET LISTS ----
with tab_lists:
    _section("Target lists")
    st.markdown('<div class="mr-note">A <b>target list</b> is your set of priority accounts &mdash; the companies '
                "you want Recon to watch and keep CRM-ready. Recon scans every account, ranks them by confidence, and "
                "surfaces who to act on first. Edit the list below; it is yours to define.</div>",
                unsafe_allow_html=True)
    txt = st.text_area("Accounts in this list (one domain per line)",
                       value="\n".join(st.session_state["target_list"]), height=150)
    st.session_state["target_list"] = [ln.strip() for ln in txt.splitlines() if ln.strip()]
    tl = st.session_state["target_list"]
    st.caption(f"{len(tl)} accounts: " + " / ".join(tl))

    if st.button("Scan target list", type="primary"):
        from brightdata_gtm.watchlist import make_item

        out, prog = [], st.progress(0.0)
        for i, d in enumerate(tl):
            with st.spinner(f"Recon: {d} ..."):
                try:
                    out.append(make_item(d, run_recon(d, location, include_jobs, deep, provider)))
                except Exception as e:  # noqa: BLE001 - one bad account must not break the batch
                    out.append(make_item(d, error=e))
            prog.progress((i + 1) / len(tl))
        st.session_state["scan"] = out

    saved = st.session_state.get("scan", [])
    if saved:
        from brightdata_gtm.watchlist import rank_and_rest, summarize_row

        ranked, others = rank_and_rest(saved)
        _section("Ranked by confidence (act on the top first)")
        st.dataframe([summarize_row(i) for i in (ranked + others)], use_container_width=True)
        if ranked:
            labels = {f"{r['intel'].get('company')} ({r['domain']})": r for r in ranked}
            pick = st.selectbox("Open an account", list(labels.keys()))
            render_plan(AccountIntel.model_validate(labels[pick]["intel"]), labels[pick]["domain"])
        else:
            st.info("No accounts returned signals - see the status column.")

# ---- SETTINGS ----
with tab_settings:
    s = Settings.load()
    _section("Technology stack")
    st.caption("Every integration Recon runs on. Green = live this session.")
    cog_on = bool(os.getenv("COGNEE_API_KEY"))
    tech = [
        ("Bright Data", "6 products: Web Unlocker, Web Scraper, Browser, Discover, SERP, Deep Lookup",
         "live" if s.bd_token else "off", "live" if s.bd_token else "not configured"),
        ("Azure OpenAI - GPT-5.5", "Account Action Plan synthesis",
         "live" if s.provider_ready("azure") else "off", "ready" if s.provider_ready("azure") else "not configured"),
        ("AI/ML API", "Alternative LLM provider (partner)",
         "ready" if s.provider_ready("aimlapi") else "off", "ready" if s.provider_ready("aimlapi") else "not configured"),
        ("Featherless", "Open-source model inference (partner)",
         "ready" if s.provider_ready("featherless") else "off", "ready" if s.provider_ready("featherless") else "not configured"),
        ("HubSpot", "CRM connector: note + task + account fields",
         "live" if s.hubspot_ready else "off", "connected" if s.hubspot_ready else "not configured"),
        ("Speechmatics", "Voice query of an account (partner, optional)",
         "ready" if s.speechmatics_key else "off", "scaffold (key set)" if s.speechmatics_key else "not configured"),
        ("TriggerWare", "Fire an automation on a signal/action (partner, optional)",
         "ready" if s.triggerware_key else "off", "scaffold (key set)" if s.triggerware_key else "not configured"),
        ("Cognee", "Cross-run memory / change detection (partner)",
         "attempted" if cog_on else "off", "key rejected (wired)" if cog_on else "not configured"),
    ]
    st.markdown(ui.tech_stack_html(tech), unsafe_allow_html=True)

    _section("CRM connection")
    st.markdown('<div class="mr-note">Recon writes its action package to <b>your CRM</b>. The live connector here is '
                "<b>HubSpot</b> (company note + urgent task + structured account fields). Writes are gated: a public "
                "demo never writes to production unless <b>RECON_ENABLE_PUSH</b> is set, and anyone can paste their own "
                "token to push to their own CRM.</div>", unsafe_allow_html=True)
    st.caption(f"HubSpot token configured: {'yes' if s.hubspot_ready else 'no'} | "
               f"live push enabled here: {'yes' if s.push_enabled else 'no (preview only)'}")

    _section("Signal priorities")
    st.caption("These weights define how much each signal type moves the deterministic confidence score "
               "(confidence = coverage x signal strength). Tune them to your motion; they apply to results you open.")
    new_w = {}
    pcols = st.columns(2)
    for i, (cat, default) in enumerate(CATEGORY_WEIGHT.items()):
        with pcols[i % 2]:
            new_w[cat] = st.slider(cat, 0.0, 1.0, float(st.session_state["weights"].get(cat, default)), 0.05)
    st.session_state["weights"] = new_w
    if st.button("Reset priorities to default"):
        st.session_state["weights"] = dict(CATEGORY_WEIGHT)
        st.rerun()

st.markdown(
    '<div class="mr-foot">Built on <b>6 Bright Data products</b> &middot; <b>Azure GPT-5.5</b> / AI/ML API / Featherless '
    "&middot; CRM connector: <b>HubSpot</b> &middot; provenance on every signal &middot; deterministic confidence "
    "&middot; gated CRM writes. Markster runs GTM on this stack.</div>",
    unsafe_allow_html=True,
)
