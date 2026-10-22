# T-08 — revisión de integración1: A+B conformes, C pendiente

2026-10-06. Nueva fase posterior al rojo GPU1; [revisión3 anterior](review-3.md) conservada sin reiniciar sus intentos. Delta completo de cuatro archivos frente a fix2: una línea de backend, nuevo test de proyección real, prosa/comandos README y tag analysis de Compose. Lentes frescas e independientes de implementar; C secuencial por límite de agentes, D=false. Scope0sinavisos/exclusionesusuario.

| Criterio | A | B |
|---|---|---|
| Estrategia y proyección compatibles con checkpoint local | Conforme CPU, prefijo BF16 real1s/30s | Conforme CPU, delta mínimo |
| Texto íntegro y presupuesto | Conforme, tokenizer sin truncamiento/exceso rechazado | Conforme, cinco regresiones propias |
| Ventana10s y duración original | Conforme, sin cobertura global ficticia | Conforme, recorte/relleno documentados |
| Alcance/freeze21+14/imagen7d0733f | Conforme;17fuentesprevias intactas | Conforme, baseline306e3b0 preservado |
| TDD/cobertura y E3README/tag | Conforme, REDreal2/GREEN8/47CPU | Conforme, contraste de README/Compose por SHA |
| Constitución/residencia/contratos | Conformidades previas conservadas; E2/OpenAPIn/a | No defectos nuevos, adapter sin cambios |
| GPUscore/ASR/QA independiente y CA completos | Pendientes, no cierre | Pendientes, no cierre |

A y B: ceroCritical/Important/Minor, sin rebates ni deuda. A ejecutó dos tests reales de prefijo en imagen7d0733f/offline/CPU→2passed13,24s; B prefijo/procesador→5passed13,93s. Ambas verificaron21fuentes/14artefactos/18fuentesimagen y correspondencia del delta con baseline. A AST15/diffcheck conformes, B imageinspect actual/histórico conforme. No ejecutaron GPU, build, suite global, pesos ni QA. La consulta auxiliar de ADR no encontró resultados; no se modificó conocimiento ajeno.

C está en curso: no hay veredicto fusionado de tres lentes ni aprobación para GPU. CA/T08/M0 siguen abiertos. Fuentes congeladas durante revisión; implementación T16 separada no toca analysis ni Compose. Root mantiene ledger/mediciónlote, sin atribuir consumo individual.
