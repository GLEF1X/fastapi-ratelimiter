import abc
import inspect
from http import HTTPStatus
from typing import Callable, Optional, Union, Awaitable

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response, PlainTextResponse
from starlette.types import ASGIApp

from fastapi_ratelimiter.strategies import AbstractRateLimitStrategy


def _default_response_on_limit_exceeded(r: Request) -> Response:
    return PlainTextResponse(
        "Too many requests!", status_code=HTTPStatus.TOO_MANY_REQUESTS
    )


class BaseRateLimitMiddleware(BaseHTTPMiddleware, abc.ABC):
    def __init__(
            self,
            app: ASGIApp,
            response_on_limit_exceeded: Optional[
                Callable[[Request], Union[Awaitable[Response], Response]]
            ] = None
    ):
        super().__init__(app)

        if response_on_limit_exceeded is None:
            response_on_limit_exceeded = _default_response_on_limit_exceeded
        self._response_on_limit_exceeded = response_on_limit_exceeded


class GlobalRateLimitMiddleware(BaseRateLimitMiddleware):
    def __init__(
            self,
            app: ASGIApp,
            rate_limit_strategy: AbstractRateLimitStrategy,
            response_on_limit_exceeded: Optional[
                Callable[[Request], Union[Awaitable[Response], Response]]
            ] = None
    ):
        super().__init__(app, response_on_limit_exceeded)
        self._rate_limit_strategy = rate_limit_strategy

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        ratelimit_status = await self._rate_limit_strategy.get_ratelimit_status(request)
        if ratelimit_status.should_limit:
            return await self._execute_response_on_limit_exceeded_callback(request)

        return await call_next(request)

    async def _execute_response_on_limit_exceeded_callback(self, request: Request) -> Response:
        if (
                inspect.iscoroutine(self._response_on_limit_exceeded)
                or inspect.iscoroutinefunction(self._response_on_limit_exceeded)
        ):
            return await self._response_on_limit_exceeded(request)  # type: ignore

        return self._response_on_limit_exceeded(request)
