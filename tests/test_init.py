"""Test component setup."""

from homeassistant.const import CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from .conftest import CONFIG_BASE, mock_gukk_aiohttp_client
from custom_components.guk_krasnodar.const import DOMAIN, DATA_ENTITIES
from custom_components.guk_krasnodar.sensor import GUKKrasnodarAccount


async def test_async_setup(hass):
    """Test the component gets setup."""
    assert await async_setup_component(hass, DOMAIN, {}) is True


async def test_config_in_config_entry(hass: HomeAssistant, gukk_aioclient_mock) -> None:
    """Test that config are loaded via config entry."""

    entry_config = CONFIG_BASE.copy()
    # no config_entry exists
    assert len(hass.config_entries.async_entries(DOMAIN)) == 0
    # no data exists
    assert not hass.data.get(DOMAIN)

    with mock_gukk_aiohttp_client(hass, gukk_aioclient_mock):
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


async def test_setup_services_and_unload_services(
    hass: HomeAssistant, gukk_aioclient_mock
) -> None:
    """Test setup services and unload services."""

    mock_config = CONFIG_BASE.copy()
    # @todo - вернуть чистый мок, без async_setup_component
    # MockConfigEntry(domain=DOMAIN, data=mock_config).add_to_hass(hass)
    with mock_gukk_aiohttp_client(hass, gukk_aioclient_mock):
        assert await async_setup_component(hass, DOMAIN, {DOMAIN: mock_config})

    config_entries = hass.config_entries.async_entries(DOMAIN)
    assert len(config_entries) == 1

    # Check services are created
    gukk_services = hass.services.async_services()[DOMAIN]
    assert len(gukk_services) == 1

    await hass.config_entries.async_unload(config_entries[0].entry_id)
    # Check services are removed
    assert not hass.services.async_services().get(DOMAIN)
