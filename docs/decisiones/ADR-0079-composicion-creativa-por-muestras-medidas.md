---
id: ADR-0079
titulo: Composición creativa por muestras medidas
estado: aceptada
fecha: 2026-10-11
iniciativa: m2-iteracion-creativa
design: ../roadmap/2026-10-10-m2-iteracion-creativa/composition-contract-design.md
destino_propuesto: docs/decisiones/ADR-0079-composicion-creativa-por-muestras-medidas.md
opcion_elegida: O1
autoridad_eleccion: ROOT bajo delegación vigente del propietario; 2026-10-11T13:43:01.014657+00:00
revision_contrato: pendiente de revisión documental y QA; incorporación por ROOT
namespace: propuesta privada, no ADR canónico reservado por el actor
model_tier:
  agente: architect
  model: opus
  effort: high
  fuente: recibo ROOT; no afirma modelo ejecutado
generacion:
  fuente: estimado
  tokens_reales: null
  eur: null
  horas_ia: null
  nota: Prosa sin estimación de consumo; marcador sólo ROOT.
---

# ADR-0079 — Composición creativa por muestras medidas

## Contexto

[ADR-0077](ADR-0077-envelope-privado-de-recetas-creativas.md) fija el envelope privado y las ocho operaciones de T02. La receta guarda intención `requested_seconds`, muestreo round-half-up/rangos semiabiertos, padres, roles, raíces, herramientas y selection del adapter. No contiene un mapa efectivo de audio ni autoridad de ejecución. [ADR-0073](ADR-0073-recetas-privadas-y-escucha-ab-de-iteracion-creativa.md) y [ADR-0074](ADR-0074-procedencia-cpu-y-contratos-versionados.md) separan CPU autónomo de inferencia y conservan sus autoridades/lectores históricos.

T03 debe resolver índices una vez y describir una construcción pura. La duración real de un engine puede diferir del request y de la región reemplazada. Un adapter puede entregar salida full o region; ensamblar ambas interpretaciones duplica audio. Rate/canales distintos exigen conversión declarada, con frames medidos después de convertir. Las aristas deben conservar ambos padres de crossfade, con raíces originales conforme [ADR-0041](ADR-0041-esquema-inicial-y-snapshots-del-server.md).

ROOT eligió O1 y ratificó sus políticas mediante recibo privado de selección el 2026-10-11. Este ADR sigue en propuesta hasta revisión documental/QA e incorporación por ROOT; no acredita implementación o aceptación T03/M2 ni decisión personal de lectura del propietario.

## Decisión propuesta

Adoptar [O1: plan cerrado sobre hechos medidos](../roadmap/2026-10-10-m2-iteracion-creativa/composition-contract-design.md). T03 implementará sólo DTO/validación/build/readers y funciones puras CPU, sin I/O, FFmpeg, GPU, SQL, jobs/takes, custodia o publicación. El caller aporta identidades/hashes/evidencias y facts medidos, y prueba su asociación real con masters o resultado del engine.

1. `BufferFacts.duration_s` es exactamente `float(frames/sample_rate)`. Los snapshots nuevos de master provienen de medición real, nunca de duration solicitada. Incoherencia de una receta sellada se rechaza; no se reescribe historia T02/M1.
2. Un preflight puro declara conversiones necesarias sin resolver muestras. El caller convierte el buffer completo, lo mide y aporta facts propios antes del cierre. No se estiman frames por ratio de rates. Crossfade target es A; extend/repaint target es padre; trim/fade conserva formato padre. Mono→stereo duplica; stereo→mono promedia; soxr se fija mediante pin existente de FFmpeg. Sin filtros arbitrarios ni normalización implícita.
3. El plan resuelve las primitivas temporales con racional decimal exacto de `repr(float(seconds))` y half-up, una vez por key/grid, anclando extremos reales a 0/N. Destinos se forman por suma de frames ya resueltos. Rechaza tipos coercibles/bools/no finitos/negativos, out-of-bounds, intervalos colapsados, overflow y facts/conversión ausentes. Rampas lineales requieren al menos dos frames; no ajusta duración silenciosamente.
4. Full consume únicamente todo el buffer de construcción engine una vez. Sus keeps representan conservación declarada, pendiente de comparación PCM; no prueba que el engine preservó el prefijo/sufijo. Repaint region ensambla prefijo+G+sufijo; extend region ensambla prefijo+G y descarta sufijo antiguo. Region consume la salida engine local completa: la región/punto global se valida sólo contra el padre. Full repaint exige E>i0+(N-i1); full extend exige E>a, usando counts target. No resuelve segundos globales contra la entrada nativa/local del engine. T08 contrasta keeps y uniones antes de emitir resultado efectivo.
5. Crossfade conserva aristas `crossfade_a/crossfade_b`, coordenadas originales con su rate/canales y destino target, y raíz mínima entre raíces originales acreditadas. Todo tramo convertido aparece como `convert` con efecto explícito. FIX1 propone `src:FrameSpan|null` para fuente literal/conservación declarada, y `nominal_src:NominalFrameRange|null` exclusivamente para B convertido. Ese rango permite igualdad, a diferencia de render/dst estrictamente no vacíos. Cada ConvertedFacts conserva `conversion_scope=[0,input.frames)` no vacío. No atribuye al rango nominal el footprint exacto de soxr ni inventa procedencia.
6. `CompositionPlanV1` es un artefacto privado, cerrado, inmutable, con recipe SHA, facts/evidencias, testigos de resolución, pieces y mapas `resolved_frames`, status `resolved_unrendered`. No es un grafo editable ni el CpuEditPlan durable. La receta y su descriptor/shape siguen idénticos. T08 sólo consume frames del plan; replay del reader verifica determinísticamente sin audio.
7. Receta y plan tienen kind/version/dominio separados y cada SHA identifica sus propios bytes canónicos. No se exige desigualdad universal de hashes; igualdad o desigualdad no acredita autoridad, transformación, ejecución ni custodia. Hashes/evidence refs aportados no sustituyen verificación real del caller ni recibo propio posterior.
8. Reader de composición sólo despacha su kind/version y rechaza extras/versiones desconocidas, duplicados, no canónico y tamper. No reinterpreta PostPlan/planes/recibos M1 ni agrega defaults a historia emitida. Los errores privados exponen sólo códigos/campos sanitizados; integración HTTP sigue siendo de otras unidades.

## Alternativas descartadas

| Alternativa | Complejidad | Riesgo | Coste relativo | Reversibilidad | Motivo |
|---|---|---|---|---|---|
| O2: plan paramétrico; resolución dentro de T08 | Baja en T03, alta en T08 | Alto | M | Media | Desplaza responsabilidad fijada de T03 y retrasa sus rechazos hasta render |
| O3: sólo formatos idénticos | Baja | Medio | S | Alta | No cubre conversiones válidas permitidas por T02 ni todo el alcance T03 |

O1 tiene complejidad Media, riesgo Bajo, coste M, reversibilidad Alta. Su elección responde a hechos medidos, construcción única y preservación explícita de coordenadas/roles. No reabre las decisiones globales de ADR-0073/0074/0077.

## Consecuencias y fronteras

`apps/server/app/creative/composition.py` y su test focal concretarán el contrato elegido antes de integrar. Los 13 controles documentales sintéticos y 18 AC del diseño trazan CA-09/11/13/14/15; no son pruebas de producto ni audio real. T02 se consume sin cambios de receta/schema/bytes. No se introduce una migración, dependencia o licencia por este ADR.

Con A100@10, B160@20, Bc81@10 y D8s, la cola Bc[80,81) ocupa dst[100,101). Su nominal_src es [160,160), src null y scope B[0,160). Se conservan los 81 frames medidos y la dependencia verdadera; la salida tiene101frames. Bc80 omite la cola y produce100; Bc79 se rechaza por D80 fuera de bounds. Nominales fuera de B/invertidos y scopes parciales fallan; el nominal vacío válido no es intervalo de render colapsado.

Repaint global[6,8) sobre padre100@10 puede consumir engine region40@20 convertido20@10: ambos buffers son locales de2s. La composición es60+20+20=100frames. Exigir que esos buffers contengan[6,8) sería mezclar grids; full mantiene sus propios mínimos de construcción.

T08 realizará conversión/medición/render con herramientas realmente verificadas, comparará PCM y true peak, y guardará recibo propio con duration/mapas efectivos vinculados al plan/receta. El crossfade lineal complementario no prueba ausencia de clipping. Las tolerancias PCM24/conversión/true peak ya fijadas en el test-plan conservan sus gates.

T04/T07 concretarán schemas y proyección de `convert` sin degradarlo a keep; el mapa privado no se publica directamente en schema histórico de cuatro ops. T07 definirá autoridad/recibo durable y publicación conforme ADR-0074, con ejecución propia y custodia, sin engine/attempt/model/seed ficticios. T11–T14 aportarán resultado/shape/capacidad verificadas y reutilizarán el builder sin un ensamblador alternativo.

Existe mayor exigencia de medición antes de captura y cierre; una receta stale o medición ausente produce error explícito. El orden preflight→conversión medida→cierre→render hace visible esa dependencia. No habilita una capacidad musical ni modifica maestro/padres.

## Gates antes de incorporar o ejecutar

- Ratificación ROOT de la representación FIX1 de procedencia nominal/scope, revisión documental fresca y QA de contrato sobre diseño/ADR; incorporación canónica sólo ROOT. El número 0079 se propuso tras comprobación de ROOT; este actor no reserva/escribe canon.
- Después del contrato ratificado: RED-GREEN-REFACTOR, verificación focal real, revisión adversarial, QA y cobertura cambiada ≥80% exigidos por el ledger. No adelantar producto RED desde esta propuesta.
- Antes de conversion/render: verificar bytes/pins, licencia vigente y capacidad runtime FFmpeg/soxr. Su presencia en locks y ToolSelection no acredita instalación/licencia ni soporte de filtro. No se ha hecho consulta actual de licencia/red ni ejecución real en esta preparación.
- Antes de publicar: autoridad/recibo/custodia/CAS/versionado/proyección convert propios y probados; conservar lectores y datos M1. Estado UNKNOWN impide fingir resultado listo.
- Antes de aceptación musical/M2: pruebas reales por task, escucha humana y restantes criterios vigentes. CPU/mock/documentación no reemplazan evidencia real.

## Estado

`propuesta` — O1 elegida por ROOT bajo delegación, contrato FIX1 en borrador pendiente de ratificación de representación/revisión/QA. Este actor sólo entrega archivos privados; no aprueba ADR/diseño, no ejecuta producto ni afirma fidelidad/clipping/capacidad real.


RatificaciónROOT 2026-10-11T14:46:46.675900+00:00: revisión2 yQA documental conformes. Decisión contractual; no implementación ni capacidad musical acreditada.
