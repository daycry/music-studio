---
documento: evaluacion-escucha
titulo: Evaluación de escucha — elegir modelo y validar calidad
estado: vigente
fecha: 2026-09-28
actualizado: 2026-09-28
origen: simplificado de archive/…/gates/g1-protocolo.md
---

# Evaluación de escucha

Sirve para dos cosas: **(1) elegir entre modelos candidatos** en M0 y **(2) comprobar que la calidad es usable** antes de construir la aplicación encima. Se repite (misma batería, mismos briefs) cada vez que se añade o actualiza un modelo, para detectar regresiones.

## 1. Material

- **10 briefs fijos** (§4), con letra propia (o dominio público). Nunca letras de terceros protegidas.
- Por brief y modelo: **3 tomas** con semillas distintas; se elige la mejor **antes** de la sesión de puntuación (≥ 24 h antes, o al menos en otra sesión), sin puntuar.
- Mismo prompt de estilo literal para todos los modelos (derivado del brief, sin retocarlo por modelo).
- Referencia opcional: una pista de una librería de música de producción para el mismo brief.

## 2. Procedimiento

1. Un script genera todas las tomas, iguala el loudness **con ganancia lineal** a −16 LUFS / −1 dBTP y renombra los ficheros con un código aleatorio (el mapa código→modelo se guarda cifrado o fuera de vista hasta terminar).
2. Escucha con el mismo sistema (auriculares/monitores declarados) y el mismo volumen.
3. Por pista: una pasada sin puntuar, otra puntuando D1→D5 sin volver atrás.
4. Solo al terminar se abre el mapa y se calculan resultados.

## 3. Rúbrica (1–5, ante la duda se puntúa a la baja)

| Dim. | Qué se juzga | 3 = | 5 = |
|---|---|---|---|
| **D1 Adecuación al brief** | Género, tempo, instrumentación, idioma, duración | Cumple género y carácter; falla un eje | Cumple todo, incluido el matiz y el uso final |
| **D2 Mezcla y artefactos** | Timbre metálico, aliasing, voz desintegrada, balance | Artefactos solo con atención o en 1–2 puntos | La mezcla no delata el origen sintético |
| **D3 Estructura** | Secciones, transiciones, final | Reconocible, con una transición floja | Desarrollo, contraste y resolución con intención |
| **D4 Letra cantada** | Inteligibilidad y prosodia (sin leer la letra) | Se entiende casi todo a la primera | 100 % inteligible y con acento natural |
| **D5 ¿La usarías?** | Decisión práctica | Solo tras retoque real | Tal cual, sin tocar |

Todo 5 exige una frase de por qué no es un 4. Todo D5 ≥ 4 exige nombrar el uso concreto.

**Métricas automáticas (complementan, no sustituyen):**

- **WER** de la letra con el transcriptor elegido en [`../arquitectura/modelos.md`](../arquitectura/modelos.md), sobre la letra sin etiquetas. Antes, medir el **suelo del transcriptor** con 2–3 grabaciones cantadas reales (para saber qué parte del WER es culpa del ASR).
- **Similitud audio-texto (CLAP)** entre la pista y el prompt de estilo.
- **Estética automática** (si hay modelo disponible con licencia adecuada).

## 4. Los 10 briefs

| ID | Uso | Género / carácter | BPM | Instrumentación | Voz / idioma | Duración |
|---|---|---|---|---|---|---|
| B-01 | Cabecera de vídeo-ensayo | Indie-rock luminoso, urgente | 112 | Batería, bajo, 2 guitarras con chorus | Masculina, doblada en estribillo · **es** | 45 s, final resuelto |
| B-02 | Maqueta de canción | Cantautor / folk-pop melancólico | 84 | Acústica, contrabajo, escobillas, coros | Femenina cercana · **es** | 3:00, V-E-V-E-P-E |
| B-03 | Sintonía de pódcast de historia | Folk oscuro / neomedieval | 96 | Percusión de marco, zanfona, coro grave | Masculina grave · **es** | 30 s |
| B-04 | Fondo de vídeo de cocina | Bedroom pop / lo-fi | 92 | Rhodes, caja suave, bajo sintético | Femenina susurrada · **en** | 2:00 |
| B-05 | Créditos de cortometraje | Balada piano y cuerdas | 68 | Piano, cuarteto; percusión solo al final | Masculina alta, frágil · **es** | 2:30, crescendo y final que se apaga |
| B-06 | Cuña de 30 s | Pop electrónico publicitario | 124 | Synths brillantes, palmas, bajo sintético | Femenina enérgica · **es** | 30 s exactos |
| B-07 | Tema de stream de rol | Metal sinfónico ligero | 140 | Guitarras distorsionadas, doble bombo, cuerdas, coro | Masculina potente · **en** | 2:30, estribillo coreable |
| B-08 | Cuña de radio | Cumbia / latin pop | 100 | Acordeón, güira, bajo, guitarra | Femenina cálida · **es** | 40 s, groove estable |
| B-09 | Montaje de fotos | Soul / R&B lento | 76 | Hammond, batería, bajo, vientos | Femenina con melismas · **en** | 2:45 |
| B-10 | Sintonía de canal tech | Synthwave 80s | 110 | Arpegios analógicos, batería 80s, pads | Masculina con vocoder solo en estribillo · **en** | 1:30 |

6 en castellano / 4 en inglés, de 30 s a 3:00, 10 géneros distintos. Las letras se guardan en `eval/briefs/B-XX.txt` (texto plano, sin etiquetas para el WER; con etiquetas para el modelo).

## 5. Decisión

| Resultado | Criterio |
|---|---|
| **Modelo aprobado** | D5 ≥ 4 en **≥ 7 de 10** briefs · ninguna dimensión con media < 3,0 · WER medio ≤ 15 % (peor caso ≤ 25 %) descontado el suelo del transcriptor |
| **Elección entre candidatos** | Gana el de más briefs con D5 ≥ 4; empate → mayor media D4 (letra) → menor tiempo de generación en la 5070 |
| **Replantear** | Ningún candidato aprobado: probar otra configuración (checkpoint base/sft, planificador LM, más pasos) una vez; si sigue sin aprobar, revisar el catálogo de modelos antes de construir la app |

Los umbrales se fijan **antes** de escuchar y no se mueven a la vista de los resultados.

## 6. Custodia

Carpeta `eval/` en la raíz del proyecto (git-ignored salvo `eval/briefs/` y `eval/results/*.md`): tomas, hojas de puntuación, mapa del ciego y el informe de resultados. Las pistas de evaluación no se usan en ningún trabajo real.
