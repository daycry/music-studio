# T-12 — marcadores de beat en la forma de onda

Fecha: 2026-10-10

La vista ya cargaba `RegionsPlugin`, pero no añadía regiones a partir de `audio.beats`. Se corrigió `Waveform` para crear una región estrecha, coloreada y no editable (`drag: false`, `resize: false`) por cada tiempo finito dentro de la duración. Los tiempos negativos, NaN y los que quedan fuera de la canción se descartan. El efecto también reacciona cuando cambia la lista de beats.

TDD y verificación:

- RED: el test nuevo esperaba dos regiones para beats válidos y obtuvo 0.
- GREEN focal: `pnpm --filter ./apps/web exec vitest run components/Waveform.test.tsx` → **2 passed**.
- Suite web: `pnpm --filter ./apps/web test` → **248 passed** en 23 ficheros.
- TypeScript: `pnpm --filter ./apps/web exec tsc --noEmit` → exit 0.
- ESLint: `pnpm --filter ./apps/web lint` → exit 0.

La implementación sigue pendiente de la QA visual Playwright sobre una canción con análisis real; este cambio no acredita todavía el cierre de T-12 ni del hito M1.
