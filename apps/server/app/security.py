"""Frontera ASGI: Host y Origin se validan antes de resolver rutas."""

from .errors import problem

METHODS = {"GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"}
HEADERS = {
    "content-type",
    "if-match",
    "last-event-id",
    "x-studio-session-token",
}
EVENT_HEADERS = HEADERS | {"x-studio-session-token"}
SESSION_PREFLIGHT = {
    "/api/session/bootstrap": ("POST", "x-studio-session-bootstrap"),
    "/api/session": ("DELETE", "x-studio-session-token"),
}


class LocalSecurity:
    def __init__(self, app, settings):
        self.app = app
        self.settings = settings

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = scope["headers"]
        session_path = scope["path"] in SESSION_PREFLIGHT
        if session_path:
            original_send = send

            async def private_send(message):
                if message["type"] == "http.response.start":
                    message = {
                        **message,
                        "headers": [
                            *(
                                item
                                for item in message["headers"]
                                if item[0].lower() != b"cache-control"
                            ),
                            (b"cache-control", b"no-store"),
                        ],
                    }
                await original_send(message)

            send = private_send
        hosts = [v.decode("latin1") for k, v in headers if k.lower() == b"host"]
        origins = [v.decode("latin1") for k, v in headers if k.lower() == b"origin"]
        if len(hosts) != 1 or hosts[0] not in self.settings.allowed_hosts:
            return await problem("INVALID_HOST")(scope, receive, send)
        if session_path and (
            len(headers) > 128
            or hosts[0].split(":", 1)[0] not in {"127.0.0.1", "localhost"}
            or ":" not in hosts[0]
        ):
            return await problem("INVALID_HOST")(scope, receive, send)
        method = scope["method"]
        is_sse = scope["path"].startswith("/api/events") or any(
            k.lower() == b"accept" and b"text/event-stream" in v.lower()
            for k, v in headers
        )
        same_origin = origins == [self.settings.web_origin]
        if (origins or method not in {"GET", "HEAD"} or is_sse) and not same_origin:
            return await problem("FORBIDDEN_ORIGIN")(scope, receive, send)

        async def cors_send(message):
            if message["type"] == "http.response.start" and same_origin:
                message = {
                    **message,
                    "headers": [
                        *message["headers"],
                        (
                            b"access-control-allow-origin",
                            self.settings.web_origin.encode("ascii"),
                        ),
                        (b"vary", b"Origin"),
                    ],
                }
            await send(message)

        if method == "OPTIONS":
            # No existe una superficie CORS genérica bajo ``/api/session``:
            # sólo los dos endpoints exactos de bootstrap y cierre pueden
            # negociar preflight. Evita que una barra o subruta desconocida
            # herede accidentalmente la política global.
            if scope["path"].startswith("/api/session/") and not session_path:
                return await problem("INVALID_PARAMS", 400)(scope, receive, cors_send)
            requested_methods = [
                v.decode("latin1")
                for k, v in headers
                if k.lower() == b"access-control-request-method"
            ]
            requested_headers = [
                v.decode("latin1")
                for k, v in headers
                if k.lower() == b"access-control-request-headers"
            ]
            allowed = (
                len(requested_methods) == 1
                and requested_methods[0] in METHODS
                and len(requested_headers) <= 1
            )
            event_path = scope["path"].startswith("/api/events")
            if event_path:
                allowed = allowed and requested_methods == ["GET"]
            if requested_headers:
                allowed_headers = EVENT_HEADERS if event_path else HEADERS
                allowed = (
                    allowed
                    and {h.strip().lower() for h in requested_headers[0].split(",")}
                    <= allowed_headers
                )
            if session_path:
                expected_method, expected_header = SESSION_PREFLIGHT[scope["path"]]
                allowed = (
                    requested_methods == [expected_method]
                    and len(requested_headers) == 1
                    and len(requested_headers[0]) <= 64
                    and requested_headers[0].strip(" \t").lower() == expected_header
                )
            if not allowed:
                return await problem("INVALID_PARAMS", 400)(scope, receive, cors_send)
            from starlette.responses import Response

            response = Response(
                status_code=200,
                headers={
                    "Access-Control-Allow-Methods": expected_method
                    if session_path
                    else "GET"
                    if event_path
                    else ", ".join(sorted(METHODS)),
                    "Access-Control-Allow-Headers": expected_header
                    if session_path
                    else requested_headers[0]
                    if event_path
                    else ", ".join(sorted(HEADERS)),
                    "Access-Control-Max-Age": "600",
                    "Vary": "Access-Control-Request-Method, Access-Control-Request-Headers",
                },
            )
            return await response(scope, receive, cors_send)
        await self.app(scope, receive, cors_send)
