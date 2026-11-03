---
id: music-studio.GOT-003
version: 1
estado: aprobado
project: music-studio
scope: pytest-cov y NumPy en Windows; colección aislada
source: .cache/dev-cycle/20261103-cpu-m1/debug-server/diagnosis.md
confidence: high
category: GOTCHA
evidencia: validated_case
fecha: 2026-11-03
fuentes:
  - .cache/dev-cycle/20261103-cpu-m1/debug-server/diagnosis.md
  - .cache/dev-cycle/20261103-cpu-m1/debug-server/minimal-results.json
  - .cache/dev-cycle/20261103-cpu-m1/debug-server/mechanism-named.json
  - .cache/dev-cycle/20261103-cpu-m1/debug-server/mechanism-directory.json
  - .cache/dev-cycle/20261103-cpu-m1/debug-server/check_regression.py
  - apps/server/app/__init__.py
  - apps/server/tests/test_api_t07.py
tags:
  - "area:pruebas"
  - "componente:coverage"
  - "entorno:windows"
  - "dependencia:numpy"
---

# Coverage puede importar NumPy dos veces al resolver un submódulo

Entrada aprobada por `knowledge-curator`, limitada al entorno Windows observado: Python 3.12.14,
NumPy 2.5.3, coverage 7.16.2 y pytest-cov 7.1.0. No establece que ocurra en
todos los entornos ni acredita una suite de producto completa.

## Caso aislado

La colección del mismo `apps/server/tests/test_api_t07.py` en procesos nuevos
produjo estos resultados, conservados en `minimal-results.json`:

| Configuración | Resultado |
|---|---|
| `--cov=app.domain_routes` | Exit 2 durante colección: `ImportError: cannot load module more than once per process` |
| `--cov=apps/server/app` | Exit 0; 47 tests recogidos |
| Sin cobertura | Exit 0; los mismos 47 tests recogidos |

Las sondas `mechanism-named.json` y `mechanism-directory.json` aislaron la
causa: resolver el nombre con `find_spec` importa el paquete padre `app` y,
transitivamente, NumPy. Coverage restaura después `sys.modules`, eliminando
esas entradas mientras la extensión nativa permanece cargada. La importación
posterior falla. Con la fuente de directorio no ocurre esa precarga y NumPy
se importa correctamente. El código instalado contrastado está en
`coverage/inorout.py` (`find_spec`, `sys_modules_saved`) y `coverage/misc.py`.

## Cómo evitarlo en este caso

Usar un directorio real como fuente, como `--cov=apps/server/app`, evita la
resolución anticipada del submódulo. Otra opción del arnés es `--cov` sin
argumento y una configuración `include` explícita de archivos completos.
`--cov=` no es equivalente: la sonda de ese perfil no recogió datos.

Conservar el JSON completo y calcular los umbrales sobre los archivos
previstos, sin excluir sus líneas para obtener un verde. Recoger 47 tests no
equivale a ejecutarlos ni a superar cobertura. `check_regression.py` verifica
la diferencia observada entre las tres colecciones; no valida el producto.

Los artefactos detallados son locales y están bajo `.cache/`, fuera de Git.
El diagnóstico no requirió WSL, GPU, Docker ni modificar NumPy o coverage.
