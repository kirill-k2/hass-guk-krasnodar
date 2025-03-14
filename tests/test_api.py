"""Test raw api."""

from .conftest import mock_gukk_aiohttp_client
from custom_components.guk_krasnodar.exceptions import AccessDenied
from custom_components.guk_krasnodar.guk_krasnodar_api import GUKKrasnodarAPI


async def test_api_login_fail(hass, gukk_aioclient_mock):
    with mock_gukk_aiohttp_client(hass, gukk_aioclient_mock):
        api: GUKKrasnodarAPI = GUKKrasnodarAPI(
            username="username_bad", password="password_bad"
        )

    try:
        await api.async_login()
    except AccessDenied:
        pass
    else:
        assert False

    assert api._token != "TOKEN"


async def test_api_login(hass, gukk_aioclient_mock):
    with mock_gukk_aiohttp_client(hass, gukk_aioclient_mock):
        api: GUKKrasnodarAPI = GUKKrasnodarAPI(
            username="username@domain.ru", password="password"
        )

    await api.async_login()

    assert api._token == "TOKEN"


async def test_api_accounts(hass, gukk_aioclient_mock):
    with mock_gukk_aiohttp_client(hass, gukk_aioclient_mock):
        api: GUKKrasnodarAPI = GUKKrasnodarAPI(username="username", password="password")

    accounts = await api.async_accounts()
    assert len(accounts) == 1


async def test_api_meters(hass, gukk_aioclient_mock, mock_account):
    with mock_gukk_aiohttp_client(hass, gukk_aioclient_mock):
        api: GUKKrasnodarAPI = GUKKrasnodarAPI(username="username", password="password")

    meters = await api.async_meters(mock_account)
    assert len(meters) == 1

    assert meters[0].last_indication == 123
    assert meters[0].last_indication_date == "18.02.2025"
    assert meters[0].push_allowed


async def test_api_update_account_detail(hass, gukk_aioclient_mock, mock_account):
    with mock_gukk_aiohttp_client(hass, gukk_aioclient_mock):
        api: GUKKrasnodarAPI = GUKKrasnodarAPI(username="username", password="password")

    accounts = await api.async_accounts()
    assert len(accounts) == 1
    account = accounts[0]
    assert account.balance is None

    await api.async_update_account_detail(account)
    assert account.balance == 1234.56
    assert account.charged == 6543.21
    assert account.area == 99.99
