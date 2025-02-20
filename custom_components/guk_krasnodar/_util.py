from __future__ import annotations

import re
from typing import Any, TypeVar, Callable, Coroutine, TYPE_CHECKING

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_USERNAME
from homeassistant.core import callback, HomeAssistant
from homeassistant.helpers.entity_platform import EntityPlatform

from .exceptions import EmptyResponse, AccessDenied, LoginError
from .const import DOMAIN

if TYPE_CHECKING:
    from .guk_krasnodar_api import GUKKrasnodarAPI


def _make_log_prefix(
    config_entry: Any | ConfigEntry, domain: Any | EntityPlatform, *args
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
) -> config_entries.ConfigEntry | None:
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
    api: GUKKrasnodarAPI,
    async_getter: Callable[..., Coroutine[Any, Any, _RT]],
    *args,
    **kwargs,
) -> _RT:
    try:
        return await async_getter(*args, **kwargs)
    except EmptyResponse:
        # Attempt once more
        return await async_getter(*args, **kwargs)
    # @todo уточнить ошибки протухания токена - вероятно, в отдельный эксепшн
    except AccessDenied or LoginError:
        await api.async_login()
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
