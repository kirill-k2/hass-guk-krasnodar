"""Test sensors refresh."""

import logging

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from conftest import (
    CONFIG_FAST_UPDATES,
    mock_gukk_aiohttp_client,
)
from guk_krasnodar import DOMAIN


async def test_entries_update(hass: HomeAssistant, gukk_aioclient_mock) -> None:
    """Проверка обновления состояний."""

    logging.getLogger("custom_components.guk_krasnodar").setLevel(logging.DEBUG)

    entry_config = CONFIG_FAST_UPDATES.copy()
    # no config_entry exists
    assert len(hass.config_entries.async_entries(DOMAIN)) == 0
    # no data exists
    assert not hass.data.get(DOMAIN)

    # @todo заменить на мок?
    with mock_gukk_aiohttp_client(hass, gukk_aioclient_mock):
        assert await async_setup_component(hass, DOMAIN, {DOMAIN: entry_config})

    assert hass.states.get("sensor.guk_krasnodar_1_12345_meter_67890").state == "123"
    assert hass.states.get("sensor.guk_krasnodar_1_12345_account").state == "1234.56"

    # @todo нужен адекватный способ обновления данных для теста
    # FIXTURE_ACCOUNT_DETAIL['info'][4]['value'] = '5678.90'
    # await hass.async_block_till_done()
    # await asyncio.sleep(3)
    # assert hass.states.get("sensor.guk_krasnodar_1_12345_account").state == "5678.90"
