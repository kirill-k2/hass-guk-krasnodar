__all__ = ("CONFIG_ENTRY_SCHEMA",)

from datetime import timedelta

import voluptuous as vol
from homeassistant.const import (
    CONF_DEFAULT,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
)
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_ACCOUNTS,
    CONF_METERS,
    CONF_USER_AGENT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_USER_AGENT,
)

MIN_SCAN_INTERVAL = timedelta(seconds=300)


SCAN_INTERVAL_SCHEMA = vol.Schema(
    {
        vol.Optional(
            CONF_ACCOUNTS, default=DEFAULT_SCAN_INTERVAL
        ): cv.positive_time_period,
        vol.Optional(
            CONF_METERS, default=DEFAULT_SCAN_INTERVAL
        ): cv.positive_time_period,
    }
)


def _validator_name_format_schema(schema):
    return vol.Any(
        vol.All(cv.string, lambda x: {CONF_ACCOUNTS: x}, schema),
        schema,
    )


GENERIC_ACCOUNT_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_ACCOUNTS, default=True): cv.boolean,
        vol.Optional(CONF_METERS, default=True): cv.boolean,
        vol.Optional(
            CONF_SCAN_INTERVAL, default=lambda: SCAN_INTERVAL_SCHEMA({})
        ): vol.Any(
            vol.All(
                cv.positive_time_period,
                lambda x: dict.fromkeys((CONF_ACCOUNTS, CONF_METERS), x),
                SCAN_INTERVAL_SCHEMA,
            ),
            SCAN_INTERVAL_SCHEMA,
        ),
    },
    extra=vol.PREVENT_EXTRA,
)


def _make_account_validator(account_schema):
    return vol.Any(
        vol.Equal(False),  # For disabling
        vol.All(vol.Equal(True), lambda _: account_schema({})),  # For default
        account_schema,  # For custom
    )


GENERIC_ACCOUNT_VALIDATOR = _make_account_validator(GENERIC_ACCOUNT_SCHEMA)


CONFIG_ENTRY_SCHEMA = vol.Schema(
    {
        # Primary API configuration
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_USER_AGENT, default=DEFAULT_USER_AGENT): cv.string,
        # Additional API configuration
        vol.Optional(
            CONF_DEFAULT, default=lambda: GENERIC_ACCOUNT_SCHEMA({})
        ): GENERIC_ACCOUNT_VALIDATOR,
        vol.Optional(CONF_ACCOUNTS): vol.Any(
            vol.All(
                cv.ensure_list,
                [cv.string],
                lambda x: {y: GENERIC_ACCOUNT_SCHEMA({}) for y in x},
            ),
            vol.Schema({cv.string: GENERIC_ACCOUNT_VALIDATOR}),
        ),
    },
    extra=vol.PREVENT_EXTRA,
)
