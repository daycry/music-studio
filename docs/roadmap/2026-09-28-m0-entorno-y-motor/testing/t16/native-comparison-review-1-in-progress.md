# Comparación nativa T-16: revisión parcial, intento1

Diff exclusivo de dos archivos privados completos: ejecutor y plan derivados. Sólo cabecera y literales; originales preservados. Alcance exit0 sin avisos ni exclusiones de usuario. Selector C+D activo. Tier reviewer del frontmatter, contexto fresco; límite del pool obliga a escalonar las lentes.

| Lente | Resultado | Evidencia y límites |
|---|---|---|
| A | Conforme, sin gaps | 51 congelados/12 artefactos/cuatro SHA; rollback/AST y alcance. CA3/4 abiertas; sin runner ni Docker ejecutados por A. |
| B | Conforme, sin defectos | Prepare-only real exit0; arranque/colisión/siete limpiezas mediante funciones reales con dobles; namespaces e inventarios. Sin ejecución GPU ni contenedores reales. |
| C | Pendiente | Revisor fresco activo. |
| D | Pendiente | Revisor fresco activo. |

Ambos revisores corrigieron una lectura JSON con codificación predeterminada de Windows en su primer probe; los probes posteriores con UTF-8 explícito terminaron exit0. No hubo cambios del candidato ni RED de producto.

Esta revisión parcial no autoriza la ejecución. Faltan C/D y QA independiente; seis90, montaje de escucha y calidad pendientes. No hubo consulta de knowledge/memorias ni cambios de producto, pesos, Git o originales.
