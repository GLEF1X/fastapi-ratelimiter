from .depends import RateLimited, RedisDependencyMarker
from .middlewares import GlobalRateLimitMiddleware
from .strategies import SlidingWindowLimitStrategy, BucketingRateLimitStrategy

__version__ = "0.0.1"
__author__ = "GLEF1X"

__all__ = (
    "RateLimited",
    "GlobalRateLimitMiddleware",
    "BucketingRateLimitStrategy",
    "SlidingWindowLimitStrategy",
    "RedisDependencyMarker"
)
