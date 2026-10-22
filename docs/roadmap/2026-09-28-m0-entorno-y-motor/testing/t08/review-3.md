# T-08 — revisión intento3 sin gaps pendientes

2026-10-06. A+B+C frescas e independientes de implementar. D=false según selector. Contextos `review_t08_fix2_a`, `review_t08_fix2_b`, `review_t08_fix2_c`; B inicial rechazado por threadlimit, admitido tras terminar diagnósticoT16, C admitida después deA. No se sustituyó un handle vivo por un timeout. Scopeexit0 sin fuera/avisos; journals ajenos excluidos por default y preservados. [Freeze20fuentes](fix2-delivery-receipt.json), imagen306e3b0, [tabla completa anterior](review-2.md).

| Criterio | Veredicto y evidencia |
|---|---|
| Base, dependencias, puerto, montajes, token y beats | Conforme CPU conservado;12fuentes idénticas a fix1 |
| Transcripción hasta600s y tiempos globales | B-LONG-01 corregido CPU; backend257/302 y regresiones450/600s, parser upstream real |
| Correspondencia texto/audio/idioma y silencios | Conforme CPU; fragmentos propios, idiomas upstream y offsets reales; precisión pendiente |
| Residencia secuencial | Conforme CPU; adapter93–102 y tests de una liberaciónASR/una cargaalineador; memoria GPU pendiente |
| Alineación independiente180s hastaM3 | Conforme al ADR0031; descriptor y rechazo181s, no sustituye el requisito completo deM3 |
| Clasificación idioma/audio inválidos | B-INPUT-01 corregido CPU; worker INVALID_PARAMS sin ocultar INTERNAL/VRAM_EXCEEDED |
| Comandos del README | A-T08-DOC-01 corregido; README69/79 y Compose2 usanfix2 |
| CLAP01/02, loaders y recursos | ConformidadesCPU anteriores conservadas, sin nueva evidencia que las reabra |
| Alcance, constitución y documentación | Conformes;20SHAfuentes y36evidencias; ADR0031/contrato/README actualizados |
| TDD y cobertura | Cinco RED reales,45CPU verdes,346/382=90,58 % mínimo88,89 %; no sustituye requisitos |
| Seguridad introducida/reabierta | C sin hallazgos, probesHTTP/AST/lock; no auditoría universal |
| Generados/interop/OpenAPI | N/a: sin cambios en esas piezas |
| Verificación completa, QA y cierre | No acreditados todavía: tres inferenciasGPU y QA pendientes; todos los CA abiertos |

## Gaps y evidencia propia

CeroCritical/Important/Minor. Los tres Important de intento2 se corrigen en alcanceCPU; no hay rebates/deuda ni reapertura de conformidades previas. Esto permite QA, no cierraT08 ni acredita inferencia/precisión.

A leyó diff por archivos y verificó20SHAfuentes+36evidencias, AST14Python, XML RED/GREEN/cobertura y gitdiffcheckexit0. CA explícitamente abiertos y límitesGPU honestos; README/Composefix2 y ADR0031 coherentes. No repitió suites para tapar evidencia.

B verificó20SHA+36evidencias y ejecutó imagen306e3b0 con networknone/CUDAoculto: `python -m pytest tests/test_segments.py -q`,12passed5,06s exit0, sólo lockreadonly montado/sin pesos. Primer ensayo sinlock:11passed/1FileNotFoundError, resuelto montando lock; consulta upstream parse inexistente corregida a parse_timestamp. Leído upstreamreal transcribe/align/parse_timestamp/merge_languages. Parser real y cómputo doble acreditan rango/consumo/errores, no precisión con pesos.

C verificó20SHA+36evidencias, ocho fuentes modificadas, AST14Python sin eval/exec/pickle/torch.load y lock111paquetes/512artefactosHTTPS+SHA/3Git fijados. `.eval()` son métodos de modelos. ProbesHTTP en memoria: token ausente/incorrecto401/válido200; segments externo/idioma inválido/traversal/absoluta/URL→422INVALID_PARAMS antes del backend; PARENT_TORCH=False/CHILD_ALIVE=False. Sin escrituras, Docker, GPU, pesos, red ni repetir suites.

No se revisaron T16/T09 ni journals ajenos. Jira/Confluence desactivados. Root corroboró de nuevo las fuentes/evidencias sin mutaciones. Siguiente: QA independiente sinUI por diseño; GPU sólo bajo nuevo preflight normal y un modelo residente. No se promueve conocimiento ajeno. M0 y objetivo completo siguen abiertos.
