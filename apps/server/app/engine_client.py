"""Cliente mínimo autenticado; no encola ni ejecuta trabajos."""

import httpx


def engine_client(settings, family, *, transport=None):
    base = httpx.URL(settings.engines[family])

    def check_destination(request):
        if (request.url.scheme, request.url.host, request.url.port) != (
            base.scheme,
            base.host,
            base.port,
        ):
            raise ValueError(
                "Engine request must remain on the configured local origin"
            )

    return httpx.Client(
        base_url=base,
        headers={"X-Studio-Engine-Token": settings.engine_token.get_secret_value()},
        timeout=10,
        trust_env=False,
        follow_redirects=False,
        transport=transport,
        event_hooks={"request": [check_destination]},
    )
