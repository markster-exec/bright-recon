"""Markster-branded UI building blocks for the Streamlit demo.

Pure string/HTML builders (no Streamlit import) so the brand layer is testable and
app.py stays readable. Brand tokens: markster.ai/brand-kit - dark hero + green accents,
Plus Jakarta Sans.
"""
from __future__ import annotations

import html

GREEN = "#00FF01"
GREEN_UI = "#00CC44"
GREEN_LABEL = "#00A84D"
BG = "#0a0a0a"

# The 6 Bright Data products, in collection order. Key = substring of the provenance method.
PRODUCTS: list[tuple[str, str]] = [
    ("web_unlocker", "Web Unlocker"),
    ("web_scraper", "Web Scraper API"),
    ("browser_api", "Browser API"),
    ("discover", "Discover API"),
    ("serp_api", "SERP API"),
    ("deep_lookup", "Deep Lookup"),
]

# Downstream stages of the loop, after collection.
STAGES: list[tuple[str, str]] = [
    ("provenance", "Provenance"),
    ("confidence", "Confidence"),
    ("synthesis", "GPT-5.5 Plan"),
    ("crm", "CRM Action"),
    ("agent", "Agent"),
]


def products_fired(methods: list[str]) -> set[str]:
    """Which Bright Data products actually fired this run, from the provenance methods."""
    blob = " ".join(methods).lower()
    return {key for key, _ in PRODUCTS if key in blob}


BRAND_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

:root {{
  --green: {GREEN}; --green-ui: {GREEN_UI}; --green-label: {GREEN_LABEL};
  --bg: {BG}; --panel: #121417; --panel2: #16191e; --line: #23262d;
  --text: #e8e8ea; --muted: #9aa0aa; --white: #fff;
}}

html, body, [class*="css"], .stApp, .stMarkdown, button, input, textarea, select {{
  font-family: 'Plus Jakarta Sans', sans-serif !important;
}}
.stApp {{ background: var(--bg); color: var(--text); }}
[data-testid="stHeader"] {{ background: transparent; }}
#MainMenu, footer {{ visibility: hidden; }}
[data-testid="stSidebar"] {{ background: #0c0e11; border-right: 1px solid var(--line); }}
.block-container {{ padding-top: 1.3rem; max-width: 1280px; }}

/* eyebrow + headings */
.mr-eyebrow {{ color: var(--green-label); font-weight: 700; letter-spacing: .18em;
  text-transform: uppercase; font-size: .72rem; margin-bottom: .35rem; }}
.mr-h1 {{ font-weight: 800; letter-spacing: -0.03em; font-size: 1.85rem; line-height: 1.0;
  color: var(--white); margin: 0; display:inline-block; }}
.mr-h1 .dot {{ color: var(--green); }}
.mr-sub {{ color: var(--muted); font-size: .9rem; max-width: 860px; margin-top: 4px; }}
.mr-section {{ color: var(--white); font-weight: 700; font-size: 1.0rem; letter-spacing: -0.01em;
  margin: 1.2rem 0 .5rem 0; }}

/* loop diagram */
.mr-loop {{ border: 1px solid var(--line); background: linear-gradient(180deg,#101317,#0b0d10);
  border-radius: 16px; padding: 16px 18px; margin: .6rem 0 .2rem 0; }}
.mr-loop-label {{ color: var(--muted); font-size: .7rem; letter-spacing: .16em; text-transform: uppercase;
  font-weight: 700; margin-bottom: 10px; }}
.mr-chips {{ display: flex; flex-wrap: wrap; gap: 8px; }}
.mr-chip {{ border: 1px solid var(--line); border-radius: 999px; padding: 6px 13px; font-size: .8rem;
  font-weight: 600; color: var(--muted); background: #0e1115; }}
.mr-chip.on {{ color: #04140a; background: var(--green); border-color: var(--green);
  box-shadow: 0 0 18px rgba(0,255,1,.25); }}
.mr-flow {{ display: flex; align-items: center; flex-wrap: wrap; gap: 6px; margin-top: 14px;
  padding-top: 14px; border-top: 1px dashed var(--line); }}
.mr-stage {{ font-size: .76rem; font-weight: 700; color: var(--text); background: #0e1115;
  border: 1px solid var(--line); border-radius: 8px; padding: 6px 11px; }}
.mr-stage.lit {{ color: var(--green); border-color: rgba(0,255,1,.4); }}
.mr-arrow {{ color: var(--green-ui); font-weight: 800; }}

/* cards */
.mr-card {{ border: 1px solid var(--line); background: var(--panel); border-radius: 14px;
  padding: 16px 18px; margin-bottom: 12px; }}
.mr-oneliner {{ color: var(--white); font-weight: 600; font-size: 1.1rem; }}

/* confidence bar */
.mr-conf-wrap {{ margin: 6px 0 2px 0; }}
.mr-conf-top {{ display:flex; justify-content: space-between; align-items: baseline; }}
.mr-conf-num {{ font-weight: 800; font-size: 1.5rem; color: var(--white); }}
.mr-conf-cap {{ color: var(--muted); font-size: .78rem; }}
.mr-conf-track {{ height: 9px; border-radius: 999px; background: #1b1f25; overflow: hidden; margin-top: 6px; }}
.mr-conf-fill {{ height: 100%; border-radius: 999px; }}

/* signal rows */
.mr-signal {{ border: 1px solid var(--line); border-left: 3px solid var(--green-ui); background: var(--panel2);
  border-radius: 10px; padding: 11px 14px; margin-bottom: 9px; }}
.mr-signal-head {{ display: flex; align-items: center; gap: 10px; }}
.mr-pill {{ font-size: .66rem; font-weight: 800; letter-spacing: .08em; text-transform: uppercase;
  color: var(--green); border: 1px solid rgba(0,255,1,.35); border-radius: 6px; padding: 2px 8px; }}
.mr-sig-conf {{ color: var(--muted); font-size: .74rem; margin-left: auto; }}
.mr-sig-sum {{ color: var(--text); margin: 6px 0 4px 0; font-size: .92rem; }}
.mr-src {{ font-size: .74rem; }}
.mr-src a {{ color: var(--green-ui); text-decoration: none; }}
.mr-src a:hover {{ text-decoration: underline; }}
.mr-src .method {{ color: #5d636d; }}

/* CRM action */
.mr-task {{ display:flex; align-items:center; gap:10px; }}
.mr-prio {{ font-size:.66rem; font-weight:800; letter-spacing:.06em; border-radius:6px; padding:2px 8px; }}
.mr-prio.HIGH {{ color:#04140a; background:var(--green); }}
.mr-prio.MEDIUM {{ color:#1a1400; background:#e7b400; }}
.mr-prio.LOW {{ color:#e8e8ea; background:#3a3f47; }}
.mr-kv {{ display:grid; grid-template-columns: 200px 1fr; gap:4px 14px; margin-top:8px; font-size:.82rem; }}
.mr-kv .k {{ color: var(--green-label); font-weight:600; }}
.mr-kv .v {{ color: var(--text); }}
.mr-gate {{ border:1px solid #6b4a00; background:#1c1500; color:#ffd75e; border-radius:10px;
  padding:10px 13px; font-size:.85rem; margin-bottom:10px; }}

/* button system: ghost (secondary) by default, solid green for the primary CTA only */
.stButton > button {{ border-radius:10px; padding:.5rem 1.05rem; font-weight:600; transition: all .14s; }}
.stButton > button[kind="secondary"], .stButton > button:not([kind]) {{
  background:#0e1115; color:var(--text); border:1px solid var(--line); }}
.stButton > button[kind="secondary"]:hover {{ border-color: var(--green-ui); color:#fff; background:#12161b; }}
.stButton > button[kind="primary"] {{ background: var(--green-ui); color:#04140a; border:0; font-weight:700; }}
.stButton > button[kind="primary"]:hover {{ background: var(--green); }}
.stTextInput input, .stTextArea textarea {{ background:#0e1115 !important; border:1px solid var(--line) !important;
  color: var(--text) !important; }}

/* tabs as real nav */
[data-baseweb="tab-list"] {{ gap: 4px; border-bottom:1px solid var(--line); margin-bottom: 6px; }}
[data-baseweb="tab"] {{ font-weight:700 !important; font-size:.92rem !important; color: var(--muted) !important;
  padding: 8px 16px !important; }}
[data-baseweb="tab"][aria-selected="true"] {{ color: var(--white) !important; }}
[data-baseweb="tab-highlight"] {{ background: var(--green) !important; height:3px !important; }}
.mr-foot {{ color:#5d636d; font-size:.74rem; margin-top:2rem; border-top:1px solid var(--line); padding-top:10px; }}
.mr-foot b {{ color: var(--muted); }}

/* hero glow + stat pills */
.mr-hero {{ position: relative; border-bottom:1px solid var(--line); padding-bottom:12px; margin-bottom:4px; }}
.mr-hero::before {{ content:""; position:absolute; left:-30px; top:-14px; width:240px; height:90px;
  background: radial-gradient(circle at left, rgba(0,255,1,.10), transparent 70%); pointer-events:none; z-index:0; }}
.mr-hero > * {{ position: relative; z-index:1; }}
.mr-herotop {{ display:flex; align-items:center; justify-content:space-between; gap:16px; flex-wrap:wrap; }}
.mr-stats {{ display:flex; flex-wrap:wrap; gap:7px; }}
.mr-stat {{ font-size:.73rem; font-weight:600; color:var(--text); background:#0e1115;
  border:1px solid var(--line); border-radius:999px; padding:5px 11px; }}
.mr-stat b {{ color: var(--green); font-weight:800; }}

/* lit loop glow */
.mr-loop {{ position: relative; }}
.mr-loop.live {{ border-color: rgba(0,255,1,.35); box-shadow: 0 0 40px rgba(0,255,1,.06) inset; }}

/* value preview strip */
.mr-divider {{ height:1px; background:linear-gradient(90deg,transparent,var(--line),transparent); margin:18px 0 6px; }}
.mr-prev {{ display:grid; grid-template-columns: repeat(3,1fr); gap:12px; }}
.mr-prev-card {{ border:1px solid var(--line); border-radius:12px; padding:13px 14px 14px;
  background:linear-gradient(180deg,#111418,#0c0e11); transition: border-color .15s, transform .15s; }}
.mr-prev-card:hover {{ border-color: rgba(0,255,1,.4); transform: translateY(-2px); }}
.mr-prev-step {{ color:var(--green-label); font-weight:800; font-size:.72rem; letter-spacing:.12em; }}
.mr-prev-h {{ color:var(--white); font-weight:700; font-size:1.02rem; margin:6px 0 6px; }}
.mr-prev-b {{ color:var(--muted); font-size:.85rem; line-height:1.4; }}
.mr-prev-card .tag {{ display:inline-block; margin-top:10px; font-size:.7rem; color:var(--green);
  border:1px solid rgba(0,255,1,.3); border-radius:6px; padding:2px 8px; }}

/* tech / sponsor stack */
.mr-stack {{ display:grid; grid-template-columns: repeat(2,1fr); gap:10px; }}
.mr-tech {{ border:1px solid var(--line); border-radius:12px; padding:13px 15px; background:var(--panel);
  display:flex; align-items:flex-start; gap:11px; }}
.mr-tech .dot {{ width:9px; height:9px; border-radius:50%; margin-top:5px; flex:0 0 auto; }}
.mr-tech .dot.live {{ background:var(--green); box-shadow:0 0 10px rgba(0,255,1,.5); }}
.mr-tech .dot.ready {{ background:#00CC44; }}
.mr-tech .dot.attempted {{ background:#e7b400; }}
.mr-tech .dot.off {{ background:#4a4f57; }}
.mr-tech .name {{ color:var(--white); font-weight:700; font-size:.92rem; }}
.mr-tech .role {{ color:var(--muted); font-size:.8rem; margin-top:2px; }}
.mr-tech .status {{ font-size:.68rem; font-weight:700; letter-spacing:.04em; text-transform:uppercase; margin-top:4px; }}
.mr-tech .status.live {{ color:var(--green); }}
.mr-tech .status.ready {{ color:#00CC44; }}
.mr-tech .status.attempted {{ color:#e7b400; }}
.mr-tech .status.off {{ color:#6b7280; }}
.mr-note {{ color:var(--muted); font-size:.84rem; background:var(--panel); border:1px solid var(--line);
  border-radius:10px; padding:11px 14px; }}
.mr-note b {{ color: var(--text); }}
.mr-badge {{ display:inline-block; font-size:.66rem; font-weight:800; letter-spacing:.06em; color:#04140a;
  background:var(--green); border-radius:6px; padding:2px 8px; text-transform:uppercase; }}
</style>
"""


def header_html() -> str:
    stats = "".join(
        f'<span class="mr-stat">{s}</span>'
        for s in (
            "<b>6</b>&nbsp;Bright Data products",
            "Every signal&nbsp;<b>sourced</b>",
            "<b>Deterministic</b>&nbsp;confidence",
            "Writes to&nbsp;<b>your CRM</b>",
        )
    )
    return (
        '<div class="mr-hero">'
        '<div class="mr-herotop">'
        '<div><div class="mr-eyebrow">Markster &middot; Web Data UNLOCKED &middot; Track 1</div>'
        '<div class="mr-h1">Markster Recon<span class="dot">.</span></div></div>'
        f'<div class="mr-stats">{stats}</div>'
        "</div>"
        '<div class="mr-sub">The signals that say <b style="color:#e8e8ea">reach out now</b> &mdash; '
        "hiring, funding, pricing shifts, competitor moves &mdash; live on the bot-walled open web, not in your CRM. "
        "Recon pulls them live via 6 Bright Data products, sources every datum, scores confidence "
        "deterministically, and lands an agentic action plan in your CRM.</div>"
        "</div>"
    )


def value_preview_html() -> str:
    """A 'what you get' strip so the payoff is visible before the judge runs anything."""
    cards = [
        ("01 · COLLECT", "Live web, 6 ways",
         "LinkedIn hiring, funding &amp; news, competitor landscape, JS-rendered pricing, structured "
         "research &mdash; in parallel, each tagged with its source URL + timestamp.", "Bright Data"),
        ("02 · DECIDE", "An Account Action Plan",
         "Why-now, terrain, routes in, who shapes the decision (names checked against the sources), "
         "honest evidence gaps, next moves &mdash; with a deterministic confidence score.", "GPT-5.5"),
        ("03 · ACT", "Agentic CRM action",
         "A sourced note + an urgent task + structured fields land on the company in your CRM, where an "
         "AI agent executes or prioritizes. Thin runs are gated to review-only.", "HubSpot live"),
    ]
    body = "".join(
        f'<div class="mr-prev-card"><div class="mr-prev-step">{step}</div>'
        f'<div class="mr-prev-h">{h}</div><div class="mr-prev-b">{b}</div>'
        f'<span class="tag">{tag}</span></div>'
        for step, h, b, tag in cards
    )
    return f'<div class="mr-prev">{body}</div>'


def loop_html(fired: set[str] | None = None, lit_stages: set[str] | None = None) -> str:
    fired = fired or set()
    lit_stages = lit_stages or set()
    chips = "".join(
        f'<span class="mr-chip {"on" if key in fired else ""}">{html.escape(label)}</span>'
        for key, label in PRODUCTS
    )
    flow_parts = []
    for i, (key, label) in enumerate(STAGES):
        if i:
            flow_parts.append('<span class="mr-arrow">&rarr;</span>')
        flow_parts.append(f'<span class="mr-stage {"lit" if key in lit_stages else ""}">{html.escape(label)}</span>')
    flow = "".join(flow_parts)
    live = " live" if fired else ""
    return (
        f'<div class="mr-loop{live}">'
        '<div class="mr-loop-label">Live web &mdash; 6 Bright Data products</div>'
        f'<div class="mr-chips">{chips}</div>'
        f'<div class="mr-flow">{flow}</div>'
        "</div>"
    )


def _conf_color(conf: float) -> str:
    if conf >= 0.6:
        return GREEN
    if conf >= 0.35:
        return "#e7b400"
    return "#c0392b"


def confidence_html(conf: float) -> str:
    pct = max(0, min(100, round(conf * 100)))
    color = _conf_color(conf)
    return (
        '<div class="mr-conf-wrap"><div class="mr-conf-top">'
        f'<span class="mr-conf-num">{pct}%</span>'
        '<span class="mr-conf-cap">deterministic &middot; coverage &times; signal strength</span>'
        '</div><div class="mr-conf-track">'
        f'<div class="mr-conf-fill" style="width:{pct}%;background:{color};"></div>'
        "</div></div>"
    )


def signal_card_html(category: str, summary: str, confidence: float, source_url: str, method: str) -> str:
    safe_url = html.escape(source_url, quote=True)
    return (
        '<div class="mr-signal"><div class="mr-signal-head">'
        f'<span class="mr-pill">{html.escape(category)}</span>'
        f'<span class="mr-sig-conf">{round(confidence * 100)}% signal</span></div>'
        f'<div class="mr-sig-sum">{html.escape(summary)}</div>'
        f'<div class="mr-src">&#128279; <a href="{safe_url}" target="_blank">{html.escape(source_url[:90])}</a>'
        f'<span class="method"> &nbsp;&middot;&nbsp; {html.escape(method)}</span></div></div>'
    )


def activity_html(sources: list[dict]) -> str:
    """A compact 'what fired' activity log from the provenance records."""
    rows = []
    for s in sources:
        method = s.get("method", "")
        url = s.get("source_url", "")
        rows.append(
            f'<div class="mr-src" style="margin:4px 0;">'
            f'<span style="color:{GREEN_UI};">&#10003;</span> '
            f'<span class="method">{html.escape(method)}</span> &nbsp; '
            f'<a href="{html.escape(url, quote=True)}" target="_blank">{html.escape(url[:70])}</a></div>'
        )
    return f'<div class="mr-card">{"".join(rows) or "No sources collected."}</div>'


def tech_stack_html(items: list[tuple[str, str, str, str]]) -> str:
    """items: (name, role, status, status_label). status in {live, ready, attempted, off}."""
    cards = "".join(
        f'<div class="mr-tech"><span class="dot {st}"></span><div>'
        f'<div class="name">{html.escape(name)}</div>'
        f'<div class="role">{html.escape(role)}</div>'
        f'<div class="status {st}">{html.escape(label)}</div></div></div>'
        for name, role, st, label in items
    )
    return f'<div class="mr-stack">{cards}</div>'


def crm_card_html(company: str, priority: str, subject: str, due_date: str, properties: dict, caveat: str) -> str:
    prio = priority if priority in ("HIGH", "MEDIUM", "LOW") else "LOW"
    gate = f'<div class="mr-gate">&#9888;&#65039; {html.escape(caveat)}</div>' if caveat else ""
    kv = "".join(
        f'<div class="k">{html.escape(k)}</div><div class="v">{html.escape(str(v)[:160])}</div>'
        for k, v in properties.items()
        if v
    )
    return (
        f'<div class="mr-card">{gate}'
        '<div class="mr-task">'
        f'<span class="mr-prio {prio}">{prio}</span>'
        f'<span style="font-weight:600;color:#fff;">{html.escape(subject)}</span></div>'
        f'<div class="mr-conf-cap" style="margin-top:6px;">Urgent task &middot; suggested due {html.escape(due_date)} '
        f'&middot; lands on the {html.escape(company)} timeline in HubSpot</div>'
        f'<div class="mr-kv">{kv}</div></div>'
    )
