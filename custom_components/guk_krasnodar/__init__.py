"""GUK Krasnodar API"""

__all__ = (
    "CONFIG_SCHEMA",
    "async_unload_entry",
    "async_reload_entry",
    "async_setup",
    "async_setup_entry",
    "const",
    "sensor",
    "DOMAIN",
)

import asyncio
import logging
from typing import Dict, Tuple, List, Any, Mapping, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv

from ._base import UpdateDelegatorsDataType
from ._schema import CONFIG_ENTRY_SCHEMA
from ._util import _find_existing_entry, mask_username, _make_log_prefix
from .const import (
    CONF_USER_AGENT,
    DATA_API_OBJECTS,
    DATA_ENTITIES,
    DATA_FINAL_CONFIG,
    DATA_UPDATE_DELEGATORS,
    DATA_UPDATE_LISTENERS,
    DATA_YAML_CONFIG,
    DOMAIN,
    SUPPORTED_PLATFORMS,
)
from .exceptions import SessionAPIException, EmptyResponse

_log = logging.getLogger(__name__)


def _unique_entries(value: List[Mapping[str, Any]]) -> List[Mapping[str, Any]]:
    users: Dict[Tuple[str, str], Optional[int]] = {}

    errors = []
    for i, config in enumerate(value):
        user = config[CONF_USERNAME]
        if user in users:
            if users[user] is not None:
                errors.append(
                    vol.Invalid(
                        "duplicate unique key, first encounter", path=[users[user]]
                    )
                )
                users[user] = None
            errors.append(
                vol.Invalid("duplicate unique key, subsequent encounter", path=[i])
            )
        else:
            users[user] = i

    if errors:
        if len(errors) > 1:
            raise vol.MultipleInvalid(errors)
        raise next(iter(errors))

    return value


CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Any(
            vol.Equal({}),
            vol.All(
                cv.ensure_list,
                vol.Length(min=1),
                [CONFIG_ENTRY_SCHEMA],
                _unique_entries,
            ),
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the GUK Krasnodar Personal Cabinet component."""

    domain_config = config.get(DOMAIN)
    if not domain_config:
        return True

    domain_data = {}
    hass.data[DOMAIN] = domain_data

    yaml_config = {}
    hass.data[DATA_YAML_CONFIG] = yaml_config

    for user_cfg in domain_config:
        if not user_cfg:
            continue

        username: str = user_cfg[CONF_USERNAME]

        key = username
        log_prefix = f"[{mask_username(username)}] "

        _log.info(log_prefix + "Получена конфигурация из YAML")

        existing_entry = _find_existing_entry(hass, username)
        if existing_entry:
            if existing_entry.source == config_entries.SOURCE_IMPORT:
                yaml_config[key] = user_cfg
                _log.debug(
                    log_prefix + "Соответствующая конфигурационная запись существует"
                )
            else:
                _log.warning(
                    log_prefix
                    + "Конфигурация из YAML переопределена другой конфигурацией!"
                )
            continue

        # Save YAML configuration
        yaml_config[key] = user_cfg

        _log.warning(log_prefix + "Создание новой конфигурационной записи")

        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": config_entries.SOURCE_IMPORT},
                data={CONF_USERNAME: username},
            )
        )

    if not yaml_config:
        _log.debug("Конфигурация из YAML не обнаружена")

    return True


async def async_setup_entry(
    hass: HomeAssistant, config_entry: config_entries.ConfigEntry
):
    username = config_entry.data[CONF_USERNAME]
    unique_key = username
    entry_id = config_entry.entry_id
    log_prefix = f"[{mask_username(username)}] "
    hass_data = hass.data

    _log.debug(log_prefix + "Настройка конфигурационной записи")

    # Source full configuration
    if config_entry.source == config_entries.SOURCE_IMPORT:
        # Source configuration from YAML
        yaml_config = hass_data.get(DATA_YAML_CONFIG)

        if not yaml_config or unique_key not in yaml_config:
            _log.info(
                log_prefix
                + f"Удаление записи {entry_id} после удаления из конфигурации YAML"
            )
            hass.async_create_task(hass.config_entries.async_remove(entry_id))
            return False

        user_cfg = yaml_config[unique_key]

    else:
        # Source and convert configuration from input post_fields
        all_cfg = {**config_entry.data}

        if config_entry.options:
            all_cfg.update(config_entry.options)

        try:
            user_cfg = CONFIG_ENTRY_SCHEMA(all_cfg)
        except vol.Invalid as e:
            _log.error(log_prefix + "Сохранённая конфигурация повреждена: " + repr(e))
            return False

    _log.info(log_prefix + "Применение конфигурационной записи")

    from session_api import SessionAPI

    api_object = SessionAPI(
        username=username,
        password=user_cfg[CONF_PASSWORD],
        user_agent=user_cfg[CONF_USER_AGENT],
    )

    try:
        try:
            await api_object.login()

        except SessionAPIException as e:
            _log.error(log_prefix + "Невозможно выполнить авторизацию: " + repr(e))
            raise ConfigEntryNotReady

        accounts = None
        for i in range(3):
            _log.debug(log_prefix + "Ожидание перед запросом лицевых счетов")
            await asyncio.sleep(5)

            try:
                accounts = await api_object.accounts()
            except EmptyResponse:
                _log.warning(
                    log_prefix + "Получен пустой ответ на запрос лицевых счетов"
                )
            except SessionAPIException as e:
                log_message = "Ошибка получения данных о лицевых счетах: " + str(e)
                _log.error(log_prefix + log_message)
                raise ConfigEntryNotReady(log_message)
            else:
                break

        if accounts is None:
            log_message = "Невозможно получить данные о лицевых счетах"
            _log.error(log_prefix + log_message)
            raise ConfigEntryNotReady(log_message)

    except BaseException:
        await api_object.async_close()
        raise

    if not accounts:
        # Cancel setup because no accounts provided
        _log.warning(log_prefix + "Лицевые счета не найдены")
        await api_object.async_close()
        return False

    _log.debug(log_prefix + f"Найдено {len(accounts)} лицевых счетов")

    api_objects: Dict[str, "SessionAPI"] = hass_data.setdefault(DATA_API_OBJECTS, {})

    # Create placeholders
    api_objects[entry_id] = api_object
    hass_data.setdefault(DATA_ENTITIES, {})[entry_id] = {}
    hass_data.setdefault(DATA_FINAL_CONFIG, {})[entry_id] = user_cfg
    hass.data.setdefault(DATA_UPDATE_DELEGATORS, {})[entry_id] = {}

    # Forward entry setup to sensor platform
    for domain in SUPPORTED_PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(
                config_entry,
                domain,
            )
        )

    # Create options update listener
    update_listener = config_entry.add_update_listener(async_reload_entry)
    hass_data.setdefault(DATA_UPDATE_LISTENERS, {})[entry_id] = update_listener

    _log.debug(log_prefix + ("Применение конфигурации успешно"))
    return True


async def async_reload_entry(
    hass: HomeAssistant,
    config_entry: config_entries.ConfigEntry,
) -> None:
    """Reload GUK Krasnodar entry"""
    log_prefix = _make_log_prefix(config_entry, "setup")
    _log.info(log_prefix + "Перезагрузка интеграции")
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(
    hass: HomeAssistant,
    config_entry: config_entries.ConfigEntry,
) -> bool:
    """Unload GUK Krasnodar entry"""
    log_prefix = _make_log_prefix(config_entry, "setup")
    entry_id = config_entry.entry_id

    update_delegators: UpdateDelegatorsDataType = hass.data[DATA_UPDATE_DELEGATORS].pop(
        entry_id
    )

    tasks = [
        hass.config_entries.async_forward_entry_unload(config_entry, domain)
        for domain in update_delegators.keys()
    ]

    unload_ok = all(await asyncio.gather(*tasks))

    if unload_ok:
        hass.data[DATA_API_OBJECTS].pop(entry_id)
        hass.data[DATA_FINAL_CONFIG].pop(entry_id)

        cancel_listener = hass.data[DATA_UPDATE_LISTENERS].pop(entry_id)
        cancel_listener()

        _log.info(log_prefix + "Интеграция выгружена")

    else:
        _log.warning(log_prefix + "При выгрузке конфигурации произошла ошибка")

    return unload_ok
