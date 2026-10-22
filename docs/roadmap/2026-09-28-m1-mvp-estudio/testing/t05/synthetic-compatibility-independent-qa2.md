# Compatibilidad sintética — QA independiente2 y aceptación técnica

Root acepta el componente de compatibilidad/procedencia sintética y la
sincronización del fixture de recuperación tras la
[revisión2 A/B/C/D](synthetic-compatibility-review2.md) y QA independiente.
T-05 permanece abierta hasta la ejecución y publicación real de audio,
integración SQL completa, Docker y recorridos de aplicación.

La QA ejecutó601 pruebas funcionales sin tracing y600 con cobertura oficial,
ambas con exit0, sin fallos, errores o skips. El parámetro801 mantiene10s y
sus controles en la suite funcional; es la única omisión instrumentada.
Los IDs, orden y fases setup/call/teardown corresponden a los manifiestos.
No se suman pases ni se unen trazas de ejecuciones anteriores.

| Módulo completo | Cobertura combinada de líneas y ramas |
|---|---:|
| admission | 87,99% |
| dispatcher | 83,52% |
| provenance | 97,26% |
| resolver | 87,61% |
| retry | 89,78% |
| runtime | 88,51% |
| synthetic_registry | 88,80% |
| worker/contracts | 96,88% |

Los ocho archivos completos superan80%, sin excluir código. Estos valores
no implican que las ramas por separado superen80% en todos los archivos.
Root cotejó1870 artefactos privados,16 fuentes de la unidad,116 fuentes
congeladas,51 protegidos y8126 herramientas actuales; antes y después
coinciden. El actor de QA es independiente del productor y las lentes,
con contexto anterior reutilizado declarado.

La QA1 roja y su diagnóstico permanecen intactos. La demora controlada
demostró el defecto de la espera fija del fixture; la causa de aquel fallo
histórico sigue desconocida. La señal nueva ocurre después del submit real
del doble y conserva cuatro aserciones y el cierre. No se introduce un SLA
global de30s ni se acredita HTTP real con un backend simulado.

[Aceptación Root](../../../../../.cache/dev-cycle/m1/t05-synthetic-compatibility-independent-qa2/root-acceptance.json),
recibo, informes, JUnit, cobertura y comandos originales están en la evidencia
privada. No se certifican publicación WAV, Docker, E2E ni cierre universal
de OS/CIM/TCB. No se fabricó un resultado Playwright a partir de JUnit.
