# STATE - brightdata-gtm-agent

**Repo:** tools/brightdata-gtm-agent (markster-exec, public)
**Purpose:** Hackathon project - Web Data UNLOCKED (Bright Data x lablab.ai), Track 1 GTM Intelligence.
**Event:** Onsite, The Web Data Loft, 625 2nd St, San Francisco. May 30-31, 2026.
**Submission cutoff:** 2026-05-30 17:00 PDT (confirm onsite). Submit on lablab.ai.

## What this is
Live GTM-intelligence agent. Input a company (name/domain); it pulls live web
signals via Bright Data (SERP API + Web Unlocker + Web Scraper datasets) and an
LLM synthesizes a structured GTM Signal Brief.

## Stack
- Python, Pydantic, requests
- Bright Data REST (/request for SERP + Web Unlocker; datasets v3 for Web Scraper)
- LLM switch: Anthropic Claude (default) or AI/ML API (partner, prize-eligible)
- Demo: Streamlit (`app.py`) + CLI (`cli.py`)

## Status: SCAFFOLD COMPLETE
- [x] Repo structure, README, MIT LICENSE, .env.example
- [x] Bright Data client, LLM layer, agent orchestration, models
- [x] CLI + Streamlit demo
- [ ] Redeem Bright Data $250 credits (promo `unlocked`), create SERP + Web Unlocker zones
- [ ] Fill .env, smoke-test against a real company
- [ ] Lock the concept / differentiator (current build is a generic skeleton)
- [ ] Record demo video + slides
- [ ] Submit on lablab.ai (public repo URL + demo URL + video + slides)

## Submission requirements (lablab.ai)
Title, short + long description, tags, cover image, video presentation, slides,
public GitHub repo, demo app + URL. MUST demonstrably use >=1 Bright Data product.
MIT-compliant (done).
