---
id: ADR-0087
estado: aceptada
fecha: 2026-10-12
---

# ADR — Cohortes independientes y aceptación por canción/método

Estado: propuesta; número final reservado únicamente por ROOT después revisión. Fecha:2026-10-12. Autoridad: ROOT bajo delegación; esta entrega no adopta ni edita canon.

Contexto: ADR0080/O1 y D02–D05 requieren resultados musicales/visuales vinculados a audio/contexto inmutables; ninguna etiqueta textual, fixture o porcentaje prueba utilidad o conformidad real. D06 tenía cifras parciales de timings/beats; D13 necesitaba fuentes/personas independientes y derechos. T06 incluye instrumento de cobertura strict-phase.

Decisión recomendada: CM-O1, schemas/readers/métodos/casos de este contrato versión1, dos anotadores ciegos y árbitro, aceptación whole por canción/método, errores de palabras y unmatched separados, rubrica completa prefreeze, evidencia por categoría y rights específicos. Performance propuesto N0 max600s/4×duración por perfil completo y recursos libre−1,5GiB; selección/ratificación numérica y pins finales permanecen ROOT. D05 loudness exacto conserva targets y precisión; ningún reader histórico/SQL envelope se amplía. Gate coverage whole ≥80 sin rounding/exclusiones/missing con raw oficial/source freeze/receipts y exits0/1/2 del ledger. Ratings humanos enteros1..5 usan unit=rating, mínimo4 intacto; score/ratio conservan0..1. La cadena acíclica A/F/I/E0/R/outputs/E/C/P/V de §8.2.1 usa SHA de bytes completos y custodia/ejecución ROOT independientes, sin hashes mutuos ni autorreferencias; registro posterior P contiene R, nunca I. Esquemas de aprobación/ejecución se proponen antes de gate code, sin ampliar readers/DTO/SQL históricos.

Alternativas: CM-O2 revisión100% con un anotador; CM-O3 límites más estrictos; performance CM-P2/P3. Coste de adquisición humano mayor en O1, riesgo de falta de material/personas explicitado. Reversible por nueva versión/SHA con nueva evaluación, sin editar resultados pasados.

Consecuencias: no conformidad musical por documentación; métodos dependientes esperan ratificación, product-real espera D13 y capacidades/liberaciones D10/D11/D12. T06 no cierra hasta gate code causal/review/QA y Verificación ejecutada. Material y personas no inventados; original Libro/Libre, audio y consent no se extienden desde un MP3 o declaración de letra. Canon v1/CPUv2/timeline/engine unchanged. No nueva herramienta, licencia, peso, servicio o almacenamiento fuera proyecto.

Validación futura: negativos A01 y A02/B01 y construcción escalar materializable acíclica de§8.2.1, todos los15 casos contractuales de§8.4, TDD causal del gate, raw coverage official completowhole, A/B y QA por SHA; después anotaciones reales y runs/métricas/actas independientes sobre canciones completas, incluyendo Libre4:15 y recovery real. La adopción documental no da pass a esos gates.


## Ratificación ROOT de criterios — 2026-10-12T13:23:49.279192+00:00

ROOT elige CM-O1 y CM-P1 bajo la delegación del usuario para implementar todo el roadmap y escoger alternativas. Se ratifican **todos** los métodos, unidades, fórmulas, límites, políticas de evidencia, recursos, rendimiento, comparación y recuperación de §§4–8 del contrato versión1 fuente6cc06770734a9a8287a10c2a00fcaacc226eca2eb255c1b31f5df7f40b70c680 (99562bytes), sin elegir umbrales desde resultados. CM-O2 introduce anclaje y CM-O3 endurece límites sin necesidad demostrada; CM-O1 mantiene dos anotadores independientes y árbitro. CM-P1 conserva el objetivo de minutos para canciones completas en la5070 y medición real por perfil; no se amplía un límite para aparentar cumplimiento.

Entre los valores ratificados: palabras onset/offset mediana≤0,100s/P95≤0,250s separados, precisión/recall≥0,95 y omisiones/repeticiones/unmatched explícitos; beats±0,070s/F1≥0,90; keytonic+mode≥0,90 por duración/frame; boundariesinterioressections±1s/F1≥0,85 ylabels≥0,85. Ratinghumanoentero1..5/min4 por todasobservaciones requeridas,0defectosmajor/critical; ausencias son indeterminate. D05 conserva sus metas LUFS/TP/precisión/EOF. Se mantienen P1floor600s/multiplier4×duración por perfilcompleto, frío+2warm; BF16/libre−1,5GiB/unmodeloVRAM/unload/spill/RAM con medición real, parejas≥8/3revisores/≥2de3porpar y nivel−23±0,2LU/sinlimitador. El contrato fija el resto de parámetros y dominios exactamente; esta lista no los sustituye.

Coverage se mide whole por cada módulo cambiado≥80 con líneas/branches/statements aplicables y rawoficial/sourceinventories/configs/ejecución-custodiaROOT reales; nunca promedio/helperexit/ASTrecompilado/fixtureperfecto. La cadena A/F/I/E0/R/outputs/E/C/P/V mantiene hashes de bytes completos y aristas sólo a artefactos anteriores. Esta ratificación normativa no instancia autoridad de ejecución del instrumento ni concede éxito musical.

Revisión2FULLA/B independiente corrigió A01rating y A02/B01cicloSHA;0Critical/Important y1MinorA03proveniencia. QA independiente287/287,26payloads/143pins/61supports/213readinputs auditadosROOT. La conservación de9cuerpos/15casos se verificó tras CRLF→LF exclusivamente para comparar texto; sourceSHA ytodosartifact/DAG siguen fullbyte. No se ejecutaron música/SDK/GPU/UI/FFmpeg/coberturaproductiva en estaQA.

**Nota de procedencia A03:** CM522 describe la instantánea readonly del workerFIX1 anterior a la derivación ROOT. Los derivados de este registro sí están regenerados y aceptados, como acreditan los hashes finales de ROOT. El contrato se conserva6cc06770 byteexacto para no atribuir revisión/QA a otra fuente; su frontmatterpropuesta refleja ese candidato histórico, y este ADR registra la adopción vigente. Personas/material/anotaciones/actas/D13 y pinsde métodos concretos se adquirirán antes de su evaluación real, nunca se inventan.

T06 sigue en progreso: falta instrumentoactual/TDD/raw80whole/revisiónQA/Verificación completa y adquisiciónD13; no se cierraFase1/M3/M0–M5. Esta decisión habilita implementación técnica de ese instrumento sin esperar conformidad musical, conservando todos los gates de producto.
