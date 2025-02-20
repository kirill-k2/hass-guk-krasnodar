from typing import Final

DOMAIN: Final = "guk_krasnodar"

ATTRIBUTION_RU: Final = "Данные получены с %s"

ATTR_ACCOUNT_NUMBER: Final = "account_number"
ATTR_ADDRESS: Final = "address"
ATTR_BALANCE: Final = "balance"
ATTR_CHARGED: Final = "charged"
ATTR_COMMENT: Final = "comment"
ATTR_DETAIL: Final = "detail"
ATTR_INDICATIONS: Final = "indications"
ATTR_INDICATION_ENTITY: Final = "indication_entity"
ATTR_INFO: Final = "info"
ATTR_LAST_INDICATION: Final = "last_indication"
ATTR_LAST_INDICATION_DATE: Final = "last_indication_date"
ATTR_METER_CODE: Final = "meter_code"
ATTR_SUCCESS: Final = "success"
ATTR_TITLE: Final = "title"

DEFAULT_NAME_FORMAT_ACCOUNTS: Final = "{type_ru_cap} {account_number}"
DEFAULT_NAME_FORMAT_METERS: Final = "{type_ru_cap} {account_number} {title}"
DEFAULT_SCAN_INTERVAL: Final = 60 * 60 * 12  # 12 hour
DEFAULT_USER_AGENT: Final = (
    "Mozilla/5.0 (X11; Linux x86_64; rv:135.0) Gecko/20100101 Firefox/135.0"
)

CONF_ACCOUNTS: Final = "accounts"
CONF_DEV_PRESENTATION: Final = "dev_presentation"
CONF_METERS: Final = "meters"
CONF_NAME_FORMAT: Final = "name_format"
CONF_USER_AGENT: Final = "user_agent"

DATA_API_OBJECTS: Final = DOMAIN + "_api_objects"
DATA_ENTITIES: Final = DOMAIN + "_entities"
DATA_FINAL_CONFIG: Final = DOMAIN + "_final_config"
DATA_PROVIDER_LOGGEROS: Final = DOMAIN + "_provider_LOGGERos"
DATA_UPDATE_DELEGATORS: Final = DOMAIN + "_update_delegators"
DATA_UPDATE_LISTENERS: Final = DOMAIN + "_update_listeners"
DATA_YAML_CONFIG: Final = DOMAIN + "_yaml_config"

FORMAT_VAR_ACCOUNT_CODE: Final = "account_code"
FORMAT_VAR_ACCOUNT_ID: Final = "account_id"
FORMAT_VAR_ACCOUNT_NUMBER: Final = "account_number"
FORMAT_VAR_CODE: Final = "code"
FORMAT_VAR_ID: Final = "id"
FORMAT_VAR_TITLE: Final = "title"
FORMAT_VAR_TYPE: Final = "type_ru"

TYPE_ACCOUNT_RU = "лицевой счёт"
TYPE_METER_RU = "счетчик"

SUPPORTED_PLATFORMS: Final = ("sensor",)
