**Lente B — M1/T-01, intento 2: sin defectos de corrección identificados en el diff completo aportado.** Perfil genérico.

| Criterio revisado | Dictamen | Evidencia estática |
|---|---|---|
| Configuración, mapa de engines y confinamiento de rutas | ✓ | `apps/server/app/settings.py:47`, `:76`, `:87` |
| Host/Origin antes del routing; lecturas ordinarias, SSE y preflight | ✓ | `apps/server/app/security.py:18`, `:23`, `:28`, `:46` |
| Errores públicos y conservación segura de cabeceras de protocolo | ✓ | `apps/server/app/errors.py:20`; `apps/server/app/main.py:35` |
| CORS en errores internos | ✓ | `apps/server/app/main.py:45` |
| Logs JSON, redacción, rotación y rechazo de sinks externos preexistentes | ✓ | `apps/server/app/logging.py:18`, `:42` |
| Token interno, destino del cliente, redirects y proxies | ✓ | `apps/server/app/engine_client.py:9`, `:19` |
| Empaquetado y configuración del server/mock CPU | ✓ | `apps/server/Dockerfile:27`; `docker-compose.yml:2` |

La corrección de **B-01** queda respaldada estáticamente: el handler transmite `exc.headers` y el generador de problemas conserva `Allow`; la prueba comprueba su valor en una respuesta405 (`apps/server/tests/test_security_errors.py:225`).

**Hallazgos:** Critical:0 · Important:0 · Minor:0.

No ejecuté herramientas ni pruebas ni comprobé hashes vivos. Los resultados86pass/2skip y201/202 proceden del paquete aportado. La paridad Docker del código corregido y la QA independiente siguen pendientes; este dictamen no cierra T-01 ni acredita los gates finales de M1.