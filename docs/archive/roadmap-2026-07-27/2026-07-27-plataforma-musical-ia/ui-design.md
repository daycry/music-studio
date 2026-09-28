---
documento: ui-design
titulo: Diseño de interfaz — Plataforma musical IA
slug: plataforma-musical-ia
estado: propuesta
fecha: 2026-08-18
actualizado: 2026-08-18
autor: Daycry (7590335+daycry@users.noreply.github.com)
spec: ./spec.md
plan: ./improvement-plan.md
tasks: ./tasks.md
---

# Diseño de interfaz: Plataforma propia de generación musical por IA

> **Cadena de artefactos:** [`spec.md`](./spec.md) → [`evaluation.md`](./evaluation.md) → [`improvement-plan.md`](./improvement-plan.md) → [`tasks.md`](./tasks.md) → **este documento** (guía de implementación frontend).
>
> **Regla de oro (D-12 / D-12b):** de Suno se deriva el **modelo de interacción** — panel de creación a la izquierda, biblioteca central, reproductor persistente inferior, generación en **pares de variantes** — y **nada más**. Logotipo, paleta, tipografía e iconografía son de Daycry. Ante la duda: si un elemento visual se reconocería como "de Suno", no entra.
>
> Este documento es normativo para T-46…T-48 y para las tareas frontend de C-13 (T-17, T-18, T-21). El implementador no debe inventar nada que esté definido aquí; lo que no esté definido aquí, se decide con el criterio de §1 y se documenta en el changelog.

---

## 1. Concepto: «estudio nocturno»

La plataforma es una **herramienta de trabajo de audio**, no un sitio de marketing. Los entornos donde se trabaja el sonido — DAWs, salas de mezcla, mesas de directo — viven en oscuro por tres razones funcionales que adoptamos:

1. **Fatiga**: sesiones de iteración largas (5–10 variantes seguidas, spec D-05b) sobre fondo claro cansan; sobre fondo oscuro cálido, no.
2. **Protagonismo del contenido**: sobre fondo oscuro, la forma de onda, los medidores y el estado de generación **son** la interfaz. El chrome desaparece.
3. **Jerarquía por luz**: en oscuro, la atención se dirige con luminancia, no con recuadros. Lo que brilla es lo que importa: el acento se reserva para audio activo, progreso real y acciones primarias.

**Principio rector:** *el audio es el protagonista visual*. La forma de onda no es decoración: es navegación (seek), es estado (progreso de generación) y es contenido (comparar variantes A/B de un vistazo). Cada píxel de color de acento debe poder justificarse como "esto suena, esto avanza o esto es la acción principal".

**Tema claro** disponible desde el día 1 (toggle en el menú de usuario + respeto a `prefers-color-scheme`), porque D-25 exige componentes accesibles por defecto y hay usuarios que trabajan en salas iluminadas. El tema claro es "papel cálido", no blanco puro: mismos tokens, valores invertidos (§2.1).

---

## 2. Sistema de diseño

### 2.1 Paleta y tokens CSS

Fondos en **capas oscuras cálidas** (base marrón-neutra, no azul-negra: el azul frío es el cliché de "dashboard tech" y el negro puro provoca smearing en OLED). Cuatro capas de elevación: cada capa es ~6 % más luminosa que la anterior.

```css
:root[data-theme="dark"] {
  /* Fondos (de fondo de página a superficie flotante) */
  --bg-0: #0E0C0A;   /* página */
  --bg-1: #171412;   /* paneles, sidebar, reproductor */
  --bg-2: #211D19;   /* tarjetas, inputs */
  --bg-3: #2B2620;   /* hover de tarjeta, popovers, tooltips */

  /* Bordes (elevación sin sombras, §2.5) */
  --border-subtle: #2E2823;
  --border-strong: #453D34;

  /* Texto */
  --text-primary:   #F2EDE7;   /* 16,8:1 sobre --bg-0 ✓ AAA */
  --text-secondary: #A89F94;   /* 7,5:1 sobre --bg-0 · 6,4:1 sobre --bg-2 ✓ AA */
  --text-muted:     #7A7166;   /* solo texto ≥ 18,66 px o decorativo (AA texto grande) */

  /* Acento (ver candidatos en §2.2) */
  --accent:          #34D399;  /* 10,2:1 sobre --bg-0 ✓ AA/AAA como texto */
  --accent-hover:    #5CE0AE;
  --on-accent:       #0E0C0A;  /* texto sobre botón de acento: 10,2:1 ✓ */
  --accent-muted:    rgba(52, 211, 153, 0.14);  /* fondos de estado, nunca texto */

  /* Semánticos */
  --danger:  #F87171;  /* 7,0:1 sobre --bg-0 ✓ */
  --warning: #E8C547;  /* 11,6:1 sobre --bg-0 ✓ — esperas largas, cold start */
  --info:    #7FB8D8;

  /* Audio (la forma de onda tiene tokens propios: no es "gris decorativo") */
  --wave-idle:     #4A423A;   /* onda no reproducida */
  --wave-played:   var(--accent);
  --wave-generating: #6E675E; /* onda en condensación, §3 */
}

:root[data-theme="light"] {
  --bg-0: #FAF7F2;  --bg-1: #F2EDE5;  --bg-2: #EAE3D9;  --bg-3: #FFFFFF;
  --border-subtle: #DDD5C9;  --border-strong: #BFB5A6;
  --text-primary: #26211B;   /* 14,9:1 sobre --bg-0 ✓ */
  --text-secondary: #5C544A; /* 7,1:1 ✓ */
  --text-muted: #8A8072;
  --accent: #0E7C5B;         /* variante oscura del verde: 4,9:1 sobre --bg-0 ✓ AA */
  --accent-hover: #0A6449;
  --on-accent: #FAF7F2;
  --danger: #B3261E;  --warning: #8A6D00;  --info: #1D6E96;
  --wave-idle: #C9BFB1;  --wave-played: var(--accent);
}
```

**Regla de contraste:** todo par texto/fondo nuevo se verifica contra WCAG AA (≥ 4,5:1 texto normal, ≥ 3:1 texto grande y componentes de UI) antes de entrar en el código. Los ratios anotados arriba están calculados sobre luminancia relativa WCAG 2.x. `--text-muted` **no** se usa para texto informativo sobre `--bg-2` o superior.

### 2.2 El acento: candidatos y elección

Prohibido: morados/rosas (identidad de Suno, D-12b) y naranja corporativo genérico. Tres candidatos, todos verificados AA sobre `--bg-0`:

| Candidato | Hex (oscuro / claro) | Contraste sobre `--bg-0` | Justificación | Riesgo |
|---|---|---|---|---|
| **A · Verde traza** (recomendado) | `#34D399` / `#0E7C5B` | 10,2:1 / 4,9:1 | Es el verde de los VU-meters, osciloscopios y LEDs de señal del hardware de estudio: significa literalmente **"hay señal"**, que es la metáfora exacta del producto (el acento marca audio activo y progreso). Máximo contraste de los tres; funciona como texto pequeño sin retocar. | Que derive hacia "verde éxito" de sistema; se mitiga reservando el verde semántico de éxito para toasts y usando el acento solo en audio/acciones |
| B · Ámbar de válvula | `#E8C547` / `#8A6D00` | 11,6:1 / 5,0:1 | Cálido, coherente con la base marrón; evoca vúmetros analógicos y cinta. Distintivo frente a todo el sector IA. | Colinda con el naranja corporativo genérico y con `--warning`; obligaría a buscar otro color para avisos |
| C · Cian señal | `#38BDF8` / `#1D6E96` | 9,1:1 / 4,6:1 | Color clásico de displays de forma de onda digitales; lectura inmediata de "audio". | Es el acento más usado en dashboards tech: el menos distintivo de los tres; rompe la calidez de la base |

**Decisión propuesta: candidato A (verde traza).** Un solo acento en toda la aplicación. Nada de gradientes multicolor: la única "segunda tinta" permitida es `--warning` para esperas largas y `--danger` para errores/kill switch.

### 2.3 Tipografía

Dos familias variables de Google Fonts + una mono para datos técnicos:

| Rol | Familia | Por qué |
|---|---|---|
| **UI** (todo el cuerpo) | **Inter** (variable) | Cifras tabulares (`font-variant-numeric: tabular-nums`) imprescindibles para cronómetros de espera, coste por generación y posiciones de cola que cambian sin bailar; x-height alta legible a 13–14 px en paneles densos; cobertura completa de castellano/catalán; un solo fichero variable (peso 400–700) |
| **Display** (H1 de página, cifras grandes del admin, pantalla de login) | **Bricolage Grotesque** (variable) | Grotesca con carácter (contraste y recortes propios) que da identidad sin parecerse a la marca de Suno ni al genérico "startup IA" (Space Grotesk/Eurostile); variable en peso y anchura, útil para titulares compactos |
| **Mono** (hashes, semillas, `job_id`, manifiesto) | **JetBrains Mono** | El certificado de procedencia (§4.3) muestra hashes SHA-256 y versiones de esquema: la mono los hace escaneables y copiables; distingue 0/O, 1/l |

Escala tipográfica (rem, base 16 px): `12 · 13 · 14 (cuerpo) · 16 · 18 · 22 · 28 · 36 · 48`. Interlineado 1,5 en cuerpo, 1,2 en display. Display **nunca** en componentes de formulario.

### 2.4 Espaciado y radios

- **Espaciado:** escala de base 4 px — `4 · 8 · 12 · 16 · 24 · 32 · 48 · 64` (Tailwind estándar: `1 · 2 · 3 · 4 · 6 · 8 · 12 · 16`). Densidad de herramienta, no de landing: padding de tarjeta 16 px, de panel 24 px.
- **Radios:** `--radius-sm: 6px` (inputs, chips), `--radius-md: 10px` (tarjetas, botones), `--radius-lg: 16px` (paneles, modales), `--radius-full` (pills de estado, avatar, botón play circular). Nada de radios mixtos en un mismo componente.

### 2.5 Elevación sin sombras pesadas

En tema oscuro las sombras negras no se ven. La elevación se comunica con **capa + borde**:

| Nivel | Receta |
|---|---|
| Reposo (tarjeta) | `background: var(--bg-2); border: 1px solid var(--border-subtle)` |
| Hover / activo | `background: var(--bg-3); border-color: var(--border-strong)` |
| Flotante (popover, menú, tooltip) | `--bg-3` + borde fuerte + `box-shadow: 0 8px 24px rgba(0,0,0,0.35)` — la **única** sombra permitida |
| Reproductor persistente | `--bg-1` + `border-top: 1px solid var(--border-strong)` — sin sombra: está anclado, no flota |

### 2.6 Motion

| Token | Valor | Uso |
|---|---|---|
| `--dur-fast: 120ms` | `ease-out` | Hover, focus, toggles, chips |
| `--dur-base: 200ms` | `cubic-bezier(0.2, 0, 0, 1)` | Apertura de popovers, cambio de tab, aparición de toast |
| `--dur-slow: 320ms` | `cubic-bezier(0.2, 0, 0, 1)` | Transiciones de estado de la tarjeta de generación, expansión del certificado |

**Qué se anima:** opacidad, transform (translate/scale ≤ 4 %), color de borde/fondo, la visualización generativa (§3).
**Qué NO se anima:** layout (nada de reflows animados al llegar pistas nuevas: la nueva tarjeta aparece con fade, sin empujar con animación), texto en curso de lectura, cifras de coste/espera (cambian en seco: son datos, no espectáculo), la posición de seek de la forma de onda (respuesta inmediata).
**`prefers-reduced-motion: reduce`:** todas las duraciones a 0, la visualización generativa pasa a su variante estática (§3.4), los skeletons dejan de pulsar (quedan estáticos). Es un media query global en la capa de tokens, no un caso por componente.

---

## 3. La firma visual: la generación como experiencia

La espera **es parte del producto**: arranque en frío de 2–6 min si el pod está apagado (spec S-01, S-12), inferencia de ~90–150 s, post-proceso. La firma de esta UI es que **la tarjeta de la pista en generación es un instrumento de medida honesto y bello**, no un spinner.

### 3.1 Anatomía de la tarjeta en generación

```
┌──────────────────────────────────────────────────────────────┐
│  Título provisional (del prompt) · modelo@versión             │
│                                                                │
│  ····•·····•∿∿•·····∿∿∿∿•···∿∿∿∿∿∿∿∿←——— zona aún "gas" ———→ │
│  [canvas: la onda se condensa de izquierda a derecha]          │
│                                                                │
│  ● Generando — 42 %            ⏱ ~1 min restante   ⚙ 0,04 €  │
│  ○───────●───────○───────○                                     │
│  En cola   GPU    Generando  Post-proceso                     │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 La visualización generativa (spec implementable)

**Técnica:** canvas 2D (no WebGL: una tarjeta a la vez lo justifica; WebGL solo si hubiera > 6 generaciones simultáneas visibles, que la cuota de concurrencia de §12.1 de la spec — 2 por usuario — hace improbable).

- **Modelo de datos:** 96 columnas (barras de la futura forma de onda). Cada columna tiene `targetAmp` (al principio desconocida → ruido perlin suave) y `chaos` (0…1).
- **Comportamiento:** cada columna se dibuja como una línea vertical cuya altura oscila con ruido `simplex(x, t)` multiplicado por `chaos`. Con el **progreso real recibido por SSE** (T-16), `chaos` decae de 1 → 0 columna a columna, de izquierda a derecha: la onda **se condensa** — pasa de gas vibrante a barras estables — exactamente hasta el porcentaje real completado. Sin progreso nuevo, la parte condensada **no avanza** (nunca mentir con una barra que se llena sola).
- **Color:** zona condensada en `--accent` al 60 % de opacidad; zona en gas en `--wave-generating`. Al llegar `succeeded`, transición de 320 ms en la que las barras adoptan los picos reales del audio (peaks del artefacto) y el color pasa a `--wave-idle`: la visualización **se convierte** en la forma de onda definitiva, sin cambio de componente.
- **Presupuesto de rendimiento:** un solo `requestAnimationFrame` compartido por todas las tarjetas visibles, 30 fps máximo, pausa total cuando la pestaña está oculta (`visibilitychange`) o la tarjeta sale del viewport (`IntersectionObserver`). Coste objetivo < 2 ms/frame.

### 3.3 Etapas visibles y mensajes honestos

El stepper de 4 etapas mapea 1:1 la máquina de estados del backend (T-15) vía SSE (T-16):

| Etapa (estado backend) | Texto UI | Datos mostrados |
|---|---|---|
| `queued` | «En cola — posición N» | Posición real, espera estimada (incluye arranque en frío si el pod está apagado, criterio de T-16) |
| `starting` | «Arrancando GPU» | **Mensaje honesto de cold start** (ver abajo) |
| `running` | «Generando — N %» | % real, tiempo restante estimado, coste acumulado en € (métrica de T-24) |
| post-proceso (fase final de `running`) | «Post-proceso — loudness y formatos» | Destino elegido (broadcast −23 / streaming −14 LUFS) |

**Estados de espera larga (cold start).** Si la estimación de `starting` supera 60 s, la tarjeta cambia a modo espera-larga: el stepper se mantiene, el mensaje pasa a `--warning` y dice la verdad:

> ⏱ **La GPU está arrancando en frío: entre 2 y 6 minutos.** Tu pista no ha empezado a generarse todavía. Puedes seguir navegando; te avisaremos.

Con dos refinamientos: (a) el cronómetro cuenta **hacia arriba** («2:14 de ~2–6 min»), nunca una barra que finge precisión; (b) si el trabajo va al pod caliente, este estado ni aparece (~0 s). Al desbordar al pod efímero (D-26), el mensaje lo explica: «Hay otra generación en curso; arrancamos una segunda GPU para ti». La honestidad es un requisito, no un tono: la spec (S-12) exige mostrar el arranque en frío en la espera estimada.

### 3.4 Variante `prefers-reduced-motion`

Sin animación: la zona pendiente se dibuja como barras estáticas atenuadas y la condensada como barras estáticas en acento; el progreso se comunica solo con el % numérico y el stepper. Toda la información persiste; solo desaparece el movimiento.

---

## 4. Pantallas

Layout global (derivado del modelo de interacción de Suno, D-12; identidad propia, D-12b):

```
┌────────┬───────────────────────────────────────────┬─────────┐
│  Nav   │            Contenido central              │ (Panel  │
│ lateral│      (crear · biblioteca · detalle)       │ contex- │
│  64px  │                                           │  tual)  │
├────────┴───────────────────────────────────────────┴─────────┤
│  ▶ Reproductor persistente (72 px) — visible en toda la app  │
└───────────────────────────────────────────────────────────────┘
```

Nav lateral estrecha (iconos + tooltip): Crear · Biblioteca · Admin (solo rol admin) · Usuario. En < 1024 px la nav pasa a barra inferior sobre el reproductor colapsado.

### 4.1 Crear (T-46, T-47, T-48)

```
┌───────────── Panel de creación (400 px) ─────────────┬──── Feed de resultados ────┐
│ LETRA                                    [Instrumental ⊘] │                        │
│ ┌───────────────────────────────────┐                 │  ┌── Par de variantes ──┐ │
│ │ [verso]                           │                 │  │ ∿∿∿ condensándose A  │ │
│ │ Luz de neón sobre el asfalto...   │                 │  │ ∿∿∿ condensándose B  │ │
│ │ [estribillo]                      │                 │  └──────────────────────┘ │
│ │ ...                               │                 │  ┌── Generación previa ─┐ │
│ └───────────────────────────────────┘                 │  │ ▶ ∿∿∿∿∿∿  A ★        │ │
│ [+ verso] [+ estribillo] [+ puente]                   │  │ ▶ ∿∿∿∿∿∿  B          │ │
│                                                        │  └──────────────────────┘ │
│ ◉ Declaración de derechos de la letra *               │                            │
│   ( ) Propia  ( ) Del asistente  ( ) Permiso doc.     │                            │
│                                                        │                            │
│ ESTILO                                                 │                            │
│ ┌ prompt de estilo (texto libre) ──────────────────┐  │                            │
│ [pop] [electrónica] [cinemática] [+ chips géneros]    │                            │
│                                                        │                            │
│ VOZ  [preset ▾ con muestra ▶]   DURACIÓN [180 s ▾]    │                            │
│ DESTINO [broadcast −23 ▾]                              │                            │
│                                                        │                            │
│ ┌────────────────────────────────────────────────┐    │                            │
│ │  ⚡ Generar   ·  ~0,04 € · cola: 2 · GPU ● lista │    │                            │
│ └────────────────────────────────────────────────┘    │                            │
│ Cuota: 154/200 este mes                                │                            │
└────────────────────────────────────────────────────────┴────────────────────────────┘
```

**Comportamiento:**

- **Editor de letra (T-46):** textarea controlada con capa espejo de resaltado — las etiquetas `[verso]`/`[estribillo]`/`[puente]` se pintan como píldoras en `--accent-muted` con texto `--accent` sin dejar de ser texto plano editable (parseable por la API, criterio de T-46). Botones de inserción rápida de etiqueta bajo el editor. Validación en vivo: etiqueta malformada → subrayado `--warning` + mensaje. Contador de líneas por sección.
- **Declaración de derechos (T-43/T-47):** grupo de radios **siempre visible**, no un checkbox escondido: es bloqueo duro (D-21). Sin selección, el botón Generar queda deshabilitado con texto explicativo (no tooltip-only). Si la letra vino del asistente (C-05, Fase 2), se autoselecciona «Del asistente».
- **Estilo:** texto libre + chips de género sugeridos (dataset estático en F1). Los chips **añaden** texto al prompt, no lo sustituyen; chip activo = fondo `--accent-muted`, borde `--accent`.
- **Voz:** select con muestra reproducible por preset (▶ de 3 s inline, C-03; en F1 puede haber < 8 presets: el select muestra los disponibles reales). **Instrumental** es un toggle en cabecera del panel: al activarlo, letra y voz se pliegan con opacidad 40 % (no desaparecen: el usuario no pierde lo escrito).
- **Duración:** select 30/60/120/180 s (máx. 300, §12.1 spec). **Destino:** broadcast/streaming/stems — fija el loudness (D-23) y se muestra el valor LUFS junto a la opción.
- **Botón Generar (T-47/T-48):** único botón en `--accent` de la pantalla. Muestra **coste estimado en €** (de la telemetría de T-24), **profundidad de cola** y **estado de la GPU** (● lista / ◐ arrancará en frío ~2–6 min). Bajo el botón, la cuota mensual restante (§12.1: 200/mes). Al pulsar: el botón pasa a estado enviando (spinner 120 ms mínimo), el par de tarjetas de generación aparece arriba del feed y el foco se mueve a la primera tarjeta (accesibilidad).
- **Pares de variantes (T-48, D-22):** cada generación produce el par A/B agrupado en un contenedor con borde común; A y B son tarjetas independientes (reproducir, favorito ★, descargar, abrir detalle). Los **errores** de la tabla §6 de la spec se muestran como estado de la tarjeta con el `job_id` visible y acción de recuperación («Cuota agotada — se reinicia el 1 de septiembre», «Cola llena — reintenta en ~N min»), nunca un toast que desaparece.

### 4.2 Biblioteca (T-17)

```
┌ Biblioteca ──────────────────────────────────────────────────┐
│ [🔍 buscar]  [Proyecto ▾] [Fecha ▾] [Modelo ▾] [Estado ▾]     │
│                                        [⊞ grid | ≡ lista]    │
├──────────────────────────────────────────────────────────────┤
│ ┌ Par ──────────────────────────────┐  ┌ Pista suelta ─────┐ │
│ │ ▶ ∿∿∿∿∿∿∿ Neón y asfalto  A ★    │  │ ▶ ∿∿∿∿ Sintonía   │ │
│ │ ▶ ∿∿∿∿∿∿∿ Neón y asfalto  B      │  │   2:41 · ace-step  │ │
│ │   3:00 · ace-step@1.5 · ayer      │  └────────────────────┘ │
│ └───────────────────────────────────┘                         │
│ ┌ En generación ────────────────────┐  ┌ Fallida ──────────┐ │
│ │ ◍ ∿∿·····  Balada 40 % ~1 min    │  │ ⚠ Ver detalle      │ │
│ └───────────────────────────────────┘  └────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

**Comportamiento:** filtros por proyecto, fecha, modelo (criterio de T-17) + estado (todas / en generación / favoritas / fallidas). Vista grid (tarjeta con mini-onda) y lista (fila densa con onda inline). Los **pares A/B se agrupan siempre** (mismo `parent`/lote), con la variante favorita marcada ★. Las tarjetas en generación usan la visualización de §3 en miniatura. Clic en tarjeta → detalle; clic en ▶ → reproduce en el reproductor persistente sin navegar. Scroll infinito con skeletons (§5.3). Estado vacío: ilustración de onda plana en `--wave-idle` + CTA «Crear tu primera pista».

### 4.3 Detalle de pista (T-21 + certificado de procedencia)

```
┌ Neón y asfalto — variante A ────────────────────────────────────┐
│ ∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿  (onda grande,   │
│ ▶ 0:00 ──────●────────────────────────── 3:00    seek + zoom)  │
│                                                                  │
│ 3:00 · ace-step@1.5.0 · broadcast −23 LUFS · proyecto Sintonías │
│                                                                  │
│ [⬇ Descargar ▾ MP3 · FLAC · WAV 48 kHz]  [🔗 Compartir]  [★]    │
│ [⤢ Extender 🔒] [◱ Regenerar sección 🔒] [≣ Stems 🔒]           │
│                                                                  │
│ ┌─ 🛡 CERTIFICADO DE PROCEDENCIA ────────────────────────────┐  │
│ │ ✓ Cadena de trazabilidad verificada        manifiesto v1   │  │
│ │                                                             │  │
│ │ Modelo      ace-step@1.5.0 · Apache-2.0                    │  │
│ │ Pesos       sha256: 3fa9…c21e                              │  │
│ │ Datos entr. no divulgada (declarado)                       │  │
│ │ Letra       declaración: propia · 2026-08-18 · daycry      │  │
│ │ Linaje      origen ← esta pista es raíz                    │  │
│ │ Ledger      #4821 ← #4820 ✓ cadena íntegra                 │  │
│ │ Semilla     84920117 · destino broadcast · 150 s GPU       │  │
│ │                                        [Exportar JSON]     │  │
│ └─────────────────────────────────────────────────────────────┘  │
│ ── Variantes del lote:  [● A]  [○ B]                             │
└──────────────────────────────────────────────────────────────────┘
```

**Comportamiento:**

- **Forma de onda grande:** seek con clic/arrastre y teclado (§7); progreso de reproducción en `--wave-played`. Zoom con rueda + modificador (preparando el editor de secciones de F3 sobre el mismo componente).
- **Certificado de procedencia — rango de feature, no letra pequeña.** Es **el diferenciador del producto** (C-10a): panel siempre visible (no colapsado) bajo las acciones, con cabecera propia, icono de escudo y el veredicto de la cadena («✓ cadena íntegra» tras validar los hashes del ledger, T-28). Datos en JetBrains Mono, hashes truncados con copiar-al-clic. `training_data_declaration: no divulgada` se muestra **tal cual, sin eufemismos** — la honestidad del manifiesto es el producto (spec §1.1). Exportar JSON desde F1; el PDF firmado C2PA llega con C-10b (Fase 2) y el botón lo anticipa deshabilitado con tooltip «Certificado PDF firmado — Fase 2».
- **Descargar:** menú con MP3 320 / FLAC / **WAV 48 kHz** (se genera a demanda, D-23: el item avisa «se prepara al momento» con spinner si tarda).
- **Compartir (T-21, D-24):** copia la **URL de la pista en la aplicación** (requiere sesión). El toast lo dice explícitamente: «Enlace copiado — solo usuarios con acceso podrán abrirlo». Jamás se expone la URL firmada.
- **Acciones futuras deshabilitadas con fase visible:** Extender y Regenerar sección (C-07, Fase 3), Stems (C-06, Fase 2) aparecen **deshabilitadas con candado y tooltip** «Disponible en Fase 2/3». Motivo: enseñan el techo del producto sin mentir sobre el presente, y reservan el layout para no re-maquetar después.
- **Conmutador A/B del lote:** tabs al pie para saltar entre variantes manteniendo la posición de scroll.

### 4.4 Reproductor persistente inferior (T-18)

```
┌──────────────────────────────────────────────────────────────────────────┐
│ [∿ mini] Neón y asfalto — A   ⏮ ▶ ⏭   0:42 ∿∿∿●∿∿∿∿∿∿∿ 3:00   🔊▁▂▄ ≡cola│
└──────────────────────────────────────────────────────────────────────────┘
```

**Comportamiento:** persiste al navegar (layout de App Router: el reproductor vive fuera del árbol de páginas, criterio de T-18). Mini-onda clicable como seek. `⏮/⏭` navegan la **cola de reproducción** (panel ≡ que se despliega hacia arriba: lista reordenable por arrastre, «reproducir a continuación» desde cualquier tarjeta de biblioteca). Volumen con slider + mute. Al reproducir una variante de un par, `⏭` va primero a su pareja (comparación A/B rápida). Toda la superficie es accesible por teclado (D-25, §7). En móvil colapsa a una fila mínima expandible. El estado (pista, posición, cola) sobrevive a la navegación pero **no** se persiste entre sesiones en F1.

### 4.5 Admin mínimo (soporta T-41 y §12.1 de la spec)

```
┌ Administración ──────────────────────────────────────────────┐
│ GASTO GPU — AGOSTO           ██████████░░░░░░  64 € / 100 €  │
│ alerta 50 % ✓ enviada · alerta 80 % pendiente                │
│                                     [⛔ KILL SWITCH]          │
│ ─────────────────────────────────────────────────────────────│
│ CUOTAS POR USUARIO                                            │
│ daycry     ████████░░ 154/200   [editar] [reset]             │
│ scampos    ███░░░░░░░  61/200   [editar] [reset]             │
│ ─────────────────────────────────────────────────────────────│
│ POD CALIENTE  L-V 8:00–18:00 Europe/Madrid  [calendario ▾]   │
│ GPU ahora: ● caliente · 2 trabajos en cola global            │
└──────────────────────────────────────────────────────────────┘
```

**Comportamiento:** solo rol admin (T-52). Gasto del mes contra el tope (D-17) con marcas del 50/80 %, en cifra grande (display). **Kill switch** en `--danger` con confirmación de dos pasos (escribir «PAUSAR») y texto de consecuencia: «Se pausa el despacho y se apagan los pods; los trabajos quedan en cola, no fallan». Edición de cuota por usuario inline (UI de administración de cuotas exigida por §12.1). Calendario del pod caliente (D-05b) editable: festivos y excepciones.

### 4.6 Login con 2FA (T-50, T-51)

```
┌──────────── centrado, --bg-0, logo Daycry ────────────┐
│         [display] Estudio de música IA                  │
│  [ Continuar con SSO corporativo ]                      │
│  [ Continuar con Google ]                               │
│  ─────────────── o ───────────────                      │
│  email [____________]  contraseña [____________]        │
│  [ Entrar ]                                             │
│                                                          │
│  (paso 2, si 2FA activo)                                │
│  Código de tu app de autenticación                      │
│  [_] [_] [_] [_] [_] [_]   ¿Sin acceso? Usa un código   │
│                             de respaldo                 │
└──────────────────────────────────────────────────────────┘
```

**Comportamiento:** dos vías con igual jerarquía (D-08). Paso TOTP con 6 casillas auto-avance, pegado completo soportado, y enlace a códigos de respaldo (un solo uso, T-51). Errores concretos («código caducado» ≠ «código incorrecto» en la medida en que el backend lo distinga sin filtrar información). Fondo: la visualización generativa de §3 en modo ambiente muy atenuado (opacidad 8 %, y estática con reduced-motion) — única licencia decorativa de la app, porque el login no compite con contenido.

### 4.7 Fase 2/3 — diseño anticipado (sin tareas en el ledger actual)

Estas pantallas **no tienen tarea en `tasks.md`** (C-06 es Fase 2 y C-07 Fase 3, fuera del plan vigente); se especifican aquí para que T-18 y el componente de onda no las cierren.

**(a) Reproductor multipista de stems (C-06)** — extiende `MultitrackBase` de T-18:

```
┌ Stems — Neón y asfalto A ───────────────────────────────┐
│ VOZ    [M][S] ▁▃▅∿∿∿∿∿∿∿∿∿∿∿∿∿∿  ─●── vol              │
│ BATERÍA[M][S] ▁▃▅∿∿∿∿∿∿∿∿∿∿∿∿∿∿  ───● vol              │
│ BAJO   [M][S] ▁▃▅∿∿∿∿∿∿∿∿∿∿∿∿∿∿  ──●─ vol              │
│ OTROS  [M][S] ▁▃▅∿∿∿∿∿∿∿∿∿∿∿∿∿∿  ─●── vol              │
│ ▶ 0:42 ──────●──────────────── 3:00  [⬇ descargar stems]│
└──────────────────────────────────────────────────────────┘
```

Mezclador vertical: una fila por stem con **mute [M] / solo [S]** (solo exclusivo con clic, aditivo con Cmd/Ctrl), fader horizontal por pista, transporte único sincronizado (±10 ms, criterio C-06). Las cuatro ondas comparten eje temporal y zoom.

**(b) Editor de secciones sobre forma de onda (C-07)** — extiende la onda del detalle:

```
│ ∿∿∿∿∿∿[░░░ selección 0:58–1:24 ░░░]∿∿∿∿∿∿∿∿∿∿           │
│        ◄ asas arrastrables ►                              │
│  [▶ escuchar selección] [⟳ regenerar sección] [✕]        │
```

Selección de región con arrastre (asas con snap a los límites de sección de la letra si existen), overlay en `--accent-muted`, preescucha en bucle de la región, y «Regenerar sección» que lanza el flujo de C-07 (misma tarjeta de generación de §3 con la región marcada). El resultado entra como nueva variante con linaje `section_inpaint` (D-22) y `section_map` visible en su certificado.

---

## 5. Microinteracciones

### 5.1 Hover con preview de audio

En biblioteca (grid y lista): mantener el cursor **400 ms** sobre una tarjeta reproduce un fragmento (desde el 25 % de la pista, 10 s máx.) a volumen 50 % del maestro. Debounce de 400 ms para que barrer la lista no dispare nada; salir de la tarjeta detiene con fade de 120 ms. **Opt-out** en preferencias de usuario («Preescucha al pasar el cursor: sí/no», por defecto sí) y desactivado automáticamente si ya hay reproducción activa en el reproductor persistente (no se pisa lo que suena). En táctil no existe.

### 5.2 Transiciones de estado de generación

`queued → starting → running → succeeded/failed` anima **solo** el stepper y el color del indicador (320 ms); el texto cambia en seco. `succeeded`: la condensación termina, las barras adoptan los picos reales, y un pulso único de borde en `--accent` (600 ms, sin repetición) señala la llegada — nada de confeti. `failed`: la onda-gas se congela en `--danger` al 40 %, mensaje de la tabla de errores + `job_id` copiable.

### 5.3 Skeletons

Biblioteca y detalle usan skeletons con la silueta real del contenido (tarjeta con rectángulo de onda, no cajas genéricas), pulso de opacidad 1,2 s (estático con reduced-motion). Regla: skeleton solo si la carga estimada > 200 ms; nunca skeleton + spinner a la vez.

### 5.4 Toasts

Esquina inferior derecha, **encima del reproductor**, máx. 3 apilados, 5 s con pausa en hover, cierre manual siempre disponible. Éxito (borde `--accent`), aviso (`--warning`), error (`--danger`) — los errores de generación **no** van en toast (viven en la tarjeta, §4.1); los toasts son para acciones puntuales: enlace copiado, descarga lista, cuota editada. `role="status"` (aria-live polite) salvo errores (`role="alert"`).

### 5.5 Atajos de teclado

| Tecla | Acción |
|---|---|
| `Espacio` | Play/pausa global (salvo foco en input/textarea) |
| `←` / `→` | Seek −5 s / +5 s en la pista activa |
| `Shift + ←/→` | Pista anterior / siguiente de la cola |
| `↑` / `↓` (foco en reproductor) | Volumen ±5 % |
| `M` | Mute |
| `V` | Alternar variante A/B del lote activo |
| `C` | Ir a Crear · `B` Ir a Biblioteca |
| `?` | Hoja de atajos (modal) |

Los atajos se documentan en el modal `?` y se anuncian en los tooltips de los controles.

---

## 6. Componentes

### 6.1 Librería base: shadcn/ui (sobre Radix UI)

**Elección: shadcn/ui.** Justificación frente a Radix "a pelo": shadcn/ui **es** Radix debajo (misma accesibilidad por defecto: foco gestionado, ARIA correcto, navegación por teclado — exactamente lo que D-25 exige para no pagar el retrofit de WCAG), pero entrega los componentes como **código copiado al repo**, estilizado con Tailwind y las variables CSS de §2.1 — sin dependencia de versión de una librería de estilos, con control total para el tema oscuro/claro por tokens. Con Radix solo, habría que escribir toda la capa visual desde cero sin ganar accesibilidad adicional. Riesgo aceptado: los componentes copiados se mantienen en el repo (son ~15 ficheros, asumible).

**Del catálogo shadcn/ui:** Button, Input, Textarea, Select, RadioGroup, Checkbox, Switch, Slider, Tabs, Dialog, DropdownMenu, Popover, Tooltip, Toast (sonner), Badge, Skeleton, Table (admin), Command (búsqueda de biblioteca).

### 6.2 Componentes custom

| Componente | Base | Decisión y motivo |
|---|---|---|
| `Waveform` | **wavesurfer.js** (F1) | Recomendado sobre canvas propio para F1: seek, zoom, regiones (plugin Regions ya preparado para el editor de C-07/F3) y render desde **peaks precomputados** (el backend genera el JSON de picos en el post-proceso T-45; el cliente nunca decodifica el FLAC entero). Se encapsula en un wrapper propio (`<Waveform peaks={} />`) para poder sustituir la librería sin tocar pantallas. Canvas propio queda como plan B si el bundle o el rendimiento multipista de F2 lo exigen — el wrapper lo hace barato |
| `GenerativeViz` | canvas 2D propio | La firma de §3. Sin librería: son ~150 líneas (simplex-noise como única dependencia). API: `<GenerativeViz progress={0..1} stage={...} peaks={peaks|null} reducedMotion />` |
| `LyricsEditor` (T-46) | textarea + capa espejo | Textarea controlada con `<div aria-hidden>` espejo para el resaltado de etiquetas. **No** CodeMirror/Lexical: una letra de canción no justifica un editor de código (peso, accesibilidad más difícil, i18n del editor). El parser de etiquetas se comparte con la validación de la API (criterio T-46) |
| `GenerationCard` (T-48) | compone GenerativeViz + stepper | Estados: la máquina de T-15 + `error(tipo)` |
| `ProvenancePanel` | propio | Certificado de §4.3; recibe el manifiesto v1 y el veredicto del verificador |
| `PersistentPlayer` / `MultitrackBase` (T-18) | propio + `<audio>`/Web Audio | F1: elemento `<audio>` (streaming con URL firmada interna). `MultitrackBase` deja la interfaz (transporte compartido, pistas registrables) para que C-06 la extienda con Web Audio API en F2 |
| `QuotaMeter`, `SpendGauge`, `KillSwitch` | propio (admin) | Barras de progreso con umbrales 50/80 % marcados |
| `StatusPill` | Badge extendido | Estados de trabajo con color semántico + icono, nunca solo color (accesibilidad) |

---

## 7. Accesibilidad e i18n

- **Contraste AA:** garantizado por construcción con los pares de §2.1 (ratios anotados). Prohibido introducir un par nuevo sin verificarlo. Los estados no dependen solo del color (icono + texto en StatusPill, subrayado en errores de validación).
- **Foco visible:** anillo de 2 px en `--accent` con `outline-offset: 2px` sobre cualquier fondo (`:focus-visible`, nunca `outline: none` sin sustituto).
- **Reproductor por teclado (D-25):** todos los controles alcanzables por Tab en orden lógico; la onda es un `role="slider"` con `aria-valuenow` (posición), operable con flechas; atajos de §5.5. Es una de las dos piezas que la spec señala como imposibles de retrofitear — se construye accesible desde T-18, no se audita después.
- **SSE y estados dinámicos:** los cambios de etapa de generación se anuncian en un `aria-live="polite"` único por página (no uno por tarjeta, para no ametrallar al lector de pantalla).
- **`prefers-reduced-motion`:** §2.6 y §3.4.
- **i18n (D-25, T-21):** `next-intl` desde el primer componente; **ninguna cadena hardcodeada** (criterio de aceptación de C-13), incluidos los mensajes de la tabla de errores, los estados del stepper y los tooltips de fase. Castellano como único locale de F1 (`es`), estructura de claves preparada para `ca`/`en` (I-19). Fechas y números con `Intl` (`es-ES`), coste en formato `0,04 €`.
- WCAG AA completo **no** es objetivo de F1 (spec §5.3): lo anterior es la línea de «accesible por defecto» comprometida; la deuda restante (auditoría formal, textos alternativos exhaustivos) queda registrada para Fase 2.

## 8. Qué NO hacer

1. **No clonar la identidad de Suno** (D-12b): ni su paleta morada/rosa, ni sus gradientes, ni su iconografía, ni sus textos. Se deriva disposición y flujo, se viste con lo definido aquí.
2. **No gradientes arcoíris de "IA"** ni brillos aurora: un acento, dos semánticos, y el color reservado a significado.
3. **No glassmorphism gratuito**: nada de `backdrop-blur` decorativo; la elevación es capa + borde (§2.5).
4. **No animaciones que tapen el estado real**: nada de barras de progreso que avanzan solas, spinners infinitos sin datos, ni esperas maquilladas — el cold start se dice con minutos (§3.3).
5. **No layout que baila**: las pistas nuevas no empujan con animación, las cifras no hacen odómetro.
6. **No modales para el flujo principal**: crear, generar y escuchar ocurren en la página; el modal se reserva para confirmaciones destructivas (kill switch) y la hoja de atajos.
7. **No esconder la procedencia**: el certificado nunca se degrada a acordeón colapsado ni a enlace de pie de página.
8. **No texto en `--text-muted` sobre `--bg-2/--bg-3`** (rompe AA), ni acento como color de texto largo.

## 9. Mapa pantalla/componente → tareas del ledger

| Pieza de este documento | Sección | Tarea(s) en `tasks.md` | Notas |
|---|---|---|---|
| Sistema de diseño (tokens, tema, tipografía) | §2 | T-10 (setup web del monorepo) + primera tarea de estilo de T-17/T-46 | Los tokens entran como capa CSS global en `apps/web` |
| Visualización generativa + estados de espera | §3 | T-48 (tarjeta de resultado) con datos de T-16 (SSE) | El % y las etapas son el contrato de T-15/T-16; sin evento no hay avance visual |
| Pantalla Crear — editor de letra | §4.1 | **T-46** | Parser de etiquetas compartido con API |
| Pantalla Crear — formulario (estilo, voz, duración, destino, declaración) | §4.1 | **T-47** (+ T-43 gate de letra, backend) | Destino → loudness (T-20/T-45); coste/cola del botón ← T-24/T-42 |
| Pantalla Crear — panel de resultados, pares A/B, errores | §4.1 | **T-48** | Tabla de errores de spec §6 mapeada a estados de tarjeta |
| Biblioteca (grid/lista, filtros, estados) | §4.2 | T-17 | Pares A/B agrupados por linaje (T-12) |
| Detalle de pista + certificado de procedencia | §4.3 | T-21 (vista de pista + compartir) | Manifiesto de T-27, veredicto de cadena de T-28; exportar JSON |
| Acciones futuras deshabilitadas (extender/stems/PDF) | §4.3 | — (sin tarea: C-06/C-07/C-10b, Fase 2/3) | Solo tooltip de fase; cero lógica |
| Reproductor persistente + cola | §4.4 | T-18 | Incluye `MultitrackBase` para C-06 |
| Admin (cuotas, gasto, kill switch, calendario pod) | §4.5 | UI sobre T-41 (tope/kill switch) y §12.1 spec (UI de cuotas); roles de T-52 | La UI de cuotas la exige spec §12.1; si no cabe en T-41, abrir tarea nueva en el ledger |
| Login + 2FA | §4.6 | T-50 (vías de acceso), T-51 (TOTP y respaldo) | Pantalla propia; errores concretos |
| Preview de audio en hover, toasts, skeletons, atajos | §5 | Transversal a T-17, T-18, T-48 | El opt-out de preview vive en preferencias de usuario |
| shadcn/ui + componentes custom | §6 | T-10 (instalación), consumidos por T-17/T-18/T-46/T-47/T-48 | Wrapper `Waveform` obligatorio (sustituibilidad) |
| i18n `next-intl` sin cadenas hardcodeadas | §7 | T-21 | Criterio de aceptación de C-13 |
| Mezclador de stems | §4.7a | **Sin tarea en el ledger actual** — C-06, Fase 2 | T-18 deja la base (`MultitrackBase`) |
| Editor de secciones sobre la onda | §4.7b | **Sin tarea en el ledger actual** — C-07, Fase 3 | El wrapper `Waveform` (plugin Regions) deja la puerta abierta |

---

## Changelog

| Fecha | Cambio | Autor |
|---|---|---|
| 2026-08-18 | Creación del documento de diseño de UI: concepto «estudio nocturno», sistema de tokens con contraste AA verificado, acento «verde traza» (candidatos A/B/C), tipografías Inter + Bricolage Grotesque + JetBrains Mono, firma visual de generación (condensación de onda por progreso SSE con mensajes honestos de cold start), 6 pantallas de F1 + 2 anticipadas de F2/F3, microinteracciones, inventario de componentes (shadcn/ui + wavesurfer.js encapsulado) y mapa a las tareas T-10…T-52 del ledger. Estado `propuesta`. | Claude (a petición de 7590335+daycry@users.noreply.github.com) |
