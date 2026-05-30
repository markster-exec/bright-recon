"""Bright Data collection adapter with uniform provenance (Phase 1).

One thin client over Bright Data:
- Web Unlocker (/request) for live page + SERP fetch
- Web Scraper API datasets (LinkedIn Jobs, discover_new) for hiring signal

Every method returns content plus a Provenance record (source URL, timestamp, method).
"""
from __future__ import annotations

import json
import re
import time
import urllib.parse
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any

import requests

from .config import Settings
from .models import Provenance, now_iso

REQUEST_URL = "https://api.brightdata.com/request"
DATASET_TRIGGER = "https://api.brightdata.com/datasets/v3/trigger"
DATASET_SNAPSHOT = "https://api.brightdata.com/datasets/v3/snapshot"


def strip_html(html: str) -> str:
    """Crude HTML -> visible text for feeding pages to the LLM."""
    html = re.sub(r"(?is)<(script|style|noscript|svg|head).*?</\1>", " ", html)
    text = re.sub(r"(?s)<[^>]+>", " ", html)
    text = re.sub(r"&[a-z]+;", " ", text)
    return re.sub(r"\s+", " ", text).strip()


class BrightDataError(RuntimeError):
    pass


@dataclass
class Collected:
    content: str
    provenance: Provenance


class BrightDataClient:
    def __init__(self, settings: Settings, timeout: int = 60):
        self.s = settings
        self.timeout = timeout
        self.http = requests.Session()
        self.http.headers.update(
            {"Authorization": f"Bearer {settings.bd_token}", "Content-Type": "application/json"}
        )

    # --- Web Unlocker (/request) ---

    def _request(self, zone: str, url: str, fmt: str = "raw") -> str:
        r = self.http.post(REQUEST_URL, json={"zone": zone, "url": url, "format": fmt}, timeout=self.timeout)
        if r.status_code >= 400:
            raise BrightDataError(f"Bright Data /request {r.status_code}: {r.text[:300]}")
        return r.text

    def fetch_page(self, url: str) -> Collected:
        content = self._request(self.s.bd_unlocker_zone, url, "raw")
        return Collected(
            content,
            Provenance(source_url=url, captured_at=now_iso(), method=f"brightdata:web_unlocker:{self.s.bd_unlocker_zone}"),
        )

    def fetch_text(self, url: str) -> Collected:
        """Fetch a page via Web Unlocker and return cleaned visible text."""
        content = self._request(self.s.bd_unlocker_zone, url, "raw")
        return Collected(
            strip_html(content),
            Provenance(source_url=url, captured_at=now_iso(), method=f"brightdata:web_unlocker:{self.s.bd_unlocker_zone}"),
        )

    def fetch_rendered(self, url: str, wait_ms: int = 2500) -> Collected:
        """Render a JS-heavy page via Bright Data Browser API (Scraping Browser) over CDP.

        Connects Playwright to Bright Data's hosted browser (no local chromium needed),
        so SPAs (Stripe, HubSpot) return real text the unlocker cannot.
        """
        from playwright.sync_api import sync_playwright

        if not self.s.bd_browser_cdp:
            raise BrightDataError("BRIGHTDATA_BROWSER_CDP not set")
        try:
            with sync_playwright() as p:
                browser = p.chromium.connect_over_cdp(self.s.bd_browser_cdp, timeout=120000)
                try:
                    page = browser.new_page()
                    page.goto(url, timeout=90000, wait_until="domcontentloaded")
                    page.wait_for_timeout(wait_ms)
                    text = page.inner_text("body")
                finally:
                    browser.close()
        except BrightDataError:
            raise
        except Exception as e:  # never surface the CDP string (it embeds the zone password)
            msg = str(e).replace(self.s.bd_browser_cdp, "<cdp-redacted>")
            raise BrightDataError(f"browser_api render failed for {url}: {msg[:200]}")
        return Collected(
            re.sub(r"\s+", " ", text or "").strip(),
            Provenance(source_url=url, captured_at=now_iso(), method="brightdata:browser_api:scraping_browser"),
        )

    def search(self, query: str, num: int = 10) -> Collected:
        """Live SERP via Web Unlocker against Google (no dedicated SERP zone required)."""
        q = urllib.parse.quote_plus(query)
        url = f"https://www.google.com/search?q={q}&num={num}"
        content = self._request(self.s.bd_unlocker_zone, url, "raw")
        return Collected(
            content, Provenance(source_url=url, captured_at=now_iso(), method="brightdata:web_unlocker:serp")
        )

    def news(self, query: str, max_items: int = 8):
        """Recent news via Google News RSS through Web Unlocker. Returns (items, Provenance).

        Each item: {title, link, pubDate}. RSS is clean and parseable, unlike raw SERP HTML.
        """
        url = (
            "https://news.google.com/rss/search?q="
            + urllib.parse.quote_plus(query)
            + "&hl=en-US&gl=US&ceid=US:en"
        )
        raw = self._request(self.s.bd_unlocker_zone, url, "raw")
        items = self._parse_rss(raw, max_items)
        prov = Provenance(
            source_url=url, captured_at=now_iso(), method="brightdata:web_unlocker:google_news_rss"
        )
        return items, prov

    @staticmethod
    def _parse_rss(raw: str, max_items: int) -> list[dict[str, str]]:
        items: list[dict[str, str]] = []
        try:
            root = ET.fromstring(raw.strip())
        except ET.ParseError:
            return items
        for it in root.iter("item"):
            title = (it.findtext("title") or "").strip()
            if not title:
                continue
            items.append(
                {
                    "title": title,
                    "link": (it.findtext("link") or "").strip(),
                    "pubDate": (it.findtext("pubDate") or "").strip(),
                }
            )
            if len(items) >= max_items:
                break
        return items

    # --- Discover API (AI-ranked URL discovery; token-only, no zone) ---

    def discover(self, query: str, num_results: int = 8, max_wait: int = 40):
        """Trigger Discover, poll for results. Returns (results, Provenance).

        results: list of {link, title, description}.
        """
        r = self.http.post(
            "https://api.brightdata.com/discover", json={"query": query, "num_results": num_results}, timeout=self.timeout
        )
        if r.status_code >= 400:
            raise BrightDataError(f"discover {r.status_code}: {r.text[:200]}")
        try:
            task_id = r.json().get("task_id")
        except ValueError:
            raise BrightDataError("discover: non-JSON trigger response")
        if not task_id:
            raise BrightDataError("discover: no task_id")
        waited = 0
        while waited < max_wait:
            g = self.http.get("https://api.brightdata.com/discover", params={"task_id": task_id}, timeout=self.timeout)
            if g.status_code < 400:
                try:
                    d = g.json()
                except ValueError:
                    d = {}
                status = d.get("status")
                if status in ("error", "failed"):
                    raise BrightDataError(f"discover: task {status}")
                if status == "done":
                    prov = Provenance(
                        source_url=f"brightdata://discover?q={urllib.parse.quote_plus(query)}",
                        captured_at=now_iso(),
                        method="brightdata:discover_api",
                    )
                    return d.get("results") or [], prov
            time.sleep(4)
            waited += 4
        raise BrightDataError("discover: timed out")

    # --- SERP API (structured Google results; needs a SERP zone) ---

    def serp(self, query: str, num: int = 10):
        """Parsed Google results via SERP API (brd_json). Returns (organic_results, Provenance)."""
        q = urllib.parse.quote_plus(query)
        target = f"https://www.google.com/search?q={q}&num={num}&brd_json=1"
        raw = self._request(self.s.bd_serp_zone, target, "raw")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            raise BrightDataError("serp: non-JSON response (zone may not be a SERP zone)")
        if not isinstance(data, dict):
            raise BrightDataError("serp: unexpected JSON shape")
        organic = data.get("organic") or data.get("organic_results") or []
        prov = Provenance(
            source_url=f"https://www.google.com/search?q={q}", captured_at=now_iso(), method="brightdata:serp_api"
        )
        return organic, prov

    # --- Deep Lookup API (AI structured research; token-only, async) ---

    def deep_lookup(self, prompt: str, max_wait: int = 90):
        """Run a Deep Lookup preview and return (sample_rows, columns, Provenance)."""
        if not prompt.lower().startswith("find all"):
            prompt = "Find all " + prompt
        base = "https://api.brightdata.com/datasets/deep_lookup/v1"
        r = self.http.post(f"{base}/preview", json={"query": prompt}, timeout=self.timeout)
        if r.status_code >= 400:
            raise BrightDataError(f"deep_lookup {r.status_code}: {r.text[:200]}")
        try:
            preview_id = r.json().get("preview_id")
        except ValueError:
            raise BrightDataError("deep_lookup: non-JSON preview response")
        if not preview_id:
            raise BrightDataError("deep_lookup: no preview_id")
        waited = 0
        while waited < max_wait:
            g = self.http.get(f"{base}/preview/{preview_id}", timeout=self.timeout)
            if g.status_code < 400:
                try:
                    d = g.json()
                except ValueError:
                    d = {}
                if d.get("status") in ("error", "failed"):
                    raise BrightDataError(f"deep_lookup: {d.get('status')}")
                if d.get("status") == "done" or d.get("sample_data"):
                    prov = Provenance(
                        source_url=f"brightdata://deep_lookup/{preview_id}",
                        captured_at=now_iso(),
                        method="brightdata:deep_lookup",
                    )
                    return d.get("sample_data", []), d.get("columns", []), prov
            time.sleep(6)
            waited += 6
        raise BrightDataError("deep_lookup: timed out")

    # --- Web Scraper API datasets (LinkedIn Jobs, discover_new) ---

    def linkedin_jobs(self, company: str, location: str = "United States", limit: int = 25):
        """Trigger + poll the LinkedIn Jobs dataset. Returns (job_records, Provenance)."""
        params = {
            "dataset_id": self.s.bd_linkedin_jobs_dataset,
            "type": "discover_new",
            "discover_by": "keyword",
            "limit_per_input": str(limit),
            "include_errors": "true",
            "format": "json",
        }
        r = self.http.post(
            DATASET_TRIGGER, params=params, json=[{"company": company, "location": location}], timeout=self.timeout
        )
        if r.status_code >= 400:
            raise BrightDataError(f"Bright Data dataset trigger {r.status_code}: {r.text[:300]}")
        snapshot_id = r.json().get("snapshot_id", "")
        records = self._poll(snapshot_id)
        jobs = [j for j in records if isinstance(j, dict) and j.get("job_title")]
        prov = Provenance(
            source_url=f"https://www.linkedin.com/jobs/search/?keywords={urllib.parse.quote_plus(company)}",
            captured_at=now_iso(),
            method="brightdata:web_scraper:linkedin_jobs",
        )
        return jobs, prov

    def _poll(self, snapshot_id: str, poll_seconds: int = 8, max_polls: int = 24) -> list[dict[str, Any]]:
        url = f"{DATASET_SNAPSHOT}/{snapshot_id}"
        for _ in range(max_polls):
            r = self.http.get(url, params={"format": "json"}, timeout=self.timeout)
            if r.status_code == 202:
                time.sleep(poll_seconds)
                continue
            if r.status_code >= 400:
                raise BrightDataError(f"Bright Data snapshot {r.status_code}: {r.text[:300]}")
            return r.json()
        raise BrightDataError(f"Snapshot {snapshot_id} not ready after {max_polls} polls.")
