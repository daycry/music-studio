**Dictamen A: sin gaps de requisitos o constitución demostrables en el diff actual de M1/T-01. Conforme para continuar a QA; no acredita cierre de la tarea.**

Revisión estática del diff completo de los 20 archivos suministrados, exclusivamente con el paquete inline. No ejecuté herramientas, tests ni comprobaciones de hashes.

| T-01 → criterio de aceptación | Resultado | Evidencia del código y tests |
|---|---|---|
| Configuración `pydantic-settings`, variables `STUDIO_*` y mapa familia→URL | ✓ | `settings.py:23–74` implementa lectura y validación; `test_settings.py:12–37` comprueba el mapa y rechazos; `:74–91`, lectura persistente de dotenv. |
| Lista cerrada de Host; inválido →403 | ✓ | `security.py:18–21`, `errors.py:6` y `settings.py:114–128`. Tests de autoridades permitidas, ajenas y duplicadas en `test_security_errors.py:16–19`, `:91–150`. |
| Origin explícito ajeno o duplicado →403 también en GET/HEAD; ausencia ordinaria permitida; SSE lo exige | ✓ | `security.py:19–29` coincide con `spec.md:66`, `convenciones.md:49` y `tasks.md:85`. Tests específicos en `test_security_errors.py:234–266`. A-01 corregido en el código suministrado. |
| CORS cerrado y sin exposición LAN | ✓ | Métodos/cabeceras limitados en `security.py:5–6`, `:46–81`; tests negativos en `test_security_errors.py:169–196`. Publicación loopback en `docker-compose.yml:9–10`; mock sin puerto publicado. |
| Errores RFC 9457 con código estable | ✓ | `errors.py:5–41`, handlers en `main.py:31–52`; tests de 404/422/500 en `test_security_errors.py:51–83`. Conservación segura de cabeceras cubierta en `:225–231`, `:269–315`. |
| Logs JSON en datos, con rotación | ✓ | `logging.py:18–64`: campos, redacción, confinamiento, rotación diaria UTC y 14 copias. Aserciones en `test_logging_token.py:9–26`, `:75–96`; escapes en `test_logging_paths.py:12–23`. |
| Token persistente y envío en cabecera interna | ✓ | `settings.py:34`, `:87–95`; `engine_client.py:19–26`. Persistencia mediante el generador existente en `test_token_persistence.py:8–24`; envío/destino/redirecciones en `test_logging_token.py:29–72`. |
| Imagen sin torch, Compose, persistencia y URLs internas | ✓ estático; QA pendiente | `Dockerfile:27–30`, dependencias en `pyproject.toml:6–13`, montajes y DNS interno en `docker-compose.yml:13–23`. La evidencia Docker aportada corresponde a la entrega anterior; no demuestra runtime del código corregido. |

| Comprobación literal de lente A | Resultado |
|---|---|
| (1) Tareas hechas realmente implementadas | ✓ Para T-01 no existe cierre anticipado: `tasks.md:71` mantiene **en-progreso** y `:84–88` conserva casillas abiertas. |
| (2) Alcance y `Archivos` | ✓ Los 20 archivos corresponden a server, empaquetado, pruebas, lock y licencias declarados en `tasks.md:77`. El cliente mínimo autenticado sirve al criterio del token; no implementa T-04. El WIP M0 de Compose queda fuera del delta. |
| (3) Criterios con tests | ✓ Las aserciones comprueban comportamientos, estados y contenido. Cobertura **aportada**, no ejecutada por mí: **201/202 = 99,50 %**, siete módulos, cero exclusiones (`t01-fix1/receipt.json:33–39`). No sustituye la lectura de tests ni acredita cobertura de ramas. |
| (4) Constitución explícita | ✓ Sin violación demostrada de `CONSTITUTION.md:17–19`, `:24–25`, `:32–37`, `:41–44`. No se añade inferencia, BD, infraestructura externa ni secretos reales al código suministrado. |
| (5) Verificación ejecutada y registrada | ✓ La nota de `tasks.md:90` registra **59 passed/8 deselected** y **403**, respaldados por recibos aportados. `:92` distingue GREEN corregido de Docker/QA pendientes. No corresponde el gap «completado sin evidencia». |
| (6) Generado y documentación | ✓ README describe el comportamiento actual, incluidas las limitaciones de `/health` y las rutas futuras. **Interop no aplica:** el diff no toca `commands/`, `agents/` ni `hooks/`. No se aportó matriz E3 para exigir otras piezas. |

**TDD:** los RED HTTP preliminares por factoría ausente no cuentan como evidencia comportamental aceptada. El paquete distingue posteriores RED contra FastAPI mínimo y RED de fix1 contra producción anterior. Los tests de configuración/logs/cliente contienen aserciones completas. Los recibos estáticos no prueban por sí solos cuándo se escribió cada feature; tampoco muestran evidencia concreta de implementación anterior al RED que permita declarar una infracción.

**Discrepancia de evidencia identificada:** `runtime-receipt-final.json:31–35` registra Host ajeno →**400**, frente a **403** exigido en `spec.md:66`. Es evidencia de la imagen anterior: el código actual devuelve403 y `t01-fix1/receipt.json:224–226`, `tasks.md:92` y `root-acceptance.json:43–44` declaran honestamente reconstrucción/paridad y QA pendientes. No la presento como prueba final ni como nueva regresión del código.

**Gaps:** Critical **0** · Important **0** · Minor **0**.

Contrato OpenAPI condicional omitido: no hay spec OpenAPI modificada en este diff. No revisé lentes B/C/D ni emití certificado global de seguridad. M0/T-13, aceptación final de M1 y gates manuales permanecen pendientes conforme a ADR-0037.