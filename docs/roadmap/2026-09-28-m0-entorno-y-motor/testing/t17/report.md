# QA final — M0/T-17, auditoría de prompts

**Conforme para auditoría CPU y documentación.** Revisión independiente A+B, intento 2: cero Critical, Important y Minor. El cierre de T-17 corresponde al orquestador; M0 continúa abierto.

ℹ️ sin UI por diseño (`test-plan: n/a (sin UI)`): ledger-lint exit 0, cero incoherencias y ocho avisos de Changelog en T-08–T-13, T-16 y T-17; coverage-check exit 0 con `applies: false`. La puerta de cobertura no se ha ejecutado; no se declara cobertura OK ni porcentaje. `qa-gate.py` no aplica: no hay escenarios Playwright, E2E ni `results.json`; no se ha fabricado un resultado vacío para obtener verde.

| Comprobación | Resultado y evidencia |
|---|---|
| Cuatro recibos originales publicados | Idénticos byte a byte a sus fuentes privadas de caché |
| Probe ya ejecutado | 16 casos; comprobadas entradas de las capturas privadas; sin repetir ejecución nativa |
| Diez originales | Nueve rechazados por esquema; cuatro truncados en descripción DiT |
| Flags y alcance del probe | Thinking activo, tres flags CoT desactivados; CPU, sin pesos musicales ni inferencia |
| Origen y tokenizers | Seis hashes de código coinciden con las copias auditadas; 16 archivos locales coinciden con el lock |
| Preservación | 32 huellas previas verificadas; 72 líneas cantadas/rapeadas conservadas en adaptación completa y candidato |
| Candidato | Nueve tags presentes, mayor sin tónica inventada y retirada al piano conservadas; sin audio ni calidad aprobada |
| T-14 y control T-15 | Archivos idénticos, configuración común verificada y alias documentado; siguen 16 casos |
| Enlaces y privacidad | 17 archivos de la allowlist, cero fugas detectadas y 181 enlaces locales válidos; referencia de vídeo y enlace de §9 verificados |
| Formato del diff | `git diff --check` exit 0; aviso de normalización CRLF de video.md, sin error |

El [recibo QA](qa-receipt.json) contiene los resultados, las salidas reales de ledger-lint y coverage-check y el alcance de ejecución. El [informe de auditoría](audit-report.md) mantiene separadas fidelidad de transporte, obediencia musical y naturalidad. Las revisiones se conservan en [intento 1](review-attempt1.md) e [intento 2](review-attempt2.md).

La salida JSON real de coverage-check es:

```json
{"applies": false, "gwt_sin_id": 0, "test_plan_na": true, "marcador_no_canonico": null, "eximidos": ["T-00", "T-01", "T-02", "T-03", "T-04", "T-05", "T-06", "T-07", "T-08", "T-09", "T-10", "T-11", "T-12", "T-13", "T-14", "T-15", "T-16", "T-17"], "eximidos_exigidos": false, "rutas_ui": [], "rutas_ui_origen": {}, "rutas_ui_degradado": "el diff contra la base «merge-base main…HEAD (84929192)» no aporta ningún fichero: solo se han mirado los cambios sin comitear"}
```

Los 18 IDs anteriores se listan para revisión, sin exigencia de cobertura GWT. No aparecen rutas de interfaz. La comprobación de interfaz está degradada: no ha examinado un diff completo contra la base, sino el alcance declarado y los cambios sin comitear. La revisión A+B y el alcance de publicación acreditan prosa/recibos; este resultado no es una auditoría de todo el producto.

No se ha repetido la suite de producto, medido cobertura unitaria, generado audio, llamado al engine por HTTP ni ejecutado GPU. Los recibos HTTP existentes acreditan únicamente health/estimate locales y cero llamadas load/jobs. El candidato y las capturas completas continúan privados. La referencia de vídeo conservada y el enlace de video.md §9 se comprueban como documentación local; no se ejecutan herramientas, modelos ni servicios de los enlaces.

**PDF pendiente:** la skill `custom-agents:to-pdf` se ha consultado; faltan sus dependencias y no se ha instalado nada. No existe `report.pdf` de esta ejecución.

Checklist manual pendiente:

- [ ] Revisar el candidato privado antes de autorizar una futura generación.
- [ ] Valorar obediencia a voz, rap/cantado, instrumentos, ritmo, crecimiento y outro mediante escucha futura; este QA no la acredita.
- [ ] Recuperar la investigación de vídeo al definir M4, sin tratar sus cifras externas como benchmark local.

La ventana de QA empieza a las 20:53:49 UTC del 2026-10-05. Las cantidades de tokens, horas de trabajo y coste permanecen `null` con fuente estimada; el tiempo de reloj no se interpreta como coste real.
