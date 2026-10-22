**Lente A: 0 Critical · 0 Important · 0 Minor**, exclusivamente para el prerrequisito registral candidato de primer nivel de M1/T-08.

| Tarea → criterio revisado | Resultado | Evidencia |
|---|---|---|
| T-08 → implementación declarada | ✓ | Las 25 filas están presentes. T-08 sigue `borrador`, sin criterios funcionales marcados como hechos: `tasks.md:280`, `:294–299`. |
| T-08 → alcance y `Archivos` | ✓ | El diff completo solo añade la sección de licencias; el registro está expresamente previsto en `tasks.md:286`. Prefijo histórico de **24.181 bytes intacto**, incluidas seis filas T04. |
| T-08 → versiones, identificadores y enlaces oficiales | ✓ | **24/24 paquetes** coinciden con `candidate-lock.json` y sus metadatos oficiales almacenados; Node tiene fila separada. Véase matriz inferior. |
| T-08 → pruebas y cobertura | ✓ N/A | Cambio de documentación. TDD y cobertura del diff no aplican; no se presentan pruebas UI como ejecutadas. |
| T-08 → Constitución | ✓ | Sin violaciones de los principios explícitos sobre confinamiento, castellano, estado canónico y decisiones: `CONSTITUTION.md:25`, `:32`, `:33`, `:37`. |
| T-08 → verificación ejecutada | ✓ | Evidencia original de `prepare3` y `verify`, ambos **exit 0**. `verify.stdout.txt:1`: «PASS historical prefix byte-exact; six T04 rows intact; 25 exact candidate rows…». T-08 no está cerrada; sus verificaciones frontend siguen pendientes. |
| T-08 → generado y documentación E2/E3 | ✓ N/A | El diff no toca `commands/`, `agents/` ni `hooks/`; no corresponde ejecutar exportación interop. La sección describe el alcance candidato y sus límites en `licencias.md:177–181`. |
| T-08 → custodia | ✓ | Recontraste independiente: **159 sellos**, **250 textos legales**, inventario original de **28 archivos** y custodia posterior de **29 archivos**, sin discrepancias. Hash actual del registro coincide con `5dece11d…63ab99`. |

Cada ✓ siguiente cubre **nombre, versión, licencia cualificada y enlaces**, contrastados con la evidencia local sellada:

| T-08 → candidato | Resultado | Fichero:línea |
|---|---|---|
| Node.js 22.23.2 | ✓ MIT + terceros; LICENSE íntegro, SHA oficial; PGP sin verificar | `docs/legal/licencias.md:185` |
| pnpm 9.12.0 | ✓ MIT + componentes; 96 avisos | `docs/legal/licencias.md:186` |
| next 16.4.0 | ✓ MIT + componentes; 132 avisos | `docs/legal/licencias.md:187` |
| react 19.3.0 | ✓ MIT | `docs/legal/licencias.md:188` |
| react-dom 19.3.0 | ✓ MIT | `docs/legal/licencias.md:189` |
| next-intl 4.14.9 | ✓ MIT | `docs/legal/licencias.md:190` |
| tailwindcss 4.3.3 | ✓ MIT | `docs/legal/licencias.md:191` |
| @tailwindcss/postcss 4.3.3 | ✓ MIT | `docs/legal/licencias.md:192` |
| postcss 8.5.29 | ✓ MIT | `docs/legal/licencias.md:193` |
| eslint-config-next 16.4.0 | ✓ MIT declarada; ausencia de LICENSE y fundamento upstream explícitos | `docs/legal/licencias.md:194` |
| @types/react 19.3.0 | ✓ MIT | `docs/legal/licencias.md:195` |
| @types/react-dom 19.3.0 | ✓ MIT | `docs/legal/licencias.md:196` |
| @playwright/test 1.64.0 | ✓ Apache-2.0, LICENSE/NOTICE; navegadores separados | `docs/legal/licencias.md:197` |
| @fontsource/inter 5.3.0 | ✓ OFL-1.1 y obligaciones | `docs/legal/licencias.md:198` |
| @fontsource/bricolage-grotesque 5.3.0 | ✓ OFL-1.1 y obligaciones | `docs/legal/licencias.md:199` |
| @fontsource/jetbrains-mono 5.3.0 | ✓ OFL-1.1 y obligaciones | `docs/legal/licencias.md:200` |
| @testing-library/react 16.3.3 | ✓ MIT | `docs/legal/licencias.md:201` |
| jsdom 30.1.2 | ✓ MIT | `docs/legal/licencias.md:202` |
| @testing-library/dom 10.4.2 | ✓ MIT | `docs/legal/licencias.md:203` |
| typescript 5.9.3 | ✓ Apache-2.0 | `docs/legal/licencias.md:204` |
| vitest 5.0.3 | ✓ MIT | `docs/legal/licencias.md:205` |
| @vitest/coverage-v8 5.0.3 | ✓ MIT | `docs/legal/licencias.md:206` |
| @types/node 22.19.15 | ✓ MIT | `docs/legal/licencias.md:207` |
| openapi-typescript 7.13.0 | ✓ MIT | `docs/legal/licencias.md:208` |
| eslint 9.39.5 | ✓ MIT | `docs/legal/licencias.md:209` |

**Gaps: ninguno en el alcance revisado.** Los fallos históricos del helper y la falta de sus preimágenes están declarados; los sellos posteriores no se presentan como recertificación histórica.

Este dictamen no cierra T-08 ni acredita frontend, cierre transitivo, comercialización del conjunto o autorización para instalar y ejecutar herramientas. La aceptación corresponde a raíz.