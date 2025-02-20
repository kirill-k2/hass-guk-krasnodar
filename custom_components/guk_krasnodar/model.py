from __future__ import annotations
from dataclasses import dataclass
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
    api: GUKKrasnodarAPI | None = None

    @property
    def code(self) -> str:
        return f"{self.company_id}_{self.id}"

    def api_meters(self):
        return self.api.async_meters(self)

    def api_update_account_detail(self):
        return self.api.async_update_account_detail(self)


@dataclass
class Meter:
    id: str
    title: str
    detail: str = ""
    info: str = ""
    last_indication: int | None = None
    account: Account | None = None

    @property
    def code(self) -> str:
        return self.id

    def api_send_indication(self, indication: int | None):
        if indication is not None:
            self.account.api.async_send_measure(self, indication)
