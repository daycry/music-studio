**0 Critical · 0 Important · 1 Minor.**

| Criterio | Resultado | Fichero:línea y escenario |
|---|---|---|
| Inicialización concurrente | **B-01 · Minor** | `scripts/pnpm.py:143–152`: con las configuraciones ya creadas y el shim ausente, dos llamadas legítimas simultáneas pueden observar `exists() == False`. Una crea `pnpm.cmd`; la otra falla en `open("xb")` con `FileExistsError` y termina con código 1, aunque el launcher resultante sea válido. |
| Ejecución anidada, validación y propagación del exit | Sin defectos adicionales | `scripts/pnpm.py:207`, `:230`; tests nativos en `tests/test_web_tool_entrypoints.py:511`, `:522`, `:570`. |

B-01 reproducido ejecutando la función real sobre un sistema de archivos **simulado en memoria**: una llamada correcta y otra con `FileExistsError`. No constituye reproducción nativa.

Fuentes actuales coinciden con el freeze. Evidencia de entrega leída: RED funcional nativo previo; 55 PASS sin skips; cobertura completa actual **113/116 = 97,41 %**, cero exclusiones. No repetí la suite ni escribí archivos. Alcance limitado al componente; no acredita aceptación completa de T08.