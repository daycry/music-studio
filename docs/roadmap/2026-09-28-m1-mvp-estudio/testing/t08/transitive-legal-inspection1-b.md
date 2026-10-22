**Lente B: 1 defecto Important; 0 Critical, 0 Minor.**

Rutas relativas a `.cache/dev-cycle/m1/t08-transitive-legal-qualification/`.

| Criterio | Resultado | Evidencia |
|---|---|---|
| Recuentos y clasificación 609/75/2 | ✓ | `qualification-manifest609.json`: 532+39+24+10+2+2; 75 casos únicos y 23 pins. |
| Integridad y declaraciones nativas | ✓ | Contraste propio de los 609 TAR: SHA-256, SRI, identidad y declaración de `package.json`; textos legales contrastados sin discrepancias. |
| Excepciones inertes | ✓ | Alias exactamente iguales en ambos TAR; LICENSE MIT contrastadas. |
| Declaración, avisos y fuente upstream diferenciados | ✓ | Ausencias cualificadas explícitamente; GPL referencial distinguida de concesión; condiciones LGPL/MPL/OFL conservadas. |
| Alcanzabilidad frente a instalación | ✓ | Conjunto instalado y compatibilidad permanecen pendientes. |
| Bloqueo automático de instalación | ✗ | `proposed-legal-addendum.md:9`, `report.md:5,15`, `remaining-blockers.json:10`. |

**B-01 — Important:** los puntos señalados presentan el rechazo del auditor estricto como un bloqueo efectivo de instalación por el validador productivo. Sin embargo, `scripts/fetch_web_tools.py:23,420` procesa los pins de **Node y pnpm**, no esos dos paquetes transitivos. La futura instalación npm mediante pnpm no se ha ejecutado.

**Escenario de fallo:** raíz podría decidir que instalar las dependencias exige modificar el validador de herramientas, o registrar como demostrado un fallo de pnpm que únicamente se observó en el auditor DATA. Debe conservarse el rechazo histórico y la decisión técnica pendiente, sin afirmar un bloqueo automático del instalador.

Verificaciones propias: siete archivos congelados, 1839 inputs y 146 outputs coinciden con sus hashes. Las ejecuciones entregadas no se repitieron; no hubo extracción a disco, ejecución de paquetes ni escrituras.

**Señal de decisión:** corregir B-01 antes de adoptar la conclusión técnica. No observé otros defectos de corrección en la cualificación acotada; adopción exclusiva de raíz y sin garantía legal global.