"""Auditor de pickle sin torch y sin `pickle.load` directo (ADR-0006 §3).

Dos pasadas, ninguna ejecuta código arbitrario:

1. **Análisis estático de opcodes** con `pickletools.genops`: recorre el stream
   sin construir ningún objeto y rechaza cualquier opcode `GLOBAL`/`STACK_GLOBAL`
   que no esté en `ALLOWED_GLOBALS`, y cualquier opcode de extensión/instancia
   (`EXT1/2/4`, `INST`, `OBJ`) que pudiera saltarse el allowlist.
2. **Reconstrucción restringida**: un `pickle.Unpickler` cuyo `find_class` solo
   resuelve nombres de `ALLOWED_GLOBALS`, devolviendo siempre marcadores propios
   (nunca las clases reales de `torch`). `persistent_id`/`persistent_load` los
   controlamos nosotros (lee los storages del zip con numpy).

La seguridad no depende de la pasada 2: la pasada 1 ya garantiza que ningún
`GLOBAL` fuera del allowlist llega a ejecutarse, porque el único modo de poner
un invocable arbitrario en la pila de un pickle es `GLOBAL`/`STACK_GLOBAL`
(o extensiones registradas, también rechazadas aquí). `REDUCE`/`BUILD`/`NEWOBJ`
solo pueden invocar lo que ya está en la pila.

Allowlist actual, verificada contra los tres pickle reales de esta tarea
(`silence_latent.pt` de ACE-Step, `pytorch_model.bin` de LAION CLAP,
`final0.ckpt` de beat_this — los tres solo usan estos cuatro globals):
- `torch._utils._rebuild_tensor_v2`
- `torch.FloatStorage` / `HalfStorage` / `BFloat16Storage` / `DoubleStorage` /
  `LongStorage` / `IntStorage` / `ShortStorage` / `ByteStorage` / `BoolStorage`
  (todas las variantes de storage que puede emitir `torch.save`, aunque solo
  Float/Long aparecen en los tres ficheros de T-02; se listan por anticipación
  a otros `.pt`/`.pth` de ADR-0006 §"Casos conocidos" que se auditarán en M0+).
- `collections.OrderedDict` (contenedor inerte; los `state_dict` de PyTorch son
  siempre `OrderedDict`).

No hay ninguna entrada `builtins.*` todavía: los `.ckpt` de Lightning
inspeccionados (beat_this) no la necesitan (su único nivel extra es un
`dict`/`str`/`int` de metadatos que el propio protocolo pickle codifica con
opcodes nativos, sin `GLOBAL`). Si un `.ckpt` futuro sí la necesita, se añade
aquí con un comentario que justifique esa entrada concreta (no antes).
"""

from __future__ import annotations

import io
import pickle
import pickletools
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

# (módulo, nombre) -> True. Solo se usa como conjunto.
ALLOWED_GLOBALS: frozenset[tuple[str, str]] = frozenset(
    {
        ("torch._utils", "_rebuild_tensor_v2"),
        ("torch", "FloatStorage"),
        ("torch", "HalfStorage"),
        ("torch", "BFloat16Storage"),
        ("torch", "DoubleStorage"),
        ("torch", "LongStorage"),
        ("torch", "IntStorage"),
        ("torch", "ShortStorage"),
        ("torch", "ByteStorage"),
        ("torch", "BoolStorage"),
        ("collections", "OrderedDict"),
    }
)

# Nombre de storage -> (dtype numpy o marcador especial, bytes por elemento).
_STORAGE_DTYPES: dict[str, tuple[str, int]] = {
    "FloatStorage": ("float32", 4),
    "HalfStorage": ("float16", 2),
    "BFloat16Storage": ("bfloat16", 2),  # marcador especial: numpy no lo soporta
    "DoubleStorage": ("float64", 8),
    "LongStorage": ("int64", 8),
    "IntStorage": ("int32", 4),
    "ShortStorage": ("int16", 2),
    "ByteStorage": ("uint8", 1),
    "BoolStorage": ("bool", 1),
}

# Opcodes que podrían invocar código sin pasar por un GLOBAL auditable, o que
# necesitarían simular la pila para saber a qué apuntan (STACK_GLOBAL, protocolo
# 4+, toma módulo/nombre de la pila en vez de llevarlos en el propio opcode).
# Ninguno hace falta para pesos de PyTorch guardados con `torch.save` por
# defecto (protocolo 2, opcode `GLOBAL` de toda la vida) — los tres pickle
# reales de esta tarea lo confirman. Se rechazan siempre, en vez de intentar
# resolverlos de forma parcial: fallar cerrado ante algo que no podemos
# auditar con certeza estática es la decisión correcta aquí.
_FORBIDDEN_OPCODE_NAMES = frozenset(
    {"EXT1", "EXT2", "EXT4", "INST", "OBJ", "STACK_GLOBAL"}
)


class PickleSecurityError(ValueError):
    """El pickle contiene algo fuera del allowlist de ADR-0006."""


def scan_opcodes(data: bytes) -> list[tuple[str, str]]:
    """Pasada 1: recorre los opcodes sin ejecutar nada. Devuelve la lista de
    globals encontrados (módulo, nombre) si todos están permitidos; lanza
    `PickleSecurityError` en el primero que no lo esté, o si aparece un opcode
    prohibido.
    """
    found: list[tuple[str, str]] = []
    try:
        ops = list(pickletools.genops(data))
    except Exception as exc:  # pickle malformado: tampoco se ejecuta
        raise PickleSecurityError(f"pickle malformado, no se audita: {exc}") from exc

    for opcode, arg, _pos in ops:
        if opcode.name in _FORBIDDEN_OPCODE_NAMES:
            raise PickleSecurityError(f"opcode prohibido: {opcode.name}")
        if opcode.name == "GLOBAL":
            module, _, name = str(arg).partition(" ")
            if (module, name) not in ALLOWED_GLOBALS:
                raise PickleSecurityError(f"global no permitido: {module}.{name}")
            found.append((module, name))
    return found


@dataclass
class _StorageTypeMarker:
    """Marcador inerte devuelto por `find_class` para un `torch.*Storage`.
    Nunca es la clase real de torch: solo lleva el nombre para mapear el dtype.
    """

    name: str


def _rebuild_tensor_v2_marker(
    storage: _StorageRef,
    storage_offset: int,
    size: tuple[int, ...],
    stride: tuple[int, ...],
    requires_grad: bool = False,
    backward_hooks: Any = None,
    metadata: Any = None,
) -> _TensorRef:
    """Sustituto seguro de `torch._utils._rebuild_tensor_v2`: no reconstruye un
    `torch.Tensor` real, solo anota lo necesario para leer los bytes crudos del
    storage con numpy.
    """
    return _TensorRef(
        storage=storage,
        storage_offset=storage_offset,
        size=tuple(size),
        stride=tuple(stride),
    )


@dataclass
class _StorageRef:
    key: str
    location: str
    numel: int
    dtype_name: str  # nombre del *Storage, p.ej. "FloatStorage"
    data: bytes = b""  # bytes crudos del storage (los rellena storage_reader)


@dataclass
class _TensorRef:
    storage: _StorageRef
    storage_offset: int
    size: tuple[int, ...]
    stride: tuple[int, ...]


class RestrictedUnpickler(pickle.Unpickler):
    """`pickle.Unpickler` con `find_class` restringido al allowlist. `GLOBAL`
    de un `torch.*Storage` no se "llama" nunca (aparece como valor plano dentro
    de la tupla de `persistent_id`, no vía REDUCE), así que basta con devolver
    un marcador con el nombre; `_rebuild_tensor_v2` sí se invoca vía REDUCE,
    pero apunta a nuestra propia función seguraque no reconstruye ningún
    `torch.Tensor` real.
    """

    def __init__(self, file: io.BytesIO, storage_reader: Callable[[str, str, int, str], _StorageRef]):
        super().__init__(file)
        self._storage_reader = storage_reader

    def find_class(self, module: str, name: str) -> Any:
        if (module, name) not in ALLOWED_GLOBALS:
            raise PickleSecurityError(f"global no permitido: {module}.{name}")
        if module == "torch" and name in _STORAGE_DTYPES:
            return _StorageTypeMarker(name)
        if module == "torch._utils" and name == "_rebuild_tensor_v2":
            return _rebuild_tensor_v2_marker
        if module == "collections" and name == "OrderedDict":
            return OrderedDict
        raise PickleSecurityError(f"global no permitido: {module}.{name}")  # pragma: no cover

    def persistent_load(self, pid: Any) -> _StorageRef:
        # pid = ('storage', storage_type_marker, key, location, numel)
        if not isinstance(pid, tuple) or len(pid) != 5 or pid[0] != "storage":
            raise PickleSecurityError(f"persistent_id inesperado: {pid!r}")
        _, storage_type, key, location, numel = pid
        if not isinstance(storage_type, _StorageTypeMarker):
            raise PickleSecurityError("persistent_id sin marcador de storage válido")
        return self._storage_reader(storage_type.name, str(key), int(numel), str(location))


def load_restricted(
    data: bytes, storage_reader: Callable[[str, str, int, str], _StorageRef]
) -> Any:
    """Pasada 2: recorre el mismo stream ya auditado en la pasada 1 y reconstruye
    la estructura con marcadores propios. `storage_reader(dtype_name, key, numel,
    location) -> _StorageRef` es quien de verdad lee los bytes del zip.
    """
    scan_opcodes(data)  # nunca se salta la pasada 1, aunque se llame directo
    unpickler = RestrictedUnpickler(io.BytesIO(data), storage_reader)
    return unpickler.load()
