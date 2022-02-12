import aioredis
from fastapi import Depends, FastAPI
from starlette.responses import JSONResponse

from fastapi_ratelimiter import RateLimited, RedisDependencyMarker
from fastapi_ratelimiter.strategies import BucketingRateLimitStrategy

app = FastAPI()
app.dependency_overrides[RedisDependencyMarker] = aioredis.from_url("redis://localhost")


@app.get(
    "/some_expensive_call", response_class=JSONResponse,
    dependencies=[
        Depends(RateLimited(BucketingRateLimitStrategy(rate="10/60s")))
    ]
)
async def handle_test_endpoint():
    return {"hello": "world"}
