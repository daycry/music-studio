"""Factoría del server."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException

from .api_models import HealthDTO, ProblemDTO
from .backup import DailyBackup
from .db import create_db_engine, migrate
from .domain_routes import register_domain_routes
from .errors import problem
from .event_routes import local_owner, register_session_routes
from .local_sessions import LocalSessionRegistry
from .logging import configure_logging
from .security import LocalSecurity
from .settings import Settings
from .snapshots import reconcile


def create_app(
    settings=None, *, queue_runtime_factory=None, session_registry_factory=None
):
    settings = settings if settings is not None else Settings()
    # Logger aislado: no hereda handlers globales ni escribe antes del lifespan.
    logger = logging.Logger("studio.server.prestartup")  # noqa: LOG001
    logger.addHandler(logging.NullHandler())
    logger.propagate = False

    @asynccontextmanager
    async def lifespan(application):
        nonlocal logger
        engine = None
        scheduler = None
        runtime = None
        registry = None
        storage_lease = None
        original_error = None
        try:
            # La validación del montaje es la primera operación con efectos de
            # arranque. Si el UUID está configurado, un bind incorrecto,
            # 9p/tmpfs o una raíz reubicada detiene el proceso antes de logs,
            # migraciones, backup o cola.
            if settings.storage_uuid is not None:
                from studio_storage_guard.preflight import verify_root

                storage_lease = verify_root(
                    settings.data_dir, str(settings.storage_uuid), "server"
                )
            logger = configure_logging(settings)
            database = settings.data_dir / "db" / "studio.sqlite"
            await asyncio.to_thread(migrate, database)
            engine = create_db_engine(database, data_dir=settings.data_dir)
            application.state.db = engine
            owner = await asyncio.to_thread(local_owner, engine)
            registry = (session_registry_factory or LocalSessionRegistry)(owner)
            application.state.session_registry = registry
            application.state.session_owner_id = owner
            scheduler = DailyBackup(database, settings.data_dir / "backups", logger)
            application.state.backup = scheduler
            await asyncio.to_thread(reconcile, engine, settings.data_dir, startup=True)
            await scheduler.initial()
            scheduler.start()
            from .queue.runtime import QueueRuntime

            factory = queue_runtime_factory or QueueRuntime
            runtime = factory(engine, settings)
            application.state.queue = runtime
            await runtime.start()
            logger.info("server.started")
            yield
        except BaseException as error:
            original_error = error
            raise
        finally:

            async def cleanup():
                try:
                    try:
                        if runtime is not None:
                            await runtime.close()
                    finally:
                        if scheduler is not None:
                            scheduler.stop.set()
                            scheduler.cancel.set()
                            if hasattr(scheduler, "task"):
                                await scheduler.close()
                            else:
                                await asyncio.to_thread(
                                    scheduler.executor.shutdown,
                                    wait=True,
                                    cancel_futures=True,
                                )
                finally:
                    try:
                        try:
                            if registry is not None:
                                registry.close()
                        finally:
                            if engine is not None:
                                engine.dispose()
                    finally:
                        logger.info("server.stopped")
                        for handler in list(logger.handlers):
                            logger.removeHandler(handler)
                            handler.close()
                    if storage_lease is not None:
                        storage_lease.close()

            cleanup_task = asyncio.create_task(cleanup())
            try:
                await asyncio.shield(cleanup_task)
            except asyncio.CancelledError as cancellation:
                try:
                    await cleanup_task
                except BaseException:  # noqa: BLE001 - Preserva la causa tras el cleanup.
                    cause = (
                        original_error if original_error is not None else cancellation
                    )
                    cause.add_note("server.cleanup_failed")
                    raise cause
                if original_error is not None:
                    raise original_error
                raise
            except BaseException:
                if original_error is None:
                    raise
                original_error.add_note("server.cleanup_failed")

    application = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)
    application.state.settings = settings
    application.add_middleware(LocalSecurity, settings=settings)
    register_session_routes(application)
    register_domain_routes(application)

    @application.exception_handler(RequestValidationError)
    async def invalid_request(request, exc):
        return problem("INVALID_PARAMS")

    @application.exception_handler(HTTPException)
    async def http_error(request, exc):
        code = {
            404: "NOT_FOUND",
            405: "METHOD_NOT_ALLOWED",
            409: "CONFLICT",
            422: "INVALID_PARAMS",
        }.get(exc.status_code, "INTERNAL")
        return problem(code, exc.status_code, headers=exc.headers)

    @application.exception_handler(Exception)
    async def internal_error(request, exc):
        logger.error("request.failed")
        response = problem("INTERNAL")
        if request.headers.getlist("origin") == [settings.web_origin]:
            response.headers["Access-Control-Allow-Origin"] = settings.web_origin
            response.headers["Vary"] = "Origin"
        return response

    @application.get(
        "/health",
        response_model=HealthDTO,
        responses={
            status: {
                "description": description,
                "content": {
                    "application/problem+json": {
                        "schema": ProblemDTO.model_json_schema()
                    }
                },
            }
            for status, description in [(403, "Forbidden"), (500, "Internal error")]
        },
    )
    async def health():
        return {"status": "running", "process": "server"}

    return application
