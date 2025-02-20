"""
Sensor for GUK Krasnodar cabinet.
Retrieves indications regarding current state of accounts.
"""

import logging
from abc import ABC
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Final,
    Hashable,
    List,
    Mapping,
    Optional,
    TypeVar,
    Union,
)

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import ServiceResponse
from homeassistant.const import (
    ATTR_ENTITY_ID,
    STATE_UNKNOWN,
)
from homeassistant.helpers.typing import ConfigType

from ._base import (
    SupportedServicesType,
    GUKKrasnodarEntity,
    make_common_async_setup_entry,
)
from .model import Account, Meter
from ._util import with_auto_auth
from .const import (
    ATTR_ACCOUNT_NUMBER,
    ATTR_ADDRESS,
    ATTR_DETAIL,
    ATTR_INFO,
    ATTR_LAST_INDICATION,
    ATTR_TITLE,
    CONF_ACCOUNTS,
    CONF_METERS,
    DOMAIN,
    FORMAT_VAR_ACCOUNT_NUMBER,
    FORMAT_VAR_CODE,
    FORMAT_VAR_ID,
    FORMAT_VAR_TITLE,
    FORMAT_VAR_TYPE,
    ATTR_COMMENT,
    ATTR_INDICATIONS,
    ATTR_SUCCESS,
    TYPE_ACCOUNT_RU,
    TYPE_METER_RU,
    ATTR_BALANCE,
    ATTR_CHARGED,
    ATTR_LAST_INDICATION_DATE,
    ATTR_INDICATION_ENTITY,
)
from .exceptions import SessionAPIException

_LOGGER = logging.getLogger(__name__)

PUSH_INDICATIONS_SCHEMA = vol.All(
    cv.make_entity_service_schema(
        {
            vol.Required(ATTR_INDICATIONS): cv.positive_int,
            vol.Optional(ATTR_INDICATION_ENTITY): cv.comp_entity_ids_or_uuids,
        }
    ),
)

SERVICE_PUSH_INDICATIONS: Final = "push_indications"
SERVICE_PUSH_INDICATIONS_SCHEMA: Final = PUSH_INDICATIONS_SCHEMA

_TGUKKrasnodarEntity = TypeVar("_TGUKKrasnodarEntity", bound=GUKKrasnodarEntity)


def get_supported_features(
    from_services: SupportedServicesType, for_object: Any
) -> int:
    features = 0
    for type_feature, services in from_services.items():
        if type_feature is None:
            continue
        check_cls, feature = type_feature
        if isinstance(for_object, check_cls):
            features |= feature

    return features


class GUKKrasnodarSensor(GUKKrasnodarEntity, SensorEntity, ABC):
    pass


class GUKKrasnodarAccount(GUKKrasnodarSensor):
    """The class for this sensor"""

    config_key: ClassVar[str] = CONF_ACCOUNTS

    _attr_unit_of_measurement = "руб."
    _attr_icon = "mdi:home-city-outline"
    _attr_device_class = DOMAIN + "_account"

    _supported_services: ClassVar[SupportedServicesType] = {
        None: {},
    }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, *kwargs)

        self.entity_id: Optional[str] = "sensor." + self.entity_id_prefix + "_account"

    @property
    def code(self) -> str:
        return self._account.code

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor"""
        return f"{DOMAIN}_account_{self._account.code}"

    @property
    def state(self) -> Union[float, str]:
        balance = self._account.balance
        if balance is None:
            return STATE_UNKNOWN
        if balance == 0.0:
            return 0.0
        return balance

    @property
    def sensor_related_attributes(self) -> Optional[Mapping[str, Any]]:
        account = self._account

        attributes = {
            ATTR_ACCOUNT_NUMBER: account.number,
            ATTR_ADDRESS: account.address,
            ATTR_BALANCE: account.balance,
            ATTR_CHARGED: account.charged,
        }

        self._handle_dev_presentation(
            attributes,
            (),
            (ATTR_ACCOUNT_NUMBER, ATTR_ADDRESS),
        )

        return attributes

    @property
    def name_format_values(self) -> Mapping[str, Any]:
        """Return the name of the sensor"""
        account = self._account
        return {
            FORMAT_VAR_ACCOUNT_NUMBER: str(account.number),
            FORMAT_VAR_ID: str(account.id),
            FORMAT_VAR_CODE: str(account.code),
            FORMAT_VAR_TYPE: TYPE_ACCOUNT_RU,
        }

    #################################################################################
    # Functional implementation of inherent class
    #################################################################################

    @classmethod
    async def async_refresh_accounts(
        cls,
        entities: Dict[Hashable, "GUKKrasnodarAccount"],
        account: "Account",
        config_entry: ConfigEntry,
        account_config: ConfigType,
        async_add_entities: Callable[[List["GUKKrasnodarAccount"], bool], Any],
    ) -> None:
        entity_key = account.code
        try:
            entity = entities[entity_key]
        except KeyError:
            entity = cls(account, account_config)
            entities[entity_key] = entity

            async_add_entities([entity], False)
        else:
            if entity.enabled:
                entity.async_schedule_update_ha_state(force_refresh=True)

    async def async_update_internal(self) -> None:
        account = self._account
        account_code = account.code
        accounts = await account.api.async_accounts()

        for account in accounts:
            if account.code == account_code:
                await account.api_update_account_detail()
                self._account = account
                break

        self.register_supported_services(account)

    #################################################################################
    # Services callbacks
    #################################################################################

    @property
    def supported_features(self) -> int:
        return get_supported_features(
            self._supported_services,
            self._account,
        )


class GUKKrasnodarMeter(GUKKrasnodarSensor):
    """The class for this sensor"""

    config_key: ClassVar[str] = CONF_METERS

    _attr_icon = "mdi:counter"
    _attr_device_class = DOMAIN + "_meter"

    _supported_services: ClassVar[SupportedServicesType] = {
        None: {
            SERVICE_PUSH_INDICATIONS: SERVICE_PUSH_INDICATIONS_SCHEMA,
        },
    }

    def __init__(self, *args, meter: "Meter", **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._meter = meter

        self.entity_id: Optional[str] = (
            "sensor." + self.entity_id_prefix + "_meter_" + meter.code
        )

    #################################################################################
    # Implementation base of inherent class
    #################################################################################

    @classmethod
    async def async_refresh_accounts(
        cls,
        entities: Dict[Hashable, Optional[_TGUKKrasnodarEntity]],
        account: "Account",
        config_entry: ConfigEntry,
        account_config: ConfigType,
        async_add_entities: Callable[[List[_TGUKKrasnodarEntity], bool], Any],
    ):
        new_meter_entities = []
        meters = await account.api.async_meters(account)

        for meter in meters:
            entity_key = (account.code, meter.code)
            try:
                entity = entities[entity_key]
            except KeyError:
                entity = cls(
                    account,
                    account_config,
                    meter=meter,
                )
                entities[entity_key] = entity
                new_meter_entities.append(entity)
            else:
                if entity.enabled:
                    entity.async_schedule_update_ha_state(force_refresh=True)

        if new_meter_entities:
            async_add_entities(new_meter_entities, False)

    async def async_update_internal(self) -> None:
        meters = await self._account.api.async_meters(self._account)
        meter_code = self._meter.code
        meter = next((m for m in meters if m.code == meter_code), None)

        if meter is None:
            self.hass.async_create_task(self.async_remove())
        else:
            self.register_supported_services(meter)
            self._meter = meter

    #################################################################################
    # Data-oriented implementation of inherent class
    #################################################################################

    @property
    def code(self) -> str:
        return self._meter.code

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor"""
        met = self._meter
        return f"{DOMAIN}_meter_{met.account.code}_{met.code}"

    @property
    def state(self) -> Union[int, str]:
        indication = self._meter.last_indication
        if indication is None:
            return STATE_UNKNOWN
        if indication == 0:
            return 0
        return indication

    @property
    def sensor_related_attributes(self) -> Optional[Mapping[str, Any]]:
        meter = self._meter

        attributes = {
            ATTR_TITLE: meter.title,
            ATTR_DETAIL: meter.detail,
            ATTR_LAST_INDICATION: meter.last_indication,
            ATTR_LAST_INDICATION_DATE: meter.last_indications_date,
        }

        if isinstance(meter.info, list):
            for idx, info in enumerate(meter.info):
                attributes[f"{ATTR_INFO}_{idx+1}"] = info
        else:
            attributes[ATTR_INFO] = meter.info

        self._handle_dev_presentation(
            attributes,
            (),
            (
                ATTR_TITLE,
                ATTR_INFO,
                ATTR_INFO + "_1",
                ATTR_INFO + "_2",
                ATTR_INFO + "_3",
                ATTR_INFO + "_4",
                ATTR_INFO + "_5",
                ATTR_DETAIL,
            ),
        )

        return attributes

    @property
    def name_format_values(self) -> Mapping[str, Any]:
        meter = self._meter
        return {
            FORMAT_VAR_ID: meter.code or "<unknown>",
            FORMAT_VAR_TITLE: meter.title or "<unknown>",
            FORMAT_VAR_TYPE: TYPE_METER_RU,
        }

    #################################################################################
    # Push service
    #################################################################################

    async def async_service_push_indications(self, **call_data) -> ServiceResponse:
        """
        Push indications entity service.
        :param call_data: Parameters for service call
        :return:
        """
        _LOGGER.info(self.log_prefix + "Начало отправки показаний")

        meter = self._meter

        if meter is None:
            raise Exception("Счетчик не доступен")

        event_data = {
            ATTR_ENTITY_ID: self.entity_id,
            ATTR_SUCCESS: False,
            ATTR_INDICATIONS: None,
            ATTR_COMMENT: None,
        }

        try:
            indication = call_data[ATTR_INDICATIONS]
            event_data[ATTR_INDICATIONS] = indication

            src_entity = call_data.get(ATTR_INDICATION_ENTITY, None)
            if (
                (not indication or indication <= 0)
                and src_entity
                and len(src_entity) == 1
            ):
                _LOGGER.debug(self.log_prefix + "Используется объект %s" % src_entity)
                indication = self.hass.states.get(src_entity[0]).state
                event_data[ATTR_INDICATIONS] = indication

            indication = round(float(indication))
            event_data[ATTR_INDICATIONS] = indication

            await with_auto_auth(
                meter.account.api, meter.api_send_indication, indications=indication
            )

        except SessionAPIException as e:
            event_data[ATTR_COMMENT] = "Ошибка API: %s" % e
            raise

        except BaseException as e:
            event_data[ATTR_COMMENT] = "Неизвестная ошибка: %r" % e
            _LOGGER.error(event_data[ATTR_COMMENT])
            raise

        else:
            event_data[ATTR_COMMENT] = "Показания успешно отправлены"
            event_data[ATTR_SUCCESS] = True
            self.async_schedule_update_ha_state(force_refresh=True)

        finally:
            _LOGGER.debug(self.log_prefix + "Отправлено событие: " + str(event_data))
            self.hass.bus.async_fire(
                event_type=DOMAIN + "_" + SERVICE_PUSH_INDICATIONS,
                event_data=event_data,
            )

            _LOGGER.info(self.log_prefix + "Отправка показаний завершена.")
            return event_data


async_setup_entry = make_common_async_setup_entry(
    GUKKrasnodarAccount,
    GUKKrasnodarMeter,
)
