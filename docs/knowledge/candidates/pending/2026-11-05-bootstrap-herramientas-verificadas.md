---
category: GOTCHA
evidencia: validated_case
fuentes:
  - scripts/bootstrap.ps1
  - scripts/pnpm.py
  - scripts/fetch_web_tools.py
  - tests/test_web_tool_entrypoints.py
  - a8b28249214abbfd97f131c9dc97b61285fcedb1
tags:
  - "area:entorno"
  - "plataforma:windows"
  - "herramienta:bootstrap"
  - "herramienta:pnpm"
---

# El bootstrap debe adquirir las herramientas antes de usar el launcher verificado

Propuesta pendiente de curación por `knowledge-curator`. La categoría es una propuesta
según `.claude/knowledge-services/taxonomy.json`; no constituye conocimiento aprobado.

## Síntoma reproducido

En un clon público limpio del commit `a8b28249214abbfd97f131c9dc97b61285fcedb1`,
`scripts/bootstrap.ps1` instala Python 3.12.14 y las 70 dependencias bloqueadas,
pero termina con código 1 al llegar a `pnpm install`. El launcher informa que falta
`node-v22.23.2-win-x64.zip` en `.cache/dev-cycle/m1/t08-web-toolchain-inventory/`.
El fallo se reprodujo en un proceso PowerShell nuevo.

Una caché existente puede ocultar este requisito del primer arranque. Tener Node o
pnpm globales no satisface la comprobación de archivos del launcher del proyecto.

## Causa comprobada

`scripts/pnpm.py::verified_tools` exige los archivos fijados en `.cache/fetch/`.
Si faltan, consulta la caché histórica anterior. En ambos casos llama a
`scripts/fetch_web_tools.py::prepare` con `check=True`.

Ese modo verifica archivos y destinos; no descarga ni extrae herramientas. Si el
archivo no existe, `prepare` lanza `Falta archivo oficial verificado`. El bootstrap
del commit reproducido invocaba pnpm después de `uv sync --frozen`, sin ejecutar
antes la preparación. Por ello, una comprobación de solo lectura acababa siendo
el primer contacto de un clon limpio con las herramientas web.

## Qué hacer

Preparar las herramientas con el Python gestionado del proyecto después de
`uv sync --frozen` y antes de `scripts/pnpm.ps1 install`. La corrección presente
en el árbol de trabajo de `scripts/bootstrap.ps1` ejecuta:

```powershell
& (Join-Path $root '.venv\Scripts\python.exe') -I -B (Join-Path $PSScriptRoot 'fetch_web_tools.py')
```

El bootstrap comprueba inmediatamente el código de salida y se detiene si la
preparación falla. Se conserva `check=True` en el launcher, junto con los pins
de la constante `PINS` y la verificación de archivos de `fetch_web_tools.py`.
No se sustituye este paso por un Node global ni se presupone una caché histórica.

## Evidencia y límites

Las fuentes públicas anteriores permiten revisar la separación entre adquisición
y comprobación. La regresión conductual
`tests/test_web_tool_entrypoints.py::test_bootstrap_prepares_web_tools_before_install_and_stops_on_failure`
ejecuta el bootstrap con dobles en los límites Python. Comprueba el orden
preparación → instalación, el intérprete gestionado, la ausencia de ejecución del
pnpm ajeno y la interrupción cuando preparar devuelve 23.

Los recibos privados auxiliares, no incluidos en este candidato, son:

- `.cache/dev-cycle/20261105-t16-readme/report.md`: clon limpio y dos reproducciones del fallo.
- `.cache/dev-cycle/20261105-t16-readme/fix1/red.log`: dos casos fallidos antes del cambio; faltaba preparar y no se interrumpía ante su fallo.
- `.cache/dev-cycle/20261105-t16-readme/fix1/green.log`: dos casos aprobados tras el cambio.

La regresión con dobles no acredita una descarga real ni un arranque completo en
frío. Al redactar esta propuesta, la revisión independiente y esa QA posterior
siguen pendientes. Este caso no acredita aceptación musical, cierre de T-16 ni
cierre de M1.
