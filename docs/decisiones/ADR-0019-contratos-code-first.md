# ADR-0019 · Contratos code-first y versionados

- **Estado:** aceptada · **Fecha:** 2026-09-28 · Precisa la línea «Contrato» de [ADR-0003](ADR-0003-stack.md)

## Decisión
- **API del server:** los modelos Pydantic y las rutas de FastAPI son la fuente del contrato. `scripts/export_contracts.py` genera `packages/contracts/openapi.json`, que se versiona en el repo. Un test falla si el fichero versionado no coincide con el generado. La web genera sus tipos TypeScript desde ese fichero (`pnpm gen`).
- **Contrato de engines:** paquete Python `packages/engine-contract/`, sin torch y compatible con 3.11 y 3.12. Lo importan el server y todos los engines. De él se genera `packages/contracts/engine-v1.json` (JSON Schema).
- **Esquemas de datos persistentes:** `manifest-v1`, `timeline-v1` y `song-v1` son JSON Schema escritos a mano en `packages/contracts/`. Server y engines los validan en sus tests.
- **Casos compartidos:** `packages/contracts/lyrics-cases.json` (etiquetas de letra válidas e inválidas). Los parsers de Python y de TypeScript deben pasar exactamente los mismos casos.
- **Cambios:** un cambio de contrato va en el mismo commit que el código que lo usa. Los cambios rompedores del `/v1` de engines exigen `/v2`. En `/api`, al haber un solo cliente, se permiten si la web se actualiza en el mismo commit.

## Motivo
Con un solo desarrollador, escribir la API a mano en OpenAPI y mantener código y especificación sincronizados es trabajo doble y fuente de desajustes. Generar el contrato desde el código y comprobarlo con un test da la misma garantía con menos fricción.
