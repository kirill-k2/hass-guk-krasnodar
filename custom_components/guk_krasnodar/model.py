from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .session_api import SessionAPI


@dataclass
class Account:
    id: str
    company_id: str
    number: str
    address: str = ""
    balance: float | None = None
    charge: float | None = None
    api: SessionAPI | None = None

    @property
    def code(self) -> str:
        return f"{self.company_id}_{self.id}"


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

    @property
    def api(self) -> SessionAPI:
        return self.account.api if self.account else None
