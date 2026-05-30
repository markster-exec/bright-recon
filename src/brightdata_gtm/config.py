"""Environment-backed configuration (Phase 1)."""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv(override=True)


@dataclass(frozen=True)
class Settings:
    # Bright Data
    bd_token: str
    bd_unlocker_zone: str
    bd_serp_zone: str
    bd_linkedin_jobs_dataset: str
    bd_browser_cdp: str

    # LLM
    provider: str
    azure_endpoint: str
    azure_key: str
    azure_deployment: str
    azure_api_version: str
    aimlapi_key: str
    aimlapi_base_url: str
    aimlapi_model: str
    featherless_key: str
    featherless_base_url: str
    featherless_model: str

    # Partner integrations (optional)
    speechmatics_key: str
    triggerware_key: str
    triggerware_webhook_url: str

    # HubSpot (live agentic CRM push)
    hubspot_token: str

    @classmethod
    def load(cls) -> "Settings":
        token = os.getenv("BRIGHTDATA_API_TOKEN", "").strip()
        if not token:
            raise RuntimeError("Missing BRIGHTDATA_API_TOKEN. Copy .env.example to .env and fill it in.")
        return cls(
            bd_token=token,
            bd_unlocker_zone=os.getenv("BRIGHTDATA_UNLOCKER_ZONE", "web_unlocker"),
            bd_serp_zone=os.getenv("BRIGHTDATA_SERP_ZONE", "serp_api"),
            bd_linkedin_jobs_dataset=os.getenv("BRIGHTDATA_LINKEDIN_JOBS_DATASET", "gd_lpfll7v5hcqtkxl6l"),
            bd_browser_cdp=os.getenv("BRIGHTDATA_BROWSER_CDP", ""),
            provider=os.getenv("LLM_PROVIDER", "azure").lower(),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "").rstrip("/"),
            azure_key=os.getenv("AZURE_OPENAI_API_KEY", ""),
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", ""),
            azure_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21"),
            aimlapi_key=os.getenv("AIMLAPI_KEY", ""),
            aimlapi_base_url=os.getenv("AIMLAPI_BASE_URL", "https://api.aimlapi.com/v1"),
            aimlapi_model=os.getenv("AIMLAPI_MODEL", "gpt-4o"),
            featherless_key=os.getenv("FEATHERLESS_API_KEY", ""),
            featherless_base_url=os.getenv("FEATHERLESS_BASE_URL", "https://api.featherless.ai/v1"),
            featherless_model=os.getenv("FEATHERLESS_MODEL", "mistralai/Mistral-7B-Instruct-v0.3"),
            speechmatics_key=os.getenv("SPEECHMATICS_API_KEY", ""),
            triggerware_key=os.getenv("TRIGGERWARE_API_KEY", ""),
            triggerware_webhook_url=os.getenv("TRIGGERWARE_WEBHOOK_URL", ""),
            hubspot_token=os.getenv("HUBSPOT_ACCESS_TOKEN") or os.getenv("MARKSTER_HS_TOKEN", ""),
        )

    @property
    def hubspot_ready(self) -> bool:
        return bool(self.hubspot_token)

    @property
    def push_enabled(self) -> bool:
        # live writes to the configured (Markster) HubSpot only when explicitly enabled,
        # so the public demo cannot let anyone write to our production CRM.
        return os.getenv("RECON_ENABLE_PUSH", "").lower() in ("1", "true", "yes")

    @property
    def browser_ready(self) -> bool:
        return bool(self.bd_browser_cdp)

    def provider_ready(self, name: str) -> bool:
        """Is a specific LLM provider fully configured? (used to show a clear disabled/
        fallback state in the UI instead of failing only at call time)."""
        if name == "azure":
            return bool(self.azure_endpoint and self.azure_key and self.azure_deployment)
        if name == "aimlapi":
            return bool(self.aimlapi_key)
        if name == "featherless":
            return bool(self.featherless_key)
        return False

    @property
    def llm_ready(self) -> bool:
        return self.provider_ready(self.provider)
