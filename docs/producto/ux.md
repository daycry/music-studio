---
documento: ux
titulo: Diseño de interfaz
estado: vigente
fecha: 2026-09-28
actualizado: 2026-09-28
origen: condensado y adaptado de archive/…/ui-design.md (2026-08-18)
---

# Diseño de interfaz

**Regla de oro:** de Suno se toma el **modelo de interacción** — panel de creación a la izquierda, feed/biblioteca en el centro, reproductor fijo abajo, generación en **pares de variantes** — y nada más. Logo, paleta, tipografía, iconos y textos son propios. Si algo se reconocería como «de Suno», no entra.

## 1. Concepto: «estudio nocturno»

Herramienta de trabajo de audio, no web de marketing. Tema oscuro cálido por defecto (fatiga en sesiones largas, protagonismo de la forma de onda), tema claro «papel cálido» disponible. **El audio es el protagonista visual:** la forma de onda es navegación (seek), estado (progreso) y contenido (comparar A/B).

## 2. Sistema de diseño

**Tokens (tema oscuro):**

```css
:root[data-theme="dark"] {
  --bg-0:#0E0C0A; --bg-1:#171412; --bg-2:#211D19; --bg-3:#2B2620;
  --border-subtle:#2E2823; --border-strong:#453D34;
  --text-primary:#F2EDE7; --text-secondary:#A89F94; --text-muted:#7A7166;
  --accent:#34D399; --accent-hover:#5CE0AE; --on-accent:#0E0C0A; --accent-muted:rgba(52,211,153,.14);
  --danger:#F87171; --warning:#E8C547; --info:#7FB8D8;
  --wave-idle:#4A423A; --wave-played:var(--accent); --wave-generating:#6E675E;
}
:root[data-theme="light"] {
  --bg-0:#FAF7F2; --bg-1:#F2EDE5; --bg-2:#EAE3D9; --bg-3:#FFFFFF;
  --border-subtle:#DDD5C9; --border-strong:#BFB5A6;
  --text-primary:#26211B; --text-secondary:#5C544A; --text-muted:#8A8072;
  --accent:#0E7C5B; --accent-hover:#0A6449; --on-accent:#FAF7F2;
  --danger:#B3261E; --warning:#8A6D00; --info:#1D6E96;
  --wave-idle:#C9BFB1; --wave-played:var(--accent);
}
```

- **Acento único «verde traza»** (el verde de los vúmetros: «hay señal»). Solo para audio activo, progreso real y la acción principal. Prohibidos morados/rosas (identidad de Suno) y gradientes «IA».
- Contraste **AA** verificado en todo par texto/fondo; `--text-muted` nunca para texto informativo sobre `--bg-2`+.
- **Tipografía:** Inter (UI, cifras tabulares), Bricolage Grotesque (titulares), JetBrains Mono (hashes, semillas, IDs).
- **Espaciado** base 4 px; radios 6/10/16 px; elevación con capa + borde (una sola sombra, para flotantes).
- **Motion:** 120/200/320 ms; se anima opacidad, transform y color, nunca el layout ni las cifras. `prefers-reduced-motion` desactiva todo.

## 3. Layout global

```
┌────────┬──────────────────────────────────────────┬──────────┐
│ Nav    │  Contenido (Crear · Biblioteca · Detalle) │ Panel    │
│ 64 px  │                                          │ contexto │
├────────┴──────────────────────────────────────────┴──────────┤
│ ▶ Reproductor persistente (72 px)                            │
└──────────────────────────────────────────────────────────────┘
```

Nav: **Crear · Canciones · Personajes · Presets · Sistema** (+ Ajustes: proveedores externos opcionales). Por debajo de 1024 px la nav pasa a barra inferior.

## 4. Pantallas

### 4.1 Crear

Dos modos con un conmutador en la cabecera del panel:

- **Simple:** un campo «Describe la canción» (+ idioma, instrumental sí/no, duración). El asistente de letras escribe la letra y el prompt de estilo; ambos se muestran editables antes de generar (nunca se genera a ciegas).
- **Personalizado:** editor de letra + estilo + opciones.

```
┌──────── Panel de creación (400 px) ─────────┬──── Feed ───────────────────┐
│ [Simple | Personalizado]    [Instrumental ⊘] │ ┌ Par de variantes ───────┐ │
│ LETRA                         [✨ Asistente] │ │ ∿∿∿ condensándose  A    │ │
│ ┌──────────────────────────────────────────┐ │ │ ∿∿∿ condensándose  B    │ │
│ │ [verse]                                   │ │ └─────────────────────────┘ │
│ │ Luz de neón sobre el asfalto…             │ │ ┌ Generación previa ──────┐ │
│ │ [chorus] …                                │ │ │ ▶ ∿∿∿∿∿  A ★           │ │
│ └──────────────────────────────────────────┘ │ │ ▶ ∿∿∿∿∿  B             │ │
│ [+verse] [+chorus] [+bridge] [+intro] [+outro]│ └─────────────────────────┘ │
│ Autoría: (•) Propia ( ) Asistente ( ) Dominio │                             │
│          público ( ) Con permiso              │                             │
│ ESTILO  [texto libre…………………]  [Preset ▾]     │                             │
│ [pop] [cinematic] [lo-fi] [+ chips]           │                             │
│ Excluir: [texto…]                             │                             │
│ ▸ Avanzado: duración · BPM · tonalidad ·      │                             │
│   idioma · semilla · variantes (1–4) ·        │                             │
│   modelo · fuerza del estilo                  │                             │
│ ┌──────────────────────────────────────────┐ │                             │
│ │ ⚡ Crear  · ~40 s · cola: 0 · GPU ● lista │ │                             │
│ └──────────────────────────────────────────┘ │                             │
└──────────────────────────────────────────────┴─────────────────────────────┘
```

- **Editor de letra:** textarea con capa espejo que resalta `[verse]`, `[chorus]`, `[bridge]`… como píldoras sin dejar de ser texto plano. Validación en vivo de etiquetas; contador de líneas y sílabas aproximadas por sección.
- **Autoría de la letra:** grupo de radios siempre visible (se guarda en el manifiesto). Si la letra viene del asistente, se autoselecciona.
- **Avanzado** se pliega; solo aparecen los controles que el **modelo seleccionado** declara (capacidades del descriptor).
- **Botón Crear:** único botón en acento. Muestra tiempo estimado (medido en esta GPU), cola y estado de la GPU (● lista · ◐ cargando modelo).
- **Pares de variantes:** cada petición produce N variantes agrupadas (por defecto 2).

### 4.2 Tarjeta en generación (la firma visual)

```
┌──────────────────────────────────────────────────────────────┐
│ Título provisional · modelo@versión                           │
│ ····•·····∿∿•·····∿∿∿∿•···∿∿∿∿∿∿∿∿ ← zona aún «gas»           │
│ ● Generando — 42 %        ⏱ ~20 s restantes                  │
│ ○──────●──────○──────○                                        │
│ En cola  Modelo  Generando  Post-proceso                      │
└──────────────────────────────────────────────────────────────┘
```

Canvas 2D de 96 columnas: con el **progreso real** (SSE) cada columna pasa de ruido vibrante a barra estable de izquierda a derecha; sin progreso nuevo no avanza. Al terminar, las barras adoptan los picos reales y la visualización **se convierte** en la forma de onda. Un solo `requestAnimationFrame`, 30 fps máx., pausa fuera de viewport. La etapa «Modelo» solo aparece si hay que cargar o cambiar de modelo (mensaje honesto: «Cargando ACE-Step en la GPU — ~15 s»).

### 4.3 Canciones (biblioteca)

Grid de **canciones** con portada (o una onda generativa si no hay portada), título, estado (borrador · en curso · final), número de takes e icono de vídeo si existe. También hay vista de lista densa. Filtros: colección, estado, fecha, modelo, etiquetas y texto (título, letra, estilo). Al pasar el cursor 400 ms suena una preescucha de 10 s del **take maestro** (desactivable). Clic en ▶ reproduce sin navegar; clic en la tarjeta abre la **vista de canción**.

### 4.4 Vista de canción (el proyecto)

```
┌ Neón y asfalto · ● en curso · colección Sintonías ─────────── [⬇ Exportar ▾] ┐
│ [portada]  Artista · 3:00 · 112 BPM · La m · maestro: v3 ★★★★               │
│ [ Audio ]  [ Letra ]  [ Vídeo ]  [ Portada ]  [ Exportar ]                    │
├──────────────────────────────────────────────────────────────────────────────┤
│ ∿∿∿∿∿∿∿∿∿∿[░░ 0:58–1:24 ░░]∿∿∿∿∿∿∿∿∿∿  (take seleccionado: seek, zoom, región)│
│ ▶ 0:42 ────●──────────────── 3:00  · beats y secciones marcados sobre la onda │
│ [⤢ Extender] [◱ Regenerar sección] [↻ Variación] [♫ Cover] [≣ Stems] [✂]     │
│ ┌ Takes ─────────────────────────────┐ ┌ Árbol de versiones ──────────────┐   │
│ │ ◉ v3 · extend · ★★★★ · MAESTRO     │ │ ● v1 original                    │   │
│ │ ○ v2 · variante B · ★★★            │ │ ├─ v2 variante B                 │   │
│ │ ○ v1 · original · ★★               │ │ └─ v3 extend ← maestro           │   │
│ │ [comparar A/B]                     │ └──────────────────────────────────┘   │
│ └────────────────────────────────────┘                                        │
│ ┌ Procedencia (take seleccionado) ─────────────────────────────────────────┐  │
│ │ ace-step@1.5 · MIT · sha256 3fa5…d947 · letra v2 (propia) · seed 8492…  │  │
│ └──────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
```

- **Audio:**
  - Muestra todos los takes de la canción con su valoración, su etiqueta y el árbol de versiones.
  - «Marcar como maestro» elige la versión que usan el vídeo, la portada y las exportaciones.
  - Las operaciones de edición se aplican sobre el take seleccionado y crean takes hijos.
  - «+ Generar» abre el panel de creación con la letra y el estilo de la canción ya cargados.
- **Regenerar sección:** se arrastra sobre la onda para seleccionar `[t0, t1]`, con imán a los límites de sección y a los beats. Hay preescucha en bucle y, opcionalmente, letra o estilo nuevos para ese tramo.
- **Letra:** editor con historial de versiones, diferencias entre versiones y qué takes cantaron cada una. Desde M3, vista karaoke sincronizada.
- **Vídeo:** los proyectos de vídeo de la canción (§4.5) y «+ Nuevo vídeo».
- **Portada:** opciones generadas desde el estilo y la letra, edición con referencia o subida manual. Se marca una como portada principal.
- **Exportar:** audio por destino, stems, vídeo renderizado, letra (`.txt` / `.lrc` / `.srt`) y la **canción completa como zip**.

### 4.5 Editor de vídeo

```
┌ Vídeo · «Neón y asfalto» · 16:9 · N1+N2 · estilo: cine nocturno ──── [Render ▾] ┐
│ ┌ Visor ──────────────────────────────┐ ┌ Plano 07 · estribillo · 0:58–1:02 ───┐ │
│ │                                      │ │ tipo: [i2v ▾]  personaje: Lía        │ │
│ │   (preview del plano / montaje)      │ │ «luz de neón sobre el asfalto…»       │ │
│ │                                      │ │ prompt: plano medio, lluvia, neón…    │ │
│ └──────────────────────────────────────┘ │ cámara: travelling lateral           │ │
│  ▶ 0:58 ─────●──────────── 3:00          │ [↻ imagen clave] [↻ clip] [9:16 ⌖]  │ │
│                                          └───────────────────────────────────────┘ │
│ SECCIONES │ intro │  verso 1  │ estribillo │  verso 2  │ estribillo │ puente │…   │
│ PLANOS    │▣01│▣02│▣03│▣04│▣05│▦06│▶07│▶08│▣09│▣10│♪11│▶12│▶13│ …                │
│ LETRA     │     luz de neón   │ sobre el asfalto │ …                                │
│ AUDIO     │∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿  (beats como marcas verticales)    │
│ ▣ imagen+movimiento · ▶ clip generativo · ♪ cantante · ▦ letra · estado ✓ ◐ ○ ⚠  │
└────────────────────────────────────────────────────────────────────────────────────┘
```

- **Asistente de nuevo vídeo:**
  - Se eligen formato (16:9 · 9:16 · 1:1), estilo visual, tratamiento en texto libre, personajes de la biblioteca y nivel: N0 vídeo con letra · N1 guion gráfico · N2 con planos protagonistas · N3 todo generativo.
  - Antes de lanzar muestra la **estimación de tiempo en esta GPU**.
  - El resultado es un guion de planos editable; todavía no se genera nada.
- **Pistas del timeline:** secciones, planos, letra y audio, todas con imán a beats y downbeats. Se pueden arrastrar los bordes de un plano, reordenar, dividir, fusionar o cambiar el tipo.
- **Estado por plano** (✓ listo · ◐ generando · ○ pendiente · ⚠ error):
  - Cada plano se puede generar, regenerar o subir de nivel por separado.
  - «Generar pendientes» encola solo lo que falta.
  - Los planos pesados se pueden marcar como **nocturnos**.
- **Inspector del plano:** tipo, personajes, fragmento de letra, prompt, cámara, semilla, imagen clave (con historial), clip, **punto de interés para el reencuadre 9:16** y, si está activado, proveedor externo del plano con su coste.
- **Subtítulos:** letra sincronizada con estilos predefinidos (karaoke, línea a línea, palabra resaltada), posición y tipografía.
- **Render:** completo en 16:9 y/o 9:16, clips cortos del estribillo, subtítulos quemados o `.srt` y reescalado opcional.
- **Aviso:** «El take maestro ha cambiado desde que se hizo este vídeo — [Reanalizar y reajustar]».

### 4.6 Personajes

Biblioteca global: un personaje se crea una vez y se reutiliza en los vídeos de cualquier canción, con la misma cara y el mismo aspecto.

```
┌ Nuevo personaje ──────────────────────────────────────────────┐
│ Nombre [Lía]   Tipo (•) Persona real ( ) Ficticio ( ) Animal  │
│ ┌ Fotos de referencia ─────────────────────────────┐          │
│ │ [foto1] [foto2] [foto3]  [+ subir]  (1–10 fotos) │          │
│ └──────────────────────────────────────────────────┘          │
│ Consentimiento: (•) Soy yo ( ) Tengo su consentimiento        │
│ Descripción: pelo corto castaño, chaqueta amarilla…           │
│ [Generar hoja de personaje]  → frente · perfil · cuerpo ·     │
│                                expresiones (revisar/regenerar)│
│ ▸ Avanzado: entrenar LoRA con 10–20 fotos (M5)                │
└───────────────────────────────────────────────────────────────┘
```

- Se crea **desde fotos subidas** (lo habitual para que el protagonista seas tú o alguien concreto) o **desde una descripción** (personaje inventado).
- La **hoja de personaje** son varias vistas generadas a partir de las fotos; es lo que se usa como referencia en cada plano. Se puede revisar y regenerar antes de usarla.
- En el editor de vídeo se asigna un personaje a los planos; los planos de cantante usan el personaje marcado como **intérprete**.
- Persona real: obligatorio marcar «soy yo» o «tengo su consentimiento»; queda en el manifiesto de cada plano.

### 4.7 Stems

Mezclador: una fila por stem con mute/solo, fader, onda compartiendo eje temporal; transporte único sincronizado; exportar todos o uno.

### 4.8 Presets

Guardar combinaciones de estilo + parámetros (+ referencia de timbre y estilo visual cuando existan) con nombre; aplicables desde Crear en un clic. Equivale a las «personas» de Suno, pero sin clonar voces reales.

### 4.9 Sistema

GPU, VRAM usada/libre, RAM, modelo cargado, cola (con trabajos nocturnos), modelos instalados (con licencia, tamaño, hash verificado ✓), cola, espacio en disco, versión del engine. Botón «descargar modelo de la VRAM».

### 4.10 Reproductor persistente

`[mini-onda] Título — A  ⏮ ▶ ⏭  0:42 ──●── 3:00  🔊  ≡ cola`. Persiste al navegar. `⏭` desde una variante salta primero a su pareja (A/B rápido). Cola reordenable.

## 5. Microinteracciones y atajos

- Toasts abajo a la derecha (máx. 3); **los errores de generación viven en la tarjeta**, con el `job_id` y acción de reintento, nunca en un toast.
- Skeletons con la silueta real del contenido solo si la carga > 200 ms.

| Tecla | Acción |
|---|---|
| `Espacio` | Play/pausa (fuera de inputs) |
| `←/→` | ±5 s · `Shift+←/→` pista anterior/siguiente |
| `V` | Alternar variante A/B |
| `L` | Bucle de la región seleccionada |
| `C` / `B` | Ir a Crear / Canciones |
| `Ctrl+Enter` | Crear (desde el panel) |
| `?` | Hoja de atajos |

## 6. Componentes

- **shadcn/ui** (Radix debajo) + Tailwind con los tokens de §2.
- **`Waveform`**: wrapper propio sobre **wavesurfer.js** (plugin Regions para seleccionar tramos), alimentado con `peaks.json`; nunca decodifica el audio entero en el navegador.
- **`GenerativeViz`**: canvas propio (~150 líneas + `simplex-noise`).
- **`LyricsEditor`**: textarea + capa espejo; el parser de etiquetas es el mismo que valida el server (se genera desde `packages/contracts`).
- **`LineageTree`**, **`StemMixer`** (Web Audio API), **`ProvenancePanel`**.
- **`Timeline`** (editor de vídeo): pistas de secciones, planos, letra y audio con imán al beat; canvas; vista previa con `<video>` por plano. El render final es siempre ffmpeg en el server.

## 7. Accesibilidad e idioma

- Foco visible (anillo de 2 px en acento); la onda es `role="slider"` operable con flechas; cambios de estado anunciados en un único `aria-live="polite"`.
- UI en **castellano**, con `next-intl` y sin cadenas hardcodeadas (añadir inglés es traducir, no refactorizar).

## 8. Qué no hacer

1. No clonar la identidad de Suno.
2. No barras de progreso que avanzan solas ni esperas maquilladas.
3. No modales en el flujo principal (solo confirmaciones destructivas y la hoja de atajos).
4. No layout que baila al llegar pistas nuevas.
5. No esconder la procedencia en un acordeón cerrado.
