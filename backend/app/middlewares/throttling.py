from fastapi import FastAPI, Request
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Callable, Awaitable
from redis import asyncio as aioredis
from typing import Union

from backend.app.utils.throttling import ip_identifier
from backend.app.utils.request import get_token, get_route
from backend.app.utils.throttling import ip_identifier
from backend.app.base.auth import get_current_user
from backend.app.base.exceptions import MissingTokenException, TooManyRequestsException
from backend.app.base.config import settings
from backend.app.data.auth import ROLES_METADATA
from backend.app.base.logging import logger

class RateLimiterPolicy:
    def __init__(
        self, 
        times: int = 5, 
        hours: int = 0,     
        minutes: int = 1, 
        seconds: int = 0, 
        milliseconds: int = 0
    ):
        self.times = times
        self.hours = hours
        self.minutes = minutes
        self.seconds = seconds
        self.milliseconds = milliseconds


async def init_redis_pool():
    return await aioredis.Redis.from_url(settings.redis_url)


async def init_rate_limiter():
    redis = await init_redis_pool()
    await FastAPILimiter.init(redis)
    
    logger.info("Rate limiter initialized!")


# Given rate limiter, find throughput
def get_throughput(rate_limiter: RateLimiterPolicy):
    times = rate_limiter.times
    interval_seconds = rate_limiter.hours * 3600 + \
        rate_limiter.minutes * 60 + \
        rate_limiter.seconds + \
        rate_limiter.milliseconds / 1000
    
    return times / interval_seconds


def get_rate_limiter(
    user_identifier: Union[str, None], 
    policy: RateLimiterPolicy = RateLimiterPolicy()
):
    return RateLimiter(
        times=policy.times, 
        hours=policy.hours,
        minutes=policy.minutes,
        seconds=policy.seconds,
        milliseconds=policy.milliseconds,
        identifier=user_identifier
    )

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        route = get_route(request)

        # Check if the route requires authentication
        if settings.route_requires_authentication(route):
            token = get_token(request)

            if not token:
                raise MissingTokenException()

            current_user = await get_current_user(token)
            user_identifier = current_user.user_username
            roles = current_user.user_roles
            rate_policies = [
                ROLES_METADATA[role]['rate_policy'] for role in roles
            ]

            # Get the most permissive rate policy
            rate_policy = max(rate_policies, key=get_throughput)
            
        else:
            # Handle non-authenticated routes
            user_identifier = await ip_identifier(request)
            rate_policy = RateLimiterPolicy()  # Default rate policy for non-authenticated routes
        
        limiter = get_rate_limiter(user_identifier, rate_policy)

        if not await limiter.check(request, route):
            raise TooManyRequestsException()

        response = await call_next(request)
        
        return response
