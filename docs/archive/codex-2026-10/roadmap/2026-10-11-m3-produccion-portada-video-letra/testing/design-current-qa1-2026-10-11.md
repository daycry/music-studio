# QA documental independiente — arquitectura M3

Fecha UTC: 2026-10-11T14:57:53.393375+00:00

**DONE_WITH_CONCERNS · VERDE documental: 175/175 checks, 0 fallos finales; qa-gate exit 0. M3 sigue pendiente de implementación y aceptación.**

La entrada es el snapshot readonly de 48 fuentes únicas del recibo ROOT. Se auditó O1, derivados tipados y escena N0 compartida offline. Requisitos aprobados: 49 CA sin marcar y 14 funciones obligatorias. Arquitectura aprobada bajo delegación, ADR-0080 propuesta y adopción canónica pendiente son estados distintos. El Minor textual de la spec está corregido en esta copia; revisión A/B antecedente: 0 Critical, 0 Important, 1 Minor corregido. No se atribuye revisión personal al propietario.

El runner ejecuta comprobaciones documentales reales. Adapta sus resultados individuales al esquema que acepta el gate oficial; **no ejecuta Playwright, pytest, E2E ni cobertura de código**. No existe plan/ledger M3 todavía: ledger-lint y coverage-check M3 no aplican a esta etapa arquitectónica. No se inventó tasks.md, task-brief ni una exención “sin UI”. El plan futuro debe incluir UI y test-plan con cada GWT 1:1.

## Gate oficial

```json
{
  "verdict": "VERDE",
  "counts": {
    "passed": 175,
    "failed": 0,
    "flaky": 0,
    "skipped": 0,
    "interrupted": 0
  },
  "flaky_sin_justificar": [],
  "flaky_justificados": {},
  "threshold": "verde ⟺ 0 failed, 0 flaky sin justificar, 0 interrumpidos y ≥1 test ejecutado"
}
```

[Checks completos](../../../../.cache/dev-cycle/m3/production-design-current-qa1-20261011/document-checks.json) · [Entrada adaptada](../../../../.cache/dev-cycle/m3/production-design-current-qa1-20261011/documentary-gate-input.json) · [Recibo de gate](../../../../.cache/dev-cycle/m3/production-design-current-qa1-20261011/qa-gate.receipt.json) · [Recibo de ejecución](../../../../.cache/dev-cycle/m3/production-design-current-qa1-20261011/document-run.receipt.json). Porcentajes unitarios y E2E: n/a; 175 checks documentales no son cobertura de producto.

## Integridad, enlaces y entorno

Las 48 fuentes coincidieron con sus pins al inicio y al final; no se escribió el snapshot. [Antes](../../../../.cache/dev-cycle/m3/production-design-current-qa1-20261011/sources-before.json) y [después](../../../../.cache/dev-cycle/m3/production-design-current-qa1-20261011/sources-after.json). Se comprobaron 39 enlaces locales de spec, diseño y ADR, desde su destino canónico futuro; las fuentes presentes en snapshot tienen prioridad y el resto usa fallback canónico readonly. [Resoluciones y SHA](../../../../.cache/dev-cycle/m3/production-design-current-qa1-20261011/links.json). Las tres referencias web son bibliográficas: no se consultó red ni se atribuyó verificación runtime a sus primitivas. Frontmatters y estados son coherentes; índice conserva ADR-0079 y añade ADR-0080.

Python gestionado 3.12, scripts/env.ps1 y uv --frozen --no-sync --all-packages. No Git, SQL, operación de datos, GPU/Ollama, Docker, servicios, privilegios ni instalaciones. La única ejecución de browser prevista es un hijo propio de Edge headless para exportar este informe, con perfil dentro del namespace QA; no navegador ni renderer de producto. Sus dependencias existentes permanecen readonly.

Divergencias canónicas durante la ventana de comprobación: 1. Se registran en canonical-delta.json y pertenecen a trabajo concurrente; no se restauraron. Las diferencias ya existentes entre canon y candidato son propuestas privadas, no adopción. ROOT debe contrastar canon fresco antes de adoptar.

## Diagnóstico preservado

El primer harness obtuvo 174/175, gate exit 1: buscaba el literal “sin detener servicio”, mientras el ADR dice “No detiene el servicio ni borra modelos”. Se corrigió únicamente el selector documental para comprobar la prohibición normativa real; ninguna fuente ni requisito cambió. [Original](../../../../.cache/dev-cycle/m3/production-design-current-qa1-20261011/diagnostic-attempt1/document-checks.json) y [gate rojo original](../../../../.cache/dev-cycle/m3/production-design-current-qa1-20261011/diagnostic-attempt1/qa-gate.stdout) quedan intactos. No es un flaky de producto ni justificación para ocultar un fallo.

## Decisiones verificadas y límites

| Frontera | Evidencia documental observada |
|---|---|
| Authority / queue / Docker / shared Ollama | único escritor SQLite; GPU1/CPU2; engines Docker; Ollama es un servicio compartido externo |
| Immutable song/take/master / CPU lineage | takes inmutables; todos sus antecedentes; maestro sólo cambia; sin modelo ni seed inventados |
| Closed script/workflow boundary | scripts, expresiones FFmpeg o workflows Comfy arbitrarios; Workflows cerrados; bundle cerrado y local |
| Mix mute solo precedence / shared transport | Mute prevalece sobre solo; transporte y origen temporal; no se sustituyen stems por cuatro elementos audio |
| Final loudness and no silent limiter | −14/−23/−16; archivo final decodificado; No activa limitador; política de tratamiento antes |
| Alignment revision / global offsets / no truncation | LyricsTimingRevision; offsets globales; no cambia audio; 180s no se usa como truncación |
| N0 time / audio clock / final audio features | time_s; frame_index / fps; reloj de audio; audio final elegido; Seek recomputa |
| Full song / human / runtime budget | Libre4:15; antes de medir; lector independiente; escucha humana |
| Comfy own child / safe pins / real generation ref | proceso hijo propietario; nodos/weights/commits quedan fijados; gates distintos; pesos/formato/licencia/pins |
| Safe candidate gates keep functionality mandatory | Las 14 funciones son obligatorias; Scope permanece obligatorio; no se elige checkpoint; gate abierto identifica trabajo obligatorio |
| Compatibility historical versions / CPU no fake inference | v1/v2 históricos; No usarlo para export/render/upload CPU con identidades de inferencia inventadas; no añade mix/render/export a CreativeRequestV1; TimelineV2 |
| Whole chain publication / UNKNOWN | ext4/UUID; NOREPLACE; CAS; UNKNOWN bloquea; sin regenerarlo |
| Portable staging closure / collisions / inert authority | staging; colisión; sin reescribir; jobs/leases |
| Backup exclusive WAL/assets / rollback | mantenimiento exclusivo; WAL+assets; sin writer abierto; backup restaurable; rollback |
| Single model / free VRAM margin / no service stop | un modelo residente; libre−margen; No detiene el servicio ni borra modelos; restauración propia |
| Contracts concretions precede RED / proposals not ratified | D02–D04/D08–D09; previos al RED; permanecen propuestas pendientes; esta elección no los ratifica |

La inspección semántica mantuvo consecuencia funcional, no sólo rechazo: export final conforme sigue obligatorio aunque la política de ganancia lineal pueda fallar; calidad alta/F19/stems/Comfy deben integrarse y probarse, no cerrarse por deshabilitación; N0 debe producir canciones completas reactivas y legibles, no cerrar por un benchmark corto; import/backup deben recuperar contenido real, no cerrar por negativos de seguridad. D02–D04/D08–D09 son tareas contractuales previas al RED dependiente. D05–D11 contienen métricas, pins y candidatos aún por ratificar: O1 no los aprobó.

## Las 14 funciones conservadas

| Función | O1 | O2 comparada | CA | Evidencia futura |
|---|---|---|---|---|
| F-06 | Handler portable/import y cierre | Export de revisión con mismo cierre | 36–39,44,48 | Roundtrip real multiversión; negativos ZIP; reproducción |
| F-18 | Compositor de regeneración de calidad | Etapa musical de documento | 32–33,46 | Modo M0 real y escucha emparejada |
| F-19 | Upload+compositor musical tipado | Entrada musical de revisión | 04–05,30–31,46 | Ruta real de producto y escucha propia |
| F-30 | Job audio.stems→assets del take | Etapa stems reutilizable | 06–07,46 | Muestras/suma y separador/escucha real |
| F-31 | MixRevision, transporte, export CPU | Mezcla capturada en revisión | 08–10 | Mute/solo/sync; comparación exportada y escucha |
| F-32 | Handlers export por perfil | Destinos dentro de revisión | 11–14,48 | FFmpeg final, lector independiente y ZIP |
| F-33 | Jobs por método y resultados parciales | Checkpoints de análisis por método | 15–17 | Contraste independiente sobre audio real |
| F-34 | LyricsTimingRevision/karaoke/export texto | Revisión temporal vinculada al documento | 18–21 | Anotación cantada castellana y corrección/seek |
| F-35 | Engine-comfy→Artwork→elección | Etapa portada y elección explícita | 22–25 | Generar/editar realmente, varias opciones y revisión visual |
| F-40 | Plan de escena→renderer offline→Render | Documento→ruta web capturada→Render | 26,28–29,44 | Canción completa, sincronía/legibilidad/perfil y recovery |
| F-41 | Features+escena temporal compartida | Features consumidas por ruta congelada | 27–29 | Onda/espectro/partículas, silencio y seek real |
| F-44c | Upload→Artwork/fondo autorizado | Fuente subida del documento | 04–05,24,26 | Contenido/derechos y render N0 |
| F-70 | Biblioteca preset→captura por acción | Biblioteca→valores congelados por revisión | 34–35,36,41 | Historia conserva refs/valores tras editar/importar |
| F-85 | Mantenimiento exclusivo/corte/restore nuevo | Mismo corte, con documentos adicionales | 40–43,45 | WAL+medios coherentes, biblioteca real y rollback |

## Los 49 destinos arquitectónicos

| CA | Destino | Evidencia futura obligatoria |
|---|---|---|
| CA-01 | Gate de aceptación | Cierre canónico M2 y heredados; mock no lo sustituye |
| CA-02 | Captura/contexto | Cambiar maestro/revisiones tras iniciar no retargetea |
| CA-03 | Resolver/capability gate | Tarea/feature no verificada rechaza antes de carga/envío |
| CA-04 | Admisión y derechos | Faltan declaración/consentimiento: rechazo sin eco privado |
| CA-05 | Upload/resolver | Malformado/oversize/hash/ajeno: rechazo sin conversión oculta |
| CA-06 | Publisher stems | Cuatro assets del take, sin toma nueva ni cambio maestro |
| CA-07 | Conformidad stems | Muestras alineadas, error<−30dB y escucha real |
| CA-08 | MixRevision/Web Audio | Mute/solo/volumen/silencio y recarga sin alterar fuentes |
| CA-09 | Handler mezcla/publicación CPU | Ganancias/sources efectivos; hijo con todos los padres cuando aplica |
| CA-10 | Preview/export mixer | Sincronía/niveles/silencio/clipping/saltos y escucha humana |
| CA-11 | Handler export/medidor | Archivo final decodificado cumple LUFS/TP/formato/bits/tasa |
| CA-12 | Original/ZIP stems | Bytes originales;48kHz/amplitud/alineación/hashes de todas las pistas |
| CA-13 | Metadata writer/reader | Lector independiente recupera take/portada/letra histórica solicitada |
| CA-14 | Terminal export | Objetivo fallido no se anuncia conforme; conserva original/evidencia |
| CA-15 | Compositor análisis/resultados | Todas las familias ligadas al audio/método/contexto y visibles para N0 |
| CA-16 | Estados por método | Ausentes/inciertos explican motivo y no ocultan válidos |
| CA-17 | Conformidad análisis | Loudness/anotaciones independientes; etiquetas no fingen medida |
| CA-18 | Binding de alineación | Single/composite/version/hash sobreviven cambio de letra vigente |
| CA-19 | Karaoke/LRC/SRT | Seek/pausa/revisión; parseo y tiempos finitos ordenados en duración |
| CA-20 | Revisión temporal | Incertidumbre/omisión/instrumental y corrección sin reescribir evidencia |
| CA-21 | Gate de alineación real | Canto castellano, omisiones/repeticiones/silencios, anotación y escucha |
| CA-22 | Comfy generación/Artwork | Varias opciones con pins/semillas; elección explícita de portada |
| CA-23 | Comfy edit/referencia | Nueva imagen, antecedentes/derechos y anterior preservada |
| CA-24 | Upload→Artwork/fondo | source upload/procedencia, sin habilitar generación ni I2V |
| CA-25 | Gate Comfy real | Docker/CUDA/generación+ref/seguridad/VRAM/RAM/unload/revisión visual |
| CA-26 | Scene/Timeline/TimingRevision | Palabra sincronizada, take/audio correcto e incertidumbre visible |
| CA-27 | Features y escena reactiva | Onda/espectro/partículas responden a audio/seek/silencio |
| CA-28 | Renderer/FFmpeg/producto | Decodificar canción completa; fps/res/duración/audio/sync/legibilidad y dos reproductores |
| CA-29 | Benchmark N0 | Canción representativa5070 y recursos/tiempo frente a objetivo prefijado |
| CA-30 | Upload+compositor musical | Capacidad real/roles/derechos; hijo y maestro intacto |
| CA-31 | Gate audio propio | Ruta producto y escucha de motivo/estructura/acompañamiento/artefactos |
| CA-32 | Selector calidad alta | Sólo perfil M0 validado y valores efectivos; ausente deshabilitado |
| CA-33 | Gate mejora musical | Pareja misma metadata/texto, niveles igualados y GPU/RAM/escucha |
| CA-34 | Preset/captura | Uso congela valores y referencias, edit posterior no altera historia |
| CA-35 | Preset/admisión | Ref ausente/permisos/param incompatibles rechazan sin omitir ni simular |
| CA-36 | Cierre portable/lectores | Roundtrip completo inferencia+CPU/letras/maps/master/presets/medios/rights |
| CA-37 | Import sandbox/catalog | Traversal/enlaces/duplicates/case/bomba/version/hash/ausente/ajeno sin promoción parcial |
| CA-38 | Import intent/CAS | Colisión/replay/concurrencia/remapeo explícito sin sobrescritura/mezcla |
| CA-39 | Filtro portable privado | Sin claves/paths/PIDs/leases; letra/fotos necesarias sólo payload privado |
| CA-40 | Mantenimiento/corte biblioteca | WAL+assets/referencias,integridad/FK/FTS/catálogo/locks/hashes |
| CA-41 | Restore nuevo/reconciliación | Biblioteca/búsqueda/reproducción, jobs inertes y dependencias faltantes diferenciadas |
| CA-42 | Backup/restore/activation intent | Fallo/cancel/disco/corrupción preserva copia válida/original y rollback |
| CA-43 | Ejercicio real de recuperación | Copia/cohorte autorizada,before/after,restore nuevo; activar con backup+exclusividad |
| CA-44 | Recovery por frontera | Cancel/acuse/restart raw/post/rename/commit/render/import/backup sin duplicar/parciales |
| CA-45 | Storage gate compartido | Ext4/UUID/NOREPLACE/CAS/replay/restart reales; wrong backend aborta |
| CA-46 | Coordinador/GPU/Ollama | Una residencia,cap libre−margen,picos/RAM/spill/unload y restauración propia |
| CA-47 | Offline/privacidad/eventos | Sin Internet/claves externas/runtime-download/eco privado ni progreso ficticio |
| CA-48 | Manifest/DTO/compatibilidad | Origen/hashes/rights/conjunción,v1/v2 intactos y cambios decididos antes de migrar |
| CA-49 | Matriz de aceptación | CPU,fixture,E2E,FFmpeg/ext4,GPU,browser y humanos registrados separadamente |

Los textos normativos completos de los 49 CA están conservados en document-checks.json junto a cada destino y verificación. La tabla anterior resume arquitectura; no sustituye dichos requisitos ni acredita ejecución.

## Checklist pendiente para plan y producto

- [ ] ROOT adopta documentalmente tras verificar hashes, canon vigente y estados; no cierra M3.
- [ ] Planner conserva 49 CA/14 funciones y cada GWT en test-plan E2E 1:1; incluye concreción de contratos, SQL aditivo, Timeline/manifiestos históricos, límites ZIP y journal/binding/quiesce antes del RED dependiente.
- [ ] Concretar y ratificar métricas/cohortes, perfiles N0, fonts/browser/FFmpeg/codec/pins/licencias; no confundir browser de QA con herramienta aprobada de producto.
- [ ] Gates reales M0/M1/M2 y M3: RTX5070/picos RAM/VRAM/unload y turno Ollama; Docker/ext4/UUID/CAS/NOREPLACE/restart y UNKNOWN; engine-comfy generación/ref en hijo propio; pesos seguros y licencias.
- [ ] Probar stems por muestras y escucha; mixer Web Audio transporte común/mute/solo/offsets y export reproducible; medir audio final decodificado y verificar metadatos con lector independiente.
- [ ] Alinear canto castellano y fragmentos históricos single/composite con anotación humana; correcciones inmutables, incertidumbre, karaoke/seek/LRC/SRT y material largo sin truncar.
- [ ] Reproducir/renderizar canción completa, incluida Libre4:15: onda/espectro/partículas ligadas a audio final/silencio/seek; palabra/pantalla, legibilidad, duración/fps/deriva, dos reproductores y presupuesto real prefijado.
- [ ] Import/backup/restore de biblioteca real autorizada: corte WAL+assets, negativos, collisions/replay, jobs inertes, cierre multiversión, reproducción/búsqueda y activación/rollback atomic con originales before/after.
- [ ] Experiencia de navegador y revisión visual/escucha humana propias para portada, F19/calidad alta, mezcla, N0 y recuperación; conservar evidencia separada de CPU/mock/E2E sintético.

## PDF y portabilidad

Se aplica custom-agents:to-pdf con renderer local derivado del script existente y tool-cache del repositorio; no se instala nada. PDF y preview HTML en modo print se verifican estructuralmente y visualmente. **Limitación: no se rasteriza el PDF final por falta de rasterizador local confirmado; la preview HTML no acredita todas sus páginas.** No se presenta el PDF como revisión visual completa. El informe y sus evidencias usan enlaces relativos al namespace, transportables juntos; el manifiesto final enumera artefactos y SHA y excluye su autorreferencia y cachés desechables explícitamente.

Entrega documental a ROOT. No handoff a documenter, estado implementada/completado ni aceptación de M3 por QA de prosa. El siguiente paso es adopción documental y planificación manteniendo todos los gates.


## Ratificación de ROOT — 2026-10-11T15:01:22.398925+00:00

ROOT88payloads/48sources/175checks/39links/streams/recibos/QA0 comprobados; MinorA01estado corregido en candidato. DiseñoO1/ADR0080 adoptados, plan siguiente. PDF8páginas estructural+printpreviewinspeccionado, sin rasterizaciónfinal; no producto ni aceptaciónM3.
