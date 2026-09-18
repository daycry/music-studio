# Migración legacy T-01…T-86

> Documento histórico incorporado desde v2. Sus destinos `RTX-*` deben seguirse después mediante [14-MIGRACION-V2-A-V4.md](14-MIGRACION-V2-A-V4.md). No migra estados ni valida código existente.

---

# Migración del ledger anterior `T-01…T-86`

Fecha: **2026-09-18**

Esta tabla no migra estados. Preserva intención y muestra el primer destino en v2; el documento de migración v2→v4 completa la traducción al ledger actual. Toda implementación previa se considera no validada.

## Cadena de trazabilidad

```mermaid
flowchart LR
    L[Legacy T-01…T-86] --> V2[RTX v2]
    V2 --> V4[AV v4]
    V4 --> E[Evidencia nueva]
```

La ausencia de una flecha directa a una tarea v4 no elimina la intención: se resuelve primero mediante el destino v2 y después con el crosswalk v2→v4.

## Leyenda

- **CONSERVAR:** la intención sigue siendo válida, con criterios nuevos.
- **REESCRIBIR/REEMPLAZAR:** no se debe ejecutar la tarea antigua.
- **FUSIONAR/DIVIDIR/ABSORBER:** cambia su unidad de planificación.
- **DEFERIR:** sale del núcleo y requiere gate/presupuesto propio.

## Crosswalk

| Antigua | Título | Decisión | Destino v2 | Motivo |
|---|---|---|---|---|
| T-01 | Gate G2 — consulta a legal (procedencia + protegibilidad) | **DEFERIR** | OPT-09/OPT-10 | Mover consulta legal al gate de comercialización; no bloquea prototipo local. |
| T-02 | Gobernanza previa — nombramiento de supervisor musical y usuarios piloto | **REEMPLAZAR** | RTX-001, RTX-002 | Gobernanza corporativa se sustituye por alcance y gates del propietario. |
| T-03 | Spike de tiempos de inferencia, VRAM y arranque en frío | **REESCRIBIR** | RTX-010, RTX-014, RTX-017 | Benchmark por perfiles RTX reales y métricas upstream. |
| T-04 | Medición de 2 inferencias concurrentes en la L40S | **REESCRIBIR** | RTX-014, RTX-017 | Comparar batch/secuencial; no asumir dos inferencias ni L40S. |
| T-05 | Contenerización mínima de ACE-Step 1.5 | **REESCRIBIR** | RTX-011, RTX-012 | Usar servicio oficial fijado; no fabricar checkpoint fusionado. |
| T-06 | Spike comparativo de modelos | **DEFERIR PARCIAL** | RTX-016, OPT-01 | Auditar capacidades; segundo modelo solo ante gap. |
| T-07 | Matriz de capacidades verificadas | **CONSERVAR REESCRITA** | RTX-016 | Matriz empírica contra revisión actual del upstream. |
| T-08 | Protocolo escrito del gate G1 | **REEMPLAZAR** | RTX-018 | Protocolo musical separado del gate técnico. |
| T-09 | Ejecutar el gate G1 — escucha ciega y decisión | **REEMPLAZAR** | RTX-019, RTX-020 | 36 outputs y puntuación completa, no solo 10 seleccionadas. |
| T-10 | Monorepo, tooling y contrato OpenAPI | **CONSERVAR REESCRITA** | RTX-021 | Monorepo mínimo y contratos. |
| T-11 | Esquema Postgres y migraciones Alembic | **CONSERVAR** | RTX-022 | Postgres sigue en núcleo. |
| T-12 | Linaje en el esquema desde la primera migración (D-22) | **CONSERVAR SIMPLIFICADA** | RTX-022, RTX-039 | Linaje desde inicio, sin sobrecarga legal. |
| T-13 | Object storage, URLs firmadas y escritura en dos fases | **REEMPLAZAR** | RTX-026 | Store local CAS; S3/URLs firmadas se difieren. |
| T-14 | Redis + cola de trabajos (idempotencia, DLQ, cuarentena) | **REEMPLAZAR** | RTX-023 | Cola SQL durable; Redis/DLQ no necesarios en MVP. |
| T-15 | Máquina de estados del trabajo | **CONSERVAR** | RTX-022, RTX-023, RTX-025 | Máquina de estados y lifecycle. |
| T-16 | Progreso en tiempo real por SSE/WebSocket | **CONSERVAR REESCRITA** | RTX-037 | SSE reconectable con etapas reales. |
| T-17 | Biblioteca: listado, filtros, búsqueda | **CONSERVAR** | RTX-034 | Biblioteca después del vertical slice. |
| T-18 | Reproductor persistente y base multipista | **DIVIDIR** | RTX-035, OPT-03 | Player básico en MVP; multipista opcional. |
| T-19 | ffmpeg: transcode FLAC/MP3/WAV + loudness EBU R128 base | **FUSIONAR** | RTX-036 | Postproceso/export unificado. |
| T-20 | Exportación a 48 kHz con soxr y loudness por destino (D-23) | **FUSIONAR** | RTX-036 | WAV 48 kHz y loudness por destino. |
| T-21 | Compartición por URL de la app + i18n con next-intl (D-24, D-25) | **DIVIDIR** | RTX-041, OPT-09 | i18n al MVP; compartir URL/multiusuario se difiere. |
| T-22 | CI/CD: pruebas, build, despliegue a stage | **CONSERVAR REESCRITA** | RTX-042 | CI local y lane GPU; stage cloud no requerido. |
| T-23 | IaC básica y entornos | **REEMPLAZAR** | RTX-029, OPT-08 | Compose local; IaC cloud opcional. |
| T-24 | Observabilidad OTel y coste por generación | **REESCRIBIR** | RTX-047 | Observabilidad de GPU/trabajos; coste cloud fuera. |
| T-25 | Checkpoint de stop-loss + runbook de desmantelamiento (D-28) | **ABSORBER** | RTX-017, RTX-043, RTX-053 | Stop-loss integrado en gates. |
| T-26 | Firma del esquema del manifiesto por legal | **DEFERIR** | OPT-10 | Firma legal del manifiesto solo si se comercializa. |
| T-27 | Manifiesto v1: esquema, emisión y verificador multi-versión | **CONSERVAR SIMPLIFICADA** | RTX-039 | Manifiesto operativo v1 sin firma/C2PA. |
| T-28 | Ledger append-only con cadena de hashes | **DEFERIR** | OPT-10 | Cadena append-only avanzada no bloquea MVP. |
| T-29 | Completar contenerización de HeartMuLa | **DEFERIR** | OPT-01 | HeartMuLa no es adapter obligatorio. |
| T-30 | Contrato, descriptor, persistencia y versionado inmutable | **CONSERVAR REDUCIDA** | RTX-024 | Contrato fino de proveedor, no registry general. |
| T-31 | Dos adapters reales sobre el contrato | **REEMPLAZAR** | RTX-024, OPT-01 | Un adapter real en MVP; segundo condicionado. |
| T-32 | Suite de conformidad perceptual | **CONSERVAR REESCRITA** | RTX-050 | Regresión técnica/perceptual por tolerancias. |
| T-33 | Fichas de licencia verificada de las herramientas de Fase 1 (I-13b) | **ADELANTAR** | RTX-004, RTX-005 | Licencias y supply chain antes de ejecutar modelos. |
| T-34 | Gate G1-bis — escucha ciega de HeartMuLa | **DEFERIR** | OPT-01 | Gate solo cuando se autorice HeartMuLa. |
| T-35 | Imagen del runner y caché de imagen en el host | **REESCRIBIR** | RTX-011, RTX-029 | Imagen local fijada y red interna. |
| T-36 | Caché de pesos en volumen persistente | **CONSERVAR** | RTX-012, RTX-045 | Cache verificada y release sets. |
| T-37 | Aprovisionamiento multiproveedor | **DEFERIR** | OPT-08 | Multiproveedor cloud fuera del núcleo. |
| T-38 | Keep-warm con idle timeout y pod caliente programado | **DEFERIR** | OPT-08 | Keep-warm solo cloud. |
| T-39 | Despacho FIFO con fairness round-robin por usuario | **DEFERIR** | OPT-09 | Fairness solo con multiusuario real. |
| T-40 | Circuit breaker y failover sin pérdida de trabajos | **DEFERIR** | OPT-08 | Failover cloud posterior. |
| T-41 | Telemetría de coste, tope de gasto agregado y kill switch | **REEMPLAZAR** | RTX-048 | Guardas locales de VRAM/disco/tiempo/temperatura. |
| T-42 | API `/generations`: validación, params_schema, idempotencia | **CONSERVAR REESCRITA** | RTX-027 | API mínima e idempotente. |
| T-43 | Gate de derechos de la letra (D-21) | **DEFERIR PARCIAL** | RTX-039, OPT-09 | Declaración puede registrarse; bloqueo jurídico en comercialización. |
| T-44 | Worker: invocación del adapter, progreso SSE, reintentos | **CONSERVAR REESCRITA** | RTX-024, RTX-025, RTX-037 | Worker sobre API oficial y cola SQL. |
| T-45 | Post-proceso: loudness al destino + transcode FLAC/MP3 | **FUSIONAR** | RTX-036 | Postproceso y exports. |
| T-46 | Editor de letras con etiquetas de sección | **CONSERVAR** | RTX-031 | Editor después de vertical slice. |
| T-47 | Formulario de creación a mano | **CONSERVAR** | RTX-031 | Formulario de creación. |
| T-48 | Panel de resultado, variantes en pares, estados de error | **CONSERVAR REESCRITA** | RTX-028, RTX-032, RTX-038 | Resultado, variantes y errores. |
| T-49 | Modo instrumental sin voz | **CONSERVAR** | RTX-033 | Instrumental, verificado upstream. |
| T-50 | Auth.js: OAuth social y corporativo + credenciales | **DEFERIR** | OPT-09 | Auth no necesaria en loopback mono-usuario. |
| T-51 | TOTP y códigos de respaldo | **DEFERIR** | OPT-09 | TOTP no necesaria en MVP local. |
| T-52 | JWT/JWKS, roles y auditoría de accesos | **DEFERIR** | OPT-09 | Roles/JWT cuando exista multiusuario/exposición. |
| T-53 | Verificación final de criterios de aceptación y ritual de cierre | **REEMPLAZAR** | RTX-043, RTX-053 | Cierres MVP y beta separados. |
| T-54 | C2PA: firma y verificador de la cadena de confianza | **DEFERIR** | OPT-10 | C2PA comercial posterior. |
| T-55 | Gestión de certificados y custodia de clave en KMS con rotación anual | **DEFERIR** | OPT-10 | KMS/certificados posterior. |
| T-56 | WORM: object lock + sello diario firmado sobre el ledger | **DEFERIR** | OPT-10 | WORM posterior. |
| T-57 | Watermarking robusto a transcode MP3 320 — condicionado a I-13 | **DEFERIR** | OPT-10 | Watermark solo con requisito y benchmark. |
| T-58 | Certificado exportable JSON/PDF y cierre legal del formato firmado | **DEFERIR** | OPT-10 | Certificado exportable posterior. |
| T-59 | Ficha de licencia verificada de los pesos de Demucs (I-13b) | **REEMPLAZAR** | RTX-016, OPT-03 | Auditar separación nativa; fallback requiere licencia propia. |
| T-60 | Integración de Demucs como post-proceso (separación en 4 stems) | **DEFERIR/CONDICIONAL** | OPT-03 | No imponer Demucs; usar nativo si cumple. |
| T-61 | Reproductor multipista sincronizado | **DEFERIR** | OPT-03 | Multipista después de validar stems. |
| T-62 | Empaquetado y descarga de stems a demanda | **DEFERIR** | OPT-03 | Descargas stems opcionales. |
| T-63 | Llamada LLM con streaming y plantilla de prompt de letra estructurada | **DEFERIR** | OPT-06 | Primero probar simple/query rewriting nativo. |
| T-64 | UI de asistente: streaming, edición e inserción en el editor | **DEFERIR** | OPT-06 | UI de asistente separada. |
| T-65 | Rate limit, contabilidad de tokens y guardrails | **DEFERIR** | OPT-06/OPT-09 | Rate limit/tokens solo si se integra LLM externo. |
| T-66 | Endurecimiento del prompt de sistema y validación de salida parseable | **DEFERIR** | OPT-06 | Guardrails al autorizar asistente. |
| T-67 | Editor de forma de onda: render, zoom y selección de regiones (I) | **DEFERIR** | OPT-02 | Editor de forma de onda avanzado posterior. |
| T-68 | Editor de forma de onda: snap a secciones y navegación por teclado (II) | **DEFERIR** | OPT-02 | Snap/navegación posterior. |
| T-69 | Alineado letra-audio con HeartTranscriptor | **REEMPLAZAR** | RTX-016, OPT-05 | Probar LRC/audio understanding nativos antes de HeartTranscriptor. |
| T-70 | Inpaint/continuación — verificación de capacidad y llamada al adapter | **DEFERIR/CONDICIONAL** | RTX-016, OPT-02 | Usar repaint/continuation nativo si es estable. |
| T-71 | Inpaint/continuación — gestión de fallos y fallback | **DEFERIR** | OPT-02 | Fallback ligado a función opcional. |
| T-72 | Empalme con crossfade y validación de costura | **DEFERIR/CONDICIONAL** | OPT-02 | Solo si el upstream devuelve regiones que requieren empalme. |
| T-73 | Preservación bit-idéntica fuera de la región editada | **REESCRIBIR** | OPT-02 | Identidad solo en PCM pre-postproceso fuera de región/crossfade. |
| T-74 | Línea de tiempo por secciones, máquina de estados de edición y linaje de la derivada | **DEFERIR** | OPT-02 | Timeline/linaje avanzado cuando exista edición. |
| T-75 | Ingesta de audio subido + gate de titularidad obligatorio | **DEFERIR PARCIAL** | OPT-04/OPT-09 | Ingesta y seguridad opcionales; gate jurídico comercial. |
| T-76 | Separación de fuentes y extracción de melodía/estructura | **REEMPLAZAR** | RTX-016, OPT-04 | Auditar capacidades nativas antes de pipeline propio. |
| T-77 | Generación AUDIO_TO_AUDIO según matriz de capacidades | **DEFERIR/CONDICIONAL** | OPT-04 | Audio-to-audio solo si upstream estable. |
| T-78 | Registro en auditoría y manifiesto de la pista derivada | **DEFERIR** | RTX-039, OPT-04 | Manifiesto derivado al habilitar función. |
| T-79 | Mezcla del resultado y validación de calidad | **DEFERIR** | OPT-04 | Mezcla/QA ligado a cover. |
| T-80 | Catálogo curado de ≥ 8 presets de voz | **DEFERIR** | OPT-01/track voz futuro | No prometer presets hasta verificar condicionamiento de voz. |
| T-81 | Previsualización de preset con audio de muestra | **DEFERIR** | track voz futuro | Preview depende de catálogo válido. |
| T-82 | Verificación documentada de derechos por preset | **DEFERIR** | track voz futuro/OPT-09 | Derechos por preset antes de comercializar. |
| T-83 | Integración del selector de voz en el formulario de generación | **DEFERIR** | track voz futuro | Selector solo tras capacidad real. |
| T-84 | Escucha ciega de validación de reconocibilidad del preset | **DEFERIR** | track voz futuro | Reconocibilidad solo tras presets verificables. |
| T-85 | Proveedor GPU local (`GPU_PROVIDER=local`) con NVIDIA Container Toolkit (D-29) | **ADELANTAR AL NÚCLEO** | RTX-003, RTX-010, RTX-011, RTX-029 | GPU local deja de ser extensión y pasa a fase inicial. |
| T-86 | Instalador del runner GPU local — preflight, pesos verificados, configuración y desinstalación (D-30) | **CONSERVAR REESCRITA** | RTX-044, RTX-045 | Instalador después del MVP, basado en release sets y RTX. |

## Resultado agregado

La lectura actual de esta tabla debe respetar además la invariante v4: ninguna Song/VideoProject se liga a una GPU; las tareas de modelos se materializan mediante ModelProfile/ModelRelease y los workers solo aparecen en ModelRun.

- El runtime local (`T-85`) pasa de ampliación tardía a fundamento de R0/R1.
- El instalador (`T-86`) se conserva, pero solo después de un MVP validado.
- Redis, S3, IaC cloud, multiproveedor, keep-warm, fairness y failover salen del núcleo.
- HeartMuLa, edición, stems, cover, asistente, presets de voz y cumplimiento avanzado son tracks opcionales.
- Se conserva la disciplina de idempotencia, estados, linaje, audio, pruebas y manifiesto técnico.
