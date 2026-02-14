"""Tests for the Gainsight API client."""

from __future__ import annotations

import httpx
import pytest
import respx

from src.client import GainsightClient, REGION_BASE_URLS

EU_BASE = REGION_BASE_URLS["eu-west-1"]
US_BASE = REGION_BASE_URLS["us-west-2"]


@pytest.fixture(autouse=True)
def _env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GS_CC_CLIENT_ID", "test-id")
    monkeypatch.setenv("GS_CC_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("GS_CC_REGION", "eu-west-1")


@pytest.fixture
def client() -> GainsightClient:
    return GainsightClient()


def _mock_token(router: respx.MockRouter) -> None:
    router.post("/oauth2/token").mock(
        return_value=httpx.Response(
            200,
            json={"access_token": "tok-123", "expires_in": 3600},
        )
    )


# ---- Token tests ----


@respx.mock(base_url=EU_BASE)
async def test_token_includes_scope(respx_mock: respx.MockRouter, client: GainsightClient) -> None:
    """Token request must include scope=read."""
    token_route = respx_mock.post("/oauth2/token").mock(
        return_value=httpx.Response(
            200, json={"access_token": "tok-scoped", "expires_in": 3600}
        )
    )
    respx_mock.get("/v2/categories").mock(
        return_value=httpx.Response(200, json={"result": []})
    )

    await client.list_categories()

    request = token_route.calls[0].request
    body = request.content.decode()
    assert "scope=read" in body
    await client.close()


@respx.mock(base_url=EU_BASE)
async def test_token_caching(respx_mock: respx.MockRouter, client: GainsightClient) -> None:
    """Token should be reused within its expiry window."""
    token_route = respx_mock.post("/oauth2/token").mock(
        return_value=httpx.Response(
            200, json={"access_token": "tok-cached", "expires_in": 3600}
        )
    )
    respx_mock.get("/v2/categories").mock(
        return_value=httpx.Response(200, json={"result": []})
    )

    await client.list_categories()
    await client.list_categories()

    assert token_route.call_count == 1
    await client.close()


# ---- Search ----


@respx.mock(base_url=EU_BASE)
async def test_search(respx_mock: respx.MockRouter, client: GainsightClient) -> None:
    _mock_token(respx_mock)
    respx_mock.get("/v2/topics/search").mock(
        return_value=httpx.Response(
            200, json={"result": [{"id": "1", "title": "SSO"}]}
        )
    )

    result = await client.search({"q": "SSO"})
    assert result["result"][0]["title"] == "SSO"
    await client.close()


# ---- List endpoints ----


@respx.mock(base_url=EU_BASE)
async def test_list_topics(respx_mock: respx.MockRouter, client: GainsightClient) -> None:
    _mock_token(respx_mock)
    respx_mock.get("/v2/topics").mock(
        return_value=httpx.Response(200, json={"result": []})
    )

    result = await client.list_topics({})
    assert result == {"result": []}
    await client.close()


@respx.mock(base_url=EU_BASE)
async def test_list_questions(respx_mock: respx.MockRouter, client: GainsightClient) -> None:
    _mock_token(respx_mock)
    respx_mock.get("/v2/questions").mock(
        return_value=httpx.Response(200, json={"result": [{"contentType": "question"}]})
    )

    result = await client.list_questions({})
    assert result["result"][0]["contentType"] == "question"
    await client.close()


@respx.mock(base_url=EU_BASE)
async def test_list_ideas(respx_mock: respx.MockRouter, client: GainsightClient) -> None:
    _mock_token(respx_mock)
    respx_mock.get("/v2/ideas").mock(
        return_value=httpx.Response(200, json={"result": [{"contentType": "idea"}]})
    )

    result = await client.list_ideas({})
    assert result["result"][0]["contentType"] == "idea"
    await client.close()


@respx.mock(base_url=EU_BASE)
async def test_list_categories(respx_mock: respx.MockRouter, client: GainsightClient) -> None:
    _mock_token(respx_mock)
    respx_mock.get("/v2/categories").mock(
        return_value=httpx.Response(
            200, json={"result": [{"id": "1", "name": "General"}]}
        )
    )

    result = await client.list_categories()
    assert result["result"][0]["name"] == "General"
    await client.close()


@respx.mock(base_url=EU_BASE)
async def test_list_tags(respx_mock: respx.MockRouter, client: GainsightClient) -> None:
    _mock_token(respx_mock)
    respx_mock.get("/v2/tags").mock(
        return_value=httpx.Response(
            200, json={"result": [{"id": "1", "name": "api"}]}
        )
    )

    result = await client.list_tags()
    assert result["result"][0]["name"] == "api"
    await client.close()


@respx.mock(base_url=EU_BASE)
async def test_list_moderator_tags(respx_mock: respx.MockRouter, client: GainsightClient) -> None:
    _mock_token(respx_mock)
    respx_mock.get("/v2/moderatorTags").mock(
        return_value=httpx.Response(
            200, json={"result": [{"id": "1", "name": "internal"}]}
        )
    )

    result = await client.list_moderator_tags()
    assert result["result"][0]["name"] == "internal"
    await client.close()


# ---- Category endpoints ----


@respx.mock(base_url=EU_BASE)
async def test_get_category(respx_mock: respx.MockRouter, client: GainsightClient) -> None:
    _mock_token(respx_mock)
    respx_mock.get("/v2/categories/5").mock(
        return_value=httpx.Response(
            200, json={"id": "5", "name": "Feature Requests"}
        )
    )

    result = await client.get_category(5)
    assert result["id"] == "5"
    assert result["name"] == "Feature Requests"
    await client.close()


@respx.mock(base_url=EU_BASE)
async def test_get_category_tree(respx_mock: respx.MockRouter, client: GainsightClient) -> None:
    _mock_token(respx_mock)
    tree = {"result": [{"id": "1", "name": "Root", "children": [{"id": "2", "name": "Child"}]}]}
    respx_mock.get("/v2/category/getTree").mock(
        return_value=httpx.Response(200, json=tree)
    )

    result = await client.get_category_tree()
    assert result["result"][0]["children"][0]["name"] == "Child"
    await client.close()


@respx.mock(base_url=EU_BASE)
async def test_get_category_topic_counts(respx_mock: respx.MockRouter, client: GainsightClient) -> None:
    _mock_token(respx_mock)
    counts = {"result": [{"categoryId": "1", "count": 42}]}
    respx_mock.get("/v2/categories/getVisibleTopicsCount").mock(
        return_value=httpx.Response(200, json=counts)
    )

    result = await client.get_category_topic_counts()
    assert result["result"][0]["count"] == 42
    await client.close()


@respx.mock(base_url=EU_BASE)
async def test_list_topics_by_category(respx_mock: respx.MockRouter, client: GainsightClient) -> None:
    _mock_token(respx_mock)
    respx_mock.get("/v2/categories/3/topics").mock(
        return_value=httpx.Response(
            200, json={"result": [{"id": "10", "title": "In category"}]}
        )
    )

    result = await client.list_topics_by_category(3, {"pageSize": 5})
    assert result["result"][0]["title"] == "In category"
    await client.close()


# ---- Idea statuses & product areas ----


@respx.mock(base_url=EU_BASE)
async def test_list_idea_statuses(respx_mock: respx.MockRouter, client: GainsightClient) -> None:
    _mock_token(respx_mock)
    statuses = {"result": [{"id": "1", "name": "Planned", "type": "PLANNED"}]}
    respx_mock.get("/v2/ideas/ideaStatuses").mock(
        return_value=httpx.Response(200, json=statuses)
    )

    result = await client.list_idea_statuses()
    assert result["result"][0]["name"] == "Planned"
    await client.close()


@respx.mock(base_url=EU_BASE)
async def test_list_product_areas(respx_mock: respx.MockRouter, client: GainsightClient) -> None:
    _mock_token(respx_mock)
    areas = {"result": [{"id": "1", "name": "Platform"}]}
    respx_mock.get("/v2/productAreas").mock(
        return_value=httpx.Response(200, json=areas)
    )

    result = await client.list_product_areas()
    assert result["result"][0]["name"] == "Platform"
    await client.close()


# ---- Poll results ----


@respx.mock(base_url=EU_BASE)
async def test_get_poll_results(respx_mock: respx.MockRouter, client: GainsightClient) -> None:
    _mock_token(respx_mock)
    poll = {"title": "Favourite colour?", "votes": [{"option": "Blue", "count": 10}]}
    respx_mock.get("/v2/questions/7/poll").mock(
        return_value=httpx.Response(200, json=poll)
    )

    result = await client.get_poll_results("question", 7)
    assert result["title"] == "Favourite colour?"
    assert result["votes"][0]["count"] == 10
    await client.close()


@respx.mock(base_url=EU_BASE)
async def test_get_poll_results_invalid_type(client: GainsightClient) -> None:
    with pytest.raises(ValueError, match="Unknown content type"):
        await client.get_poll_results("invalid", 1)


# ---- Single reply ----


@respx.mock(base_url=EU_BASE)
async def test_get_reply(respx_mock: respx.MockRouter, client: GainsightClient) -> None:
    _mock_token(respx_mock)
    reply = {"id": "200", "content": "Great answer"}
    respx_mock.get("/v2/articles/5/replies/200").mock(
        return_value=httpx.Response(200, json=reply)
    )

    result = await client.get_reply("article", 5, 200)
    assert result["id"] == "200"
    assert result["content"] == "Great answer"
    await client.close()


@respx.mock(base_url=EU_BASE)
async def test_get_reply_invalid_type(client: GainsightClient) -> None:
    with pytest.raises(ValueError, match="Unknown content type"):
        await client.get_reply("invalid", 1, 1)


# ---- Topic detail ----


@respx.mock(base_url=EU_BASE)
async def test_get_topic_detail(respx_mock: respx.MockRouter, client: GainsightClient) -> None:
    _mock_token(respx_mock)
    respx_mock.get("/v2/questions/42").mock(
        return_value=httpx.Response(200, json={"id": "42", "title": "Test"})
    )

    result = await client.get_topic_detail("question", 42)
    assert result["id"] == "42"
    await client.close()


@respx.mock(base_url=EU_BASE)
async def test_get_topic_replies(respx_mock: respx.MockRouter, client: GainsightClient) -> None:
    _mock_token(respx_mock)
    respx_mock.get("/v2/conversations/10/replies").mock(
        return_value=httpx.Response(
            200,
            json={"result": [{"id": "100"}], "_metadata": {"totalCount": 1}},
        )
    )

    result = await client.get_topic_replies("conversation", 10)
    assert result["result"][0]["id"] == "100"
    await client.close()


@respx.mock(base_url=EU_BASE)
async def test_get_topic_by_id(respx_mock: respx.MockRouter, client: GainsightClient) -> None:
    _mock_token(respx_mock)
    respx_mock.get("/v2/topics").mock(
        return_value=httpx.Response(
            200,
            json={"result": [{"id": "42", "contentType": "question"}]},
        )
    )

    result = await client.get_topic_by_id(42)
    assert result["result"][0]["contentType"] == "question"
    await client.close()


# ---- Region tests ----


def test_eu_region_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GS_CC_REGION", "eu-west-1")
    client = GainsightClient()
    assert client.base_url == "https://api2-eu-west-1.insided.com"


def test_us_region_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GS_CC_REGION", "us-west-2")
    client = GainsightClient()
    assert client.base_url == "https://api2-us-west-2.insided.com"


def test_default_region_is_eu(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GS_CC_REGION", raising=False)
    client = GainsightClient()
    assert client.region == "eu-west-1"
    assert client.base_url == "https://api2-eu-west-1.insided.com"


@respx.mock(base_url=US_BASE)
async def test_us_region_api_call(
    respx_mock: respx.MockRouter, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify US region client sends requests to the correct base URL."""
    monkeypatch.setenv("GS_CC_REGION", "us-west-2")
    us_client = GainsightClient()

    respx_mock.post("/oauth2/token").mock(
        return_value=httpx.Response(
            200, json={"access_token": "tok-us", "expires_in": 3600}
        )
    )
    respx_mock.get("/v2/categories").mock(
        return_value=httpx.Response(
            200, json={"result": [{"id": "1", "name": "US Category"}]}
        )
    )

    result = await us_client.list_categories()
    assert result["result"][0]["name"] == "US Category"
    await us_client.close()


# ---- Error cases ----


def test_invalid_region(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GS_CC_REGION", "ap-southeast-1")
    with pytest.raises(ValueError, match="Unknown region"):
        GainsightClient()


async def test_invalid_content_type(client: GainsightClient) -> None:
    with pytest.raises(ValueError, match="Unknown content type"):
        await client.get_topic_detail("invalid", 1)
