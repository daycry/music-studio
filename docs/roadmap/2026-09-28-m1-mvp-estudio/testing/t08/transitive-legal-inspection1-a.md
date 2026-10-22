**Lente A: 0 Critical · 1 Important · 1 Minor.** Revisión limitada al prerrequisito legal candidato de M1/T-08; no acredita cierre de T-08 ni adopción de las transitivas.

| T-08 → criterio de aceptación del ledger | Resultado |
|---|---|
| Tokens, temas, preferencias y tipografías | ✗ Pendiente; esta entrega sólo cualifica licencias. |
| Navegación y reproductor persistente | ✗ Pendiente, fuera de esta entrega. |
| Cliente tipado y SSE con reconexión | ✗ Pendiente, fuera de esta entrega. |
| Texto desde `messages/es.json` | ✗ Pendiente, fuera de esta entrega. |
| Infraestructura E2E y smoke | ✗ Pendiente; no se acredita ejecución. |
| Docker/Compose, URLs internas y SSE | ✗ Pendiente; no se acredita despliegue. |

Estos pendientes **no son gaps de esta entrega parcial**: los seis criterios siguen abiertos y T-08 figura `en-progreso` en `docs/roadmap/2026-09-28-m1-mvp-estudio/tasks.md:280`.

| Criterio de revisión de la entrega | Resultado y evidencia |
|---|---|
| Implementación de lo declarado | ✓ Manifest con 609 claves únicas, 23 primeros pins y 75 resoluciones individuales enlazadas. |
| Alcance y `Archivos` | ✓ Prerrequisito de `docs/legal/licencias.md`, expresamente declarado en `tasks.md:286`, coherente con la fase Web del plan. Candidato privado; registro y locks canónicos intactos. |
| Integridad y clasificación | ✓ Comprobaciones propias: SHA256/SRI y `package.json` nativo de los 609 archivos; SHA1 contra metadata; 705 miembros legales; dos alias byteidénticos. Conteos reales: **532 + 39 + 24 + 2 cabecera/README + 10 bundles LGPL + 2 excepciones MIT = 609**. |
| Tests y cobertura | ✓ **No aplica** al delta DATA/legal. No hay cambio de código de producto; no atribuyo porcentaje de cobertura ni ejecuciones de tests. |
| Constitución | ✓ Sin violación observada de localidad, Docker, confinamiento, elegibilidad comercial o ledger único (`docs/CONSTITUTION.md:9,17,25,27,33`). No se incorpora una opción no comercial ni se instala producto. |
| Verificación declarada | ✓ La entrega final conserva comando, fechas, exit **0** y stdout: `DATA delivery assertions PASS; 609/75/2; 17+2935 exact; predecessor exact; legal blockers 0`. Las verificaciones frontend no se presentan como ejecutadas y T-08 continúa abierta. |
| Generados E2 / descripciones E3 | ✓ **No aplica**: el candidato no toca `commands/`, `agents/` o `hooks/` del producto. Los `commands/` privados son recibos. Tampoco existe `scripts/export-interop.py` en la raíz; no ejecuté exportador. |
| Precisión de bloqueos e historial | ✗ Los dos gaps siguientes. |

**Gaps**

| ID | Gravedad | Fichero:línea | Escenario concreto |
|---|---|---|---|
| A-01 | **Important** | `.cache/dev-cycle/m1/t08-transitive-legal-qualification/proposed-legal-addendum.md:9` y `:124–125`; `report.md:5,15`; `remaining-blockers.json`, clave `technical_installation` | Se presenta el rechazo del auditor TAR como bloqueo de extracción/instalación por el validador productivo. `scripts/fetch_web_tools.py:412–450` prepara exclusivamente los pins de herramientas portátiles; no instala `agent-base` ni `https-proxy-agent`. La instalación npm futura mediante pnpm **no se ejecutó**. Para adjudicar el siguiente paso, debe distinguirse rechazo del auditor, seguridad aún no acreditada y decisión técnica pendiente, sin afirmar un bloqueo productivo demostrado. Conservar ambos rechazos y no conceder una excepción general. |
| A-02 | **Minor** | `.cache/dev-cycle/m1/t08-transitive-legal-qualification/report.md:13` | «Cada helper ejecutó exit0» contradice el recibo `commands/20261008T0109522984471Z/command.json`, clave `exit: 1`, cuyo stderr registra `AssertionError` al comparar un aviso. El intento posterior terminó en 0. La evidencia existe y el fallo permanece conservado; debe corregirse la descripción histórica para evitar certificar todos los intentos como exitosos. |

**Evidencia propia frente a entregada:** mis lecturas comprobaron los siete sellos de raíz, 1.839 entradas, 146 outputs/inventario y 17 fuentes más 2.935 payloads protegidos, sin discrepancias. Los comandos de cualificación y entrega son ejecuciones **entregadas**, no repetidas por mí.

La cualificación distingue correctamente declaración nativa, aviso completo y suplemento upstream; mantiene pendientes LGPL/MPL, atribuciones y distribución, sin convertir metadata MIT en licencia universal del bundle. **Señal para raíz: corregir A-01 antes de adoptar la adenda y A-02 antes de certificar su historial.** No supone garantía jurídica, autorización de instalación ni aceptación nueva de T-08.