from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import Response
import json
from datetime import datetime
import uuid

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class CustomSessionMiddleware(SessionMiddleware):
    def __init__(self, app, secret_key: str):
        super().__init__(app, secret_key)
        self.sessions = {}

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            session_id = request.headers.get("X-Session-ID")
            if session_id and session_id in self.sessions:
                scope["session"] = self.sessions[session_id]
            else:
                scope["session"] = {}

            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    session_id = request.headers.get("X-Session-ID")
                    if not session_id:
                        session_id = str(uuid.uuid4())
                    self.sessions[session_id] = scope["session"]
                    message["headers"].append(
                        (
                            b"x-session-id",
                            session_id.encode("utf-8"),
                        )
                    )
                await send(message)

            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)