from typing import Mapping

import httpx
from loguru import logger
from pydantic import BaseModel


class ServiceError(Exception):
    pass


class ServiceResponseError(ServiceError):
    def __init__(self, message: str, response: httpx.Response):
        super().__init__(message)
        self.response = response


DEFAULT_TIMEOUT = 60.0
DEFAULT_CONNECT_TIMEOUT = 5.0


class Service:
    def __init__(
        self,
        base_url: str,
        timeout: float = DEFAULT_TIMEOUT,
        connect_timeout: float = DEFAULT_CONNECT_TIMEOUT,
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.connect_timeout = connect_timeout

    async def _make_request(self, method: str, path: str, json=None, params=None):
        timeout_config = self._get_timeout_config()
        log_prefix = self._log_prefix(path=path, method=method)

        async with httpx.AsyncClient(base_url=self.base_url, timeout=timeout_config) as client:
            try:
                logger.info(f"{log_prefix} requested: {json or params}")
                response = await client.request(method, path, json=json, params=params)
                logger.info(f"{log_prefix} response: {response.text}")
                response.raise_for_status()
            except httpx.RequestError as exc:
                logger.error(f"{log_prefix} request failed: {repr(exc)}")
                raise ServiceError(str(exc)) from exc
            except httpx.HTTPStatusError as exc:
                logger.error(
                    f"{log_prefix} non-2xx response: " f"code={exc.response.status_code} response={exc.response.text}"
                )
                raise ServiceResponseError(str(exc), exc.response) from exc

        return response.json()

    async def _make_post_request(self, path: str, dto_in: BaseModel | None) -> dict:
        json_data = dto_in.model_dump() if dto_in else None
        return await self._make_request("POST", path, json=json_data)

    async def _make_get_request(self, path: str, query_params: Mapping = {}):
        return await self._make_request("GET", path, params=query_params)

    def _log_prefix(self, *, path: str, method: str):
        return f"{method} {self.__class__.__name__} {path}"

    def _get_timeout_config(self, custom_timeout: float | None = None):
        return httpx.Timeout(custom_timeout or self.timeout, connect=self.connect_timeout)
