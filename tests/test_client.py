"""Tests for the Gainsight API client."""

from __future__ import annotations

import os
import time

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


@respx.mock(base_url=EU_BASE)
@pytest.mark.asyncio
async def test_search(respx_mock: respx.MockRouter, client: GainsightClient) -> None:
    _mock_token(respx_mock)
    respx_mock.get("/api/v2/search").mock(
        return_value=httpx.Response(200, json={"data": [{"id": 1, "title": "SSO"}]})
    )

    result = await client.search({"q": "SSO"})
    assert result["data"][0]["title"] == "SSO"
    await client.close()


@respx.mock(base_url=EU_BASE)
@pytest.mark.asyncio
async def test_list_topics(respx_mock: respx.MockRouter, client: GainsightClient) -> None:
    _mock_token(respx_mock)
    respx_mock.get("/api/v2/topics").mock(
        return_value=httpx.Response(200, json={"data": []})
    )

    result = await client.list_topics({})
    assert result == {"data": []}
    await client.close()


@respx.mock(base_url=EU_BASE)
@pytest.mark.asyncio
async def test_get_topic(respx_mock: respx.MockRouter, client: GainsightClient) -> None:
    _mock_token(respx_mock)
    respx_mock.get("/api/v2/topics/42").mock(
        return_value=httpx.Response(200, json={"id": 42, "title": "Test"})
    )

    result = await client.get_topic(42)
    assert result["id"] == 42
    await client.close()


@respx.mock(base_url=EU_BASE)
@pytest.mark.asyncio
async def test_get_topic_replies(respx_mock: respx.MockRouter, client: GainsightClient) -> None:
    _mock_token(respx_mock)
    respx_mock.get("/api/v2/topics/42/replies").mock(
        return_value=httpx.Response(200, json={"data": [{"id": 100}]})
    )

    result = await client.get_topic_replies(42)
    assert result["data"][0]["id"] == 100
    await client.close()


@respx.mock(base_url=EU_BASE)
@pytest.mark.asyncio
async def test_list_categories(respx_mock: respx.MockRouter, client: GainsightClient) -> None:
    _mock_token(respx_mock)
    respx_mock.get("/api/v2/categories").mock(
        return_value=httpx.Response(200, json={"data": [{"id": 1, "name": "General"}]})
    )

    result = await client.list_categories()
    assert result["data"][0]["name"] == "General"
    await client.close()


@respx.mock(base_url=EU_BASE)
@pytest.mark.asyncio
async def test_token_caching(respx_mock: respx.MockRouter, client: GainsightClient) -> None:
    """Token should be reused within its expiry window."""
    token_route = respx_mock.post("/oauth2/token").mock(
        return_value=httpx.Response(
            200, json={"access_token": "tok-cached", "expires_in": 3600}
        )
    )
    respx_mock.get("/api/v2/categories").mock(
        return_value=httpx.Response(200, json={"data": []})
    )

    await client.list_categories()
    await client.list_categories()

    # Token endpoint should only be called once
    assert token_route.call_count == 1
    await client.close()


def test_invalid_region(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GS_CC_REGION", "ap-southeast-1")
    with pytest.raises(ValueError, match="Unknown region"):
        GainsightClient()
