from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from django_redis import get_redis_connection


@database_sync_to_async
def get_user_from_ticket(ticket):
    from authentication.models import CustomUser

    redis_conn = get_redis_connection("default")
    key = f"ws_ticket:{ticket}"
    user_id = redis_conn.get(key)

    if user_id is None:
        return AnonymousUser()

    redis_conn.delete(key)  # single-use: burn it immediately

    try:
        return CustomUser.objects.get(pk=user_id.decode())
    except CustomUser.DoesNotExist:
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query_string = parse_qs(scope["query_string"].decode())
        ticket = query_string.get("ticket", [None])[0]

        if ticket:
            scope["user"] = await get_user_from_ticket(ticket)
        else:
            scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)