import abc
import hashlib
import inspect
import time
import zlib
from typing import Sequence, Union, Callable, Optional, Awaitable

from aioredis.client import Pipeline, Redis
from starlette.requests import Request

from fastapi_ratelimiter.types import RateLimitConfig, RateLimitStatus
from fastapi_ratelimiter.utils import extract_ip_from_request

DEFAULT_PREFIX = "rl:"

# Extend the expiration time by a few seconds to avoid misses.
EXPIRATION_FUDGE = 5
RequestIdentifierFactoryType = Callable[[Request], Union[str, bytes, Awaitable[Union[str, bytes]]]]


class AbstractRateLimitStrategy(abc.ABC):

    def __init__(
            self,
            rate: str,
            prefix: str = DEFAULT_PREFIX,
            request_identifier_factory: Optional[RequestIdentifierFactoryType] = None,
            group: Optional[str] = None
    ):
        if request_identifier_factory is None:
            request_identifier_factory = extract_ip_from_request
        self._request_identifier_factory = request_identifier_factory
        self._ratelimit_config = RateLimitConfig.from_string(rate)
        self._prefix = prefix
        self._group = group

    @abc.abstractmethod
    async def get_ratelimit_status(self, request: Request) -> RateLimitStatus:
        pass

    async def _get_request_identifier(self, request: Request) -> Union[str, bytes]:
        if (
                inspect.iscoroutine(self._request_identifier_factory)
                or inspect.iscoroutinefunction(self._request_identifier_factory)
        ):
            return await self._response_on_limit_exceeded(request)  # type: ignore

        return self._request_identifier_factory(request)


class BucketingRateLimitStrategy(AbstractRateLimitStrategy):

    async def get_ratelimit_status(self, request: Request) -> RateLimitStatus:
        request_identifier = await self._get_request_identifier(request)
        window = self._get_window(request_identifier)
        storage_key = self._create_storage_key(request_identifier, str(window))

        redis: Redis = request.state.redis
        async with redis.pipeline() as pipe:  # type: Pipeline
            pipeline_result: Sequence[int, bool] = await (
                pipe.incr(storage_key).expire(
                    storage_key,
                    self._ratelimit_config.period_in_seconds + EXPIRATION_FUDGE
                ).execute()
            )

        number_of_requests = pipeline_result[0]
        return RateLimitStatus(
            number_of_requests=number_of_requests,
            ratelimit_config=self._ratelimit_config,
            time_left=window - int(time.time())
        )

    def _create_storage_key(self, *parts: str) -> str:
        safe_rate = '%d/%ds' % (self._ratelimit_config.max_count, self._ratelimit_config.period_in_seconds)
        key_parts = [safe_rate, *parts]
        if self._group is not None:
            key_parts.insert(0, self._group)
        return self._prefix + hashlib.md5(u''.join(key_parts).encode('utf-8')).hexdigest()

    def _get_window(self, request_identifier: Union[str, bytes]) -> int:
        """
        Given a request identifier, and time period return when the end of the current time
        period for rate evaluation is.
        """
        period = self._ratelimit_config.period_in_seconds
        epoch_time = int(time.time())
        if period == 1:
            return epoch_time
        if not isinstance(request_identifier, bytes):
            request_identifier = request_identifier.encode('utf-8')
        # This logic determines either the last or current end of a time period.
        # Subtracting (epoch_time % period) gives us the a consistent edge from the epoch.
        # We use (zlib.crc32(value) % period) to add a consistent jitter so that
        # all time periods don't end at the same time.
        w = epoch_time - (epoch_time % period) + (zlib.crc32(request_identifier) % period)
        if w < epoch_time:
            return w + period
        return w


class SlidingWindowLimitStrategy(AbstractRateLimitStrategy):
    async def get_ratelimit_status(self, request: Request) -> RateLimitStatus:
        storage_key = await self._create_storage_key(request)
        epoch_time = int(time.time() * 1000)

        redis: Redis = request.state.redis
        async with redis.pipeline() as pipe:  # type: Pipeline
            result = await (
                pipe.zremrangebyscore(
                    storage_key, 0, epoch_time - (self._ratelimit_config.period_in_seconds * 100)
                ).zadd(
                    storage_key,
                    {f"{epoch_time}:1": epoch_time}
                ).zrange(
                    storage_key, 0, -1
                ).expire(
                    storage_key, (self._ratelimit_config.period_in_seconds * 1000) + 1
                ).execute()
            )

        number_of_requests = 0
        for set_key in result[2]:  # type: str
            if isinstance(set_key, bytes):
                set_key = set_key.decode("utf-8")

            number_of_requests += int(set_key.split(':')[-1])

        return RateLimitStatus(
            number_of_requests=number_of_requests,
            ratelimit_config=self._ratelimit_config,
            time_left=-1
        )

    async def _create_storage_key(self, request: Request):
        request_identifier = await self._get_request_identifier(request)
        group_name = f"{self._group}:" if self._group is not None else ""
        return f"{group_name}{self._prefix}:{request_identifier}"
