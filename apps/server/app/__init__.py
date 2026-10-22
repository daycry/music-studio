"""Server FastAPI: fuente de verdad, API, SSE, dispatcher y worker CPU.

Base local de configuración, seguridad HTTP y logs; el dominio llega en tareas posteriores.
"""

from .engine_client import engine_client
from .logging import configure_logging
from .main import create_app
from .settings import Settings

__all__ = ["Settings", "configure_logging", "create_app", "engine_client"]
