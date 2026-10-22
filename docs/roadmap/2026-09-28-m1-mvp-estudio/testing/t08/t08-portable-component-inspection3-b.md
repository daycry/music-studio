| Criterio | Resultado | Fichero:línea y escenario concreto |
|---|---|---|
| Revalidación de propiedad antes de borrar | **Important — FIXTURE-OWNER01** | [scripts/test_workspace.py:88](../../../../../scripts/test_workspace.py:88): si el marcador cambia de token durante `collect()`, las comprobaciones previas a `unlink()` validan padres e identidad, pero no el token. Se borra `payload` y después se lanza `ValueError` en la validación final del marcador. El rechazo llega después de la eliminación. |

**Prueba ejecutada:** sonda exclusivamente en memoria sobre el código actual, con filesystem simulado e inyección del cambio durante `scandir`. Resultado: `deleted_before_rejection=[…/payload]`, seguido de `ValueError: Marcador alterado durante limpieza`. No constituye reproducción nativa.

Hashes actuales coinciden con el freeze. Evidencia documental comprobada: tres RED funcionales anteriores al cambio; cobertura completa del helper **107/112 (95,54 %), cero exclusiones**. No reejecuté suites ni modifiqué archivos.

**Critical: 0 · Important: 1 · Minor: 0.**