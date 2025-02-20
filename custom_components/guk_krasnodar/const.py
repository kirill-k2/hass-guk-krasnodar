from typing import Final

DOMAIN: Final = "guk_krasnodar"

ATTRIBUTION_RU: Final = "Данные получены с %s"

ATTR_ACCOUNT_CODE: Final = "account_code"
ATTR_ACCOUNT_COMPANY_ID: Final = "account_company_id"
ATTR_ACCOUNT_ID: Final = "account_id"
ATTR_ACCOUNT_NUMBER: Final = "account_number"
ATTR_ADDRESS: Final = "address"
ATTR_COMMENT: Final = "comment"
ATTR_IGNORE_INDICATIONS: Final = "ignore_indications"
ATTR_INDICATIONS: Final = "indication"
ATTR_LAST_INDICATIONS_DATE: Final = "last_indications_date"
ATTR_METER_CODE: Final = "meter_code"
ATTR_METER_DETAIL: Final = "meter_detail"
ATTR_METER_ID: Final = "meter_id"
ATTR_METER_INFO: Final = "meter_info"
ATTR_METER_LAST_INDICATION: Final = "meter_last_indication"
ATTR_METER_TITLE: Final = "meter_title"
ATTR_SUCCESS: Final = "success"

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
DATA_PROVIDER_LOGOS: Final = DOMAIN + "_provider_logos"
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
