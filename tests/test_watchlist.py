"""Tests for the watchlist transform: ok / empty / failed states + ranking."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from brightdata_gtm.watchlist import make_item, rank_and_rest, rankable, summarize_row  # noqa: E402


def test_ok_item():
    intel = {"company": "Vercel", "confidence": 0.82, "signals": [{"summary": "funding"}]}
    item = make_item("vercel.com", intel)
    assert item["status"] == "ok"
    row = summarize_row(item)
    assert row["account"] == "Vercel" and row["confidence"] == "82%" and row["signals"] == 1


def test_empty_item():
    item = make_item("nosignal.com", {"company": "NoSignal", "confidence": 0.1, "signals": []})
    assert item["status"] == "empty"
    assert summarize_row(item)["confidence"] == "-"


def test_failed_item():
    item = make_item("bad.com", error=RuntimeError("boom"))
    assert item["status"] == "failed" and item["intel"] is None
    row = summarize_row(item)
    assert row["account"] == "bad.com" and row["signals"] == 0


def test_rankable_only_keeps_ok():
    items = [
        make_item("a.com", {"company": "A", "confidence": 0.5, "signals": [{"summary": "x"}]}),
        make_item("b.com", {"company": "B", "confidence": 0.9, "signals": []}),  # empty
        make_item("c.com", error=RuntimeError("x")),  # failed
    ]
    keep = rankable(items)
    assert len(keep) == 1 and keep[0]["domain"] == "a.com"


def test_rank_and_rest_orders_and_isolates_bad():
    items = [
        make_item("a.com", {"company": "A", "confidence": 0.5, "signals": [{"summary": "x"}]}),
        make_item("d.com", {"company": "D", "confidence": 0.9, "signals": [{"summary": "y"}]}),
        make_item("b.com", {"company": "B", "confidence": 0.9, "signals": []}),  # empty
        make_item("c.com", error=RuntimeError("x")),  # failed
    ]
    ranked, others = rank_and_rest(items)
    assert [r["domain"] for r in ranked] == ["d.com", "a.com"]  # ok-only, conf desc
    assert {o["domain"] for o in others} == {"b.com", "c.com"}  # empty + failed isolated
