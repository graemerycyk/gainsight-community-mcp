"""MCP server for Gainsight Customer Communities."""

from __future__ import annotations

import json
from typing import Any

import httpx
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
    page: int | None = None,
    page_size: int | None = None,
) -> str:
    """Search community content by keyword across all content types.

    Args:
        query: Search term (required).
        page: Page number for pagination (starts at 1).
        page_size: Results per page.
    """
    client = _get_client()
    params = _clean(
        {
            "q": query,
            "page": page,
            "pageSize": page_size,
        }
    )
    result = await client.search(params)
    return json.dumps(result, indent=2)


@mcp.tool()
async def list_topics(
    content_type: str | None = None,
    page: int | None = None,
    page_size: int | None = None,
) -> str:
    """List community topics, optionally filtered by content type.

    Use content_type to filter to a specific type. To list only ideas, questions,
    etc., prefer the dedicated endpoints (list_ideas, list_questions).

    Args:
        content_type: Filter to a single content type: article, conversation, question, idea, productUpdate. Uses the type-specific endpoint when set.
        page: Page number (starts at 1).
        page_size: Results per page.
    """
    client = _get_client()
    params = _clean({"page": page, "pageSize": page_size})

    # Use type-specific endpoints for proper filtering
    if content_type == "question":
        result = await client.list_questions(params)
    elif content_type == "conversation":
        result = await client.list_conversations(params)
    elif content_type == "article":
        result = await client.list_articles(params)
    elif content_type == "idea":
        result = await client.list_ideas(params)
    elif content_type == "productUpdate":
        result = await client.list_product_updates(params)
    else:
        result = await client.list_topics(params)

    return json.dumps(result, indent=2)


@mcp.tool()
async def get_topic(topic_id: int) -> str:
    """Retrieve full details for a specific topic, including body content and replies.

    Looks up the topic by ID to determine its content type, then fetches the
    full detail and replies from the type-specific endpoint.

    Args:
        topic_id: The numeric ID of the topic to retrieve.
    """
    client = _get_client()

    # Look up the topic to find its content type
    lookup = await client.get_topic_by_id(topic_id)
    results = lookup.get("result", [])
    if not results:
        return json.dumps({"error": f"Topic {topic_id} not found"})

    content_type = results[0]["contentType"]

    # Fetch full detail and replies using the type-specific endpoints
    topic = await client.get_topic_detail(content_type, topic_id)
    try:
        replies = await client.get_topic_replies(content_type, topic_id)
    except httpx.HTTPStatusError:
        replies = {"result": [], "_metadata": {"totalCount": 0}}
    topic["replies"] = replies

    return json.dumps(topic, indent=2)


@mcp.tool()
async def list_ideas(
    page: int | None = None,
    page_size: int | None = None,
) -> str:
    """List feature ideas/requests from the community.

    Args:
        page: Page number (starts at 1).
        page_size: Results per page.
    """
    client = _get_client()
    params = _clean({"page": page, "pageSize": page_size})
    result = await client.list_ideas(params)
    return json.dumps(result, indent=2)


@mcp.tool()
async def list_categories() -> str:
    """List all community categories with their IDs.

    Useful for discovering community structure.
    """
    client = _get_client()
    result = await client.list_categories()
    return json.dumps(result, indent=2)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
