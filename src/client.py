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

# Maps content type names to their API path segments
CONTENT_TYPE_PATHS = {
    "article": "articles",
    "conversation": "conversations",
    "question": "questions",
    "idea": "ideas",
    "productUpdate": "productUpdates",
}


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
                "scope": "read",
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
            headers={
                "Authorization": f"Bearer {self._access_token}",
                "Accept": "*/*",
            },
        )
        resp.raise_for_status()
        return resp.json()

    # ---- public API methods ----

    async def search(self, params: dict[str, Any]) -> Any:
        """Search topics by keyword.  GET /v2/topics/search"""
        return await self._request("GET", "/v2/topics/search", params=params)

    async def list_topics(self, params: dict[str, Any]) -> Any:
        """List all topics.  GET /v2/topics"""
        return await self._request("GET", "/v2/topics", params=params)

    async def list_questions(self, params: dict[str, Any]) -> Any:
        """List questions.  GET /v2/questions"""
        return await self._request("GET", "/v2/questions", params=params)

    async def list_conversations(self, params: dict[str, Any]) -> Any:
        """List conversations.  GET /v2/conversations"""
        return await self._request("GET", "/v2/conversations", params=params)

    async def list_articles(self, params: dict[str, Any]) -> Any:
        """List articles.  GET /v2/articles"""
        return await self._request("GET", "/v2/articles", params=params)

    async def list_ideas(self, params: dict[str, Any]) -> Any:
        """List ideas.  GET /v2/ideas"""
        return await self._request("GET", "/v2/ideas", params=params)

    async def list_product_updates(self, params: dict[str, Any]) -> Any:
        """List product updates.  GET /v2/productUpdates"""
        return await self._request("GET", "/v2/productUpdates", params=params)

    async def get_topic_detail(self, content_type: str, topic_id: int) -> Any:
        """Get a single topic by content type and ID.

        GET /v2/{contentTypes}/{id}  (e.g. /v2/questions/42)
        """
        path_segment = CONTENT_TYPE_PATHS.get(content_type)
        if not path_segment:
            raise ValueError(
                f"Unknown content type '{content_type}'. "
                f"Supported: {', '.join(CONTENT_TYPE_PATHS)}"
            )
        return await self._request("GET", f"/v2/{path_segment}/{topic_id}")

    async def get_topic_replies(
        self, content_type: str, topic_id: int, params: dict[str, Any] | None = None
    ) -> Any:
        """Get replies for a topic.

        GET /v2/{contentTypes}/{id}/replies
        """
        path_segment = CONTENT_TYPE_PATHS.get(content_type)
        if not path_segment:
            raise ValueError(
                f"Unknown content type '{content_type}'. "
                f"Supported: {', '.join(CONTENT_TYPE_PATHS)}"
            )
        return await self._request(
            "GET", f"/v2/{path_segment}/{topic_id}/replies", params=params
        )

    async def get_topic_by_id(self, topic_id: int) -> Any:
        """Look up a topic by ID (any content type).  GET /v2/topics?id={id}"""
        return await self._request("GET", "/v2/topics", params={"id": topic_id})

    async def list_categories(self, params: dict[str, Any] | None = None) -> Any:
        """List categories.  GET /v2/categories"""
        return await self._request("GET", "/v2/categories", params=params)

    async def list_tags(self, params: dict[str, Any] | None = None) -> Any:
        """List tags.  GET /v2/tags"""
        return await self._request("GET", "/v2/tags", params=params)

    async def list_moderator_tags(self, params: dict[str, Any] | None = None) -> Any:
        """List moderator tags.  GET /v2/moderatorTags"""
        return await self._request("GET", "/v2/moderatorTags", params=params)

    async def get_category(self, category_id: int) -> Any:
        """Get a single category by ID.  GET /v2/categories/{id}"""
        return await self._request("GET", f"/v2/categories/{category_id}")

    async def get_category_tree(self) -> Any:
        """Get the full category hierarchy.  GET /v2/category/getTree"""
        return await self._request("GET", "/v2/category/getTree")

    async def get_category_topic_counts(self) -> Any:
        """Get visible topic counts per category.  GET /v2/categories/getVisibleTopicsCount"""
        return await self._request("GET", "/v2/categories/getVisibleTopicsCount")

    async def list_topics_by_category(
        self, category_id: int, params: dict[str, Any] | None = None
    ) -> Any:
        """List topics for a specific category.  GET /v2/categories/{id}/topics"""
        return await self._request(
            "GET", f"/v2/categories/{category_id}/topics", params=params
        )

    async def list_idea_statuses(self) -> Any:
        """List idea statuses.  GET /v2/ideas/ideaStatuses"""
        return await self._request("GET", "/v2/ideas/ideaStatuses")

    async def list_product_areas(self) -> Any:
        """List product areas.  GET /v2/productAreas"""
        return await self._request("GET", "/v2/productAreas")

    async def get_poll_results(self, content_type: str, topic_id: int) -> Any:
        """Get poll results for a topic.  GET /v2/{contentTypes}/{id}/poll"""
        path_segment = CONTENT_TYPE_PATHS.get(content_type)
        if not path_segment:
            raise ValueError(
                f"Unknown content type '{content_type}'. "
                f"Supported: {', '.join(CONTENT_TYPE_PATHS)}"
            )
        return await self._request("GET", f"/v2/{path_segment}/{topic_id}/poll")

    async def get_reply(
        self, content_type: str, topic_id: int, reply_id: int
    ) -> Any:
        """Get a single reply by ID.  GET /v2/{contentTypes}/{id}/replies/{replyId}"""
        path_segment = CONTENT_TYPE_PATHS.get(content_type)
        if not path_segment:
            raise ValueError(
                f"Unknown content type '{content_type}'. "
                f"Supported: {', '.join(CONTENT_TYPE_PATHS)}"
            )
        return await self._request(
            "GET", f"/v2/{path_segment}/{topic_id}/replies/{reply_id}"
        )

    async def close(self) -> None:
        await self._http.aclose()
