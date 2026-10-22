# T-09 — Auditoría del recibo fuera del camino durable del episodio

**Fecha:** 2026-10-10  
**Estado:** corrección implementada; revisión, QA y benchmark completo pendientes.

## Causa observada

La sesión `01M4JPDDH5BFJZ67AXDYV1T68R` aceptó 1.307 episodios y el intento
1.308 terminó con `worker_deadline` sin ningún evento de progreso del sensor.
El directorio del episodio interrumpido sólo contenía `request.json`, mientras
que el episodio anterior ya contenía `supervisor-audit.json`. Esto sitúa el
bloqueo antes de la primera llamada de observación: la confirmación del recibo
anterior escribía y sincronizaba físicamente su auditoría dentro del plazo de
2 s del episodio siguiente.

El `commit.json`, `prepared.json`, RAW y progreso siguen usando `fsync`. La
auditoría del recibo describe un commit ya durable y se escribe como metadato;
su escritura no añade una segunda barrera física al camino de adquisición.

## TDD

- **RED:** `test_supervisor_audit_metadata_does_not_add_a_durable_sync_to_next_episode`
  esperaba `durable=False` y observó una llamada sin esa declaración.
- **GREEN:** el mismo test pasa tras añadir el parámetro `durable` a
  `EpisodeProvider.write` y usar `durable=False` para `supervisor-audit.json`.

Verificaciones ejecutadas:

```text
uv run --no-sync pytest scripts/eval/tests/test_benchmark_episode_v3.py::test_supervisor_audit_metadata_does_not_add_a_durable_sync_to_next_episode -q
1 passed

uv run --no-sync pytest scripts/eval/tests/test_benchmark_episode_v3.py -q
53 passed

uv run --no-sync ruff check scripts/eval/benchmark_episode.py scripts/eval/tests/test_benchmark_episode_v3.py
All checks passed
```

## Revalidación real en curso

Se creó el plan nuevo `01M4JR3BJZP2M7SA780VVP8ZRV` con hash
`a671ae872f9daf363fabeb46b32d40d9833cdeabc586dcf85b2c71488fc4d05c`.
La acreditación pasó con 304 publicaciones y el piloto ACE-Step cargó el
modelo (~9,1 GB de VRAM). La matriz todavía está en curso; sus filas no se
presentan como aceptación hasta disponer del terminal y de la auditoría final.
