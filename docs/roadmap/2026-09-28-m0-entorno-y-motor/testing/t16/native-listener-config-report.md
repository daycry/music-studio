# Servidor privado de escucha T16: preparación de configuración

Estado: **READY_CONFIG_ONLY**. Revisión de contexto fresco y QA pendientes.

El derivado `serve-listening.py` conserva las 38 líneas del baseline T15 y cambia
solo cuatro literales: pointer nativo, confinamiento `libre-sft`, puerto preferido
8768 y registro privado `native-listening/listening-server.json`.

Se conservan la allowlist de ocho rutas, GET/HEAD, `urlsplit`, loopback,
`SimpleHTTPRequestHandler`, `ThreadingHTTPServer`, silencio del log y fallback
de puerto efímero. El algoritmo coincide por AST tras invertir los cuatro
constantes. La inversión de literales recupera exactamente los bytes originales,
incluidos los finales CRLF. Ambos scripts pasan parseo AST con gramática Python
3.11 y compilación en memoria; ninguno se ejecutó.

Entorno: `scripts/env.ps1` y `uv run --frozen --no-sync --all-packages python`;
Python gestionado 3.12.14 dentro del repositorio. TDD n/a: cuatro literales de
configuración, algoritmo intacto. No se registra un RED ficticio.

El primer intento comprobó 40 líneas según el brief y se detuvo antes de crear
el candidato. El baseline real tiene 38; se corrigió únicamente esta expectativa
del preparador privado y se conservaron sus bytes reales.

`freeze-before.json` y `freeze-after.json` contienen rutas relativas a la raíz,
baseline, candidato y dependencias estáticas, incluidas las nueve fuentes
productivas declaradas por el receipt nativo y ambos planes inmutables. Sus
hashes coinciden; las nueve fuentes y los planes coinciden con aquel receipt.
No se congelan ni se leen pointers, carpetas de sesiones o inventarios vivos.

No se arrancó servidor ni se ocupó puerto. No hubo GPU, jobs, modelos, Docker,
build, instalaciones, suites de producto ni empaquetado completo. Los servidores
históricos 8766/8767 no se tocaron. La generación en curso y los seis takes de
90 segundos no se verificaron aquí; no se declara calidad musical ni ganador.

La puesta en servicio de 8768 queda a cargo del orquestador después de verificar
los seis terminales y el pack completo. Este resultado prepara su configuración.

Artefactos: `literal-changes.json`, `delta.patch`, `rollback.patch`, snapshots
de congelación, `receipt.json` y `SHA256SUMS.txt`. El rollback documenta la
inversión; no se aplica al baseline ni se altera ningún original.
