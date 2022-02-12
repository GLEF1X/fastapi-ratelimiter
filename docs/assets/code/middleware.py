import aioredis
from fastapi import FastAPI
from starlette.responses import JSONResponse

from fastapi_ratelimiter import RedisDependencyMarker
from fastapi_ratelimiter.middlewares import GlobalRateLimitMiddleware
from fastapi_ratelimiter.strategies import BucketingRateLimitStrategy

app = FastAPI()


@app.get("/some_expensive_call", response_class=JSONResponse)
async def handle_test_endpoint():
    return {"hello": "world"}


app.dependency_overrides[RedisDependencyMarker] = aioredis.from_url("redis://localhost")

# 1000 requests per one hour on all routes
app.add_middleware(GlobalRateLimitMiddleware, rate_limit_strategy=BucketingRateLimitStrategy(rate="1000/h"))
