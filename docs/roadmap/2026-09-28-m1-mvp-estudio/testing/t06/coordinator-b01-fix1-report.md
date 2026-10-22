> Publicación: las rutas locales se han anonimizado. Los argv y originales exactos se conservan en la evidencia privada.

# B01: confirmación explícita de publicación

Corregido únicamente en los tres ficheros OWNED. EventBus.publish conserva None y efectos legacy; publish_confirmed retorna bool estricto desde la aceptación del evento bajo el lock existente. El coordinador no interpreta None/False/1 como aceptación. Conserva el valor durable y el error primario, incluido fallo secundario de gap. No cambia HTTP ni contratos públicos.

RED causal: tres fallos de assert published con EventBus y SQLite reales (stage inválido, certificado inválido, shutdown); caso válido PASS. Artefactos originales en red-real-bus, fuentes/test/runner antes del run. Los mocks adaptados no acreditan ese RED. El primer green-focal tuvo un fallo de fixture por None; se conserva íntegro y se reparó devolviendo True después del append existente.

Final: 246 PASS, 0 FAIL/ERROR/SKIP = 239 originales + 7 nuevos; exactamente los siete WHOLE del productor. Una sola traza fresh mide cuatro módulos WHOLE, oficial líneas+ramas >=80 y cero exclusiones; véase whole-current-coverage.json. Ruff check y format-check: exits 0.

Semántica vacía conservada explícitamente: published significa que se cumplió el batch solicitado, incluida invalidación deliberada; confirmed_count=0 deja claro que no se emitió ningún evento. En batches fallidos el contador es histórico de aceptaciones, no promesa de retención tras mark_gap. Todas las assertions/decorators/params previas conservadas; publishers doubles ahora usan publish_confirmed.

Custodia: preimages/source-root-before y snapshots por ejecución físicos antes de imports del test/Popen; copias read-only de receta runner, aliases y fixture antes de adaptación. Python.exe y runner copiados. Bibliotecas del intérprete/dependencias y OS TCB/UNKNOWN; inventario de imports transitorios UNKNOWN, sin afirmación retrospectiva. Los children registrados se esperaron; censo universal UNKNOWN. Los hashes de fuentes protegidas son byteexact. Historial first239/current4 y todos RED previos sólo referenciados, sin mutar.

QA2 permanece FAILED; preocupación de formato disjunta intacta. No aceptación de tarea/calidad/E2E/GPU, sin claims de rendimiento. Root debe realizar review2 y QA independiente. Model/tokens/EUR/horas null.

Historial adicional: finalize.py inicial falló por SyntaxError de quoting antes de cualquier ejecución de su cuerpo; preimagen y stderr preservados, reparación privada ejecutada. No es RED de producto. Deriva observada fuera de ownership: scripts/eval/benchmark_process.py, unidad disjunta activa; no escrito ni revertido por este actor. Los once archivos protegidos enumerados en protected-parity.json permanecen byteexact. El resultado 239 original y su preocupación de formato disjunta no se reinterpretan.

Cobertura oficial actual líneas+ramas: publication 90,3225806451613 %; event_snapshot 93,75 %; queue/events 94,51612903225806 %; sse 95,22673031026252 %. Una traza final-selected/.coverage, sin combinación con anteriores.
