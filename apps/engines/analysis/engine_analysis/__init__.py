"""Engine de análisis local con contrato /v1."""

from .adapter import AnalysisAdapter
from .descriptor import descriptors
from .safety import verify_model
from .server import create_app

__all__ = ["AnalysisAdapter", "create_app", "descriptors", "verify_model"]
