# ADR-0089 · Reencauce tras la etapa de Codex: alcance mínimo y proceso ligero

- **Estado:** aceptada por delegación del propietario («haz lo que tengas que hacer para dejarlo limpio y poder seguir con la implementación», 2026-10-22). Reversible.
- **Fecha:** 2026-10-22.
- **Sustituye en parte:** ADR-0037 (avance condicionado de M2/M3), ADR-0069, ADR-0071, ADR-0075, ADR-0076, ADR-0078, ADR-0081 y ADR-0084 (almacenamiento VHDX/ext4 y journal Windows).

## Contexto

Entre el 2026-10-05 y el 2026-10-12 el trabajo, hecho con Codex, abrió cuatro hitos a la vez y cerró pocos:

| Hito | Estado al parar |
|---|---|
| M0 | 13/21 tareas |
| M1 | 0/17 formales, aunque había ~23k líneas de server sin commitear |
| M2 | 5/30 |
| M3 | 5/42, todas documentales |

Señales de que el proceso pesaba más que el producto:

- 88 ADR en tres semanas.
- Ledgers de 200–600 KB y un `CONTINUE-HERE.md` de 338 KB.
- ~26 MB de recibos JSON de revisión.

El agujero más profundo fue el almacenamiento:

1. `renameat2(RENAME_NOREPLACE)` devuelve `EINVAL` sobre el bind 9p/DrvFS de Docker Desktop.
2. ADR-0069 optó por un VHDX ext4 propio.
3. De ahí salieron ~11k líneas de journal Windows (ABI NT, identidad, adquisición, custodia).

Aun así, **no existe todavía una canción de punta a punta en la web**.

Todo ese estado está congelado, con las rutas personales limpiadas, en el commit `36d4e99` (rama `rescue/2026-10-22-codex`).

## Decisión

1. **Un hito activo a la vez.**
   - M0 se cierra con lo que ya funciona.
   - M1 se recorta a un camino mínimo de punta a punta.
   - **M2 y M3 quedan congelados**: sus carpetas pasan a [`../archive/codex-2026-10/`](../archive/codex-2026-10/README.md) y se rehacen cuando M1 esté cerrado.
2. **El almacenamiento Windows/VHDX se aparca.**
   - Salen del árbol `scripts/storage*.py`, sus tests, `docker-compose.storage.yml` y `scripts/fetch_storage_linux.py`.
   - La publicación de takes en M1 se rediseña sencilla (M1/T-05):
     - un directorio por id único (ULID), así que no hay colisión posible y no hace falta `NOREPLACE`;
     - `rename`/copia normal dentro de `data/`;
     - la fila de SQLite como autoridad: el take existe cuando la fila se confirma y los huérfanos se limpian al arrancar.
   - `packages/storage-guard` sigue siendo opcional (solo actúa con `STUDIO_STORAGE_UUID`) y su retirada se decide en M1/T-05.
3. **M0 se cierra así:**
   - T-10, T-11 y T-12 → `cancelado` y pasan al backlog. La batería y la matriz exhaustivas no bloquean el MVP.
   - T-09 se reduce a un benchmark básico.
   - T-13 sigue exigiendo la escucha del propietario.
4. **Proceso ligero.** Sigue siendo obligatorio el plugin `custom-agents`, pero:
   - el `tasks.md` guarda **estado, criterios y la salida de la Verificación**, no el diario de intentos;
   - los informes de revisión y QA se resumen en el ledger en ≤ 10 líneas y los recibos crudos no se commitean (`.cache/`);
   - un ADR solo cuando cambia algo documentado de verdad, no por cada corrección;
   - `CONTINUE-HERE.md` ocupa una pantalla;
   - cambios pequeños → `quick-implement`.

## Consecuencias

- Los ledgers, briefs y evidencias de la etapa Codex pasan a `docs/archive/codex-2026-10/`. Las evidencias crudas solo existen en el commit `36d4e99`.
- El código de M2 que ya está en el árbol (`apps/server/app/creative/`, recetas) no se borra. En M1/T-05 y T-07 se decide si se queda o sale, según lo que use el camino mínimo.
- La aceptación de M1 vuelve a exigir una canción real con ACE-Step escuchada en la web.
