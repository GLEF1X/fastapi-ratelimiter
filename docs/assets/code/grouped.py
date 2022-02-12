from dataclasses import asdict

import aioredis
import uvicorn
from fastapi import FastAPI, Depends
from starlette.responses import JSONResponse

from fastapi_ratelimiter import RateLimited, RedisDependencyMarker
from fastapi_ratelimiter.strategies import BucketingRateLimitStrategy
from fastapi_ratelimiter.types import RateLimitStatus

redis = aioredis.from_url("redis://localhost")
app = FastAPI()
app.dependency_overrides[RedisDependencyMarker] = aioredis.from_url("redis://localhost")


@app.get("/handler1", response_class=JSONResponse)
async def handler1(
        ratelimit_status: RateLimitStatus = Depends(
            RateLimited(
                BucketingRateLimitStrategy(rate="10/h", group="expensive")
            )
        )
):
    return {"hello": "world", **asdict(ratelimit_status)}


@app.get("/handler2", response_class=JSONResponse)
async def handler2(
        ratelimit_status: RateLimitStatus = Depends(
            RateLimited(
                BucketingRateLimitStrategy(rate="10/h", group="expensive"),
            )
        )
):
    return {"hello": "world", **asdict(ratelimit_status)}


if __name__ == '__main__':
    uvicorn.run(app)
