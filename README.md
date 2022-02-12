# FastAPI Ratelimit

[![PyPI version](https://img.shields.io/pypi/v/fastapi-ratelimiter.svg)]

**Documentation**: https://fastapi-ratelimit.readthedocs.io/en/latest/ 

## Quick start:

```python

import asyncio

import aioredis
import uvicorn
from fastapi import FastAPI, Depends
from starlette.responses import JSONResponse

from fastapi_ratelimit import RateLimited, RedisDependencyMarker
from fastapi_ratelimit.strategies import BucketingRateLimitStrategy

app = FastAPI()
redis = aioredis.from_url("redis://localhost", decode_responses=True, encoding="utf-8")


@app.get(
    "/some_expensive_call", response_class=JSONResponse,
    dependencies=[
        Depends(RateLimited(BucketingRateLimitStrategy(rate="10/60s")))
    ]
)
async def handle_test_endpoint():
    await asyncio.sleep(5)
    return {"hello": "world"}


app.dependency_overrides[RedisDependencyMarker] = lambda: redis

uvicorn.run(app)

```