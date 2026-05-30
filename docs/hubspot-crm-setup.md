---
id: hubspot-crm-setup
title: HubSpot CRM Setup for the GTM Demo
type: reference
status: active
owner: ivan
created: 2026-05-30
updated: 2026-05-30
tags: [hubspot, crm, gtm, demo, breeze]
---

# HubSpot CRM Setup for the GTM Demo

Status of the HubSpot CRM work backing the `brightdata-gtm-agent` demo.

- Portal: `145596685` (EU1, app-eu1.hubspot.com)
- Last updated: 2026-05-30
- Owner: Ivan

This document is the source of truth for what was changed in HubSpot, the record
IDs to reference from the agent, and the tasks that remain.

---

## 1. Demo target company set (17)

All 17 are deduped, correctly named, enriched (`hs_is_enriched=true`), flagged as
Target Accounts, ICP-tiered, in the demo list, and have one deal each in the demo
pipeline.

| Company | Domain | Category | HubSpot company id | ICP tier |
|---|---|---|---|---|
| Vercel | vercel.com | Mid-market | 333994765557 | tier_2 |
| Linear | linear.app | Mid-market | 332170430709 | tier_2 |
| Notion | notion.so | Mid-market | 431737314541 | tier_2 |
| Webflow | webflow.com | Mid-market | 275178588396 | tier_2 |
| Airtable | airtable.com | Mid-market | 431682353340 | tier_2 |
| Zapier | zapier.com | Mid-market | 260972483830 | tier_2 |
| Loom | loom.com | Mid-market | 431724146913 | tier_2 |
| ClickUp | clickup.com | Mid-market | 431735516371 | tier_2 |
| Microsoft | microsoft.com | F500 | 251160323284 | tier_1 |
| Amazon | amazon.com | F500 | 431733543156 | tier_1 |
| NVIDIA | nvidia.com | F500 | 431691330800 | tier_1 |
| Salesforce | salesforce.com | F500 | 288630295756 | tier_1 |
| Adobe | adobe.com | F500 | 333337093345 | tier_1 |
| Google | google.com | F500 | 332790528231 | tier_1 |
| Cisco | cisco.com | F500 | 253365808327 | tier_1 |
| Palo Alto Networks | paloaltonetworks.com | F500 | 282379652345 | tier_1 |
| IBM | ibm.com | F500 | 261062330612 | tier_1 |

NOTE: Amazon (431733543156) and NVIDIA (431691330800) got NEW canonical ids after
merges. Any agent config referencing the old ids (257535489253, 260990406844) must
be updated.

---

## 2. Event sponsor companies

Created and auto-enriched. Held in a separate "Event Sponsors" list, NOT in the GTM
target list or pipeline (sponsors are not sales targets).

| Company | Domain | HubSpot company id |
|---|---|---|
| Bright Data | brightdata.com | 431724348646 |
| lablab.ai | lablab.ai | 431685395677 |
| NativelyAI | nativelyai.com | 431735520494 |

Marked `type=PARTNER`.

---

## 3. What was done

### Dedup and naming
- Merged "NVIDIA GmbH" into "NVIDIA" (survivor 431691330800, 1 contact retained).
- Merged "StepHow" (an unrelated Korean company wrongly on amazon.com, 0 contacts)
  into the Amazon/AWS record at Ivan's explicit instruction (survivor 431733543156,
  16 contacts retained), then renamed to "Amazon".
- Renamed "Slack Technologies, Inc" to "Salesforce" (record was Salesforce all along;
  description, revenue, HQ confirmed).
- Renamed "U" to "Google".

### Created missing targets
- Notion, Airtable, Loom, ClickUp created and auto-enriched.

### Enrichment
- All 17 confirmed `hs_is_enriched=true` via Breeze auto-enrichment (free tier,
  populated from domain). The 9 F500 + Vercel carry annualrevenue; the 7 private
  mid-market companies carry total_money_raised (funding) instead of revenue, which
  is a Breeze data-availability limit, not a miss.
- Industry corrections Breeze would not overwrite:
  - Salesforce: WIRELESS to COMPUTER_SOFTWARE
  - Google: CONSUMER_GOODS to INTERNET
  - Amazon: ONLINE_MEDIA to INTERNET

### Target accounts and ICP
- All 17 flagged `hs_is_target_account=true`.
- ICP tiers set: 9 F500 = tier_1, 8 mid-market = tier_2.
- `gtm_source=brightdata-gtm-agent` stamped on all 17.

### Custom properties (repo to CRM loop)
Property group "GTM Intelligence" with 13 company properties mirroring the agent's
`AccountIntel` output schema:

`gtm_one_liner`, `gtm_why_now`, `gtm_recommended_action`, `gtm_confidence`,
`gtm_signal_count`, `gtm_hiring_signal`, `gtm_funding_signal`, `gtm_pricing_signal`,
`gtm_news_signal`, `gtm_top_source_url`, `gtm_llm_used`, `gtm_generated_at`,
`gtm_source`.

These are currently empty shells until the agent runs (see remaining tasks).

### Lists
- Static company list "BrightData GTM Demo - 17", listId `557`, 17 members.
- Static company list "Event Sponsors", listId `558`, 3 members.

### Pipeline
- Deal pipeline "BrightData GTM Demo", pipelineId `3857913073`.
- Stages and ids:
  - Signal Detected `5454677210`
  - Researched `5454677211`
  - Engaged `5454677212`
  - Demo Booked `5454677213`
  - Proposal `5454677214`
  - Closed Won `5454677215`
  - Closed Lost `5454677216`
- 17 deals created (one per target company) at "Signal Detected", associated to each
  company. Deal name pattern: "<Company> - GTM Demo".

### Contact cleanup
- Detached 11 mismatched contacts (corporate email domain did not match the
  associated company): KPMG, Klarna, OneTrust, RapidAPI, pickhacks, ethicalapparel
  on Amazon; dialexa, weschool, inkind on IBM; fictivekin on Microsoft.
- Reassigned 2 to the correct accounts: Tanner Godarzi (makenotion.com) to Notion,
  Jocelyne Wright-McLemore (zapier.com) to Zapier.
- Deleted 4 fake-persona contacts (archived, recoverable 90 days): fabricated CEOs
  and Founder on Amazon, IBM, Google, Zapier.
- Result: Amazon 16 to 10 contacts, Notion 0 to 1, Zapier 2 to 3.

---

## 4. Tasks that remain

### A. Enable Buyer Intent (HubSpot UI only, cannot be done by API)
Buyer Intent is read-only via API (returns READ_ONLY). It must be enabled in the
portal because it depends on the website tracking code and a per-user permission.

Verified path (from HubSpot KB, not memory):
1. Marketing > Buyer Intent > Configuration tab. Add a Market and add visitor intent
   criteria. Point monitoring at the "BrightData GTM Demo - 17" list or Target Accounts.
2. If "Buyer Intent" does not appear under Marketing: Settings > Users and Teams >
   your user > Access tab > Edit permissions > toggle "Buyer Intent" on > Save.
3. Prerequisite: HubSpot tracking code installed on the site (Configuration tab has a
   "Check Code Installation" button). Credits are already available on this portal.

Reference: https://knowledge.hubspot.com/reports/configure-buyer-intent

After enabling, re-read `hs_is_intent_monitored` and `hs_count_intent_signals_*` on
the 17 to confirm monitoring is live.

### B. Run the agent to populate the gtm_* fields for real
- Needs `BRIGHTDATA_API_TOKEN` (and optional Azure OpenAI vars) in the repo `.env`.
- Ivan to unlock the secrets vault and provide the token.
- Then run `python cli.py "<company>" --json` per target (or batch) and PATCH the
  output onto each company's `gtm_*` properties.
- Scope: 17 targets, optionally the 3 sponsors.

### C. Add the remaining event sponsors
- Only Bright Data, lablab.ai, and NativelyAI are added so far.
- Full sponsor list still needed. AI/ML API (aimlapi.com) is referenced in the repo
  `.env` as a partner and is a likely sponsor; confirm before adding.
- Decide sponsor treatment: keep as a separate Sponsors list (current), or give them
  the target-account and pipeline treatment.

### D. Optional follow-ups
- Consider a workflow that alerts when `gtm_*` signals update or intent fires.

---

## 5. Notes and limitations

- Breeze has three separate features sharing one credit pool: Enrichment (auto, ON),
  Buyer Intent (separate toggle, OFF until configured in UI), Form Shortening (n/a).
  Having credits auto-runs enrichment but does NOT auto-enable Buyer Intent.
- Buyer Intent surfaces companies based on first-party site visits (de-anonymized via
  the tracking code) plus intent criteria. It is not global third-party surveillance.
  The agent is the external-signal engine (hiring, funding, pricing, news); Buyer
  Intent is the first-party complement.
- HubSpot company merges can mint a new canonical id for the survivor. Always re-read
  the id after a merge.
