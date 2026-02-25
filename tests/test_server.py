"""Tests for the MCP server tools."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from src import server as server_module
from src.server import (
    search_community,
    search_tags,
    list_topics,
    get_topic,
    list_ideas,
    list_categories,
    list_tags,
    get_category,
    get_category_tree,
    get_category_topic_counts,
    list_topics_by_category,
    list_idea_statuses,
    list_product_areas,
    get_poll_results,
    get_reply,
    get_community_info,
)


@pytest.fixture(autouse=True)
def _reset_client() -> None:
    """Reset the module-level client between tests."""
    server_module._client = None


def _make_client_mock() -> AsyncMock:
    mock = AsyncMock()
    mock.community_url = None
    return mock


# ---- search_community ----


async def test_search_community() -> None:
    mock = _make_client_mock()
    mock.search.return_value = {"community": [{"id": "1"}]}

    with patch.object(server_module, "_client", mock):
        result = json.loads(await search_community(query="SSO"))

    assert result["community"][0]["id"] == "1"
    mock.search.assert_called_once_with({"q": "SSO"})


async def test_search_community_with_pagination() -> None:
    mock = _make_client_mock()
    mock.search.return_value = {"community": []}

    with patch.object(server_module, "_client", mock):
        result = json.loads(await search_community(query="api", page=2))

    assert result == {"community": []}
    mock.search.assert_called_once_with({"q": "api", "page": 2})


async def test_search_community_with_filters() -> None:
    mock = _make_client_mock()
    mock.search.return_value = {"community": [{"id": "2", "contentType": "question"}]}

    with patch.object(server_module, "_client", mock):
        result = json.loads(
            await search_community(
                query="SSO",
                category_ids="1,2",
                content_types="question",
                tags="api,sso",
                moderator_tags="internal",
                has_answer=True,
            )
        )

    assert result["community"][0]["contentType"] == "question"
    call_params = mock.search.call_args[0][0]
    assert call_params["q"] == "SSO"
    assert call_params["categoryIds"] == "1,2"
    assert call_params["contentTypes"] == "question"
    assert call_params["tags"] == "api,sso"
    assert call_params["moderatorTags"] == "internal"
    assert call_params["hasAnswer"] is True


async def test_search_community_none_filters_excluded() -> None:
    mock = _make_client_mock()
    mock.search.return_value = {"community": []}

    with patch.object(server_module, "_client", mock):
        await search_community(query="test")

    call_params = mock.search.call_args[0][0]
    assert "categoryIds" not in call_params
    assert "contentTypes" not in call_params
    assert "tags" not in call_params
    assert "hasAnswer" not in call_params


# ---- search_tags ----


async def test_search_tags_tool() -> None:
    mock = _make_client_mock()
    mock.search_tags.return_value = {"tags": [{"id": "1", "name": "api", "count": 42}]}

    with patch.object(server_module, "_client", mock):
        result = json.loads(await search_tags(query="api"))

    assert result["tags"][0]["name"] == "api"
    assert result["tags"][0]["count"] == 42
    mock.search_tags.assert_called_once_with({"q": "api"})


async def test_search_tags_with_pagination() -> None:
    mock = _make_client_mock()
    mock.search_tags.return_value = {"tags": []}

    with patch.object(server_module, "_client", mock):
        await search_tags(query="test", page=2)

    mock.search_tags.assert_called_once_with({"q": "test", "page": 2})


# ---- list_topics ----


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


async def test_list_topics_with_category_and_tag_filters() -> None:
    mock = _make_client_mock()
    mock.list_topics.return_value = {"result": [{"id": "10"}]}

    with patch.object(server_module, "_client", mock):
        result = json.loads(
            await list_topics(category_ids="1,2", tags="api,sso", page_size=5)
        )

    assert result["result"][0]["id"] == "10"
    call_params = mock.list_topics.call_args[0][0]
    assert call_params["categoryIds"] == "1,2"
    assert call_params["tags"] == "api,sso"
    assert call_params["pageSize"] == 5


async def test_list_topics_with_date_filters() -> None:
    mock = _make_client_mock()
    mock.list_topics.return_value = {"result": []}

    with patch.object(server_module, "_client", mock):
        await list_topics(created_after="2024-01-01", active_before="2024-06-01")

    call_params = mock.list_topics.call_args[0][0]
    assert "createdAt" in call_params
    assert "lastActivity" in call_params
    created = json.loads(call_params["createdAt"])
    assert created == {"from": "2024-01-01"}
    activity = json.loads(call_params["lastActivity"])
    assert activity == {"to": "2024-06-01"}


async def test_list_topics_with_sort_and_content_types() -> None:
    mock = _make_client_mock()
    mock.list_topics.return_value = {"result": []}

    with patch.object(server_module, "_client", mock):
        await list_topics(content_types="question,idea", sort="createdAt")

    call_params = mock.list_topics.call_args[0][0]
    assert call_params["contentTypes"] == "question,idea"
    assert call_params["sort"] == "createdAt"


# ---- get_topic ----


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


# ---- list_ideas ----


async def test_list_ideas_tool() -> None:
    mock = _make_client_mock()
    mock.list_ideas.return_value = {"result": [{"id": "7", "contentType": "idea"}]}

    with patch.object(server_module, "_client", mock):
        result = json.loads(await list_ideas())

    assert result["result"][0]["contentType"] == "idea"
    mock.list_ideas.assert_called_once()


# ---- list_categories ----


async def test_list_categories_tool() -> None:
    mock = _make_client_mock()
    mock.list_categories.return_value = {
        "result": [{"id": "1", "name": "General"}]
    }

    with patch.object(server_module, "_client", mock):
        result = json.loads(await list_categories())

    assert result["result"][0]["name"] == "General"


# ---- list_tags ----


async def test_list_tags_tool() -> None:
    mock = _make_client_mock()
    mock.list_tags.return_value = {"result": [{"id": "1", "name": "api"}]}

    with patch.object(server_module, "_client", mock):
        result = json.loads(await list_tags())

    assert result["result"][0]["name"] == "api"
    mock.list_tags.assert_called_once()


async def test_list_tags_with_pagination() -> None:
    mock = _make_client_mock()
    mock.list_tags.return_value = {"result": []}

    with patch.object(server_module, "_client", mock):
        await list_tags(page=2, page_size=10)

    mock.list_tags.assert_called_once_with({"page": 2, "pageSize": 10})


# ---- get_category ----


async def test_get_category_tool() -> None:
    mock = _make_client_mock()
    mock.get_category.return_value = {"id": "5", "name": "Feature Requests"}

    with patch.object(server_module, "_client", mock):
        result = json.loads(await get_category(category_id=5))

    assert result["name"] == "Feature Requests"
    mock.get_category.assert_called_once_with(5)


# ---- get_category_tree ----


async def test_get_category_tree_tool() -> None:
    mock = _make_client_mock()
    tree = {"result": [{"id": "1", "name": "Root", "children": []}]}
    mock.get_category_tree.return_value = tree

    with patch.object(server_module, "_client", mock):
        result = json.loads(await get_category_tree())

    assert result["result"][0]["name"] == "Root"
    mock.get_category_tree.assert_called_once()


# ---- get_category_topic_counts ----


async def test_get_category_topic_counts_tool() -> None:
    mock = _make_client_mock()
    mock.get_category_topic_counts.return_value = {
        "result": [{"categoryId": "1", "count": 42}]
    }

    with patch.object(server_module, "_client", mock):
        result = json.loads(await get_category_topic_counts())

    assert result["result"][0]["count"] == 42
    mock.get_category_topic_counts.assert_called_once()


# ---- list_topics_by_category ----


async def test_list_topics_by_category_tool() -> None:
    mock = _make_client_mock()
    mock.list_topics_by_category.return_value = {
        "result": [{"id": "10", "title": "In category"}]
    }

    with patch.object(server_module, "_client", mock):
        result = json.loads(await list_topics_by_category(category_id=3))

    assert result["result"][0]["title"] == "In category"
    mock.list_topics_by_category.assert_called_once_with(3, {})


async def test_list_topics_by_category_with_filters() -> None:
    mock = _make_client_mock()
    mock.list_topics_by_category.return_value = {"result": []}

    with patch.object(server_module, "_client", mock):
        await list_topics_by_category(
            category_id=3, tags="api", sort="createdAt", page_size=10
        )

    call_args = mock.list_topics_by_category.call_args
    assert call_args[0][0] == 3
    params = call_args[0][1]
    assert params["tags"] == "api"
    assert params["sort"] == "createdAt"
    assert params["pageSize"] == 10


async def test_list_topics_by_category_with_date_filters() -> None:
    mock = _make_client_mock()
    mock.list_topics_by_category.return_value = {"result": []}

    with patch.object(server_module, "_client", mock):
        await list_topics_by_category(
            category_id=3, created_after="2024-01-01", created_before="2024-12-31"
        )

    params = mock.list_topics_by_category.call_args[0][1]
    created = json.loads(params["createdAt"])
    assert created == {"from": "2024-01-01", "to": "2024-12-31"}


# ---- list_idea_statuses ----


async def test_list_idea_statuses_tool() -> None:
    mock = _make_client_mock()
    mock.list_idea_statuses.return_value = {
        "result": [{"id": "1", "name": "Planned"}]
    }

    with patch.object(server_module, "_client", mock):
        result = json.loads(await list_idea_statuses())

    assert result["result"][0]["name"] == "Planned"
    mock.list_idea_statuses.assert_called_once()


# ---- list_product_areas ----


async def test_list_product_areas_tool() -> None:
    mock = _make_client_mock()
    mock.list_product_areas.return_value = {
        "result": [{"id": "1", "name": "Platform"}]
    }

    with patch.object(server_module, "_client", mock):
        result = json.loads(await list_product_areas())

    assert result["result"][0]["name"] == "Platform"
    mock.list_product_areas.assert_called_once()


# ---- get_poll_results ----


async def test_get_poll_results_tool() -> None:
    mock = _make_client_mock()
    mock.get_poll_results.return_value = {
        "title": "Best feature?",
        "votes": [{"option": "Search", "count": 15}],
    }

    with patch.object(server_module, "_client", mock):
        result = json.loads(await get_poll_results(topic_id=7, content_type="question"))

    assert result["title"] == "Best feature?"
    mock.get_poll_results.assert_called_once_with("question", 7)


# ---- get_reply ----


async def test_get_reply_tool() -> None:
    mock = _make_client_mock()
    mock.get_reply.return_value = {"id": "200", "content": "Helpful answer"}

    with patch.object(server_module, "_client", mock):
        result = json.loads(
            await get_reply(topic_id=5, reply_id=200, content_type="article")
        )

    assert result["id"] == "200"
    assert result["content"] == "Helpful answer"
    mock.get_reply.assert_called_once_with("article", 5, 200)


# ---- get_community_info ----


# ---- URL resolution in search_community ----


async def test_search_community_resolves_relative_urls() -> None:
    mock = _make_client_mock()
    mock.community_url = "https://community.example.com"
    mock.search.return_value = {
        "community": [
            {"id": "1", "url": "/topic/show?tid=586&fid=37"},
            {"id": "2", "url": "https://other.example.com/page"},
        ]
    }

    with patch.object(server_module, "_client", mock):
        result = json.loads(await search_community(query="test"))

    assert result["community"][0]["url"] == "https://community.example.com/topic/show?tid=586&fid=37"
    # Absolute URLs should not be modified
    assert result["community"][1]["url"] == "https://other.example.com/page"


async def test_search_community_no_resolution_without_community_url() -> None:
    mock = _make_client_mock()
    mock.community_url = None
    mock.search.return_value = {
        "community": [{"id": "1", "url": "/topic/show?tid=1"}]
    }

    with patch.object(server_module, "_client", mock):
        result = json.loads(await search_community(query="test"))

    # Relative URL should remain unchanged
    assert result["community"][0]["url"] == "/topic/show?tid=1"


# ---- URL resolution in get_topic ----


async def test_get_topic_resolves_relative_urls() -> None:
    mock = _make_client_mock()
    mock.community_url = "https://community.example.com/"
    mock.get_topic_by_id.return_value = {
        "result": [{"id": "42", "contentType": "question"}]
    }
    mock.get_topic_detail.return_value = {
        "id": "42",
        "url": "/topic/show?tid=42",
        "seoCommunityUrl": "/support-37/what-is-ai-answers-42",
        "contentType": "question",
    }
    mock.get_topic_replies.return_value = {
        "result": [{"id": "100", "url": "/reply/100"}],
    }

    with patch.object(server_module, "_client", mock):
        result = json.loads(await get_topic(topic_id=42))

    # Trailing slash on community_url should be handled
    assert result["url"] == "https://community.example.com/topic/show?tid=42"
    assert result["seoCommunityUrl"] == "https://community.example.com/support-37/what-is-ai-answers-42"
    assert result["replies"]["result"][0]["url"] == "https://community.example.com/reply/100"


# ---- get_community_info ----


async def test_get_community_info_with_url() -> None:
    mock = _make_client_mock()
    mock.region = "eu-west-1"
    mock.base_url = "https://api2-eu-west-1.insided.com"
    mock.community_url = "https://community.example.com"

    with patch.object(server_module, "_client", mock):
        result = json.loads(await get_community_info())

    assert result["region"] == "eu-west-1"
    assert result["api_base_url"] == "https://api2-eu-west-1.insided.com"
    assert result["community_url"] == "https://community.example.com"


async def test_get_community_info_without_url() -> None:
    mock = _make_client_mock()
    mock.region = "us-west-2"
    mock.base_url = "https://api2-us-west-2.insided.com"
    mock.community_url = None

    with patch.object(server_module, "_client", mock):
        result = json.loads(await get_community_info())

    assert result["region"] == "us-west-2"
    assert result["api_base_url"] == "https://api2-us-west-2.insided.com"
    assert "community_url" not in result
