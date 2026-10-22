**Veredicto Lente C, revisión 2/3: sin hallazgos de seguridad introducidos o reabiertos.** Critical: **0** · Important: **0** · Minor: **0**.

Lectura estática del diff completo, delta fix1 y las 25 fuentes INLINE, considerando ambos paths de los schemas idénticos y todos los bloques modificados del lock. Sin herramientas, tests ni comprobaciones propias de hashes. Las referencias auxiliares de cybersecurity no se aportaron; aplico criterio propio.

| Criterio C | ✓/✗ | Evidencia y valoración |
|---|:---:|---|
| Inyección SQL — CWE-89 | ✓ | `fix1_invariants.py:62` e `initial_invariants.py:63` interpolan mapas, columnas y expresiones definidos por código. Los datos importados se parametrizan en `snapshots.py:573` y `migrations/env.py:25`. |
| Inyección de comandos o plantillas | ✓ | Ningún sink nuevo de ejecución de comandos, evaluación de código o plantillas con entradas externas. |
| Autenticación y sesión | ✓ | `main.py:49` conserva `LocalSecurity`. No se añaden rutas de negocio ni se modifica la frontera Host/Origin. |
| Permisos y propietarios | ✓ | `snapshots.py:240` rechaza propietarios mezclados; `:542` exige coincidencia con el usuario persistido. Identidades inmutables y validación de sujetos en `initial_invariants.py:79,105,122`. |
| Secretos — CWE-798/200 | ✓ | Configuración/proveedores excluidos del snapshot (`snapshots.py:22`); rechazo recursivo de campos secretos (`:143`). Los nuevos eventos seguros son literales y no incorporan excepciones, rutas ni tokens. |
| Deserialización insegura — CWE-502 | ✓ | JSON con schemas empaquetados y referencias internas. Sin pickle, `eval`, carga de código ni referencias remotas controladas por el documento. |
| Traversal y sobrescritura — CWE-22 | ✓ | Confinamiento en `db.py:18`; rutas y symlinks de medios validados sobre ambas secciones en `snapshots.py:217`. Publicación con temporal; restauración de backup mediante creación exclusiva en `backup.py:128`. No identifico un escape concreto introducido por fix1. |
| SSRF — CWE-918 | ✓ | Ninguna petición de red nueva ni interpretación de strings importados como destinos de red. |
| Dependencias y recursos | ✓ | Versiones y hashes fijados en los bloques aportados de `uv.lock`, con origen PyPI HTTPS. Su autenticidad externa no fue comprobada por este revisor. |

La evaluación independiente de los nueve IDs distingue la corrección visible del cierre que corresponde a las otras lentes:

| ID | Evaluación desde C | Evidencia estática |
|---|---|---|
| R02-01 | Corrección visible; cierre A/B pendiente | `fix1_invariants.py:94` valida raíz en INSERT/UPDATE. |
| R02-02 | Corrección visible; cierre A/B pendiente | `fix1_invariants.py:116` comprueba extremos y pertenencia transitiva tras movimientos. |
| R02-03 | Corrección visible; cierre A/B pendiente | `snapshots.py:95,199,338,520`: soporte dirigido, validación de unión/procedencia y colisiones transaccionales. |
| R02-04 | Corrección visible; cierre B pendiente | `snapshots.py:484,511`: aislamiento individual durante auditoría y publicación. |
| R02-05 | Corrección visible; cierre B pendiente | `backup.py:23,92,121`: mismo validador en selección y restauración. |
| R02-06 | Corrección visible; cierre B pendiente | `db.py:15,39,68` y `backup.py:17,154`: eventos identificables en logger configurado, sin ampliar datos registrados. |
| R02-07 | Corrección visible; cierre A/B/D pendiente | `fix1_invariants.py:22` y `snapshots.py:448,506`: invalidación durable, pendientes y comparación de generación. |
| R02-08 | Corrección visible; cierre D pendiente | `fix1_invariants.py:107`: descendientes OLD/NEW y actualización sólo de raíces diferentes. |
| R02-09 | Corrección visible; cierre D pendiente | `fix1_invariants.py:145,161,180`: identidad entera estable y borrados FTS por rowid. |

**Ningún ID se reabre por un escenario de explotación identificado en C.** Esta lente no cierra los nueve hallazgos de conformidad, corrección o rendimiento, ni acredita QA, M-03 o aceptación de T02.