"""Lock de modelos, verificación SHA-256, auditor y conversor de pickle
(ADR-0006). Sin torch: solo `safetensors`, `numpy`, `huggingface_hub` y
`pickletools`/`pickle` (el `pickle.Unpickler` restringido de `audit_pickle.py`
es el único uso legítimo de deserialización pickle de todo el proyecto).
"""

from .audit_pickle import (
    ALLOWED_GLOBALS,
    PickleSecurityError,
    load_restricted,
    scan_opcodes,
)
from .convert import ConversionError, ConversionResult, convert_torch_pickle_zip
from .hashing import sha256_bytes, sha256_file
from .lock import LockError, load_lock
from .safetensors_format import TensorEntry, read_safetensors_header, write_safetensors
from .seal import Seal, read_seal, verified_sha256, write_seal
from .verify import VerifyResult, verify_file, verify_remote_code

__all__ = [
    "ALLOWED_GLOBALS",
    "ConversionError",
    "ConversionResult",
    "LockError",
    "PickleSecurityError",
    "Seal",
    "TensorEntry",
    "VerifyResult",
    "convert_torch_pickle_zip",
    "load_lock",
    "load_restricted",
    "read_safetensors_header",
    "read_seal",
    "scan_opcodes",
    "sha256_bytes",
    "sha256_file",
    "verified_sha256",
    "verify_file",
    "verify_remote_code",
    "write_safetensors",
    "write_seal",
]
