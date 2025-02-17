from typing import Final

DOMAIN: Final = "guk_krasnodar"

DEFAULT_SCAN_INTERVAL: Final = 60 * 60 * 12  # 12 hour
DEFAULT_USER_AGENT: Final = "okhttp/3.7.0"

CONF_ACCOUNTS: Final = "accounts"
CONF_METERS: Final = "meters"
CONF_USER_AGENT: Final = "user_agent"

DATA_YAML_CONFIG: Final = DOMAIN + "_yaml_config"
DATA_API_OBJECTS: Final = DOMAIN + "_api_objects"
DATA_ENTITIES: Final = DOMAIN + "_entities"
DATA_FINAL_CONFIG: Final = DOMAIN + "_final_config"
DATA_PROVIDER_LOGOS: Final = DOMAIN + "_provider_logos"
DATA_UPDATE_DELEGATORS: Final = DOMAIN + "_update_delegators"
DATA_UPDATE_LISTENERS: Final = DOMAIN + "_update_listeners"

SUPPORTED_PLATFORMS: Final = ("sensor",)
