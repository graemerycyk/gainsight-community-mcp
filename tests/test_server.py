"""Tests for the MCP server tools."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from src import server as server_module
from src.server import (
    search_community,
    list_topics,
    get_topic,
    list_ideas,
    list_categories,
)


@pytest.fixture(autouse=True)
def _reset_client() -> None:
    """Reset the module-level client between tests."""
    server_module._client = None


def _make_client_mock() -> AsyncMock:
    return AsyncMock()


@pytest.mark.asyncio
async def test_search_community() -> None:
    mock = _make_client_mock()
    mock.search.return_value = {"data": [{"id": 1}]}

    with patch.object(server_module, "_client", mock):
        result = json.loads(await search_community(query="SSO"))

    assert result["data"][0]["id"] == 1
    mock.search.assert_called_once_with({"q": "SSO"})


@pytest.mark.asyncio
async def test_search_community_with_filters() -> None:
    mock = _make_client_mock()
    mock.search.return_value = {"data": []}

    with patch.object(server_module, "_client", mock):
        result = json.loads(
            await search_community(
                query="api",
                content_types=["question", "article"],
                tags="api,rest",
                sort="createdAt",
                page=2,
                page_size=10,
            )
        )

    assert result == {"data": []}
    mock.search.assert_called_once_with(
        {
            "q": "api",
            "content_types": "question,article",
            "tags": "api,rest",
            "sort": "createdAt",
            "page": 2,
            "page_size": 10,
        }
    )


@pytest.mark.asyncio
async def test_list_topics_tool() -> None:
    mock = _make_client_mock()
    mock.list_topics.return_value = {"data": [{"id": 5}]}

    with patch.object(server_module, "_client", mock):
        result = json.loads(await list_topics(content_types=["question"]))

    assert result["data"][0]["id"] == 5
    mock.list_topics.assert_called_once()


@pytest.mark.asyncio
async def test_get_topic_tool() -> None:
    mock = _make_client_mock()
    mock.get_topic.return_value = {"id": 42, "title": "Test topic"}
    mock.get_topic_replies.return_value = {"data": [{"id": 100, "body": "Reply"}]}

    with patch.object(server_module, "_client", mock):
        result = json.loads(await get_topic(topic_id=42))

    assert result["id"] == 42
    assert result["replies"]["data"][0]["id"] == 100
    mock.get_topic.assert_called_once_with(42)
    mock.get_topic_replies.assert_called_once_with(42)


@pytest.mark.asyncio
async def test_list_ideas_tool() -> None:
    mock = _make_client_mock()
    mock.list_topics.return_value = {"data": [{"id": 7, "type": "idea"}]}

    with patch.object(server_module, "_client", mock):
        result = json.loads(await list_ideas(sort="voteCount"))

    assert result["data"][0]["type"] == "idea"
    call_params = mock.list_topics.call_args[0][0]
    assert call_params["content_types"] == "idea"
    assert call_params["sort"] == "voteCount"


@pytest.mark.asyncio
async def test_list_categories_tool() -> None:
    mock = _make_client_mock()
    mock.list_categories.return_value = {"data": [{"id": 1, "name": "General"}]}

    with patch.object(server_module, "_client", mock):
        result = json.loads(await list_categories())

    assert result["data"][0]["name"] == "General"
