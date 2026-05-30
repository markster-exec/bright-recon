# MASTER_LOG - brightdata-gtm-agent

Historical log of repo-owned and demo-supporting work. Append after state changes.

## 2026-05-30

### [HubSpot CRM demo setup]

1. **Prepared the HubSpot CRM demo dataset (portal 145596685)**
   - Deduped, renamed, enriched, and tiered a 17-company GTM target set.
   - Merged 2 duplicate pairs (NVIDIA, Amazon), renamed 3 mislabeled records
     (Salesforce, Google, Amazon), created 4 missing targets (Notion, Airtable,
     Loom, ClickUp), corrected 3 wrong industries.
   - Flagged all 17 as Target Accounts with ICP tiers (9 tier_1, 8 tier_2).
   - Created 13 `gtm_*` company properties mirroring the agent output schema so the
     agent can write signals back to HubSpot.
   - Built list "BrightData GTM Demo - 17" (557) and pipeline "BrightData GTM Demo"
     (3857913073) with 17 deals.
   - Cleaned contacts: detached 11 mismatched, reassigned 2, deleted 4 fakes.
   - Added 3 sponsor companies (Bright Data, lablab.ai, NativelyAI) to "Event
     Sponsors" list (558).
   - Full detail and remaining tasks: `docs/hubspot-crm-setup.md`.
   - Remaining: enable Buyer Intent in HubSpot UI, run the agent to populate
     `gtm_*`, add the rest of the sponsors.
