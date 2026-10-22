# Regresion actual de la web

Fecha: 2026-10-10

```text
pnpm --filter web test
23 ficheros, 248 passed

pnpm --filter web lint
exit 0

pnpm --filter web typecheck
exit 0

pnpm --filter web build
exit 0; Next.js webpack production build, 6/6 paginas generadas
```

La regresion cubre layout, temas, cliente API, eventos, compositor, biblioteca,
tarjeta de generacion, reproductor y vistas de cancion. Los avisos de jsdom sobre
canvas/media no producen fallos. T-08 y las tareas web dependientes siguen abiertas
por Docker/Playwright, revisión y QA de cierre.
