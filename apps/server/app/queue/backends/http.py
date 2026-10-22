"""Transporte local /v1 con resultados tipados e incertidumbre explícita."""

import asyncio
import json
import math
import re
import time

import httpx
from engine_contract import Estimate, Health, JobStatus, LoadedModel, ModelDescriptor
from pydantic import TypeAdapter

from app.migrations.job_attempt_invariants import validate_contract
from app.settings import Settings

from .protocol import (
    BackendFailure,
    CancelAck,
    ConfirmedAbsent,
    Submission,
    UnloadResult,
)


def checked_id(value):
    if isinstance(value, str) and re.fullmatch(r"[0-7][0-9A-HJKMNP-TV-Z]{25}", value):
        return value
    raise ValueError("Invalid attempt ULID")


class HttpEngineBackend:
    def __init__(
        self,
        settings,
        family,
        *,
        transport=None,
        control_s=30,
        load_s=120,
        silence_s=30,
        stream_s=300,
        max_line_bytes=1024 * 1024,
        clock=time.monotonic,
    ):
        self.origin = Settings.parse_engines({family: settings.engines[family]})[
            family
        ].rstrip("/")
        self.control_s, self.load_s = control_s, load_s
        self.silence_s, self.stream_s = silence_s, stream_s
        self.max_line_bytes, self.clock = max_line_bytes, clock
        if any(
            not math.isfinite(v) or v <= 0
            for v in (control_s, load_s, silence_s, stream_s, max_line_bytes)
        ):
            raise ValueError("Positive finite deadlines and line bound required")
        origin = httpx.URL(self.origin)

        async def guard(request):
            if (request.url.scheme, request.url.host, request.url.port) != (
                origin.scheme,
                origin.host,
                origin.port,
            ):
                raise ValueError("Engine request left configured origin")

        self._client = httpx.AsyncClient(
            base_url=origin,
            transport=transport,
            headers={"X-Studio-Engine-Token": settings.engine_token.get_secret_value()},
            trust_env=False,
            follow_redirects=False,
            timeout=httpx.Timeout(10, read=silence_s),
            event_hooks={"request": [guard]},
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.aclose()

    async def aclose(self):
        await self._client.aclose()

    @staticmethod
    def _media(response, expected):
        actual = (
            response.headers.get("content-type", "").partition(";")[0].strip().lower()
        )
        if actual != expected:
            raise BackendFailure("MEDIA")

    @classmethod
    def _decode(cls, response, status):
        if response.status_code != status:
            code = "HTTP"
            try:
                cls._media(response, "application/problem+json")
                problem = response.json()
                if isinstance(problem, dict) and problem.get("code") in (
                    "BUSY",
                    "MODEL_NOT_FOUND",
                ):
                    code = problem["code"]
            except (ValueError, BackendFailure):
                pass
            raise BackendFailure(code)
        cls._media(response, "application/json")
        try:
            return response.json()
        except ValueError:
            raise BackendFailure("JSON") from None

    async def _exchange(self, method, path, *, payload=None, duration=None):
        bound = self.control_s if duration is None else duration
        try:
            async with asyncio.timeout(bound):
                return await self._client.request(
                    method, path, json=payload, timeout=httpx.Timeout(10, read=bound)
                )
        except (httpx.HTTPError, TimeoutError):
            raise BackendFailure("TRANSPORT") from None

    async def _result(
        self, method, path, dtype, *, payload=None, status=200, duration=None
    ):
        response = await self._exchange(
            method, path, payload=payload, duration=duration
        )
        body = self._decode(response, status)
        try:
            return TypeAdapter(dtype).validate_python(body, strict=True)
        except (ValueError, TypeError):
            raise BackendFailure("BODY") from None

    async def health(self):
        value = await self._result("GET", "/v1/health", Health)
        gpu = value.gpu
        if (
            value.contract_version != "1"
            or not all((value.engine_id, value.engine_version, value.image_digest))
            or any(
                not math.isfinite(v) for v in (gpu.total_mb, gpu.free_mb, gpu.cap_mb)
            )
            or gpu.free_mb > gpu.total_mb
        ):
            raise BackendFailure("HEALTH")
        if value.job_id is not None:
            checked_id(value.job_id)
        return value

    async def models(self):
        return await self._result("GET", "/v1/models", list[ModelDescriptor])

    @staticmethod
    def _wire(request, kind):
        return validate_contract(request, kind).model_dump(mode="json")

    async def load(self, request):
        loaded = await self._result(
            "POST",
            "/v1/load",
            LoadedModel,
            payload=self._wire(request, "load"),
            duration=self.load_s,
        )
        if (loaded.model_id, loaded.mode) != (request.model_id, request.mode):
            raise BackendFailure("IDENTITY")
        return loaded

    async def unload(self):
        return await self._result("POST", "/v1/unload", UnloadResult)

    async def estimate(self, request):
        return await self._result(
            "POST", "/v1/estimate", Estimate, payload=self._wire(request, "request")
        )

    async def submit(self, request):
        ack = await self._result(
            "POST",
            "/v1/jobs",
            Submission,
            status=202,
            payload=self._wire(request, "request"),
        )
        if ack.job_id != request.job_id:
            raise BackendFailure("IDENTITY")
        return ack

    async def status(self, attempt_id):
        checked_id(attempt_id)
        response = await self._exchange("GET", "/v1/jobs/" + attempt_id)
        if response.status_code == 404:
            self._media(response, "application/problem+json")
            try:
                body = response.json()
            except ValueError:
                raise BackendFailure("UNKNOWN_404") from None
            keys = {"type", "title", "status", "detail", "code", "retryable"}
            if (
                isinstance(body, dict)
                and set(body) == keys
                and body["type"] == "about:blank"
                and (
                    body["title"] == body["code"] == "NOT_FOUND"
                    and type(body["status"]) is int
                    and body["status"] == 404
                    and isinstance(body["detail"], str)
                    and body["retryable"] is False
                )
            ):
                return ConfirmedAbsent(attempt_id)
            raise BackendFailure("UNKNOWN_404")
        body = self._decode(response, 200)
        try:
            value = JobStatus.model_validate(body, strict=True)
        except ValueError:
            raise BackendFailure("BODY") from None
        if value.job_id != attempt_id:
            raise BackendFailure("IDENTITY")
        return value

    async def cancel(self, attempt_id):
        checked_id(attempt_id)
        value = await self._result("DELETE", "/v1/jobs/" + attempt_id, CancelAck)
        if value.job_id != attempt_id:
            raise BackendFailure("IDENTITY")
        return value

    async def events(self, attempt_id, after=0):
        checked_id(attempt_id)
        if type(after) is not int or after < 0:
            raise ValueError("Invalid event cursor")
        response = None
        deadline = self.clock() + self.stream_s
        pending = bytearray()
        try:
            async with asyncio.timeout(self.stream_s):
                request = self._client.build_request(
                    "GET", "/v1/jobs/" + attempt_id + "/events", params={"after": after}
                )
                response = await self._client.send(request, stream=True)
                if response.status_code != 200:
                    raise BackendFailure("HTTP")
                self._media(response, "application/x-ndjson")
                chunks = response.aiter_bytes().__aiter__()
                while True:
                    left = deadline - self.clock()
                    if left <= 0:
                        raise BackendFailure("DEADLINE")
                    try:
                        chunk = await asyncio.wait_for(
                            anext(chunks), min(left, self.silence_s)
                        )
                    except StopAsyncIteration:
                        break
                    # LF determina líneas; no decodificar UTF8 antes de completarlas.
                    pieces = chunk.split(b"\n")
                    for index, part in enumerate(pieces):
                        if (
                            len(pending) + len(part) + (index < len(pieces) - 1)
                            > self.max_line_bytes
                        ):
                            raise BackendFailure("LINE_LIMIT")
                        pending.extend(part)
                        if index == len(pieces) - 1:
                            continue
                        if not pending:
                            raise BackendFailure("EMPTY_LINE")
                        event = validate_contract(
                            json.loads(pending.decode("utf-8")), "event"
                        )
                        pending.clear()
                        if event.job_id != attempt_id or event.seq <= after:
                            raise BackendFailure("EVENT_IDENTITY")
                        after = event.seq
                        yield event
                if pending:
                    raise BackendFailure("TRUNCATED_LINE")
        except (httpx.HTTPError, TimeoutError):
            raise BackendFailure("TRANSPORT") from None
        except (ValueError, TypeError, UnicodeError):
            raise BackendFailure("EVENT_BODY") from None
        finally:
            if response is not None:
                await response.aclose()
