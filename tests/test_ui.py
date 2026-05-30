"""Tests for the pure UI builders (no Streamlit needed)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from brightdata_gtm import ui  # noqa: E402


def test_products_fired_maps_methods_to_products():
    methods = [
        "brightdata:web_unlocker:google_news_rss",
        "brightdata:web_scraper:linkedin_jobs",
        "brightdata:serp_api",
        "brightdata:discover_api",
    ]
    fired = ui.products_fired(methods)
    assert {"web_unlocker", "web_scraper", "serp_api", "discover"} <= fired
    assert "browser_api" not in fired  # did not fire
    assert "deep_lookup" not in fired


def test_loop_html_lights_fired_products_only():
    html = ui.loop_html(fired={"serp_api"}, lit_stages={"synthesis"})
    assert "SERP API" in html
    assert "mr-chip on" in html  # at least one lit chip
    assert "GPT-5.5 Plan" in html


def test_confidence_html_clamps_and_colors():
    assert "95%" in ui.confidence_html(0.95)
    assert ui.GREEN in ui.confidence_html(0.8)  # high -> brand green
    assert "0%" in ui.confidence_html(-1.0)  # clamped


def test_signal_card_escapes_and_links():
    html = ui.signal_card_html("hiring", "12 roles <script>", 0.72, "https://x/y", "brightdata:test")
    assert "&lt;script&gt;" in html  # escaped
    assert 'href="https://x/y"' in html
    assert "hiring" in html


def test_crm_card_renders_gate_and_props():
    html = ui.crm_card_html("ACME", "HIGH", "do it", "2026-05-31", {"gtm_confidence": "0.7"}, "")
    assert "do it" in html and "gtm_confidence" in html
    gated = ui.crm_card_html("ACME", "LOW", "review", "2026-05-31", {}, "low confidence")
    assert "low confidence" in gated
