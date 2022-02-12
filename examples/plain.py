import aioredis
import uvicorn
from fastapi import FastAPI, Depends
from starlette.responses import JSONResponse

from fastapi_ratelimiter import RateLimited, SlidingWindowLimitStrategy, RedisDependencyMarker

app = FastAPI()
redis = aioredis.from_url("redis://localhost:6400", decode_responses=True, encoding="utf-8")


@app.get("/some_expensive_call", response_class=JSONResponse,
         dependencies=[
             Depends(RateLimited(SlidingWindowLimitStrategy(rate="10/60s")))
         ])
async def handle_test_endpoint():
    return {"hello": "world"}


app.dependency_overrides[RedisDependencyMarker] = lambda: redis

uvicorn.run(app)
