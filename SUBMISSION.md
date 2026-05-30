# Submission - Web Data UNLOCKED (Track 1: GTM Intelligence)

Paste-ready content for lablab.ai. Team leader submits by 5:00 PM PDT.

## Project title
Markster Recon - the live web -> CRM intelligence loop for GTM teams

## Short description
Point Markster Recon at any company and it produces an enterprise-grade Account Action Plan from live web signals via 6 Bright Data products - then lands agentic actions in the CRM: a sourced note + an urgent task in HubSpot, where an AI agent executes (or prioritizes the rep's queue). Every claim links to its source.

## Long description
GTM teams act on stale CRM data. The signals that say "reach out now" - hiring surges, funding, pricing/positioning shifts, competitor moves - live on the open web, scattered and bot-walled.

Markster Recon turns that live web into a decision, end to end:
- Collects in parallel via 6 Bright Data products: LinkedIn hiring (Web Scraper API, discover_new), news + funding (Web Unlocker + Google News RSS), competitor landscape (Discover API), structured market results (SERP API), JS-rendered pricing (Browser API), and structured funding research (Deep Lookup).
- Tags every datum with provenance (source URL + timestamp + method).
- Scores deterministically (coverage x signal strength) - not the LLM's guess.
- Synthesizes (Azure OpenAI GPT-5.5) an Account Action Plan: the read, terrain, routes to enter, who shapes the decision (names validated against the sources), evidence gaps (honest), next actions.
- Lands it as agentic CRM action: enriched company properties + a sourced note + an urgent task in HubSpot, where an AI agent executes or prioritizes for the rep.

Enterprise-grade by design: uniform provenance, deterministic confidence, a gated CRM write (a thin/low-confidence run is downgraded to "review only" and can never look like an approved action), and it runs on a real production CRM. Built by a team that runs GTM on this stack.

## Technology tags (tag ALL)
Bright Data Web Unlocker, Bright Data Web Scraper API, Bright Data Browser API, Bright Data Discover API, Bright Data Deep Lookup, Bright Data SERP API, HubSpot, Azure OpenAI, GPT-5.5, Python, Playwright, Streamlit, Pydantic

## Bright Data products used (6 - requirement: >=1)
Web Unlocker, Web Scraper API (datasets), Browser API (Scraping Browser), Discover API, Deep Lookup, SERP API.

## The 3-minute demo (script)
1. (0:00-0:25) Watchlist - mid-market SaaS + enterprise (Linear, Notion, Webflow, Vercel, Salesforce, NVIDIA). "Every GTM team runs a target list; their CRM on these is stale."
2. (0:25-0:50) Run watchlist -> 6 Bright Data products fire; ranked-by-confidence table; the top account surfaces.
3. (0:50-1:40) Drill in -> the Account Action Plan. Click a source link live (provenance). Read the why-now + next action.
4. (1:40-2:20) CRM action package preview - note + urgent task + fields. "Judge-testable, no login."
5. (2:20-2:45) Push to HubSpot (live) -> the note lands on the timeline + an urgent task in the queue for an AI agent / rep. (Optional: a judge pastes their own token to push to theirs.)
6. (2:45-3:00) "Live web -> CRM -> agent action, built by a team that runs GTM on this CRM. Markster Recon."

## Judge-testable
Any company -> a full Account Action Plan + a preview of the CRM actions, no login. Live push is gated (RECON_ENABLE_PUSH) so the public app can't write to our prod; a judge can paste their own HubSpot token to push to their own instance.

## Run it
- CLI: `python cli.py "salesforce.com" --crm` (add `--deep`, `--push-hubspot [--hubspot-live]`)
- Demo: `streamlit run app.py` (Single account + Watchlist modes)
- Config via `.env` (see `.env.example`): Bright Data token + zones, Azure OpenAI, HubSpot token.

## Slide outline
1. Title + one-liner  2. Problem (stale CRM)  3. Solution (web->CRM->agent loop)  4. Architecture (6 BD products -> provenance -> confidence -> GPT-5.5 -> CRM/agent)  5. Live Account Action Plan screenshot (sources visible)  6. Differentiator (provenance + deterministic confidence + real production CRM + agent action)  7. Business value  8. Team / what's next.

## Cover image concept
Dark hero (Markster brand: near-black + brand green #00FF01, Plus Jakarta Sans). A company name flowing into labeled live signals (hiring/funding/competitor/pricing/news) that converge into one "Account Action Plan" card, then an arrow into a CRM with a glowing task. Tagline: "Live web intelligence that acts in your CRM."

## Submission checklist (team leader, by 5pm)
- [ ] Flip the repo to public.
- [ ] Deploy the demo -> public URL (Streamlit Community Cloud).
- [ ] Record the 3-min video (script above).
- [ ] Build slides + cover image.
- [ ] Submit on the lablab team page; tag every technology above.

## Deploy (Streamlit Community Cloud)
1. share.streamlit.io -> New app -> point at this repo, `app.py`.
2. Add secrets (Settings -> Secrets) as env: BRIGHTDATA_API_TOKEN, BRIGHTDATA_*_ZONE, AZURE_OPENAI_* , (optional HUBSPOT_ACCESS_TOKEN). Do NOT set RECON_ENABLE_PUSH on the public app (keeps prod CRM safe; judges use preview / BYO-token).
3. For stage reliability: pre-run the watchlist once (results cache for an hour).
