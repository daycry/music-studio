# T-08 — revisión parcial del intento 1

Fecha: 2026-10-06. Antecedente parcial de las lentes previstas A+B+C; D=false según selector. A/C comparten contexto reutilizado de QA T-19 por el límite de threads. Son independientes de la implementación, pero no se presentan como revisores frescos. B reutilizaba el revisor anterior T-17 y fue interrumpida al confirmar defectos CLAP. [Resultado incompleto del intento 1 y gaps obligatorios](review-1.md). **No hay aprobación global.**

| Criterio de A | Resultado parcial | Evidencia |
|---|---|---|
| CA1: base/dependencias y servicio | Conforme CPU | Dockerfile:1–24, pyproject:34–49, Compose:9/14/18–20 |
| CA1: beats CPU | Conforme CPU | descriptor:92–93; antecedente real 120 BPM/61 beats |
| CA2: loaders, tareas y pesos seguros | Implementación CPU conforme | descriptor:8–13; backend:95–119/144–165/204; tests semánticos |
| CA2: texto y tiempos reconocidos | Conforme con dobles; GPU pendiente | adapter:91–108; test_analysis:188–210 |
| Alineación independiente | Preparada, pendiente M3 | descriptor y ADR-0030 |
| CA3: residencia, hijo y unload | Conforme CPU y beats; memoria GPU pendiente | adapter:54–56/91–96, backend:59/221–228; tests de residencia/descarga |
| Alcance/constitución/licencias | Conforme en el diff | Ledger T-08, CONSTITUTION:19–25, licencias:23–28/63–78 |
| RED/cobertura/documentación | Evidencia conforme | Entrega CPU, 307/341 y mínimo87,50 %, README/ADR/contrato actualizados |
| Verificación completa y cierre | Pendientes explícitos | T-08 en-progreso; tres inferencias GPU y QA pendientes |
| Interop/OpenAPI | No aplica | Sin cambios en ese alcance |

A ejecutó 31 passed/4 deselected/cero avisos en host, exit0, sin torch real ni GPU. Comprobó dieciocho SHA de fuentes, siete de evidencias, tres pins, AST y cobertura oficial. Esta ejecución no sustituye QA ni la inferencia en contenedor. El antecedente de contenedor mantiene su aviso de Starlette; la prueba de beats también mostró un aviso. No se declaran como ejecuciones sin avisos.

**C: sin vulnerabilidades introducidas/reabiertas encontradas.** AST no contiene eval/exec/compile dinámicos en producción: los disparadores .eval() son métodos de modelos. Localhost/token, safetensors estrictos, trust_remote_code=False, recursos SHA/tamaño, entradas/salidas restringidas, loaders offline y usuario no root conformes en lo leído. Dieciocho SHA comprobados; sin repetir suite ni auditar todo upstream. A/C no encontraron gaps, sin afirmar seguridad universal ni inferencia GPU validada.

La revisión B debe comprobar corrección de loaders, estados y casos límite; ese alcance permanece incompleto. La investigación CPU confirmó el [fallo de kwargs del ClapProcessor](clap-preprocessing-diagnosis.md) y, posteriormente, la regresión de ruta real reprodujo también el atributo `chunk_length_s` inexistente. La interrupción explícita por esos defectos se comprobó en el handle; no equivale a aprobación ni a sustituir un proceso por un timeout. Fix1 continúa con RED previo; revisión 2 debe cubrir también B pendiente, seguida de QA independiente. No cargar GPU ni cerrar T-08 por esta evidencia parcial.
