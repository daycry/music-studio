---
estado: borrador
opcion_elegida: pendiente
fecha: 2026-10-07
generacion: {fuente: estimado, allocation: 1.5, model: null, tokens: null, cost_eur: null, ai_hours: null}
---

# T04: empaquetado y límites de la siguiente unidad

## 1. Contexto y restricciones

Diseño privado para root, conforme al método architect custom-agents 1.22.0. La instrucción de alcance sustituye sus destinos canónicos y su medidor: sólo esta carpeta; decisiones, ADR, ledger y publicación pertenecen a root. No constituye otro ledger. Spec M1 aprobada; ocho CA T04 abiertos. La primera unidad de identidad está bajo corrección/revisión: R04-S01 permite terminal SQL sin timestamp y lecturas no deterministas. No se acepta esa dependencia por diseñar su consumidor.

Se analizan las seis copias enumeradas en frozen-inputs.json, no sus familiares vivos. Hechos: wheel `packages=["app"]`; httpx 0.28.1 ya es dependencia runtime; engine_client es síncrono, autenticado, origen confinado, sin redirects/proxy de entorno; lifespan actual migra/reconcilia/backup, sin dispatcher. Job admite queued/blocked/running/interrupted/terminal; JobAttempt ya separa identidad contractual y lógica. No se reabre ADR-0043. SQLite GPU1/CPU2, producto Docker y excepción Ollama compartido están fijados.

## 2. Opciones

| Opción | Implementación | Complejidad | Riesgo | Coste relativo | Reversibilidad |
|---|---|---|---|---|---|
| O1 | `apps/server/app/queue/`, imports `app.queue`; tres unidades secuenciales | Media, módulos dentro del wheel existente | Menor de empaquetado; exige corregir rutas documentadas | M | Alta: mover namespace interno, sin cambiar `/v1` |
| O2 | `apps/server/studio_queue/`, imports `studio_queue`; wheel explícito `packages=["app","studio_queue"]`; mismas tres unidades | Media-alta: segundo paquete y dependencia hacia app | Omisión en wheel/sdist/Docker, ciclos con app | L | Alta, pero requiere migrar imports y reglas de empaquetado |
| O3 | `apps/server/app/queue/`; dos unidades, runtime completo primero y cadenas después | Alta por tamaño del primer cambio | Revisión mezcla transporte, claims, eventos, retries y recovery | S de coordinación, L de retrabajo potencial | Media: rollback de runtime más grande |

La carpeta física documentada `apps/server/queue/` sólo podría conservarse mapeándola explícitamente a un namespace seguro como `app.queue` en build, sdist y desarrollo. El frozen pyproject no contiene tal mapping. Añadir `queue` como paquete top-level o al sys.path colisiona con stdlib usada por threads/httpx; no es alternativa admisible. Un mapping de wheel aislado deja imports nativos de desarrollo inconsistentes. No se propone una cuarta opción sin pruebas reales del backend de build ni hacks importlib.

## 3. Criterios de decisión

Imports normales desde código fuente y wheel instalado; stdlib queue intacta. Reutilizar dependencias y configuración existentes. Cada entrega debe ejecutar comportamiento durable observable y tener revisión/QA acotadas. Recovery y eventos requieren prueba adversarial, no una promesa de exactly-once en red. Mantener frontera T05/T06/T07 y aceptación real I-01.

## 4. Recomendación y elección

Recomendada O1: namespace seguro incluido por la configuración existente y tres entregas funcionales. Elegida pendiente; root decide tras recibir estos documentos, sin consultar al propietario ausente. O2 es viable si interesa separar el paquete pero no aporta aislamiento del dominio: depende de modelos/settings de app. O3 reduce coordinación a costa de un primer diff difícil de revisar. Ninguna descartada por root todavía.

La subdivisión recomendada: U1 admisión transaccional y ejecución básica real contra backend HTTP/resolver; U2 consumo durable, retries/recovery/cancelación; U3 construcción/resolución de cadenas y reintento manual. Detalle en plan-boundaries.md. Alternativa monolítica (runtime+resolver+cadenas de una vez): menor coordinación, riesgo alto, coste relativo L de revisión, reversible sólo con rollback amplio; no recomendada.

## 5. Impacto por rutas

Nuevas rutas exactas recomendadas en plan-boundaries.md. Integración posterior `apps/server/app/main.py`, extensión compatible `app/engine_client.py`. O2 añade cambio `apps/server/pyproject.toml`; O1 no necesita cambiar packages. El root registra ADR nuevo de ubicación si sustituye el path vigente de tasks/sistema; no cambia identidad ADR43. No se escribe aquí ADR ni canonical plan.

## 6. Riesgos y mitigaciones

| Riesgo | Probabilidad / impacto | Mitigación |
|---|---|---|
| Confundir prepared con no enviado | Alta / doble generación | Mismo ID/payload, reconciliación contractual |
| SSE falla después del commit | Alta / evento perdido | Registro durable transaccional + replay del bus, no reaplicar efecto |
| Reset seq sin epoch | Media / confundir replay viejo con ejecución reiniciada | Root debe aprobar extensión durable acotada antes U2 |
| Instalar wheel parece cubrir Docker | Media / imports o recursos ausentes | QA futura wheel nativo fuera de checkout y Docker independiente |
| Modelos reales no verificados | Alta / falsa aceptación | Sólo mock técnico; I-01/M-01 abiertos |

## 7. Decisiones abiertas para root

Opción de empaquetado/subdivisión. Aprobar análisis de persistencia de eventos/epoch/claims de state-transitions.md antes de escribir nuevas tablas o migraciones. Confirmar evidencia nativa de ausencia de status y de reinicio: `/v1/health` no incluye boot_id. No usar engine_version/image_digest como prueba de reinicio. Sin decisiones del propietario necesarias para esta entrega.

No se certifica implementación, pruebas, wheel, Docker, live integration, GPU, calidad ni cierre de T04/M1. Futuras revisión independiente A/B/C/D y QA son gates separados.
