import inspect
from http import HTTPStatus
from typing import Any, TypeVar, Callable, Optional, Union, Awaitable

from aioredis import Redis
from fastapi import Depends, HTTPException
from starlette.requests import Request

from fastapi_ratelimiter.strategies import AbstractRateLimitStrategy, RateLimitStatus

T = TypeVar("T", bound=Callable[..., Any])


class RedisDependencyMarker:
    pass


class RateLimited:

    def __init__(
            self,
            rate_limit_strategy: AbstractRateLimitStrategy,
            response_on_limit_exceeded: Optional[
                Union[
                    Callable[[Request], Union[Awaitable[HTTPException], HTTPException]],
                    HTTPException
                ]
            ] = None,
    ):
        self._rate_limit_strategy = rate_limit_strategy

        if response_on_limit_exceeded is None:
            response_on_limit_exceeded = HTTPException(
                status_code=HTTPStatus.TOO_MANY_REQUESTS,
                detail="Too many requests!"
            )

        self._response_on_limit_exceeded = response_on_limit_exceeded

    async def __call__(self, request: Request,
                       redis: Redis = Depends(RedisDependencyMarker)) -> RateLimitStatus:
        request.state.redis = redis

        ratelimit_status = await self._rate_limit_strategy.get_ratelimit_status(request)
        if ratelimit_status.should_limit:
            raise await self._get_response_on_limit_exceeded(request)

        return ratelimit_status

    async def _get_response_on_limit_exceeded(self, request: Request) -> HTTPException:
        if isinstance(self._response_on_limit_exceeded, HTTPException):
            return self._response_on_limit_exceeded

        if (
                inspect.iscoroutine(self._response_on_limit_exceeded)
                or inspect.iscoroutinefunction(self._response_on_limit_exceeded)
        ):
            return await self._response_on_limit_exceeded(request)  # type: ignore

        return self._response_on_limit_exceeded(request)
