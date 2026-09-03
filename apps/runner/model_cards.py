"""Inventario de fichas de modelo: que pesos hay instalados y cuales se pueden usar.

Que problema resuelve, hoy
--------------------------
En el directorio de pesos de esta maquina hay **tres** ficheros `.safetensors`
que son el **mismo modelo**: `ace_step_1_5`, `ace_step_1_5_lm` y
`ace_step_1_5_sft_lm`. Los dos ultimos se diferencian en 2 KB y traen las mismas
677 claves con las mismas formas, asi que **el artefacto no dice cual es cual**.
Uno es el de produccion y otro quedo descartado en `T-06` por sonar peor. Elegir
mal no da ningun error: da audio peor. Un escaneo del directorio ofreceria tres
modelos donde hay uno.

La ficha `<pesos>.model.json` es la respuesta: lo que el artefacto no puede
declarar de si mismo, lo declara quien lo instala, por escrito y auditable.

La regla que sostiene el diseno: **evidencia, nunca autoridad**
---------------------------------------------------------------
Una ficha describe unos pesos que ya estan en disco. **No decide que codigo se
importa.** El campo `adapter` es un NOMBRE que se valida contra
`ADAPTERS_CONOCIDOS`, un `frozenset` de este repositorio; no se resuelve por
`importlib` ni por nada parecido, y este modulo no importa nada por nombre (hay
un test que lo comprueba leyendo su propio fuente). Una ficha hostil que diga
`adapter: "os:system"` solo consigue aparecer en la lista como `rechazada`.

Por la misma razon, el campo `env` tiene lista blanca y `ACE_STEP_SKIP_INTEGRITY`
y `ACE_STEP_MOCK` estan **excluidas a proposito**: una ficha configura, jamas
desactiva la verificacion de integridad ni convierte una generacion real en
simulada.

Lo que esto NO es
-----------------
No es el registry de `T-30` (Fase 5, con `ModelDescriptor` persistido y suite de
conformidad), ni el catalogo HTTP, ni un instalador (`T-86`). Es biblioteca
estandar pura, sin torch y sin red, para poder correr en cualquier sitio y
decirle a su duenio que tiene instalado. Cuando llegue `T-30`, esto es la semilla
del descriptor o se tira; hay que decidirlo entonces, no ahora.

Tampoco decide si un modelo **sirve**: `min_vram_mb` responde «cabe», que no es
lo mismo. ACE-Step cabe en 8 GB y tarda 623-690 s en una pista de 240 s.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, NamedTuple

__all__ = [
    "SCHEMA_SOPORTADO",
    "ADAPTERS_CONOCIDOS",
    "ENV_PERMITIDAS",
    "ENV_PROHIBIDAS",
    "DISPONIBLE",
    "NO_SELECCIONABLE",
    "RECHAZADA",
    "SIN_FICHA",
    "Ficha",
    "inventariar",
    "formatear",
]

#: Version del esquema de la ficha. Se sube cuando cambie su forma; una ficha que
#: declare una version mayor se RECHAZA en vez de interpretarse a medias.
SCHEMA_SOPORTADO = 1

#: Adapters que este repositorio sabe ejecutar. Lista CERRADA y escrita aqui: es
#: la frontera entre «un dato del disco» y «codigo que se ejecuta». Anadir uno
#: exige un commit, que es justo el punto de control que se quiere.
ADAPTERS_CONOCIDOS = frozenset({"ace_step"})

#: Variables de entorno que una ficha puede fijar. Todo lo demas se rechaza: sin
#: lista blanca, `env` seria un vector para tocar el entorno del proceso.
ENV_PERMITIDAS = frozenset({
    "ACE_STEP_VARIANTE",
    "ACE_STEP_DTYPE",
    "ACE_STEP_DEVICE",
    "ACE_STEP_WEIGHTS_FILE",
})

#: Excluidas EXPLICITAMENTE aunque empiecen por el mismo prefijo. Estan aqui, y
#: no simplemente fuera de la lista blanca, para que el motivo quede escrito:
#: apagan la verificacion de integridad y el modo real. Una ficha no puede.
ENV_PROHIBIDAS = frozenset({"ACE_STEP_SKIP_INTEGRITY", "ACE_STEP_MOCK"})

#: Estados del inventario.
DISPONIBLE = "disponible"          #: valida y elegible
NO_SELECCIONABLE = "no_seleccionable"  #: valida, pero deprecada o no cabe
RECHAZADA = "rechazada"            #: la ficha no supera la validacion
SIN_FICHA = "sin_ficha"            #: hay pesos y nadie los ha declarado

_SUFIJO_PESOS = ".safetensors"
_SUFIJO_FICHA = ".model.json"
_SUFIJO_PROCEDENCIA = ".provenance.json"
_ESTADOS_DECLARABLES = frozenset({"activo", "deprecado"})


class Ficha(NamedTuple):
    """Una entrada del inventario: unos pesos y lo que se sabe de ellos."""

    ref: str
    """`id@version`, o el nombre del fichero si no hay ficha."""

    ruta_pesos: Path
    adapter: str | None
    estado: str
    motivo: str
    min_vram_mb: int | None
    env: dict[str, str]
    licencias: list[dict[str, Any]]
    ruta_ficha: Path | None


class _Rechazo(Exception):
    """Motivo por el que una ficha no vale. No se propaga: se convierte en estado."""


def _texto(valor: Any, campo: str) -> str:
    if not isinstance(valor, str) or not valor.strip():
        raise _Rechazo(f"el campo {campo!r} tiene que ser una cadena no vacia")
    return valor.strip()


def _validar(documento: Any, ruta_ficha: Path) -> dict[str, Any]:
    """Comprueba la ficha campo a campo. Levanta `_Rechazo` con el motivo."""
    if not isinstance(documento, dict):
        raise _Rechazo("la ficha no es un objeto JSON")

    schema = documento.get("schema")
    if schema != SCHEMA_SOPORTADO:
        raise _Rechazo(
            f"schema {schema!r}: este runner entiende el {SCHEMA_SOPORTADO}. "
            "Una ficha de un esquema que no se conoce no se interpreta a medias."
        )

    adapter = _texto(documento.get("adapter"), "adapter")
    if adapter not in ADAPTERS_CONOCIDOS:
        raise _Rechazo(
            f"adapter {adapter!r} desconocido. Los que este repositorio sabe ejecutar son "
            f"{sorted(ADAPTERS_CONOCIDOS)}. La ficha NOMBRA el adapter; no lo resuelve: "
            "anadir uno exige escribirlo en el codigo y revisarlo."
        )

    estado = _texto(documento.get("estado"), "estado")
    if estado not in _ESTADOS_DECLARABLES:
        raise _Rechazo(f"estado {estado!r}: se esperaba uno de {sorted(_ESTADOS_DECLARABLES)}")

    env = documento.get("env") or {}
    if not isinstance(env, dict):
        raise _Rechazo("el campo 'env' tiene que ser un objeto")
    for clave, valor in env.items():
        if clave in ENV_PROHIBIDAS:
            raise _Rechazo(
                f"{clave} no puede fijarse desde una ficha: apaga una salvaguarda "
                "(integridad de pesos o modo real). Una ficha configura, no desactiva."
            )
        if clave not in ENV_PERMITIDAS:
            raise _Rechazo(f"{clave} no esta en la lista blanca de variables de entorno")
        if not isinstance(valor, str):
            raise _Rechazo(f"el valor de {clave} tiene que ser una cadena")

    hardware = documento.get("hardware") or {}
    if not isinstance(hardware, dict):
        raise _Rechazo("el campo 'hardware' tiene que ser un objeto")
    min_vram = hardware.get("min_vram_mb")
    if min_vram is not None and (not isinstance(min_vram, int) or min_vram <= 0):
        raise _Rechazo("hardware.min_vram_mb tiene que ser un entero positivo")

    licencias = documento.get("licencias") or []
    if not isinstance(licencias, list):
        raise _Rechazo("el campo 'licencias' tiene que ser una lista")

    nombre_pesos = _texto(documento.get("pesos"), "pesos")
    if os.path.basename(nombre_pesos.replace("\\", "/")) != nombre_pesos:
        raise _Rechazo(f"el campo 'pesos' es un nombre de fichero, no una ruta: {nombre_pesos!r}")
    if not nombre_pesos.lower().endswith(_SUFIJO_PESOS):
        raise _Rechazo(f"los pesos declarados no son un {_SUFIJO_PESOS}: {nombre_pesos!r}")

    return {
        "id": _texto(documento.get("id"), "id"),
        "version": _texto(documento.get("version"), "version"),
        "adapter": adapter,
        "estado": estado,
        "pesos": nombre_pesos,
        "min_vram_mb": min_vram,
        "env": dict(env),
        "licencias": licencias,
    }


def _evaluar(ruta_ficha: Path, vram_mb: int | None) -> Ficha:
    """Lee y valida una ficha; devuelve su entrada de inventario, nunca lanza."""
    ruta_pesos = ruta_ficha.with_name(ruta_ficha.name[: -len(_SUFIJO_FICHA)] + _SUFIJO_PESOS)
    vacia = Ficha(ruta_ficha.name, ruta_pesos, None, RECHAZADA, "", None, {}, [], ruta_ficha)
    try:
        documento = json.loads(ruta_ficha.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return vacia._replace(motivo=f"ficha ilegible: {exc}")

    try:
        campos = _validar(documento, ruta_ficha)
    except _Rechazo as exc:
        return vacia._replace(motivo=str(exc))

    ruta_pesos = ruta_ficha.with_name(campos["pesos"])
    ref = f"{campos['id']}@{campos['version']}"
    base = Ficha(
        ref=ref,
        ruta_pesos=ruta_pesos,
        adapter=campos["adapter"],
        estado=RECHAZADA,
        motivo="",
        min_vram_mb=campos["min_vram_mb"],
        env=campos["env"],
        licencias=campos["licencias"],
        ruta_ficha=ruta_ficha,
    )

    if not ruta_pesos.is_file():
        return base._replace(motivo=f"los pesos declarados no existen: {ruta_pesos.name}")

    # Una sola regla de hash: la procedencia la escribe el fusor junto al
    # artefacto. Sin ella no hay nada que contrastar y la ficha seria una
    # promesa sin respaldo. La ficha NO trae su propio hash a proposito: dos
    # fuentes de verdad para el mismo dato acaban discrepando.
    procedencia = ruta_pesos.with_suffix(_SUFIJO_PROCEDENCIA)
    if not procedencia.is_file():
        return base._replace(
            motivo=(
                f"falta el {_SUFIJO_PROCEDENCIA} hermano ({procedencia.name}), que es lo "
                "unico que acredita el origen y el hash de estos pesos"
            )
        )

    if campos["estado"] == "deprecado":
        return base._replace(
            estado=NO_SELECCIONABLE,
            motivo="declarado deprecado en su ficha: sigue en disco y a la vista, no se elige",
        )

    minimo = campos["min_vram_mb"]
    if minimo is not None and vram_mb is not None and minimo > vram_mb:
        return base._replace(
            estado=NO_SELECCIONABLE,
            motivo=f"pide {minimo} MiB de VRAM y hay {vram_mb} MiB",
        )
    if minimo is not None and vram_mb is None:
        return base._replace(
            estado=DISPONIBLE,
            motivo=f"pide {minimo} MiB de VRAM, sin comprobar (no se dio la VRAM disponible)",
        )
    return base._replace(estado=DISPONIBLE, motivo="")


def inventariar(dir_pesos: str | os.PathLike[str], vram_mb: int | None = None) -> list[Ficha]:
    """Que hay instalado en `dir_pesos` y en que estado, ordenado por referencia.

    `vram_mb` se **inyecta**; este modulo no importa torch ni consulta el driver,
    para poder correr en cualquier interprete y ser testeable sin tarjeta. Si no
    se da, no se emite veredicto de encaje: se dice que no se comprobo.

    Los pesos sin ficha aparecen como `sin_ficha` en vez de ocultarse: estan ahi
    y alguien los usara; callarlos seria peor que listarlos.
    """
    raiz = Path(dir_pesos)
    if not raiz.is_dir():
        return []

    fichas = [_evaluar(p, vram_mb) for p in sorted(raiz.glob("*" + _SUFIJO_FICHA))]
    declarados = {f.ruta_pesos.name for f in fichas}
    for pesos in sorted(raiz.glob("*" + _SUFIJO_PESOS)):
        if pesos.name in declarados:
            continue
        fichas.append(
            Ficha(
                ref=pesos.name,
                ruta_pesos=pesos,
                adapter=None,
                estado=SIN_FICHA,
                motivo=f"no hay {pesos.stem}{_SUFIJO_FICHA}: nadie ha declarado que es esto",
                min_vram_mb=None,
                env={},
                licencias=[],
                ruta_ficha=None,
            )
        )
    return sorted(fichas, key=lambda f: (f.estado, f.ref))


def formatear(fichas: list[Ficha]) -> str:
    """Listado legible para la consola."""
    if not fichas:
        return "No hay pesos en ese directorio."
    ancho = max(len(f.ref) for f in fichas)
    lineas = []
    for f in fichas:
        marca = "*" if f.estado == DISPONIBLE else " "
        lineas.append(f"{marca} {f.ref:<{ancho}}  {f.estado:<17}  {f.motivo}".rstrip())
    lineas.append("")
    lineas.append("(*) elegible. El resto se lista a proposito: ocultarlo no lo borra del disco.")
    return "\n".join(lineas)


def main(argv: list[str] | None = None) -> int:
    import argparse  # noqa: PLC0415  (solo lo necesita la linea de comandos)

    p = argparse.ArgumentParser(description="Lista los modelos instalados y su estado.")
    p.add_argument("directorio", nargs="?", default=os.environ.get("ACE_STEP_WEIGHTS_DIR", "."),
                   help="Directorio de pesos (por defecto, ACE_STEP_WEIGHTS_DIR).")
    p.add_argument("--vram-mb", type=int, default=None,
                   help="VRAM disponible en MiB. Sin esto no se juzga el encaje.")
    args = p.parse_args(argv)
    print(formatear(inventariar(args.directorio, vram_mb=args.vram_mb)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
