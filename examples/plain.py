from dataclasses import asdict

import aioredis
import uvicorn
from fastapi import FastAPI, Depends
from starlette.responses import JSONResponse

from fastapi_ratelimit import RateLimited, RedisDependencyMarker
from fastapi_ratelimit.strategies import BucketingRateLimitStrategy
from fastapi_ratelimit.types import RateLimitStatus

app = FastAPI()
redis = aioredis.from_url("redis://localhost:6400", decode_responses=True, encoding="utf-8")


@app.get("/some_expensive_call", response_class=JSONResponse)
async def handle_test_endpoint(
        ratelimit_status: RateLimitStatus = Depends(RateLimited(BucketingRateLimitStrategy(rate="10/60s")))
):
    return {"hello": "world", **asdict(ratelimit_status)}


app.dependency_overrides[RedisDependencyMarker] = lambda: redis

uvicorn.run(app)
