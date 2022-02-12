from __future__ import annotations

import re
from dataclasses import dataclass

_PERIODS = {
    's': 1,
    'm': 60,
    'h': 60 * 60,
    'd': 24 * 60 * 60,
}

# Following regexp catches such strings:
#    100/5m
#    100/300s

rate_re = re.compile(r'([\d]+)/([\d]*)([smhd])?')


@dataclass
class RateLimitConfig:
    max_count: int
    period_in_seconds: int

    @classmethod
    def from_string(cls, rate: str) -> RateLimitConfig:
        request_count_per_period, multi, period = rate_re.match(rate).groups()
        request_count_per_period = int(request_count_per_period)
        if not period:
            period = 's'
        seconds = _PERIODS[period.lower()]
        if multi:
            seconds *= int(multi)
        return cls(request_count_per_period, seconds)


@dataclass
class RateLimitStatus:
    number_of_requests: int
    ratelimit_config: RateLimitConfig
    time_left: int

    @property
    def remaining_number_of_requests(self) -> int:
        return self.limit - self.number_of_requests

    @property
    def limit(self) -> int:
        return self.ratelimit_config.max_count

    @property
    def should_limit(self) -> bool:
        return self.number_of_requests > self.limit