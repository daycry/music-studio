# Roadmap

Cada hito es una iniciativa en `docs/roadmap/<YYYY-MM-DD>-<slug>/` con el formato del plugin `custom-agents`: `spec.md` (qué y criterios de aceptación), `improvement-plan.md` (fases, riesgos, `test-plan:`), `tasks.md` (**ledger canónico**, validado con `ledger-lint`) y `test-plan.md` si hay UI. **Sin evaluación económica** (proyecto personal, [ADR-0001](../decisiones/ADR-0001-reinicio-desde-cero.md)): el esfuerzo se expresa en horas orientativas.

| Fecha | Slug | Título | Prioridad | Estado spec | Estado eval. | Esfuerzo | Spec | Tasks |
|-------|------|--------|-----------|-------------|--------------|----------|------|-------|
| 2026-09-28 | `m0-entorno-y-motor` | M0 · Entorno, motor por CLI y elección de modelo | Crítica | **aprobada** | n/a | ~88 h (80 sin la opcional) | [spec](./2026-09-28-m0-entorno-y-motor/spec.md) | [tasks](./2026-09-28-m0-entorno-y-motor/tasks.md) |
| 2026-09-28 | `m1-mvp-estudio` | M1 · MVP del estudio web | Alta | **aprobada** | n/a | ~153 h | [spec](./2026-09-28-m1-mvp-estudio/spec.md) | [tasks](./2026-09-28-m1-mvp-estudio/tasks.md) |

## Hitos siguientes (sin carpeta todavía; se abren al cerrar el anterior)

| Hito | Contenido ([funcionalidades](../producto/funcionalidades.md)) | Condición para abrirlo |
|---|---|---|
| **M2 · Iteración creativa** | Variación (F-20), extender (F-21), regenerar sección (F-22), cover (F-23), recortar y fundidos (F-24), árbol de versiones (F-25), comparador A/B (F-26), modo simple (F-16), asistente de letras con LLM local (F-17), ajustes de proveedores externos opcionales (F-86) | M1 cerrado y en uso real (≥ 30 generaciones propias) |
| **M3 · Producción, portada y vídeo con letra** | Stems + mezclador (F-30, F-31), exportación por destino (F-32), análisis completo (F-33), letra sincronizada (F-34), **portada** (F-35), **vídeo con letra y visualizador — N0** (F-40, F-41), fotos propias como fondo/portada (F-44c), canción desde audio propio (F-19), calidad alta con XL (F-18), presets (F-70), exportar/importar canción (F-06), copia de seguridad (F-85) | M2 cerrado |
| **M4 · Vídeo musical** | **Spike de vídeo en la 5070** (tiempos, VRAM, RAM con 32 GB) → proyecto de vídeo (F-42), guion automático al beat (F-43), personajes y **protagonista desde fotos** (F-44, F-44b), guion gráfico N1 (F-45), planos generativos N2/N3 (F-46), cantante con sincronía labial (F-47), editor de timeline (F-48), render 16:9/9:16 y cola nocturna (F-49, F-81), aviso de desfase (F-50), proveedor externo por plano opcional (F-51) | M3 cerrado |
| **M5 · Personalización avanzada** | Referencia de timbre (F-71), LoRA de estilo musical (F-72), LoRA de personaje (F-73), segundo motor musical (F-74) | M4 cerrado; ≥ 100 generaciones y ≥ 1 canción usada en algo real |
| **Futuro** | Acceso por LAN con token, multiusuario, comercialización ([gate GC](../legal/comercializacion.md)) | Decisión explícita en un ADR |

## Cómo implementar un hito

1. **Aprobar la spec**: revisarla y cambiar `estado: borrador` → `aprobada` en `spec.md` (y la fila de esta tabla).
2. Lanzar `/dev-cycle docs/roadmap/<fecha>-<slug>`. Como la spec está aprobada y el plan escrito, **se saltan las Fases 1–2 del ciclo** (evaluar/planificar): se va a implementación. Si el ciclo ofrece `evaluator`, responder que la evaluación es `n/a` (ADR-0001).
3. El `implementer` sigue el orden de fases de `tasks.md`, marca cada tarea y ejecuta su **Verificación**; la revisión adversarial usa [`../CONSTITUTION.md`](../CONSTITUTION.md) como referencia; `qa` ejecuta `test-plan.md` (o modo «sin UI» en M0).
4. Validar el ledger en cualquier momento: `python <plugin>/agent-kits/shared/ledger-lint.py docs/roadmap/<…>/tasks.md` → `0 incoherencias`.
5. Cerrar: todos los criterios con evidencia, retro (`/retro`), spec → `implementada`; abrir la carpeta del hito siguiente.

## Vocabulario de estados

- **Spec:** `borrador` · `aprobada` · `implementada` · `obsoleta`
- **Plan y tareas** (lo exige `ledger-lint`): `borrador` · `en-progreso` · `en-revision` · `completado` · `cancelado`. Una tarea que espera a otra sigue en `borrador` (sus **Dependencias** lo indican); la opcional que no se haga pasa a `cancelado` con justificación.
- **Prioridad:** `Baja` · `Media` · `Alta` · `Crítica`

## Histórico

La iniciativa anterior `2026-07-27-plataforma-musical-ia` (planificación corporativa, 85 tareas, 2 completadas) está archivada en [`../archive/roadmap-2026-07-27/`](../archive/roadmap-2026-07-27/). No se continúa.
