__all__ = (
    "make_common_async_setup_entry",
    "GUKKrasnodarEntity",
    "async_refresh_api_data",
    "async_register_update_delegator",
    "UpdateDelegatorsDataType",
    "EntitiesDataType",
    "SupportedServicesType",
)

import asyncio
import logging
import re
from abc import abstractmethod
from datetime import timedelta
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Generic,
    Hashable,
    Iterable,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Set,
    SupportsInt,
    TYPE_CHECKING,
    Tuple,
    Type,
    TypeVar,
    Union,
)
from urllib.parse import urlparse

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_ATTRIBUTION,
    CONF_DEFAULT,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.typing import ConfigType, StateType
from homeassistant.util import as_local, utcnow

from ._util import mask_value, with_auto_auth
from .const import (
    ATTRIBUTION_RU,
    ATTR_ACCOUNT_CODE,
    ATTR_ACCOUNT_ID,
    CONF_ACCOUNTS,
    CONF_DEV_PRESENTATION,
    CONF_NAME_FORMAT,
    DATA_API_OBJECTS,
    DATA_ENTITIES,
    DATA_FINAL_CONFIG,
    DATA_UPDATE_DELEGATORS,
    DOMAIN,
    FORMAT_VAR_ACCOUNT_CODE,
    FORMAT_VAR_ACCOUNT_ID,
    FORMAT_VAR_CODE,
    FORMAT_VAR_ID,
    SUPPORTED_PLATFORMS,
    FORMAT_VAR_ACCOUNT_NUMBER,
)
from .guk_krasnodar_api import GUKKrasnodarAPI, API_URL

if TYPE_CHECKING:
    from .model import Account
    from homeassistant.helpers.entity_registry import RegistryEntry

_log = logging.getLogger(__name__)

_TGUKKrasnodarEntity = TypeVar("_TGUKKrasnodarEntity", bound="GUKKrasnodarEntity")

AddEntitiesCallType = Callable[[List["GUKKrasnodarEntity"], bool], Any]
UpdateDelegatorsDataType = Dict[
    str, Tuple[AddEntitiesCallType, Set[Type["GUKKrasnodarEntity"]]]
]
EntitiesDataType = Dict[
    Type["GUKKrasnodarEntity"], Dict[Hashable, "GUKKrasnodarEntity"]
]


def make_common_async_setup_entry(
    entity_cls: Type["GUKKrasnodarEntity"], *args: Type["GUKKrasnodarEntity"]
):
    async def _async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_devices,
    ):
        current_entity_platform = entity_platform.current_platform.get()

        log_prefix = (
            f"[{mask_value(config_entry.data[CONF_USERNAME])}]"
            f"[{current_entity_platform.domain}][setup] "
        )
        _log.debug(log_prefix + "Регистрация делегата обновлений")

        await async_register_update_delegator(
            hass,
            config_entry,
            current_entity_platform.domain,
            async_add_devices,
            entity_cls,
            *args,
        )

    _async_setup_entry.__name__ = "async_setup_entry"

    return _async_setup_entry


async def async_register_update_delegator(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    platform: str,
    async_add_entities: AddEntitiesCallType,
    entity_cls: Type["GUKKrasnodarEntity"],
    *args: Type["GUKKrasnodarEntity"],
    update_after_complete: bool = True,
):
    entry_id = config_entry.entry_id

    update_delegators: UpdateDelegatorsDataType = hass.data[DATA_UPDATE_DELEGATORS][
        entry_id
    ]
    update_delegators[platform] = (async_add_entities, {entity_cls, *args})

    if update_after_complete:
        if len(update_delegators) != len(SUPPORTED_PLATFORMS):
            return

        await async_refresh_api_data(hass, config_entry)


DEV_CLASSES_PROCESSED = set()


async def async_refresh_api_data(hass: HomeAssistant, config_entry: ConfigEntry):
    entry_id = config_entry.entry_id

    update_delegators: UpdateDelegatorsDataType = hass.data[DATA_UPDATE_DELEGATORS][
        entry_id
    ]

    log_prefix_base = f"[{mask_value(config_entry.data[CONF_USERNAME])}]"
    refresh_log_prefix = log_prefix_base + "[refresh] "

    _log.info(refresh_log_prefix + "Запуск обновления связанных с профилем данных")

    if not update_delegators:
        return

    entities: EntitiesDataType = hass.data[DATA_ENTITIES][entry_id]
    final_config: ConfigType = dict(hass.data[DATA_FINAL_CONFIG][entry_id])

    dev_presentation = final_config.get(CONF_DEV_PRESENTATION)
    dev_log_prefix = log_prefix_base + "[dev] "

    if dev_presentation:
        from pprint import pformat

        _log.debug(dev_log_prefix + "Конечная конфигурация:\n" + pformat(final_config))

    tasks = []

    async def _wrap_update_task(update_task):
        try:
            return await update_task
        except BaseException as task_exception:
            _log.exception(
                f"Error occurred during task execution: {repr(task_exception)}",
                exc_info=task_exception,
            )
            return None

    accounts_config = final_config.get(CONF_ACCOUNTS) or {}
    account_default_config = final_config[CONF_DEFAULT]

    api: "GUKKrasnodarAPI" = hass.data[DATA_API_OBJECTS][entry_id]
    accounts = await with_auto_auth(api, api.async_accounts)

    for account in accounts:
        account_config = accounts_config.get(account.code)
        account_log_prefix_base = refresh_log_prefix + f"[{mask_value(account.code)}]"

        if account_config is None:
            account_config = account_default_config

        if account_config is False:
            continue

        for platform, (async_add_entities, entity_classes) in update_delegators.items():
            platform_log_prefix_base = account_log_prefix_base + f"[{platform}]"
            for entity_cls in entity_classes:
                cls_log_prefix_base = (
                    platform_log_prefix_base + f"[{entity_cls.__name__}]"
                )
                if account_config[entity_cls.config_key] is False:
                    _log.debug(
                        log_prefix_base + " Лицевой счёт пропущен согласно фильтрации"
                    )
                    continue

                if dev_presentation:
                    dev_key = (entity_cls, account.number)
                    if dev_key in DEV_CLASSES_PROCESSED:
                        _log.debug(
                            cls_log_prefix_base
                            + "[dev] Пропущен лицевой счёт ({mask_username(account.code)}) по уникальности номера счёта"
                        )
                        continue

                    DEV_CLASSES_PROCESSED.add(dev_key)

                current_entities = entities.setdefault(entity_cls, {})

                _log.debug(
                    cls_log_prefix_base + "[update] Планирование процедуры обновления"
                )

                tasks.append(
                    hass.async_create_task(
                        _wrap_update_task(
                            entity_cls.async_refresh_accounts(
                                current_entities,
                                account,
                                config_entry,
                                account_config,
                                async_add_entities,
                            )
                        )
                    )
                )

    if tasks:
        _log.info(
            refresh_log_prefix
            + "Выполняется действий по обновлению : "
            + str(len(tasks))
        )
        await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)

    else:
        _log.warning(
            refresh_log_prefix + "Отсутствуют подходящие платформы для конфигурации"
        )


class NameFormatDict(dict):
    def __missing__(self, key: str):
        if key.endswith("_upper") and key[:-6] in self:
            return str(self[key[:-6]]).upper()
        if key.endswith("_cap") and key[:-4] in self:
            return str(self[key[:-4]]).capitalize()
        if key.endswith("_title") and key[:-6] in self:
            return str(self[key[:-6]]).title()
        return "{{" + str(key) + "}}"


_TData = TypeVar("_TData")
_TAccount = TypeVar("_TAccount", bound="Account")

SupportedServicesType = Mapping[
    Optional[Tuple[type, SupportsInt]],
    Mapping[str, Union[dict, Callable[[dict], dict]]],
]


class GUKKrasnodarEntity(Entity, Generic[_TAccount]):
    config_key: ClassVar[str] = NotImplemented

    _supported_services: ClassVar[SupportedServicesType] = {}

    _attr_should_poll = False

    @property
    def entity_id_prefix(self) -> str:
        return f"{DOMAIN}_{self._account.code}"

    def __init__(
        self,
        account: _TAccount,
        account_config: ConfigType,
    ) -> None:
        self._account: _TAccount = account
        self._account_config: ConfigType = account_config
        self._entity_updater = None

    @property
    def api_hostname(self) -> str:
        return urlparse(API_URL).netloc

    @property
    def device_info(self) -> Dict[str, Any]:
        account_object = self._account

        return {
            "name": f"№ {account_object.number}",
            "identifiers": {(DOMAIN, f"{account_object.code}")},
            "manufacturer": "GUK Krasnodar",
            "model": self.api_hostname,
            "suggested_area": account_object.address,
        }

    def _handle_dev_presentation(
        self,
        mapping: MutableMapping[str, Any],
        filter_vars: Iterable[str],
        blackout_vars: Optional[Iterable[str]] = None,
    ) -> None:
        if self._account_config[CONF_DEV_PRESENTATION]:
            filter_vars = set(filter_vars)
            if blackout_vars is not None:
                blackout_vars = set(blackout_vars)
                filter_vars.difference_update(blackout_vars)

                for attr in blackout_vars:
                    value = mapping.get(attr)
                    if value is not None:
                        if isinstance(value, float):
                            value = "#####.###"
                        elif isinstance(value, int):
                            value = "#####"
                        elif isinstance(value, str):
                            value = "XXXXX"
                        else:
                            value = "*****"
                        mapping[attr] = value

            for attr in filter_vars:
                value = mapping.get(attr)
                if value is not None:
                    value = re.sub(r"[A-Za-z]", "X", str(value))
                    value = re.sub(r"[0-9]", "#", value)
                    value = re.sub(r"\w+", "*", value)
                    mapping[attr] = value

    #################################################################################
    # Config getter helpers
    #################################################################################

    @property
    def scan_interval(self) -> timedelta:
        return self._account_config[CONF_SCAN_INTERVAL][self.config_key]

    @property
    def name_format(self) -> str:
        return self._account_config[CONF_NAME_FORMAT][self.config_key]

    #################################################################################
    # Base overrides
    #################################################################################

    @property
    def device_state_attributes(self):
        """Return the attribute(s) of the sensor"""

        attributes = {
            ATTR_ATTRIBUTION: (ATTRIBUTION_RU % self.api_hostname),
            **(self.sensor_related_attributes or {}),
        }

        if ATTR_ACCOUNT_CODE not in attributes:
            attributes[ATTR_ACCOUNT_CODE] = self._account.code

        self._handle_dev_presentation(
            attributes,
            (ATTR_ACCOUNT_CODE, ATTR_ACCOUNT_ID),
        )

        return attributes

    @property
    def name(self) -> Optional[str]:
        name_format_values = {
            key: ("" if value is None else str(value))
            for key, value in self.name_format_values.items()
        }

        if FORMAT_VAR_CODE not in name_format_values:
            name_format_values[FORMAT_VAR_CODE] = self.code

        if FORMAT_VAR_ACCOUNT_CODE not in name_format_values:
            name_format_values[FORMAT_VAR_ACCOUNT_CODE] = self._account.code

        if FORMAT_VAR_ACCOUNT_NUMBER not in name_format_values:
            name_format_values[FORMAT_VAR_ACCOUNT_NUMBER] = self._account.number

        self._handle_dev_presentation(
            name_format_values,
            (FORMAT_VAR_CODE, FORMAT_VAR_ACCOUNT_CODE),
            (FORMAT_VAR_ACCOUNT_ID, FORMAT_VAR_ID),
        )

        return self.name_format.format_map(NameFormatDict(name_format_values))

    #################################################################################
    # Hooks for adding entity to internal registry
    #################################################################################

    async def async_added_to_hass(self) -> None:
        _log.info(self.log_prefix + "Adding to HomeAssistant")
        self.updater_restart()
        self.register_supported_services()

    async def async_will_remove_from_hass(self) -> None:
        _log.info(self.log_prefix + "Removing from HomeAssistant")
        self.updater_stop()

        registry_entry: Optional["RegistryEntry"] = self.registry_entry
        if registry_entry:
            entry_id: Optional[str] = registry_entry.config_entry_id
            if entry_id:
                data_entities: EntitiesDataType = self.hass.data[DATA_ENTITIES][
                    entry_id
                ]
                cls_entities = data_entities.get(self.__class__)
                if cls_entities:
                    remove_indices = []
                    for idx, entity in enumerate(cls_entities):
                        if self is entity:
                            remove_indices.append(idx)
                    for idx in remove_indices:
                        cls_entities.pop(idx)

    #################################################################################
    # Updater management API
    #################################################################################

    @property
    def log_prefix(self) -> str:
        return f"[{self.config_key}][{self.entity_id or '<no entity ID>'}] "

    def updater_stop(self) -> None:
        if self._entity_updater is not None:
            _log.debug(self.log_prefix + "Остановка планировщика обновлений")
            self._entity_updater()
            self._entity_updater = None

    def updater_restart(self) -> None:
        log_prefix = self.log_prefix
        scan_interval = self.scan_interval

        self.updater_stop()

        async def _update_entity(*_):
            nonlocal self
            _log.debug(log_prefix + "Выполнение запланированной задачи обновления")
            await self.async_update_ha_state(force_refresh=True)

        _log.debug(
            log_prefix + f"Starting updater "
            f"(interval: {scan_interval.total_seconds()} seconds, "
            f"next call: {as_local(utcnow()) + scan_interval})"
        )
        self._entity_updater = async_track_time_interval(
            self.hass,
            _update_entity,
            scan_interval,
        )

    async def updater_execute(self) -> None:
        self.updater_stop()
        try:
            await self.async_update_ha_state(force_refresh=True)
        finally:
            self.updater_restart()

    async def async_update(self) -> None:
        await with_auto_auth(
            self._account.api,
            self.async_update_internal,
        )

    #################################################################################
    # Functional base for inherent classes
    #################################################################################

    @classmethod
    @abstractmethod
    async def async_refresh_accounts(
        cls: Type[_TGUKKrasnodarEntity],
        entities: Dict[Hashable, _TGUKKrasnodarEntity],
        account: "Account",
        config_entry: ConfigEntry,
        account_config: ConfigType,
        async_add_entities: Callable[[List[_TGUKKrasnodarEntity], bool], Any],
    ):
        raise NotImplementedError

    #################################################################################
    # Data-oriented base for inherent classes
    #################################################################################

    @abstractmethod
    async def async_update_internal(self) -> None:
        raise NotImplementedError

    @property
    @abstractmethod
    def code(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def state(self) -> StateType:
        raise NotImplementedError

    @property
    @abstractmethod
    def sensor_related_attributes(self) -> Optional[Mapping[str, Any]]:
        raise NotImplementedError

    @property
    @abstractmethod
    def name_format_values(self) -> Mapping[str, Any]:
        raise NotImplementedError

    @property
    @abstractmethod
    def unique_id(self) -> str:
        raise NotImplementedError

    def register_supported_services(self, for_object: Optional[Any] = None) -> None:
        for type_feature, services in self._supported_services.items():
            result, features = (
                (True, None)
                if type_feature is None
                else (isinstance(for_object, type_feature[0]), (int(type_feature[1]),))
            )

            if result:
                for service, schema in services.items():
                    service_name = "async_service_" + service
                    _log.debug("Registering service: %s", service_name)
                    self.platform.async_register_entity_service(
                        service, schema, service_name, features
                    )
