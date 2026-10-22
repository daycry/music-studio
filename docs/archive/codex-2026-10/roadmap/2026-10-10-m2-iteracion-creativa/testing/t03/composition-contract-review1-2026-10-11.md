# Revisión documental 1 — contrato de composición M2/T03

ROOT 2026-10-11T14:09:43.120534+00:00: A/B frescas, 0Critical/3Important/1Minor. C/Dauto false, siete documentos dentro del alcance. O1 elegida bajo delegación; contrato y ADR continúan como propuesta, sin producto ni QA de T03.

| Gap | Grado | Veredicto | Corrección requerida |
|---|---|---|---|
| A01 | Important | confirmado | Extend region descarta sufijo original; no aplicar resumen de repaint. |
| A02 | Minor | confirmado | Consolidar opciones en una tabla comparativa. |
| B01 | Important | confirmado | Separar procedencia nominal convertida de span de render no vacío. |
| B02 | Important | confirmado | Región global del padre y grid local engine region tienen bounds distintos. |

ROOT verifica26fuentes congeladas y24guardas canónicas. Sus sondas independientes de captura T02 aceptan B01/B02; aritmética reproduce cola nominal[160,160) frente render[80,81), salida101, y repaint global[6,8] frente engine local2s, salida100. Los frames convertidos son supuestos explícitos de los ejemplos, no mediciones reales. Extend correcto110 frente resumen erróneo140. Respuestas de auditores conservadas, sin rebate/deuda. FIX1 privado autorizado en tres documentos, revisión2 y QA pendientes; T03/M2 siguen abiertos.

## Lente A

Lente A · intento 1 de 3 · diff `87548c755e6937d34644309b58fbbb76c1448495...HEAD` ∪ cambios preparados (7 documentos).

Revisión completa por bloques sobre snapshot readonly. Las rutas citadas pertenecen a `.cache/dev-cycle/m2/creative-composition-t03-contract-review1-20261011/snapshot/`. **Resultado: 0 Critical, 1 Important, 1 Minor.** El contrato O1 mantiene sus políticas ratificadas; el Important corresponde al resumen arquitectónico.

| Criterio (T-03 / objetivo) | ✓/✗/no verificable | Evidencia |
|---|---|---|
| Alcance conforme al plan | ✓ | `tasks.md:137`; recibo de preparación: 7 documentos dentro, 0 fuera, 0 avisos/exclusiones |
| T-01/T-02 completadas con verificación registrada | ✓ | `tasks.md:93` y `:125`: acta contractual y QA independiente `183 passed, exit0`; no se reabren unidades aprobadas |
| Estado T-03 y evidencia honesta | ✓ | `tasks.md:130`, `:144`: en-progreso, criterios abiertos; diseño `:33`, `:226`, `:265`: propuesta y controles documentales sin atribuir ejecución |
| Constitución explícita | ✓ | Constitución `:11`, `:18`, `:23`, `:33`, `:37`, `:43`; diseño `:37`, `:82`, `:146`, `:170`, `:203`: padres intactos, server/CPU, lectores separados, estados y autoridades preservados |
| E2/generated | ✓ — n/a | Diff sólo `docs/**`; no `commands/`, `agents/`, `hooks/`, API ni schemas ejecutables |
| E3/documentos que describen | ✗ | `iteracion-creativa.md:152` añade sufijo genéricamente a region; contradice extend del diseño `:181` y C06 `:235` |
| Enlaces, frontmatter e índices | ✓ | Comprobación independiente: 18 enlaces Markdown añadidos y 4 referencias de fichero frontmatter existentes; ADR propuesta/diseño borrador y O1 coherentes |
| Interfaz T-02 y seams T-04/T-07/T-08 | ✓ | `recipes.py:563`, `:607`, `:618`, `:1268`; diseño `:86`, `:94`, `:102`, `:170`, `:278`: campos existentes, raíces originales, proyección convert y ejecución posteriores |
| AC01 / CA-13/14: intervalos y fade | ✓ documental | Diseño `:118`, `:176`, `:246`; C01/C02 verificados aritméticamente |
| AC02: half-up único | ✓ documental | `:110–116`, `:247`; reproducción racional: `.05@10→1`, `.15@10→2` |
| AC03: colapso/singleton | ✓ documental | `:118`, `:248`; rechazo explícito y rampas ≥2 frames |
| AC04: tipos exactos/no finitos | ✓ documental | `:84`, `:88`, `:92`, `:249` |
| AC05: límites/overflow | ✓ documental | `:88`, `:112`, `:250`; límites sin materializar audio |
| AC06: facts/bindings/duración | ✓ documental | `:92–96`, `:251`; duración medida exacta, receta stale rechazada |
| AC07: extremo N y bounds | ✓ documental | `:114`, `:252`; anclaje medido sin clamp |
| AC08 / CA-15: dos padres/roles/root | ✓ documental | `:94`, `:120`, `:152`, `:253`; C11 mínimo de raíces originales |
| AC09: convert explícito | ✓ documental | `:102–106`, `:166`, `:254`; coordenadas nativas y destino target conservados |
| AC10: frames convertidos medidos | ✓ documental | `:104–106`, `:255`; C10 usa 81 aportados, salida161; no estima80 |
| AC11 / CA-11: repaint region/full | ✓ documental | `:179–180`, `:256`; C04/C05 salida105, construcción distinta y sufijo desplazado |
| AC12 / CA-09/11: extend/full único | ✓ documental | `:181–185`, `:257`; C06/C07 salida110; full consume engine una vez |
| AC13: extremos/keeps vacíos | ✓ documental | `:118`, `:185`, `:258`; C08/C09 comprobados |
| AC14: keeps full sin fidelidad fingida | ✓ documental | `:168`, `:187`, `:259`; gate PCM posterior explícito |
| AC15: inmutabilidad receta/plan | ✓ documental | `:39`, `:84`, `:201`, `:260`; sin modificar contrato T-02 |
| AC16: codec/dominos/replay | ✓ documental | `:146`, `:203–205`, `:261`; no exige desigualdad de SHA como custodia |
| AC17 / CA-14: pureza CPU | ✓ documental | `:37`, `:262`; I/O/render/SQL/GPU fuera de T-03 |
| AC18: errores y lectores históricos | ✓ documental | `:203`, `:207–222`, `:263` |
| Cumplimiento ejecutado de CA-09/11/13/14/15 y verificación T-03 | no verificable — pendiente declarado | Producto/test focal aún no implementados; no se ejecutan para aprobar esta propuesta |
| Docs-style regla 4 | ✗ Minor | Regla citada en `docs-style.md:18`; tres tablas opciones de una fila (diseño :47,:55,:63) |

Gaps:

| # | Grado | Gap | Tarea | fichero:línea | Escenario concreto |
|---|---|---|---|---|---|
| A01 | Important | El resumen de arquitectura atribuye sufijo a toda salida region, contradiciendo extend | T-03 / CA-09 / E3 | `docs/arquitectura/iteracion-creativa.md:152` | Padre100, punto70, engine40: extend normativo produce110 y descarta sufijo30; seguir prefijo+región+sufijo produce140. ROOT confirmó que la frase es general y no presentó rebate. |
| A02 | Minor | Comparación O1/O2/O3 fragmentada en tres tablas de una fila; incumple docs-style regla4 | T-03 / prosa | `docs/roadmap/2026-10-10-m2-iteracion-creativa/composition-contract-design.md:47` | Las mismas cuatro dimensiones se repiten en tres tablas separadas (`:47`, `:55`, `:63`), señal explícita de la regla4 (`docs-style.md:18`). |

Lo ejecutado:

- Lectura completa del diff y fuentes contractuales; `git diff --stat HEAD` → **7 documentos, 402 inserciones, 1 eliminación**.
- Python gestionado, auditoría readonly → **26 SHA intactos; 18 enlaces; 4 referencias frontmatter; 11 controles aritméticos; 18 AC; errors=[]; exit0**.
- Contraejemplo documental → **contract110 frames; generic prefix+engine+suffix140 frames; exit0**.
- `ledger-lint.py` → **0 incoherencias, 28 avisos preexistentes de Changelog; exit0**.
- `knowledge-find.py --tipo adr --tipo-tarea backend ...` → **0 aciertos, exit0**.
- Primera sonda de referencias confundió el identificador `design:` con una ruta; corregida para comprobar referencias `.md`, sin mutaciones.
- Sin tests de producto, cobertura, audio, E2E, GPU, Docker, red ni instalaciones. Cobertura porcentual n/a para este diff documental.

Fuera de mi lente (no reportado): ninguno. Canon, ledger y snapshot sin modificaciones.


## Lente B

Lente B · intento 1 · diff `87548c755e6937d34644309b58fbbb76c1448495...HEAD` ∪ cambios sin comitear del snapshot (7 ficheros; leído completo por secciones).

| Criterio / objetivo T-03 | ✓/✗/no verificable | Evidencia |
|---|---|---|
| Half-up, extremos, límites y rampas | ✓ contractual | `composition-contract-design.md:112–120`; sonda: ties `[1,2]`, controles interiores correctos |
| Crossfade: coordenadas nativas y convertidas representables | ✗ | B01; sonda y captura T02 aceptada |
| Repaint region con conversión y coordenadas locales engine | ✗ | B02; sonda y captura T02 aceptada |
| Full/region: fuentes únicas y duración por frames medidos | ✓ contractual | `composition-contract-design.md:174–187`; C04/C05→105, C06/C07→110 |
| Raíces originales, aristas, inmutabilidad y replay | ✓ contractual | `composition-contract-design.md:94,146,152,201–205`; `recipes.py:1053–1065,1218–1265` |
| Render, fidelidad, codec implementado y audio | no verificable | Producto T03 pendiente; controles documentales no sustituyen ejecución |

Gaps:

| # | Grado | Gap | Tarea | fichero:línea | Escenario concreto |
|---|---|---|---|---|---|
| B01 | Important | El contrato permite un sufijo convertido positivo cuya procedencia nominal nativa es un span vacío, prohibido por sus DTO. | T-03 | `docs/roadmap/2026-10-10-m2-iteracion-creativa/composition-contract-design.md:166` | C10 con `D=8s`: A100@10Hz, B160@20Hz, Bc81@10Hz. Dtarget80/Dnative160 cumplen límites. El render conserva Bc `[80,81)`→dst `[100,101)`; su src nominal B `[160,160)` queda vacío. `convert/effect=keep` exige src no-null y `FrameSpan` exige start<stop (l88), mientras la regla de composición consume ese sufijo (l178). No existe representación que satisfaga simultáneamente estas reglas. T02 acepta esta receta. |
| B02 | Important | La contención temporal exigida para conversión mezcla coordenadas globales del padre y coordenadas locales de una salida engine region. | T-03 | `docs/roadmap/2026-10-10-m2-iteracion-creativa/composition-contract-design.md:106` | Padre100@10Hz, repaint `[6,8]`, engine region40@20Hz convertido20@10Hz: ambos buffers engine duran2s y se consumen localmente desde0 según l179. La salida válida es60+20+20=100frames. Exigir que ambas grids engine contengan `[6,8]` rechaza el caso; la región global pertenece al padre. T02 acepta receta/shape region. |

Lo ejecutado: Python gestionado, `-X utf8 -B`, sin escrituras: guards snapshot **26/26** y SHA del diff conformes; aritmética C01–C10 interior y half-up correctas; B01 devuelve `native_suffix=[160,160]`, `render_suffix=[80,81]`, `output_frames=101`; B02 devuelve ambas contenciones engine falsas y `output_frames=100`. Captura real T02: **B01 y B02 aceptadas**, fuentes contrastadas por SHA con snapshot. Consulta `knowledge-find.py`: sin aciertos aplicables; persona backend aplicada.

Fuera de mi lente (no reportado): ninguno. No modifiqué ledger, canon, producto ni snapshot.
