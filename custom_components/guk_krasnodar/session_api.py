import logging
from logging import exception
from typing import Any, Union, SupportsInt, SupportsFloat, Final, Optional
import asyncio
import aiohttp

import json

from .exceptions import ResponseError, LoginError, EmptyResponse, ResponseTimeout
from .model import Account, Meter

_log = logging.getLogger(__name__)

DEFAULT_TIMEOUT: Final = aiohttp.ClientTimeout(total=30)


class SessionAPI:
    def __init__(
        self,
        username,
        password,
        timeout: Union[
            SupportsInt, SupportsFloat, aiohttp.ClientTimeout
        ] = DEFAULT_TIMEOUT,
        user_agent: str = "okhttp/3.7.0",
    ):
        self._username = username
        self._password = password
        self._token = None

        if not isinstance(timeout, aiohttp.ClientTimeout):
            if isinstance(timeout, SupportsInt):
                timeout = aiohttp.ClientTimeout(total=int(timeout))
            elif isinstance(timeout, SupportsFloat):
                timeout = aiohttp.ClientTimeout(total=float(timeout))
            else:
                raise TypeError("invalid argument type for timeout provided")

        self._session = aiohttp.ClientSession(
            timeout=timeout,
            cookie_jar=aiohttp.CookieJar(),
            headers={aiohttp.hdrs.USER_AGENT: user_agent},
        )

        self._main_account: Optional[Account] = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self._session.__aexit__(*args)
        await self.async_close()

    async def async_close(self):
        if not self._session.closed:
            await self._session.close()

    @property
    def base_url(self) -> str:
        return "https://lk.gukkrasnodar.ru"

    async def __request(
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

            if response_status == 200 and json_data.get("success", False) is True:
                return json_data
            else:
                _log.debug(f"[{response_status}] {response_text}")
                raise ResponseError(
                    f"Ошибка сервера: [{response_status}] {json_data.get('code', None)}: {json_data.get('message', None)}"
                )

        except aiohttp.ClientError as e:
            raise ResponseError(f"Общая ошибка запроса: {repr(e)}")

        except asyncio.TimeoutError:
            raise ResponseTimeout("Ошибка ожидания ответа от сервера")

    async def _get(self, url, referer=None):
        return await self.__request(url=url, referer=referer, method="GET")

    async def _post(self, url, referer=None, data=None):
        return await self.__request(url=url, referer=referer, data=data, method="POST")

    async def _login(self, login, password):
        self._token = None
        data = {
            "login": login,
            "password": password,
        }
        try:
            response = await self._post(
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

    async def login(self):
        await self._login(self._username, self._password)

    async def accounts(self) -> list[Account]:
        response = await self._get(
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
            )
            for account in response
        ]
        _log.debug(_accounts)
        return _accounts

    async def meters(self, account: Account) -> [Meter]:
        data = {"id_company": account.company_id, "id_account": account.id}
        response = await self._post(
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
                detail=meter["detail"],
                info=meter["info"],
            )
            for meter in response
        ]
        _log.debug(_meters)
        return _meters

    async def send_measure(self, account: Account, meter: Meter, value: int):
        data = {
            "id_company": account.company_id,
            "id_account": account.id,
            "id_meter": meter.id,
            "value": value,
            "volume": None,
        }
        try:
            await self._post(
                f"{self.base_url}/api/v1/user/account/meter/measure/set",
                referer=f"{self.base_url}/cabinet/accounts/{account.company_id}/{account.id}/meters",
                data=data,
            )
        except ResponseError as e:
            raise ResponseError(f"Ошибка передачи показаний {str(e)}")

        _log.info(f"Показания переданы. {meter.title}: {value}")


async def push_measure(
    username: str,
    password: str,
    account_number: str,
    meter_title: str,
    meter_value: int,
):
    async with SessionAPI(username=username, password=password) as session:
        await session.login()

        account = next(
            (
                account
                for account in await session.accounts()
                if account.number == account_number
            ),
            None,
        )
        if account is None:
            raise Exception(f"Ошибка: лицевой счет {account_number} не найден")

        meter = next(
            (
                meter
                for meter in await session.meters(account=account)
                if meter.title == meter_title
            ),
            None,
        )
        if meter is None:
            raise exception(f"Ошибка: счетчик {meter_title} не найден")

        await session.send_measure(account=account, meter=meter, value=meter_value)
