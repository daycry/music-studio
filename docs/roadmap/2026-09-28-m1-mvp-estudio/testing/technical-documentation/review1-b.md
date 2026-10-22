**Lente B genérica · attempt1: sin defectos de corrección identificados** en los cinco Markdown del alcance, contrastados con las fuentes inline disponibles.

| Criterio | Resultado | Evidencia |
|---|---|---|
| Configuración y frontera HTTP | ✓ | Autoridades exactas, Origin y preflight concuerdan con `settings.py` y `security.py`. La documentación distingue parser HTTP de aplicación. |
| Factoría, lifespan y health | ✓ | Concuerda con `main.py`: recursos runtime en lifespan; health sólo confirma proceso. T03 queda señalado como candidato. |
| Exportación neutral code-first | ✓ | `ContractSettings` conserva validaciones y utiliza exclusivamente `init_settings`; el exportador comprueba ambos contratos sin iniciar lifespan. |
| Persistencia y ampliaciones futuras | ✓ | Baseline histórico de 23 tablas separado de infraestructura posterior; `job_attempt` y dispatcher siguen pendientes. |
| Snapshots y restauración | ✓ | Cierre dirigido, colisiones, propietario, hashes de medios presentes, bloqueo escritor y CAS concuerdan con `snapshots.py`. No se promete atomicidad BD/filesystem. |
| Backup y parada | ✓ | API nativa, validación previa, rotación propia, comprobación horaria, cancelación y destino nuevo concuerdan con `backup.py`. |
| Despliegue documentado | ✓ | Perfil `studio` CPU coherente con Compose/Dockerfile; arquitectura objetivo conserva la excepción Ollama de ADR-0035. |
| Alcance de aceptación | ✓ | QA técnica limitada a unidades; no convierte mocks en canciones reales ni acepta M0/M1, calidad musical o T03. |
| Parser candidato | ✓ | Conservación de `original`, alias y rangos UTF-16 coherentes con `lyrics.py`; sin atribuir QA al cambio concurrente. |

**Hallazgos:** Critical **0** · Important **0** · Minor **0**.

Revisión estática inline, sin herramientas ni ejecuciones. Las afirmaciones sobre CLI, tooling raíz y QA T01 cuyos cuerpos completos no aparecen aquí no quedan verificadas independientemente. El comprobador de 106 enlaces acredita existencia según su informe; no acredita anchors semánticos ni E2E. Los criterios exclusivos de lente A no se convierten en hallazgos B.