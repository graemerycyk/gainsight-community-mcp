"""HTTP client for the Gainsight Customer Communities (inSided) API."""

from __future__ import annotations

import os
import time
from typing import Any

import httpx

REGION_BASE_URLS = {
    "eu-west-1": "https://api2-eu-west-1.insided.com",
    "us-west-2": "https://api2-us-west-2.insided.com",
}

TOKEN_PATH = "/oauth2/token"


class GainsightClient:
    """Async client for the Gainsight Customer Communities API using OAuth2."""

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        region: str | None = None,
    ) -> None:
        self.client_id = client_id or os.environ["GS_CC_CLIENT_ID"]
        self.client_secret = client_secret or os.environ["GS_CC_CLIENT_SECRET"]
        self.region = region or os.environ.get("GS_CC_REGION", "eu-west-1")

        if self.region not in REGION_BASE_URLS:
            raise ValueError(
                f"Unknown region '{self.region}'. "
                f"Supported: {', '.join(REGION_BASE_URLS)}"
            )

        self.base_url = REGION_BASE_URLS[self.region]
        self._access_token: str | None = None
        self._token_expires_at: float = 0
        self._http = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)

    async def _ensure_token(self) -> None:
        """Obtain or refresh the OAuth2 access token."""
        if self._access_token and time.time() < self._token_expires_at:
            return

        resp = await self._http.post(
            TOKEN_PATH,
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        self._access_token = data["access_token"]
        # Refresh 60 s before actual expiry
        self._token_expires_at = time.time() + data.get("expires_in", 3600) - 60

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> Any:
        await self._ensure_token()
        resp = await self._http.request(
            method,
            path,
            params=params,
            headers={"Authorization": f"Bearer {self._access_token}"},
        )
        resp.raise_for_status()
        return resp.json()

    # ---- public helpers ----

    async def search(self, params: dict[str, Any]) -> Any:
        return await self._request("GET", "/api/v2/search", params=params)

    async def list_topics(self, params: dict[str, Any]) -> Any:
        return await self._request("GET", "/api/v2/topics", params=params)

    async def get_topic(self, topic_id: int) -> Any:
        return await self._request("GET", f"/api/v2/topics/{topic_id}")

    async def get_topic_replies(
        self, topic_id: int, params: dict[str, Any] | None = None
    ) -> Any:
        return await self._request(
            "GET", f"/api/v2/topics/{topic_id}/replies", params=params
        )

    async def list_categories(self, params: dict[str, Any] | None = None) -> Any:
        return await self._request("GET", "/api/v2/categories", params=params)

    async def close(self) -> None:
        await self._http.aclose()
