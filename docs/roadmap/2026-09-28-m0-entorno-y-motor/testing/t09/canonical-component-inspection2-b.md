**0 Critical · 1 Important · 0 Minor**

| Criterio | Resultado | Fichero:línea y escenario concreto |
|---|---|---|
| Inmutabilidad del ancla durante el fold | **Important — B01** | [benchmark_canonical.py:486](../../../../../scripts/eval/benchmark_canonical.py:486): se eliminó la copia congelada de cada intento. Tras comparar las anclas, `transition` utiliza el diccionario mutable del llamador. Si otro hilo modifica el recibo durante la lectura, el fold incorpora datos distintos del ancla sin rechazarlos. |
| Publicación atómica y candidatos obsoletos | Sin defectos adicionales | `benchmark_canonical.py:620` |
| Plazos, frescura y revocación | Sin defectos adicionales | `benchmark_canonical.py:545`, `:581`, `:656` |

**B01 reproducido** leyendo originales aceptados e inyectando únicamente una modificación del llamador al leer `request.json`: el ancla conservó `pid=27448`, pero el resultado publicó `pid=0` y `accepted_count=1`. Es una sonda ejecutada con intercalación simulada, sin procesos nativos nuevos ni escrituras.

Fuentes coincidentes con el freeze. Evidencia cotejada: 88 PASS, 34 RED funcionales y cobertura completa actual de 87,08 % / 81,32 %, cero exclusiones; 89 partes de la misma corrida con copias byte a byte. Esto no acredita la integración pendiente de T09.