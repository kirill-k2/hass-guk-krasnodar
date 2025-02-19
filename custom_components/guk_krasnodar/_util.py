import re
from typing import Optional, Union, Any, TypeVar, Callable, Coroutine

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_USERNAME
from homeassistant.core import callback, HomeAssistant
from homeassistant.helpers.entity_platform import EntityPlatform

from . import EmptyResponse, SessionAPIException
from .const import DOMAIN
from .session_api import SessionAPI


def _make_log_prefix(
    config_entry: Union[Any, ConfigEntry], domain: Union[Any, EntityPlatform], *args
):
    join_args = [
        (
            config_entry.entry_id[-6:]
            if isinstance(config_entry, ConfigEntry)
            else str(config_entry)
        ),
        (domain.domain if isinstance(domain, EntityPlatform) else str(domain)),
    ]
    if args:
        join_args.extend(map(str, args))

    return "[" + "][".join(join_args) + "] "


@callback
def _find_existing_entry(
    hass: HomeAssistant, username: str
) -> Optional[config_entries.ConfigEntry]:
    existing_entries = hass.config_entries.async_entries(DOMAIN)
    for config_entry in existing_entries:
        if config_entry.data[CONF_USERNAME] == username:
            return config_entry


_RE_USERNAME_MASK = re.compile(r"^(\W*)(.).*(.)$")


def mask_username(username: str):
    parts = username.split("@")
    return "@".join(map(lambda x: _RE_USERNAME_MASK.sub(r"\1\2***\3", x), parts))


_T = TypeVar("_T")
_RT = TypeVar("_RT")


async def with_auto_auth(
    api: "SessionAPI",
    async_getter: Callable[..., Coroutine[Any, Any, _RT]],
    *args,
    **kwargs,
) -> _RT:
    try:
        return await async_getter(*args, **kwargs)
    except EmptyResponse:
        # Attempt once more
        return await async_getter(*args, **kwargs)
    except SessionAPIException:
        await api.login()
        return await async_getter(*args, **kwargs)


def float_or_none(s: str | None) -> float | None:
    try:
        return float(s)
    except ValueError:
        return None


def int_or_none(s: str | None) -> int | None:
    try:
        return int(s)
    except ValueError:
        return None
