"""Test component setup."""

from homeassistant.const import CONF_USERNAME
from homeassistant.setup import async_setup_component

from guk_krasnodar.exceptions import AccessDenied
from .conftest import BASE_CONFIG, mock_raw_aiohttp_client
from guk_krasnodar.const import DOMAIN, DATA_ENTITIES
from custom_components.guk_krasnodar.sensor import GUKKrasnodarAccount


async def test_async_setup(hass):
    """Test the component gets setup."""
    assert await async_setup_component(hass, DOMAIN, {}) is True


# async def test_api_call(hass, gukk_aioclient_mock):
#     from guk_krasnodar.guk_krasnodar_api import GUKKrasnodarAPI
#
#     with mock.patch(
#         "guk_krasnodar.guk_krasnodar_api._aiohttp_create_session", side_effect=lambda **kwargs: gukk_aioclient_mock.create_session(hass.loop)
#     ):
#         api: GUKKrasnodarAPI = GUKKrasnodarAPI(username="username", password="password")
#         assert len(await api.accounts()) == 1


async def test_api_accounts(hass, gukk_aioclient_mock):
    from guk_krasnodar.guk_krasnodar_api import GUKKrasnodarAPI

    with mock_raw_aiohttp_client(hass, gukk_aioclient_mock):
        api: GUKKrasnodarAPI = GUKKrasnodarAPI(username="username", password="password")
        assert len(await api.accounts()) == 1


async def test_api_login_fail(hass, gukk_aioclient_mock):
    from guk_krasnodar.guk_krasnodar_api import GUKKrasnodarAPI

    with mock_raw_aiohttp_client(hass, gukk_aioclient_mock):
        api: GUKKrasnodarAPI = GUKKrasnodarAPI(
            username="username_bad", password="password_bad"
        )
        try:
            await api.login()
        except AccessDenied:
            pass
        else:
            assert False

        assert api._token != "TOKEN"


async def test_api_login(hass, gukk_aioclient_mock):
    from guk_krasnodar.guk_krasnodar_api import GUKKrasnodarAPI

    with mock_raw_aiohttp_client(hass, gukk_aioclient_mock):
        api: GUKKrasnodarAPI = GUKKrasnodarAPI(
            username="username@domain.ru", password="password"
        )
        await api.login()
        assert api._token == "TOKEN"


async def test_config_in_config_entry(hass, gukk_aioclient_mock) -> None:
    """Test that config are loaded via config entry."""

    with mock_raw_aiohttp_client(hass, gukk_aioclient_mock):
        entry_config = BASE_CONFIG.copy()

        # no config_entry exists
        assert len(hass.config_entries.async_entries(DOMAIN)) == 0
        # no data exists
        assert not hass.data.get(DOMAIN)

        assert await async_setup_component(hass, DOMAIN, {DOMAIN: entry_config})

        # config_entry created for access point
        config_entries = hass.config_entries.async_entries(DOMAIN)
        assert len(config_entries) == 1

        from homeassistant.config_entries import ConfigEntryState

        assert config_entries[0].state == ConfigEntryState.LOADED
        assert config_entries[0].data.get(CONF_USERNAME) == "username@domain.ru"

        entity_id = config_entries[0].entry_id
        assert isinstance(
            hass.data[DATA_ENTITIES][entity_id][GUKKrasnodarAccount]["1_12345"],
            GUKKrasnodarAccount,
        )


# async def test_setup_services_and_unload_services(
#     hass: HomeAssistant, gukk_aioclient_mock: AiohttpClientMocker
# ) -> None:
#     """Test setup services and unload services."""
#
#     with mock_raw_aiohttp_client(hass, gukk_aioclient_mock):
#         mock_config = BASE_CONFIG.copy()
#         MockConfigEntry(domain=DOMAIN, data=mock_config).add_to_hass(hass)
#
#         # Check services are created
#         gukk_services = hass.services.async_services()[DOMAIN]
#         assert len(gukk_services) == 9
#
#         config_entries = hass.config_entries.async_entries(DOMAIN)
#         assert len(config_entries) == 1
#
#         await hass.config_entries.async_unload(config_entries[0].entry_id)
#         # Check services are removed
#         assert not hass.services.async_services().get(DOMAIN)
