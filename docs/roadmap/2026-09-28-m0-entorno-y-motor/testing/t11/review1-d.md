**Lente D — 1 hallazgo Minor; 0 Critical y 0 Important.** Revisión estática de las cuatro fuentes nuevas completas suministradas, sin herramientas ni ejecución propia.

| Criterio | Resultado | Evidencia |
|---|---|---|
| Bloqueo síncrono que perjudique concurrencia prevista | ✓ | `run.py:296`: pausa de 10 ms en un controlador CLI secuencial; no demuestra degradación relevante para 120 jobs. |
| Trabajo evitable repetido con volumen real | ✗ | `metrics.py:219`: verifica íntegramente el mismo FFmpeg por cada toma. |
| N+1 o crecimiento desproporcionado restante | ✓ | Sin otros hallazgos sustentados para los 30 slots y 90 jobs métricos previstos. |
| Fuentes de tests | ✓ | Sin problemas de rendimiento relevantes identificados en ambos archivos nuevos. |

**Minor — Verificación completa de FFmpeg repetida por toma.**  
` scripts/eval/metrics.py:219` llama a `verified_ffmpeg()` desde cada normalización; `metrics.py:153–171` vuelve a hashear el ZIP, descomprimir y hashear su ejecutable, hashear el binario instalado y ejecutar `-version`. `scripts/eval/run.py:564–566` repite esa normalización dentro del bucle de tomas.

**Carga concreta:** una batería CPU/mock de 30 tomas con `normalization=metrics.normalize_audio` realiza 30 verificaciones del mismo archivo de 171.536.113 bytes y binario de 134.496.256 bytes. Eso supone aproximadamente **9,18 GB de lecturas para hashes y 4,03 GB de ejecutable descomprimido**, frente a unos **306 MB y 134 MB**, respectivamente, con una verificación compartida por sesión; además, 30 procesos `-version` frente a uno. Es trabajo adicional independiente del audio. Conviene verificar una vez por sesión conservando la vinculación al binario verificado.

Las mediciones y pruebas aportadas son evidencia declarada, no ejecutada por esta revisión. Derechos, corpus cantado real, suelo WER, integración GPU, 30 generaciones musicales y escucha siguen pendientes; este hallazgo no convierte esos pendientes en defectos introducidos ni acredita CA-08. **T-11 conserva `en-progreso`; candidato CPU pendiente de QA.**