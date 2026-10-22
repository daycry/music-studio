**0 Critical · 1 Important · 0 Minor.**

| Criterio | Resultado | Fichero:línea y escenario concreto |
|---|---|---|
| Aislar carreras de entrada antes del claim | **Important B4-01** | [admission.py:225](../../../../../apps/server/app/queue/admission.py:225): si el fichero desaparece después de `confined_path()` y antes de `source.open()` ([inputs.py:213](../../../../../apps/server/app/queue/inputs.py:213)), staging propaga `FileNotFoundError`. Solo `ResolutionError` se convierte en `PreclaimResolutionError`; por ello [dispatcher.py:196](../../../../../apps/server/app/queue/dispatcher.py:196) deja escapar la excepción y aborta el scan automático sin visitar el siguiente job válido. |

**Prueba independiente ejecutada:** funciones actuales extraídas por AST, con intercalación sintética en memoria y operaciones de fichero simuladas. Resultado: `FileNotFoundError`, visitada únicamente la cabeza. No acredita una carrera nativa de filesystem/SQLite.

Freeze: **3/3 hashes exactos**. Evidencia entregada comprobada: **206 PASS**, cobertura completa admission **94,58 %** y dispatcher **88,28 %**, cero exclusiones. Sin escrituras ni reejecución de suites. Alcance limitado a fix3/U1; no aceptación de T04.