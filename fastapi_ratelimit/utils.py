from __future__ import annotations

from starlette.requests import Request


def extract_ip_from_request(request: Request) -> str:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        ip = forwarded_for.split(",")[0]
    else:
        ip = request.client.host
    return ip
