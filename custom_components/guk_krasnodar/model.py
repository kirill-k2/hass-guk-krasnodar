from dataclasses import dataclass


@dataclass
class Account:
    id: str
    company_id: str
    number: str
    address: str


@dataclass
class Meter:
    id: str
    title: str
    detail: str
    info: str
