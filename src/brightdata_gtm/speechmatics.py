"""Speechmatics integration (optional, partner): voice -> text, so a rep can query an
account by speaking instead of typing.

Real client over the Speechmatics Batch API. Enabled only when SPEECHMATICS_API_KEY is set;
otherwise the app simply does not offer the voice input. Kept thin and self-contained so it
sits in front of the pipeline (audio -> company name -> normal Recon run) without touching it.
"""
from __future__ import annotations

import time

import requests

BASE = "https://asr.api.speechmatics.com/v2"


class SpeechmaticsError(RuntimeError):
    pass


class SpeechmaticsClient:
    def __init__(self, api_key: str, timeout: int = 30):
        if not api_key:
            raise SpeechmaticsError("No SPEECHMATICS_API_KEY set")
        self.http = requests.Session()
        self.http.headers.update({"Authorization": f"Bearer {api_key}"})
        self.timeout = timeout

    def transcribe(self, audio: bytes, filename: str = "query.wav", language: str = "en", max_wait: int = 60) -> str:
        """Submit audio to the Batch API, poll to completion, return the plain transcript."""
        config = (
            '{"type":"transcription","transcription_config":{"language":"%s","operating_point":"enhanced"}}' % language
        )
        files = {"data_file": (filename, audio), "config": (None, config)}
        r = self.http.post(f"{BASE}/jobs", files=files, timeout=self.timeout)
        if r.status_code >= 400:
            raise SpeechmaticsError(f"job submit {r.status_code}: {r.text[:200]}")
        job_id = r.json().get("id")
        if not job_id:
            raise SpeechmaticsError("no job id returned")
        waited = 0
        while waited < max_wait:
            g = self.http.get(f"{BASE}/jobs/{job_id}", timeout=self.timeout)
            status = (g.json().get("job", {}) or {}).get("status") if g.status_code < 400 else None
            if status == "done":
                t = self.http.get(f"{BASE}/jobs/{job_id}/transcript", params={"format": "txt"}, timeout=self.timeout)
                if t.status_code >= 400:
                    raise SpeechmaticsError(f"transcript {t.status_code}: {t.text[:200]}")
                return t.text.strip()
            if status in ("rejected", "deleted", "expired"):
                raise SpeechmaticsError(f"job {status}")
            time.sleep(3)
            waited += 3
        raise SpeechmaticsError("transcription timed out")
