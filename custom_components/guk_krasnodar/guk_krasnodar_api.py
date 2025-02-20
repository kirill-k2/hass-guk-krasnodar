import asyncio
import json
import logging
import re
from logging import exception
from typing import Any, Union, SupportsInt, SupportsFloat, Final

import aiohttp

from .model import Account, Meter
from ._util import float_or_none, int_or_none
from .exceptions import (
    ResponseError,
    LoginError,
    EmptyResponse,
    ResponseTimeout,
    SessionAPIException,
    AccessDenied,
)

_log = logging.getLogger(__name__)

DEFAULT_TIMEOUT: Final = aiohttp.ClientTimeout(total=30)

FIELD_DETAIL_METRIC_INDICATION: Final = re.compile(
    "Последнее показание (\\d+) от (.+)г"
)
FIELD_NAME_ACCOUNT_CHARGED: Final = re.compile(
    "Начисление за (.+) \\(основные услуги\\)"
)
FIELD_NAME_ACCOUNT_DEBT: Final = re.compile("Задолженность \\(основные услуги\\)")

API_URL: Final = "https://lk.gukkrasnodar.ru"


def _aiohttp_create_session(*args, **kwargs):
    return aiohttp.ClientSession(*args, **kwargs)


class GUKKrasnodarAPI:
    def __init__(
        self,
        username,
        password,
        timeout: Union[
            SupportsInt, SupportsFloat, aiohttp.ClientTimeout
        ] = DEFAULT_TIMEOUT,
        user_agent: str = "Mozilla/5.0",
        base_url: str = API_URL,
    ):
        self._username = username
        self._password = password
        self._timeout = timeout
        self._user_agent = user_agent
        self._base_url = base_url or API_URL

        if not isinstance(timeout, aiohttp.ClientTimeout):
            if isinstance(timeout, SupportsInt):
                timeout = aiohttp.ClientTimeout(total=int(timeout))
            elif isinstance(timeout, SupportsFloat):
                timeout = aiohttp.ClientTimeout(total=float(timeout))
            else:
                raise TypeError("invalid argument type for timeout provided")

        self._session = _aiohttp_create_session(
            timeout=timeout,
            cookie_jar=aiohttp.CookieJar(),
            headers={aiohttp.hdrs.USER_AGENT: self._user_agent},
        )
        self._token = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self._session.__aexit__(*args)
        await self.async_close()

    async def async_close(self):
        if not self._session.closed:
            await self._session.close()

    @property
    def username(self):
        return self._username

    @property
    def password(self):
        return self._password

    @property
    def timeout(self):
        return self._timeout

    @property
    def user_agent(self):
        return self._user_agent

    @property
    def base_url(self) -> str:
        return self._base_url

    async def __async_request(
        self,
        url: str,
        referer: str = base_url,
        data: dict = None,
        method: str = "GET",
    ) -> Any:
        headers = {
            aiohttp.hdrs.ORIGIN: self.base_url,
            aiohttp.hdrs.REFERER: referer or self.base_url,
            aiohttp.hdrs.CONTENT_TYPE: "application/json",
        }
        if self._token is not None:
            headers[aiohttp.hdrs.AUTHORIZATION] = "Bearer " + self._token

        try:
            if method == "POST":
                async with self._session.post(
                    url, headers=headers, data=json.dumps(data)
                ) as response:
                    response_status = response.status
                    response_text = await response.text()
            elif method == "GET":
                async with self._session.get(url, headers=headers) as response:
                    response_status = response.status
                    response_text = await response.text()
            else:
                raise NotImplementedError

            if response_text is None or not response_text:
                raise EmptyResponse(f"Пустой ответ сервера: [{response_status}]")

            try:
                json_data = json.loads(response_text)
            except json.JSONDecodeError as e:
                _log.debug(f"[{response_status}] {response_text}")
                raise ResponseError(
                    f"Ошибка разбора ответа: [{response_status}] {e.msg}"
                )

            if len(json_data) == 0:
                raise EmptyResponse(f"Пустой ответ сервера: [{response_status}]")

            if response_status == 200 and json_data.get("success", False) is True:
                return json_data
            elif response_status == 400 or response_status == 401:
                _log.warning(f"Ошибка доступа [{response_status}] {response_text}")
                raise AccessDenied(
                    f"Ошибка доступа: [{response_status}] {json_data.get('code', None)}: {json_data.get('message', None)}"
                )
            else:
                _log.debug(f"[{response_status}] {response_text}")
                raise ResponseError(
                    f"Ошибка сервера: [{response_status}] {json_data.get('code', None)}: {json_data.get('message', None)}"
                )

        except aiohttp.ClientError as e:
            raise ResponseError(f"Общая ошибка запроса: {repr(e)}")

        except asyncio.TimeoutError:
            raise ResponseTimeout("Ошибка ожидания ответа от сервера")

    async def _async_get(self, url, referer=None):
        return await self.__async_request(url=url, referer=referer, method="GET")

    async def _async_post(self, url, referer=None, data=None):
        return await self.__async_request(
            url=url, referer=referer, data=data, method="POST"
        )

    async def _async_login(self, login, password):
        self._token = None
        data = {
            "login": login,
            "password": password,
        }
        try:
            response = await self._async_post(
                f"{self.base_url}/api/v1/user/login",
                referer=f"{self.base_url}/login",
                data=data,
            )
        except ResponseError as e:
            raise LoginError(f"Ошибка авторизации {repr(e)}") from e

        token = response.get("token", None)
        if token is not None and token:
            _log.info("Успешная авторизация")
            self._token = token
        else:
            raise LoginError("Ошибка авторизации: нет токена")

    async def async_login(self):
        await self._async_login(self._username, self._password)

    async def async_accounts(self) -> list[Account]:
        response = await self._async_get(
            f"{self.base_url}/api/v1/user/accounts",
            referer=f"{self.base_url}/cabinet/accounts",
        )

        response = response.get("accounts", [])
        _log.info(f"Список лицевых счетов получен ({len(response)})")
        _accounts = [
            Account(
                id=account["id_account"],
                company_id=account["id_company"],
                number=account["account"],
                address=account["address"],
                api=self,
            )
            for account in response
        ]
        _log.debug(_accounts)
        return _accounts

    async def async_update_account_detail(self, account: Account) -> [Account]:
        data = {"id_company": account.company_id, "id_account": account.id}
        response = await self._async_post(
            f"{self.base_url}/api/v1/user/account/info/extend",
            referer=f"{self.base_url}/cabinet/accounts",
            data=data,
        )

        response = response.get("info", [])
        _log.info(f"Детали по счету {account.id} получены ({len(response)})")
        for detail in response:
            if FIELD_NAME_ACCOUNT_DEBT.match(detail["name"]):
                account.balance = float_or_none(detail["value"])
            elif FIELD_NAME_ACCOUNT_CHARGED.match(detail["name"]):
                account.charged = float_or_none(detail["value"])
        _log.debug(account)
        return account

    @staticmethod
    def _parse_last_indication(s: str) -> int | None:
        m = FIELD_DETAIL_METRIC_INDICATION.match(s)
        if not m:
            return None
        return int_or_none(m.group(1))

    async def async_meters(self, account: Account) -> [Meter]:
        data = {"id_company": account.company_id, "id_account": account.id}
        response = await self._async_post(
            f"{self.base_url}/api/v1/user/account/meters",
            referer=f"{self.base_url}/cabinet/accounts/{account.company_id}/{account.id}/meters",
            data=data,
        )

        response = response.get("meter", [])
        _log.info(f"Список счетчиков получен ({len(response)})")
        _meters = [
            Meter(
                id=meter["id_meter"],
                title=meter["title"],
                account=account,
                detail=meter["detail"],
                info=meter["info"],
                last_indication=self._parse_last_indication(meter["detail"]),
            )
            for meter in response
        ]
        _log.debug(_meters)
        return _meters

    async def async_send_measure(self, meter: Meter, value: int):
        data = {
            "id_company": meter.account.company_id,
            "id_account": meter.account.id,
            "id_meter": meter.id,
            "value": value,
            "volume": None,
        }
        try:
            await self._async_post(
                f"{self.base_url}/api/v1/user/account/meter/measure/set",
                referer=f"{self.base_url}/cabinet/accounts/{meter.account.company_id}/{meter.account.id}/meters",
                data=data,
            )
        except SessionAPIException as e:
            raise ResponseError(f"Ошибка передачи показаний {str(e)}")

        _log.info(f"Показания переданы. {meter.title}: {value}")


async def async_push_measure(
    username: str,
    password: str,
    account_number: str,
    meter_title: str,
    meter_value: int,
):
    async with GUKKrasnodarAPI(username=username, password=password) as api:
        await api.async_login()

        account = next(
            (
                account
                for account in await api.async_accounts()
                if account.number == account_number
            ),
            None,
        )
        if account is None:
            raise Exception(f"Ошибка: лицевой счет {account_number} не найден")

        meter = next(
            (
                meter
                for meter in await api.async_meters(account=account)
                if meter.title == meter_title
            ),
            None,
        )
        if meter is None:
            raise exception(f"Ошибка: счетчик {meter_title} не найден")

        await api.async_send_measure(meter=meter, value=meter_value)
