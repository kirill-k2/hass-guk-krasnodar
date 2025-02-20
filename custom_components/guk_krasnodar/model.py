from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .guk_krasnodar_api import GUKKrasnodarAPI


@dataclass
class Account:
    id: str
    company_id: str
    number: str
    address: str = ""
    balance: float | None = None
    charged: float | None = None

    # @todo - вынести api в coordinator или аналогичный механизм
    api: GUKKrasnodarAPI | None = field(default=None, repr=False)

    @property
    def code(self) -> str:
        return f"{self.company_id}_{self.id}"

    async def api_meters(self):
        return await self.api.async_meters(self)

    async def api_update_account_detail(self):
        return await self.api.async_update_account_detail(self)


@dataclass
class Meter:
    id: str
    title: str
    detail: str = ""
    info: str | list[str] | None = None
    last_indication: int | None = None
    last_indications_date: str | None = None
    account: Account | None = None

    @property
    def code(self) -> str:
        return self.id

    async def api_send_indication(self, indications: int | None):
        if indications is not None:
            await self.account.api.async_send_measure(self, value=indications)
