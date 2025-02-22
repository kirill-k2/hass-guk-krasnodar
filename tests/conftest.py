"""Fixtures for testing."""

import json
import logging
from contextlib import contextmanager
from http import HTTPStatus
from typing import Final, Iterator
from unittest import mock

import pytest
from homeassistant.const import (
    CONF_USERNAME,
    CONF_PASSWORD,
    EVENT_HOMEASSISTANT_CLOSE,
    CONF_SCAN_INTERVAL,
    CONF_DEFAULT,
)
from pytest_homeassistant_custom_component.common import load_fixture
from pytest_homeassistant_custom_component.test_util.aiohttp import (
    AiohttpClientMocker,
    AiohttpClientMockResponse,
)
from pytest_socket import enable_socket, socket_allow_hosts

from custom_components.guk_krasnodar.const import CONF_USER_AGENT

pytest_plugins = ["asyncio", "socket"]

FIXTURE_JSON_AUTH = "auth.json"
FIXTURE_JSON_AUTH_BAD_PASSWORD = "auth_bad_password.json"
FIXTURE_JSON_ACCOUNTS = "accounts.json"
FIXTURE_JSON_ACCOUNT_DETAIL = "account_detail.json"
FIXTURE_JSON_METERS = "meters.json"

CONFIG_BASE: Final = {
    CONF_USERNAME: "username@domain.ru",
    CONF_PASSWORD: "password",
    CONF_USER_AGENT: "TEST_UA",
}

CONFIG_FAST_UPDATES: Final = {
    CONF_USERNAME: "username@domain.ru",
    CONF_PASSWORD: "password",
    CONF_USER_AGENT: "TEST_UA",
    CONF_DEFAULT: {
        CONF_SCAN_INTERVAL: 1,
    },
}

FIXTURE_ACCOUNT_DETAIL = json.loads(load_fixture(f"{FIXTURE_JSON_ACCOUNT_DETAIL}"))

logging.getLogger("custom_components.guk_krasnodar").setLevel(logging.INFO)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations."""
    return


@pytest.fixture
def gukk_aioclient_mock(aioclient_mock: AiohttpClientMocker):
    """Create a mock config entry."""

    aioclient_mock.get(
        "https://lk.gukkrasnodar.ru/api/v1/user/accounts",
        text=load_fixture(f"{FIXTURE_JSON_ACCOUNTS}"),
    )

    async def _account_detail(method, url, data):
        return AiohttpClientMockResponse(
            method=method,
            url=url,
            json=FIXTURE_ACCOUNT_DETAIL,
        )

    aioclient_mock.post(
        "https://lk.gukkrasnodar.ru/api/v1/user/account/info/extend",
        text=load_fixture(f"{FIXTURE_JSON_ACCOUNT_DETAIL}"),
        side_effect=_account_detail,
    )

    aioclient_mock.post(
        "https://lk.gukkrasnodar.ru/api/v1/user/account/meters",
        text=load_fixture(f"{FIXTURE_JSON_METERS}"),
    )

    async def _auth_check(method, url, data):
        data = json.loads(data)
        if data["login"] == "username@domain.ru" and data["password"] == "password":
            return AiohttpClientMockResponse(
                method=method,
                url=url,
                text=load_fixture(f"{FIXTURE_JSON_AUTH}"),
            )
        else:
            return AiohttpClientMockResponse(
                method=method,
                url=url,
                text=load_fixture(f"{FIXTURE_JSON_AUTH_BAD_PASSWORD}"),
                status=HTTPStatus.BAD_REQUEST,
            )

    # {
    #     "login": "login",
    #     "password": "password",
    # }
    aioclient_mock.post(
        "https://lk.gukkrasnodar.ru/api/v1/user/login",
        side_effect=_auth_check,
    )

    return aioclient_mock


@pytest.fixture
def mock_account():
    from guk_krasnodar.model import Account

    yield Account(
        id="12345", company_id="1", number="230123456", address="ул.Красная, д.1 кв.1"
    )


@pytest.hookimpl(trylast=True)
def pytest_runtest_setup():
    enable_socket()
    socket_allow_hosts(["127.0.0.1", "localhost", "::1"], allow_unix_socket=True)


@contextmanager
def mock_gukk_aiohttp_client(
    hass, gukk_aioclient_mock
) -> Iterator[AiohttpClientMocker]:
    def create_session(*args, **kwargs):
        session = gukk_aioclient_mock.create_session(hass.loop)

        async def close_session(event):
            """Close session."""
            await session.close()

        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_CLOSE, close_session)

        return session

    with (
        mock.patch(
            "custom_components.guk_krasnodar.guk_krasnodar_api._aiohttp_create_session",
            side_effect=create_session,
        ),
        mock.patch(
            "homeassistant.helpers.aiohttp_client._async_create_clientsession",
            side_effect=create_session,
        ),
    ):
        yield gukk_aioclient_mock


# @contextmanager
# def mock_gukk_api(hass, gukk_aioclient_mock) -> Iterator[GUKKrasnodarAPI]:
#     with mock_gukk_aiohttp_client(hass, gukk_aioclient_mock):
#         yield GUKKrasnodarAPI(username="username", password="password")
