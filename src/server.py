"""MCP server for Gainsight Customer Communities."""

from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from .client import GainsightClient

mcp = FastMCP(
    "Gainsight Customer Communities",
    instructions=(
        "Search and retrieve content from Gainsight Customer Communities "
        "(formerly inSided)."
    ),
)

_client: GainsightClient | None = None


def _get_client() -> GainsightClient:
    global _client
    if _client is None:
        _client = GainsightClient()
    return _client


def _clean(params: dict[str, Any]) -> dict[str, Any]:
    """Remove None values so they are not sent as query params."""
    return {k: v for k, v in params.items() if v is not None}


# ---------- Tools ----------


@mcp.tool()
async def search_community(
    query: str,
    content_types: list[str] | None = None,
    tags: str | None = None,
    sort: str | None = None,
    page: int | None = None,
    page_size: int | None = None,
) -> str:
    """Search community content by keyword across all content types.

    Args:
        query: Search term (required).
        content_types: Filter by content type(s): article, conversation, question, idea, productUpdate.
        tags: Comma-separated public tags to filter by.
        sort: Sort field: lastActivityAt, createdAt, likes, voteCount, replyCount.
        page: Page number for pagination.
        page_size: Results per page (1-100).
    """
    client = _get_client()
    params = _clean(
        {
            "q": query,
            "content_types": ",".join(content_types) if content_types else None,
            "tags": tags,
            "sort": sort,
            "page": page,
            "page_size": page_size,
        }
    )
    result = await client.search(params)
    return json.dumps(result, indent=2)


@mcp.tool()
async def list_topics(
    content_types: list[str] | None = None,
    category_ids: list[str] | None = None,
    tags: str | None = None,
    moderator_tags: str | None = None,
    sort: str | None = None,
    created_after: str | None = None,
    created_before: str | None = None,
    page: int | None = None,
    page_size: int | None = None,
) -> str:
    """List and filter community topics with rich filtering options.

    Args:
        content_types: Filter by content type(s): article, conversation, question, idea, productUpdate.
        category_ids: Filter by category ID(s).
        tags: Comma-separated public tags.
        moderator_tags: Comma-separated moderator tags.
        sort: Sort field.
        created_after: ISO date string, e.g. "2025-01-01".
        created_before: ISO date string.
        page: Page number.
        page_size: Results per page (1-100).
    """
    client = _get_client()
    params = _clean(
        {
            "content_types": ",".join(content_types) if content_types else None,
            "category_ids": ",".join(category_ids) if category_ids else None,
            "tags": tags,
            "moderator_tags": moderator_tags,
            "sort": sort,
            "created_after": created_after,
            "created_before": created_before,
            "page": page,
            "page_size": page_size,
        }
    )
    result = await client.list_topics(params)
    return json.dumps(result, indent=2)


@mcp.tool()
async def get_topic(topic_id: int) -> str:
    """Retrieve full details for a specific topic, including body content and replies.

    Args:
        topic_id: The numeric ID of the topic to retrieve.
    """
    client = _get_client()
    topic = await client.get_topic(topic_id)
    replies = await client.get_topic_replies(topic_id)
    topic["replies"] = replies
    return json.dumps(topic, indent=2)


@mcp.tool()
async def list_ideas(
    sort: str | None = None,
    tags: str | None = None,
    created_after: str | None = None,
    created_before: str | None = None,
    page: int | None = None,
    page_size: int | None = None,
) -> str:
    """List feature ideas/requests, sorted by votes or activity.

    Convenience wrapper that filters topics to ideas only.

    Args:
        sort: Sort field, e.g. voteCount, createdAt, lastActivityAt.
        tags: Comma-separated public tags.
        created_after: ISO date string.
        created_before: ISO date string.
        page: Page number.
        page_size: Results per page (1-100).
    """
    client = _get_client()
    params = _clean(
        {
            "content_types": "idea",
            "sort": sort,
            "tags": tags,
            "created_after": created_after,
            "created_before": created_before,
            "page": page,
            "page_size": page_size,
        }
    )
    result = await client.list_topics(params)
    return json.dumps(result, indent=2)


@mcp.tool()
async def list_categories(
    page: int | None = None,
    page_size: int | None = None,
) -> str:
    """List all community categories with their IDs.

    Useful for discovering community structure and obtaining category IDs
    for filtering topics.

    Args:
        page: Page number.
        page_size: Results per page.
    """
    client = _get_client()
    params = _clean(
        {
            "page": page,
            "page_size": page_size,
        }
    )
    result = await client.list_categories(params)
    return json.dumps(result, indent=2)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
