> Publicación: las rutas locales se han anonimizado. Los argv y originales exactos se conservan en la evidencia privada.

# Entrega privada — custodia Windows

Unidad implementada en los cuatro ficheros asignados. Entrega del productor para revisión A/B/C/D fresca y QA del root, pendientes. No aceptación de T05/M1, Linux, CPU2, audio, BD, FS ni E2E.

`final04`: **31 passed**, exit0, 2026-10-08T22:22:42.412692+00:00 → 2026-10-08T22:22:58.249036+00:00; UUID `6bf044b8-1804-4b89-9c9c-164e8a79605f`. JUnit, argv/PID/UTC/exit/stdout/stderr originales y fuentes previas en `final04/`. Ninguna unión con final01/final02 ni corridas históricas.

| Módulo completo actual | Líneas | Cobertura oficial | Excluidas |
|---|---:|---:|---:|
| `apps/server/app/worker/custody.py` | 182/207 | 87.92270531% | 0 |
| `apps/server/app/worker/custody_windows.py` | 331/362 | 91.43646409% | 0 |

Coverage.py 7.16.2: dos trazas del mismo run, del pytest padre y del padre efímero que importa el runtime. El padre efímero verifica hashes antes del spawn y guarda cobertura ANTES de su muerte real. `raw-traces-before-combine.json`, originales paralelos y copias en `raw-traces/`; combine oficial limitado a final04, JSON con `--keep-combined`. Los workloads benignos importan sólo el protocolo puro aceptado, no los dos módulos de custodia; no se atribuye cobertura de runtime a sus imports.

## Conducta implementada y probada

- Job no heredable creado antes de CreateProcessW, KILL_ON_JOB_CLOSE sin breakaway. Nacimiento CREATE_SUSPENDED con hProcess/hThread reales retenidos. Identidad GetProcessId/GetProcessTimes, Assign/IsProcessInJob y marker ausente antes de ResumeThread. Test de layout Windows x64 y llamadas reales; no deducciones desde Linux.
- STARTUPINFOEX HANDLE_LIST sólo con los tres extremos autorizados; Unicode env allowlist, executable Python gestionado y fixture internos fijados. argv quoteado con list2cmdline, cwd/temporales en proyecto. Sin imports de engines/benchmark/torch, Settings, token o SQLite en la unidad aislada actual.
- Registro del nieto inmediato con nacimiento y pertenencia usando el mismo handle retenido. Handshake de fixture confiable sella nacimientos; accounting es comprobación adicional. Un miembro no registrado o sin salida conserva UNKNOWN; nunca se acredita completitud por snapshot/Job vacío aislado.
- Guard con duplicados no heredables y anclaje independiente; referencias comparadas antes de terminar o cerrar. Reutilización NUMÉRICA real por DuplicateHandle documentada en `numeric-reuse/numeric-reuse-proof.json`; testigo ajeno sigue vivo. Escrow erróneo también conserva UNKNOWN y no termina el Job ajeno.
- Terminación del Job propio, waits de handles de líder/miembro, cero activos, accounting reconciliado y cierres comprobados. Recibo kernel separado del recibo completo de transporte. UNKNOWN conserva referencias, resources_returned=false y gate inerte de retención.
- Framing, secuencia y límites se consumen del protocolo aceptado sin duplicarlos. Reader exclusivo PeekNamedPipe/ReadFile de bytes disponibles evita lectura bloqueada; writer independiente, cola4, CancelSynchronousIo de su hilo real, joins y EOF reales antes de cierre completo. stdout/stderr retenidos ≤16KiB. Writer lleno acreditado por bytes completados y operación pendiente; stderr lleno y backpressure también probados.
- Cancelación explícita/concurrente, coroutine cancel, deadline, hijos/nietos colgados y muerte real del padre. Referencias fuertes a finalizador/owner; CancelledError no retorna recursos. La prueba parent-death usa trabajo que ya dejó de leer y witness que conserva sólo handles de procesos, nunca Job.
- EOF temprano/truncamiento/JSON inválido/flood/backpressure producen UNKNOWN aunque la terminación propia tenga waits acreditados. No equivale a publicación ni release CPU2 real.

## TDD y fallos preservados

- RED red02: `test_suspended_birth_assign_before_resume_and_tree_cleanup`, pertenencia False en hijo real del baseline Popen; GREEN green03 tras CreateProcess real y resolver conhost.
- RED red06: `test_parent_real_death_kills_tree_foreign_witness_survives`, handle de árbol no señalado tras muerte real del padre sin kill-on-close; GREEN green04. red03/red04 fueron bootstrap/import, NO causales; red05 salía por EOF voluntario y NO acredita kill-on-close.
- RED red07/red08: custodia completa UNKNOWN en baseline kernel-only; GREEN green05/green06 y prueba de bloqueo reforzada green15. No atribuir WriteFile bloqueado al baseline red08, donde writer aún no existía.
- RED red09: cancelación coroutine/concurrente devolvía UNKNOWN en baseline; GREEN green07.
- RED red10: transporte truncado devolvía razón kernel_only; GREEN green08, y suite actual cubre frames truncados físicos. El baseline no validaba transporte.
- RED red11: entrypoint alternativo no rechazado; GREEN green13. Validación conductual sin spawn, no prueba nativa.
- RED red12: inyección DuplicateHandle fallido dejaba hProcess real suspendido sin señal; cleanup privado por referencia exacta; GREEN green14/green21 tras conservar creación cruda y contenerla.
- RED red13: escrow sustituido por Job del witness benigno terminó ese witness; GREEN green20 con anclaje independiente. Inyección suplementaria sobre objetos OS reales, no evidencia de fallo espontáneo de la DLL.

Cada fase tiene fuentes/test/fixture/runner/config previos, comandos y JUnit. Los primeros RED no tienen todos los recibos estructurados de nacimiento/stdio por hijo; se declara esa carencia, sin reconstruir números ni elevarla a prueba. Errores iniciales del runner/allowlist/import/display/quotes se conservan y NO se cuentan como RED. debug-root-cause identificó y comprobó Kernelbase para CompareObjectHandles, conhosts reales en el Job, bootstrap app.__init__, separadores de hashes y auto-combine del JSON.

final01 pasó 29 tests pero su exportación JSON consumió los paralelos; binary combinado preservado. final02 repitió sólo por esa incidencia de evidencia. Después se añadió prueba de reutilización numérica y se corrigió el defecto real red13: final04 es la única corrida final declarada del código ACTUAL. Las anteriores permanecen históricas. final03 preserva el gate tras red13. Después se reforzó el writer para duplicar su propio GetCurrentThread dentro del hilo, comparar su objeto retenido y comprobar WaitForSingleObject además del join; final04 sustituye sólo esa fuente actual, con 31 tests y trazas propias. No utiliza TID como autoridad ni une coberturas anteriores.

Referencia primaria adicional: [GetCurrentThread](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getcurrentthread) explica cómo DuplicateHandle convierte el pseudo-handle en referencia real utilizable por otros hilos; [CancelSynchronousIo](https://learn.microsoft.com/en-us/windows/win32/api/ioapiset/nf-ioapiset-cancelsynchronousio) no espera la terminación. Por eso se conserva la referencia del writer hasta su wait nativo y cierre comprobados.

## Alcance y fuentes

13 protegidos exactos frente al mapa root y antes/después final04, incluidos contratos, protocolo, init, SSE y JSON declarados. Sólo se afirma esa lista: no ausencia global de cambios de otros actores. No edición de docs/ADRs/ledger/Git/medidor, ni deps, GPU, servicios, modelos o Linux. Ruff5 exit0 (E402 ignorado por bootstrap privado de paquete; ninguna exclusión de cobertura).

ABI documental: ADR0057 y Microsoft Learn [CompareObjectHandles](https://learn.microsoft.com/en-us/windows/win32/api/handleapi/nf-handleapi-compareobjecthandles) (Kernelbase), [STARTUPINFOW](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/ns-processthreadsapi-startupinfow), [Job limits](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_extended_limit_information), [UpdateProcThreadAttribute](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-updateprocthreadattribute), [QueryInformationJobObject](https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-queryinformationjobobject), [creation flags](https://learn.microsoft.com/en-us/windows/win32/procthread/process-creation-flags). DETACHED_PROCESS evita consola y CREATE_NO_WINDOW se ignora al combinarlo, según esa fuente; prueba real confirmó dos miembros. Queries de imagen sólo sobre Job propio durante diagnóstico, no autoridad de kill. No downloads/install/network adicional.

Actor/model/tokens/EUR/IA_hours reales NULL, sin estimaciones. CLI originales del parent intactos y excluidos del inventario sólo por sus cuatro nombres exactos. Inventario NONCLI completo de esta carpeta, excluye esos cuatro y su propio JSON. El root decide aceptación tras revisión y QA frescas.

DONE_WITH_CONCERNS: evidencias históricas iniciales parcialmente estructuradas; revisión A/B/C/D y QA frescas del root pendientes.
