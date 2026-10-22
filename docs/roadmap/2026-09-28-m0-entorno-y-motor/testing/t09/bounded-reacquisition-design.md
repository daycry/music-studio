# T-09 — Diseño de readquisición acotada

Decisión: [ADR-0039](../../../../decisiones/ADR-0039-readquisicion-wddm-acotada.md). La política anterior y todos sus originales permanecen históricos. Arquitecto fresco: tres alternativas; raíz elige O2 bajo delegación, no una elección específica del propietario.

La adquisición completa conserva NVML, PDH, WSL, navegador, contexto fijado antes de consultar y todos los brackets. El coordinador persiste el original antes de aceptarlo. Clasifica el fallo dedicado solamente después de comprobar los demás campos, incluida continuidad. Si hay una discrepancia aislada, permite una readquisición completa inmediata; presupuesto fijo2s desde el comienzo original y máximo dos adquisiciones. No reutiliza valores ni reinicia el presupuesto.

Cada episodio conserva originales ordenados, clasificación, contexto y vínculos con la muestra aceptada. El validador offline reconstruye la decisión y rechaza originales omitidos, reordenados, duplicados, sustituidos o con cadenas incompatibles. Un original discordante sigue rechazado y fuera de métricas aceptadas. La continuidad aceptada solo avanza tras validar el episodio. Cualquier hueco que exceda la cadencia detiene el lote. La recuperación no prueba observación continua válida del rechazo y rompe la consecutividad empleada por el diagnóstico de shared.

Ownership del implementador: módulos de benchmark en `scripts/eval/` y pruebas correspondientes, con cambios mínimos para política, coordinador, persistencia y validación de episodios. No engines, contrato/v1, pesos, dependencias, sesiones anteriores o GPU. Raíz conserva documentación, ledger y decisión. Se preserva el modo anterior para lectura histórica o se rechaza expresamente su uso con fuentes cambiadas, sin reinterpretar su resultado.

Pruebas decisivas: replay del original exacto permanece rechazado; discrepancia seguida de adquisición válida recupera únicamente bajo política nueva; discrepancia junto con otro fallo no reintenta; segundo desacuerdo o presupuesto/cadencia agotados detienen; no se reutilizan consultas parciales; episodios adulterados se rechazan; calibración mantiene diez aceptadas por fase y lifecycle real; runner no duplica inferencia y conserva ownership y cleanup.

La matriz nueva conserva160casos y requiere acreditación nueva tras TDD, revisión y QA. Las18tomas completadas anteriores son evidencia parcial separada. No hay números de rendimiento completos, ganador musical ni acreditación de cero spill en esta decisión.
