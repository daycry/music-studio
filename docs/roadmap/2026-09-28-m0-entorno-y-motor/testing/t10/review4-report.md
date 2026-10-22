# Revisión T-10 — intento 4

**Sin defectos nuevos: 0 Critical, 0 Important, 0 Minor.** Lentes A+B de contexto fresco, diff correctivo completo de dos archivos leído y reconstruido. Alcance exit 0 sin avisos, info ni exclusiones de usuario; selector automático C/D false. [Recibo](review4-receipt.json).

| Criterio | Veredicto | Evidencia |
|---|---|---|
| Firma y parámetros preservados | ✓ CPU | capabilities_native.py:307–313; filtro real upstream conserva captions y kwargs |
| Restauración normal y tras excepción | ✓ | test parametrizado con mismo método original restaurado |
| Proxy tokenizer | ✓ | objeto invocable y delegación conservados, identidad restaurada |
| TDD y cobertura | ✓ | RED TypeError válido; archivo cambiado 307/346 = 88,7283 % |
| Alcance/custodia/constitución | ✓ | 59 fuentes actuales, 57 ajenas y protegidos coinciden; planes anteriores intactos |
| R10-01…07 | ✓ preservados | sin reapertura ni evidencia nueva contra aprobados |
| GPU y música | pendiente | CPU model-free no demuestra aceptación ni primera excepción GPU histórica |

R10-08 queda corregido CPU. Cada lente ejecuta nueve pruebas dirigidas sin fallos, errores ni omisiones; se solapan y no se suman como 18 únicas. Ambas verifican el filtro del test contra el upstream instalado mediante AST normalizando sólo el receptor. Root verifica los JUnit y las 59 fuentes. No se repite la suite91 ni se ejecutan Docker/GPU/modelos por las lentes.

Esta revisión posterior conserva la historia de los intentos 1–3: aborda un defecto nuevo detectado durante la ejecución GPU después de una revisión limpia. No reinicia ni borra los veredictos anteriores. QA fresca y nueva toma GPU siguen pendientes. T-10 sigue en progreso.
