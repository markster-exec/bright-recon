# Markster Recon

**The live web -> CRM intelligence loop for GTM teams.**
Web Data UNLOCKED Hackathon (Bright Data x lablab.ai) - Track 1: GTM Intelligence.

> Point Recon at any company. It pulls live signals via **6 Bright Data products**, tags
> every datum with provenance, scores confidence deterministically, synthesizes an
> enterprise-grade **Account Action Plan** (Azure GPT-5.5), and lands an **agentic action**
> in your CRM (HubSpot): a sourced note + an urgent task + structured `gtm_*` fields, where
> an AI agent executes or prioritizes. Every claim links to its source.

**Live demo:** point at any company, or open the pre-baked samples (Salesforce, Vercel,
NVIDIA) for an instant, real result. Export any plan to PDF. Run a whole **Target List**.

---

## The loop

```
input (company / domain)
   -> Bright Data collection (6 products, in parallel)  ->  Signals + Provenance
   -> deterministic confidence (coverage x signal strength)   (computed, not the LLM)
   -> synthesis (Azure GPT-5.5 / AI-ML API / Featherless)  ->  Account Action Plan
   -> agentic CRM action (HubSpot: note + task + gtm_* fields, gated)
   -> [optional] event egress (TriggerWare), cross-run memory (Cognee), voice in (Speechmatics)
```

**Honesty is the differentiator:** uniform provenance on every signal; confidence is
deterministic, not a model guess; `who_decides` names are validated against the sources
(unsourced names are flagged); and a thin/low-confidence run is gated to "review only" so it
can never look like an approved CRM action.

---

## Partners & technologies - what each does, and why it matters here

### Bright Data (core - 6 products)
The entire live-web collection layer. Each product covers a signal the others cannot, and
every call returns content **plus a provenance record** (source URL + timestamp + method).

| Product | Use case in Recon | Why it is the right tool |
|---|---|---|
| **Web Unlocker** | Fetch bot-walled news, funding press, homepages; Google News RSS | Gets through bot walls / geo-blocks where a plain fetch fails |
| **Web Scraper API** (datasets) | LinkedIn hiring signal via the Jobs dataset (`discover_new`) | Structured hiring intelligence (velocity, departments, seniority) without scraping LinkedIn yourself |
| **Browser API** (Scraping Browser, CDP) | JS-rendered pricing pages (SPAs like Stripe/Vercel) | Renders client-side pricing the unlocker can't see, over remote CDP - no local browser |
| **Discover API** | Competitor / alternative landscape | AI-ranked URL discovery for "who competes with X" |
| **SERP API** | Structured Google results (news/pricing/market) | Parsed, machine-readable SERP instead of brittle HTML |
| **Deep Lookup** | Structured funding research (`--deep`) | Async AI research that returns rows + columns, not prose |

### Azure OpenAI - GPT-5.5 (synthesis)
Turns the sourced signals into the Account Action Plan (the read, terrain, routes,
who-decides, evidence gaps, next actions). **The model only writes narrative - it never
invents a signal or a source**; the real provenance-tagged signals pass through untouched.

### HubSpot (agentic CRM, live)
The action layer. Recon finds the company by domain and writes a sourced **note** + an urgent
**task** + 13 structured `gtm_*` company fields (the GTM Intelligence property group), where a
HubSpot AI agent / rep executes or prioritizes. Writes are **gated**: a public demo never
writes to production unless `RECON_ENABLE_PUSH` is set, and anyone can paste their own token to
push to their own CRM. (CRM is connector-agnostic by design; HubSpot is the live connector.)

### AI/ML API (partner - LLM provider)
Drop-in alternative synthesis provider (OpenAI-compatible). Selectable in the UI. Proves the
plan is **provider-portable**: the same sourced plan regardless of model vendor.

### Featherless (partner - open-source inference)
Alternative provider running **open-source models** (OpenAI-compatible). Shows Recon works on
OSS inference, not just frontier APIs - same provenance contract.

### Speechmatics (partner - voice, optional)
`speechmatics.py`: a Batch-API client for **voice query of an account** (speak a company name
instead of typing). Sits in front of the pipeline; enabled when `SPEECHMATICS_API_KEY` is set.

### TriggerWare (partner - event egress, optional)
`triggerware.py`: fires a structured **account-actionable event** to a configured endpoint
after the CRM action, wiring "what changed -> do something" (alert/workflow). Enabled when
`TRIGGERWARE_API_KEY` + `TRIGGERWARE_WEBHOOK_URL` are set.

### Cognee (partner - cross-run memory)
`memory.py`: cross-run **change detection** ("what changed since last run" - confidence moves,
new/dropped signal categories, lead-story shifts). Local store works out of the box; the Cognee
cloud adapter mirrors snapshots when a valid key authenticates.

---

## Run it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # fill in your keys

streamlit run app.py                        # the app (Accounts / Target Lists / Settings)
python cli.py "salesforce.com" --crm        # CLI: plan + CRM action package preview
python cli.py "vercel.com" --push-hubspot --hubspot-live   # write to HubSpot
```

`LLM_PROVIDER=azure|aimlapi|featherless`. See `.env.example` for all settings.

## License

MIT - see [LICENSE](LICENSE).
