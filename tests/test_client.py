"""Tests for the Gainsight API client."""

from __future__ import annotations

import httpx
import pytest
import respx

from src.client import GainsightClient, REGION_BASE_URLS

EU_BASE = REGION_BASE_URLS["eu-west-1"]


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


# ---- Error cases ----


def test_invalid_region(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GS_CC_REGION", "ap-southeast-1")
    with pytest.raises(ValueError, match="Unknown region"):
        GainsightClient()


async def test_invalid_content_type(client: GainsightClient) -> None:
    with pytest.raises(ValueError, match="Unknown content type"):
        await client.get_topic_detail("invalid", 1)
