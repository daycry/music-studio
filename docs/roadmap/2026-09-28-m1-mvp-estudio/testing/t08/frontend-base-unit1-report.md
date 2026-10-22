> Publicación: las rutas locales se han anonimizado. Los argv y originales exactos se conservan en la evidencia privada.

# T08 — base frontend funcional, unidad acotada

Entrega de los 30 paths autorizados. Next App Router compila las rutas `/`, `/create`, `/songs` y `/system`; `/` redirige a Crear. Layout raíz compartido con next-intl 4.14.9, navegación Crear/Canciones/Sistema y reproductor fuera del subtree de páginas. Estado vacío, controles deshabilitados con explicación, sin audio/canciones/progreso/telemetría ficticios. Sistema consulta `/health` en un efecto de navegador y permite actualizar/reintentar; cancela e ignora resultados después del desmontaje. Cliente tipado con el `paths` generado vigente, sin proxy ni tipos de endpoints futuros.

Tokens UX §2 oscuros/claros, fallback CSS de sistema, elección explícita persistida, reduced-motion, foco, salto al contenido y navegación inferior bajo 1024 px. Inter/Bricolage Grotesque/JetBrains Mono se empaquetan desde los tres paquetes Fontsource OFL ya instalados; no next/font ni descargas. Base nativa propia: **no acredita el requisito completo shadcn**. Todos los textos de las rutas/componentes propios salen de `messages/es.json`. La página 404 automática de Next conserva su texto inglés: añadir un not-found propio requiere ownership adicional; no se ha añadido un fichero fuera de alcance.

SSE usa un único EventSource, los ocho tipos de `engine-v1.json`, escucha mensajes/envelopes y permite cierre explícito idempotente. No instala onerror que recree la instancia: la reconexión y Last-Event-ID son responsabilidad nativa del navegador. No se inventa una ruta SSE del server: el suscriptor recibe una URL local, y no se abre en la UI sin contrato publicado. Los tests de fetch/EventSource son **dobles unitarios**, no E2E de red ni prueba on-wire de Last-Event-ID.

## Comprobaciones actuales

Originales completos en `native-final-*/command.json`, `stdout.txt`, `stderr.txt`. Ejecución por el mismo Node portable 22.23.2 y pnpm 9.12.0 comprobados por `scripts/pnpm.ps1 --version`; no gestor/intérprete del perfil en la comprobación final. El launcher privado usa los ejecutables verificados directamente para conservar las variables de confinamiento que el wrapper sanitiza. Cada ejecución copia los sources antes de lanzar el comando.

| Comando real (pnpm portable `--filter web`) | Resultado |
| --- | --- |
| `run typecheck` | exit 0 |
| `run lint` | exit 0, sin avisos |
| `run test --coverage --reporter=default --reporter=junit --outputFile=.../native-final-tests/junit.xml` | exit 0, 133 PASS en 9 ficheros |
| `run build` | exit 0, Next 16.4.0 webpack, 6 páginas estáticas incluyendo 404 |

112 PASS corresponden a las pruebas previas de letras, intactas. 21 PASS nuevos. Corpus compartido actual: 56 fixtures. `protected-after.json`: los 12 paths protegidos por root coinciden byte/hash con `root-protected-before.json`, incluidos lyrics, tests, generado, locks y wrappers. No se ejecutó gen de nuevo ni la baseline portable65. Sin installs, cambios de pins/dependencias/lock, Playwright, Docker, Linux, GPU ni aceptación musical/manual.

Cobertura **WHOLE EACH**, fresh single trace final, `exclude: []`, sin extracción ni unión de trazas. Los 12 módulos de runtime modificados tienen 100% de líneas/statement/functions/branches individualmente. También se incluye lyrics completo, 100% líneas y 91,935% branches, aunque no cambió. Véase `coverage-whole-each.json` y el original `native-final-tests/coverage/coverage-final.json`; crudos Node V8 en `native-final-tests/raw-v8/`. El texto resumido de Vitest omite filas perfectas; el JSON individual conserva todas.

## TDD y originales

- `red-theme-causal`: `resolveTheme('light', true)` devolvía dark, expected light. Causal assertion RED.
- `red-theme-storage`: lectura devolvía system para light, escritura no guardaba elección. Causal assertion RED.
- `red-api`: fetch no llamado, HTTP/abort resueltos incorrectamente. Causal behavior RED.
- `red-events`: evento no entregado, destinos ajenos aceptados. Causal behavior RED.
- `red-ui`: navegación ausente al renderizar children, dock vacío, tema no aplicado, redirección ausente, Crear/Sistema sin estados visibles y locale en incorrecto. Fallos de assertions/roles, no imports rotos.
- `red-layout`: lengua HTML incorrecta con request-config ya corregida, Canciones sin heading y consulta de Sistema no ejecutada. Causal RED independiente de la excepción del primer fixture tardío.
- `green-foundation`, `green-ui-fixture-repair`: GREEN pertinentes; conservados aparte de los finales.

Tests nuevos escritos antes de los módulos. Los baselines mínimos compilables se escribieron después de los tests y antes del RED; no se sustituyó ningún módulo productivo preexistente. Sources/test/config/contratos generados archivados en cada `sources-before/` y hashes `sources-before.json`. Copias finales en `sources-after/`; preimágenes iniciales de los tres existentes suministradas por root en `preimages/`, con hashes en `root-owned-before.json`.

**TDD n/a:** package/tsconfig/vitest/next/postcss/eslint/next-env, mensajes JSON, CSS y esta prosa/configuración de evidencias. No se fabrican tests de configuración. Ledger/Git/docs/aceptación exclusivamente root; ninguna escritura realizada allí.

## Incidentes y cualificaciones conservadas

1. Errores de transporte inicial del wrapper: parse PowerShell, opción después de exec, array no transportado y restricción exec a tsc/vitest. Están en CLI original del padre, sin etiquetarlos RED. Las primeras llamadas fallaron antes de ejecutar tests. `red-theme` registró también un error pnpm de opción outputFile; el RED causal es el directorio distinto `red-theme-causal`. El parse de PowerShell abortó antes de escribir la primera configuración; después se migró Vitest antes de tests.
2. `green-ui` encontró dos defectos de fixtures: un Response reutilizado ya tenía el body consumido al actualizar; el doble de matchMedia no actualizaba matches al emitir change. Se repararon los dobles (respuesta nueva por petición y matches mutable), conservando assertions y ejecución original. La excepción `resolve is not a function` del fixture tardío en `red-ui` no cuenta como RED; se añadió la assertion de llamada antes de usar el resolver y se obtuvo RED causal en `red-layout`.
3. `final-tests` dio 133 PASS pero coverage branch 50% en ThemeProvider por el guard imposible de ref montado. Se eliminó ese guard redundante, sin excluir código ni alterar los tests. Los finales actuales cubren el módulo completo al 100%.
4. `final-typecheck` encontró declaraciones de terceros ausentes (`webpack`, URLPattern/Input/Options) en el set instalado. Se adoptó `skipLibCheck: true` estándar de Next, manteniendo strict/noEmit y chequeo del código propio/test/config. **No se acredita chequeo de declaraciones externas**; ni se descargaron tipos ni se inventaron shims. El error inicial sigue disponible. Next añadió allowJs y reescribió next-env dentro de los paths autorizados.
5. `final-build` compiló, pero los workers invocaron `C:/laragon/.../node.exe` y Next propagó `--e=` inválido desde el bootstrap inline. Incidente de confinamiento real, no ocultado. El launcher ahora fija PATH al portable y limpia NODE_OPTIONS heredado; los scripts limpian process.execArgv antes de entrar en Next. `final-build-repair` y la serie `native-final-*` pasan. **La identidad de los hijos de los RED/GREEN anteriores no fue observada y queda UNKNOWN**; no se certifica retrospectivamente que todos fueran portables. El wrapper inicial también prepara sus directorios mutables `.cache/web-runtime`; sin snapshot previo no se acredita ausencia de cambios allí, y no se limpia estado compartido ajeno.
6. La sonda privada native-preload comprueba executable antes de los imports y produce recibos self de los hijos finales. `native-process-summary.json` contiene 27 registros, 16 exits no observados/UNKNOWN. Algunos workers de Vitest comparten PID y dañaron el recibo original por escrituras concurrentes; sus bytes se conservan y se cualifican. No se inventa ClosedConfirmed ni se rastrean/matan procesos ajenos. La salida de los comandos padres fue observada. El runner privado no se copió en cada snapshot pre-run inicial; el código original está en el CLI padre, y el actual queda inventariado. Los snapshots de corpus56 se incorporaron antes de la serie nativa final, no antes del primer RED. No se convierte esa custodia parcial en prueba histórica perfecta.
7. `seal.mjs` falló inicialmente leyendo un JSON self truncado de la sonda; la reparación conserva el original y registra UNKNOWN en vez de abortar el inventario. No cambió producto ni se repitieron tests por este error de evidencia.

## Entrega y límites

`derived-next-receipt.json` enumera todos los assets generados bajo apps/web/.next. `non-cli-inventory.json` incluye ficheros y directorios de la unidad y solo excluye los cuatro nombres top reservados del padre y el inventario mismo. Scripts/evidencias/copies propios se mantienen en esta unidad. No se alteran fuentes de unidades concurrentes ni los originales CLI reservados.

Horas/modelo/tokens/EUR reales **NULL**, no medidos por este actor. Peso5 procede de root y es estimado, sin convertirlo en consumo. Los argv/UTC/exit/stdout/stderr de las ejecuciones registradas son reales; timestamps de otros tool calls están en el CLI padre y no se reconstruyen como mediciones observadas.

Unidad concreta lista para revisión fresca y QA de root. No se acepta T08/M1, shadcn, M-02 visual, E2E, Docker/Linux ni playback/flujo musical completo. La página 404 y declaraciones externas requieren atención explícita en revisión; las cualificaciones de custodia original no desaparecen con GREEN.
