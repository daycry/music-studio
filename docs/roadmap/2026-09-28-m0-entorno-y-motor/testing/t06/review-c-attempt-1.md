# Lente C · T-06 · intento 1

Revisión fresca de seguridad del diff frente a `main` (`19ab239`), incluidos archivos
nuevos. Activada por Dockerfile y `exec` en `patches.py`; D no se activó.

| Criterio | Resultado | Evidencia |
|---|---|---|
| Ejecución del parche fijado | ✓ | `patches.py:90` comprueba SHA antes de `exec` (`:97`). Fuente upstream recalculada: `22b41692bcb73fead4c831d16eaef3dda56cc995577f2353d763445dae7362e1`; coincide. |
| Deserialización e integridad | ✓ | `patches.py:30` comprueba tamaño/hash y rechaza enlaces, escapes y pesos/código adicionales; `:114` fuerza safetensors y lectura local. |
| Autenticación | ✓ | `engine_acestep.py:12` delega en el servidor autenticado; test HTTP verifica 200 con token y 401 sin él. |
| Rutas y código remoto | ✓ | `adapter.py:127` verifica antes de cargar; `:243` usa nombres internos de salida. `engine_contract/__init__.py:224` valida las rutas relativas de `remote_code`. |
| SSRF, secretos y permisos introducidos | ✓ | Sin secretos, destinos de red controlados por petición ni ampliación de permisos; el diff de Dockerfile cambia un comentario. |

**Sin hallazgos:** 0 Critical, 0 Important, 0 Minor. Se consultaron las referencias
Python, Dockerfile y supresión de falsos positivos de cybersecurity.

Comprobación independiente: tras `. ./scripts/env.ps1`,
`uv run --no-sync pytest apps/engines/acestep/tests/test_adapter.py packages/engine-contract/tests/test_contract.py -q --tb=short -p no:cacheprovider`
→ **45 passed, 1 skipped**, exit 0. SHA upstream recalculado y coincidente.

La carga, generación y liberación real de VRAM no se han ejecutado. No se editaron
archivos ni el ledger. Las líneas citadas corresponden al intento 1.
