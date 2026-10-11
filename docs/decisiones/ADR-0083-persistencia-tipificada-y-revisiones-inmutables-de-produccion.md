---
id: ADR-0083
titulo: Persistencia aditiva tipada y revisiones inmutables de producción
estado: aceptada
fecha: 2026-10-11
decision: D-03
opcion_elegida: PD-O1
autoridad_de_eleccion: ROOT bajo delegación vigente; 2026-10-11T19:28:24.366015+00:00
namespace: candidato sin número; pendiente revisión/QA/adopción ROOT
---

# ADR candidato — persistencia de producción y revisiones

## Contexto

ADR-0080 fija derivados sobre cola job/job_dependency y ADR-0082 fija ProductionRequest1/Recipe1 privados,19parejas/7sujetos, CAS y recibos discriminados. El baseline Analysis tiene UNIQUE(take_id,kind,analyzer_id), analyzer_version fuera; Asset no admite job/analysis/import/backup. Los snapshots/planes M1/M2 y manifiestos v1/v2 conservan bytes/semántica originales. ADR-0074 limita sus reconstrucciones a3tablas CPU, sin permiso análogo para Analysis/Asset/Preset.

Se compararon PD-O1 y PD-O2 en la primera pasada preservada SHA428b5cecdbde017ce5616a7c139e4cec6a81674e177e58011398deb668a91cd4. ROOT eligió PD-O1 mediante choice-root.receipt.json SHAc0c651cee5b4a0eaa58fa02ac3a9a081a6dad49cfe3dbd6cd6a44b7e54495ea1 bajo delegación vigente. No se atribuye ratificación personal de cada fila al propietario.

## Decisión propuesta

Añadir40tablas m3_* con relaciones tipadas, capturas canónicas privadas cerradas, roots/children append-only y sello único antes de consumo. Guards SQL directos forward/inverse fijan pertenencia, estados, referencias, DAG, revisiones y CAS. Results/receipts tienen siete sujetos independientes; preview sigue temporal, import/backup mantienen scope/autoridad propia sin Take/Asset fake. El contrato completo se adoptará en `docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/production-data-contract.md` y un apéndice aditivo en `docs/arquitectura/datos.md`.

El FIX1 documental B01 seleccionado por ROOT reserva `seal_kind` en los11schemas internos nuevos: su valor es m3_seal.kind, mientras root.kind conserva íntegro su enum SQL. El payload exacto incluye root/H/NULLs/rows ordenadas, seal_kind y schema_version1, con namespace reservado disjunto de las40tablas/header capture, parsing sin duplicates, extras, gaps, overwrite ni fallback. G02/G09 comparan reader/family/version, SQL, bytes canónicos y hash del payload completo; hashes de fuente/evidencia y refs históricas conservan su dominio. Se aplica a todas las familias internas, no sólo audio; request/recipe/receipt D-02 y otros schemas originales/históricos no reciben seal_kind. La fuente anterior no adoptada sigue preservada: no versión legacy fabricada ni renombre SQL, reescritura histórica o nueva alternativa a PD-O1.

MixRevision conserva4stems/controles y no modifica audio. LyricsTimingRevision conserva resultado inicial, tokens/texto/single-composite/bindings/audio medido/hash/duración, con tiempos y procedencia de corrección nuevos. PresetRevision congela valores y refs efectivas de cada edición/uso. Resultados por método nuevos viven fuera del UNIQUE Analysis original, sin overwrite ni analyzer ficticio.

Reservation revision1 se confirma con evidencia reserved existente antes de efectos; no requiere ni inventa receipt succeeded. Nuevas fases tienen evidence propia y CAS del cursor/estado/identidad completos. Terminales raw/CPU/upload no son publicación; entidades/results/receipt final son commit SQLite indivisible, FS tiene recovery separado. Commit durable prevalece ante cancel tardío/ACK perdido; UNKNOWN bloquea efectos/serving/cleanup/liberación hasta reconciliación.

Upgrade es aditivo tras head0007 del corte revalidado y ventana propia exclusiva; no reconstruye Analysis/Asset/Preset ni modifica0001–0007. Sin backfill ficticio. Downgrade vacío guardado antes de efectos; con datos conserva historia/readers o restaura corte completo inerte mediante activación D-09. Readers de perfiles/formatos futuros son gates cerrados, no catch-all ni defaults. /v1, DTO/schema M1, histórico y ADR-0074 permanecen intactos.

## Alternativas descartadas

- PD-O2: documentos tipados versionados con índices y lectores SQL. Viable, menor DDL y coste relativo M, pero más dependencia de registro por conexión y duplicación de identidad en columnas/documento. PD-O1 cuesta L y más DDL; aporta relaciones explícitas que responden mejor a pertenencia, bindings y fases.
- Modificar UNIQUE/data de Analysis, añadir Asset.subject_type job/analysis/import/backup, fabricar Take/JobAttempt/seed para sujetos CPU/biblioteca o sesión agregada: contradicen baseline/ADR-0074/0080/0082 y no se adoptan.

## Consecuencias y límites

Aumenta el número de tablas y guards; la implementación debe expandir íntegra la matriz, probar SQL directo, migraciones, readers por conexión, race/cancel/replay y rollback. Todas las fuentes/historia se conservan, con head separado de revisión inmutable. Las conexiones sin reader/guards fallan cerradas; privilegios administrativos de SQLite no se confunden con el boundary del server autenticado.

La fuente sigue propuesta seleccionada hasta revisión/QA/adopción ROOT. No hay DDL/código/DB/runtime ejecutado ni T-03 cerrada por esta entrega; funciones M3 implementadas0. D-04/05/06/07/08/09/11 y releases de plataforma D-12 permanecen gates propios. El inventario99 de fuentes es snapshot readonly; cualquier overlay K2/M2 y head futuro se revalida al handoff del implementador.

## Verificación requerida

PD-01..PD-20 en el contrato, criterios CA-02/08/18/20/34/48 y E2E-02/08/18/20/34/M-48 del plan. ROOT reserva ADR, completa índice/enlaces y adopta junto a contrato/apéndice sólo tras revisión/QA. El sello/hash documental no certifica mediciones, derechos, custodia, inferencia ni conformidad audiovisual.


## Reserva administrativa ROOT para revisión2 — 2026-10-11T20:22:01.002729+00:00

ID0083 reservado en revisión privada anterior, no canon/adopción. FuenteFIX1ca094b15 yoriginalf982 intactos. MetadataROOT no cambia decisionesnormativas; [contratoD03](../roadmap/2026-10-11-m3-produccion-portada-video-letra/production-data-contract.md) y apéndice quedancondicionados areviewQAadopción. CampoJSONseal_kind separadodekindroot; formatosD02/históricosSQL intactos. T03/M3abiertos, no ejecuciónproducto.


## Ratificación ROOT — 2026-10-11T20:57:46.782766+00:00

PD-O1 queda aceptada documentalmente tras revisión2 sin defectos y QA579/579. El discriminante seal_kind del sello conserva el kind propio del root. No cambia los contratos históricos ni amplía ADR0074. La migración y los lectores reales pertenecen a las tareas de implementación posteriores.
