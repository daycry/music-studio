**1 Important; 0 Critical; 0 Minor.**

| Criterio | Resultado | Fichero:línea y escenario |
|---|---|---|
| Comandos autorizados sin regresiones | ✗ Important — B-01 | `scripts/pnpm.py:143`: `pnpm gen` desde la raíz ejecuta el script de `package.json:7`, que contiene `pnpm --filter web gen`. El entorno reemplaza PATH por el directorio de Node, que carece de launcher `pnpm`; tampoco existe en `node_modules/.bin`. El lifecycle de pnpm añade bins de dependencias y node-gyp, pero ningún launcher propio. La llamada anidada falla al resolver `pnpm`, impidiendo generar el contrato por el comando existente. La función PowerShell instalada por `env.ps1` no se transmite al shell hijo. **Evidencia estática sobre fuentes y layout actuales; sin ejecutar el wrapper.** |
| Transporte de argumentos y propagación de errores | ✓ | `scripts/pnpm.ps1:10`, `scripts/pnpm.py:178`: transporte JSON/base64 y conservación del exit. Evidencia archivada nativa PowerShell; receptor Python simulado en las pruebas de transporte. |
| Bootstrap incompleto produce fallo | ✓ | `scripts/bootstrap.ps1:19`, `scripts/bootstrap.sh:18`: ausencia de lock o fallo del wrapper impiden anunciar éxito. Las pruebas usan uv simulado explícitamente. |
| Integridad antes de ejecución | ✓ | `scripts/pnpm.py:169`: comprobación de archivos oficiales y payloads mediante el manager aceptado antes del subprocess. Sin atribuir protección frente a mutaciones concurrentes posteriores. |
| Fuentes y cobertura actuales | ✓ | Los diez ficheros coinciden con `sources-freeze.json`. JUnit original: 43 PASS; cobertura oficial whole de `scripts/pnpm.py`: **88/91, 96,70 %, cero exclusiones**. |

B-01 no está cubierto por las pruebas actuales: `test_preserves_allowed_argv` comprueba `run gen`, pero no la resolución de la llamada anidada del script raíz.

Revisión estrictamente de lectura. No ejecuté wrappers, manager ni suites; no modifiqué archivos. El hallazgo queda limitado a esta unidad técnica de T08.