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


async def test_search_community() -> None:
    mock = _make_client_mock()
    mock.search.return_value = {"result": [{"id": "1"}]}

    with patch.object(server_module, "_client", mock):
        result = json.loads(await search_community(query="SSO"))

    assert result["result"][0]["id"] == "1"
    mock.search.assert_called_once_with({"q": "SSO"})


async def test_search_community_with_pagination() -> None:
    mock = _make_client_mock()
    mock.search.return_value = {"result": []}

    with patch.object(server_module, "_client", mock):
        result = json.loads(
            await search_community(query="api", page=2, page_size=10)
        )

    assert result == {"result": []}
    mock.search.assert_called_once_with({"q": "api", "page": 2, "pageSize": 10})


async def test_list_topics_no_filter() -> None:
    mock = _make_client_mock()
    mock.list_topics.return_value = {"result": [{"id": "5"}]}

    with patch.object(server_module, "_client", mock):
        result = json.loads(await list_topics())

    assert result["result"][0]["id"] == "5"
    mock.list_topics.assert_called_once()


async def test_list_topics_filtered_by_question() -> None:
    mock = _make_client_mock()
    mock.list_questions.return_value = {"result": [{"contentType": "question"}]}

    with patch.object(server_module, "_client", mock):
        result = json.loads(await list_topics(content_type="question"))

    assert result["result"][0]["contentType"] == "question"
    mock.list_questions.assert_called_once()


async def test_list_topics_filtered_by_article() -> None:
    mock = _make_client_mock()
    mock.list_articles.return_value = {"result": [{"contentType": "article"}]}

    with patch.object(server_module, "_client", mock):
        result = json.loads(await list_topics(content_type="article"))

    mock.list_articles.assert_called_once()


async def test_get_topic_tool() -> None:
    mock = _make_client_mock()
    mock.get_topic_by_id.return_value = {
        "result": [{"id": "42", "contentType": "question"}]
    }
    mock.get_topic_detail.return_value = {
        "id": "42",
        "title": "Test topic",
        "contentType": "question",
    }
    mock.get_topic_replies.return_value = {
        "result": [{"id": "100", "body": "Reply"}],
        "_metadata": {"totalCount": 1},
    }

    with patch.object(server_module, "_client", mock):
        result = json.loads(await get_topic(topic_id=42))

    assert result["id"] == "42"
    assert result["replies"]["result"][0]["id"] == "100"
    mock.get_topic_by_id.assert_called_once_with(42)
    mock.get_topic_detail.assert_called_once_with("question", 42)
    mock.get_topic_replies.assert_called_once_with("question", 42)


async def test_get_topic_not_found() -> None:
    mock = _make_client_mock()
    mock.get_topic_by_id.return_value = {"result": []}

    with patch.object(server_module, "_client", mock):
        result = json.loads(await get_topic(topic_id=9999))

    assert "error" in result


async def test_list_ideas_tool() -> None:
    mock = _make_client_mock()
    mock.list_ideas.return_value = {"result": [{"id": "7", "contentType": "idea"}]}

    with patch.object(server_module, "_client", mock):
        result = json.loads(await list_ideas())

    assert result["result"][0]["contentType"] == "idea"
    mock.list_ideas.assert_called_once()


async def test_list_categories_tool() -> None:
    mock = _make_client_mock()
    mock.list_categories.return_value = {
        "result": [{"id": "1", "name": "General"}]
    }

    with patch.object(server_module, "_client", mock):
        result = json.loads(await list_categories())

    assert result["result"][0]["name"] == "General"
