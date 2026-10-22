# T08 fix1 — verificación reanudada

**FAILED_NO_ACCEPTANCE_VERIFICATION_COMPLETE**. Baseline única actual: 64 PASS / 1 FAIL / 0 ERROR / 0 SKIP, 65 casos; native child PID19764 exit1, 2026-10-08T19:49:44.774536+00:00 → 2026-10-08T20:28:35.576488+00:00, JUnit 2329.521s. El fallo conserva su estado; no corregido ni relanzado dentro de este despacho de verificación. No aceptación T08/componente/E2E/hardware/fullM1.

Agente nativo `/root/resume_t08_stable_inputs` reutilizado para la MISMA tarea: no fresh independent QA. Producto readonly, ningún cambio de los tres archivos cuya ownership mantiene root. Fuentes/config/tests/runner completas archivadas ANTES del child nuevo; argv/PID/UTC/exit/stdout/stderr/JUnit originales en commands/baseline-final. No scripts históricos reejecutados.

Cobertura oficial WHOLE fetch actual: 93.69627507163324%; gate >=80/ceroexcluded=True. Datos raw .coverage y JSON de la traza actual únicamente ejecutada; una suite fallida no constituye verificación verde. Sin unión histórica, promedio ni extracción. Resultados de cada testcase en junit-cases-original-result.json; detalles originales de fallos en failures-original.json y abajo.

Cuarenta y cinco tests anteriores:44 AST enteros exactos y una excepción declarada del bootstrap de test_original586_missing23, con args/decorators/source variable y cola original de rechazo/assert idénticos. Nuevo bootstrap intenta construir un subconjunto físico propio desde canonical609 menos los23 directos actuales; su resultado REAL aparece en el JUnit, sin presumir que pasó. Cuatro casos None/int×library/main y regresiones ROOT/canonical se conservan igualmente con estado individual real.

Custodia: 968 fuentes exactas=True; 11 protected exactos=True; canonical609 exacto=True; 180 originales fix1 exactos=True. Workspace actual restantes=[]; observerjoined=True. Manifest actual disponible=True, metadata cotejada en current-manifest-result.json si existe. No segunda copia ni freeze independiente del payload.

Coordinación root: posible overlap autorizado con packages/contracts/song-v1.schema.json detectado, luego resuelto. U2aCLI terminó INCOMPLETE20:08:45UTC según root, sin tocar producción/tests; root informó mismo SHA a20:09:20UTC y este actor lo cotejó en concurrent-schema-coordination.json. No se inventa drift: las diferencias finales reales están en source-parity.json. Nuevos JSON bajo packages/contracts también afectarían las fixtures aunque no estuvieran en la lista inicial; root evitó cambios/adiciones hasta terminal. Cotejo de nombres actuales frente a nombres presentes en freeze en custody-result.json, sin afirmar inventario inicial de directorio independiente.

Handle anteriorCLI96670 MISSING según root, PID1364 ausente CIM y ningún Python/Codex phase-match en preflight. Exits anteriores UNKNOWN, sin reconstruir metadata/JUnit/receipt faltantes ni fingir CLI0. Todos los originales y temporales fix1 se retienen; cleanup viejo UNKNOWN. Se reanuda una entrega incompleta por ausencia confirmada, no por timeout de observación. Limitación REDcopias reconstruidas histórica mantenida; no copies-before inventadas. Modelo/tokens/EUR/horas IA reales NULL, nestedOSPIDUNKNOWN.

Incidente helper privado de esta reanudación: freeze realizó todas las capturas y asserts antes de fallar únicamente en último print por len(FunctionDef); original y exit1 preservados. Sólo se corrigió variable de print; no rerunfreeze ni producto. El generador verde finalize_current.py se conserva original SIN ejecutar; se usa este finalizador privado de resultado real fallido.

La solicitud temporal de parada fue REVOCADA por el propietario: objetivo ACTIVO de todo el roadmap, sin pausa. Ownership de este actor sigue limitado a verificar; root continúa causa/fix/reviewQA después de esta entrega. Fecha/procesos directos finales en receipt y process-close-before-finalize.json.

## Fallos originales

### test_original586_missing23

```text
repository = WindowsPath('/.cache/dev-cycle/m1/t08-stable-inputs-review1-fix-resume1/test-workspaces/c32e0742f06149f9876e7c6a402a5077/repo')

    def test_original586_missing23(repository):
        source = repository / "input"
        package = json.loads(deps.read_file(PROJECT, PROJECT / "apps/web/package.json"))
        direct = set(package["dependencies"]) | set(package["devDependencies"])
        lock, _ = deps.load_lock(PROJECT)
        omitted = {
            row["sha256"] + ".tgz" for row in lock["artifacts"] if row["name"] in direct
        }
>       assert len(omitted) == 23
E       AssertionError: assert 24 == 23
E        +  where 24 = len({'02034af8d41dcc67ac8eab88f642e129bb8a2e8922abf30229c32725f54d8fd6.tgz', '057af0a53995f7a57dcb044f4da9b629baca7ad70c01...35f697e6db9fe350bc50740cdaefb865d580.tgz', '1bbea47d1387406da5b6ccc4184cc61eae6851cc0db5c1d9bbd088ea9daa0b4a.tgz', ...})

tests\test_fetch_web_dependencies.py:212: AssertionError
```

El caso586 FALLÓ antes de shutil.copytree y antes del rechazo MISSING_ARCHIVES; no se creó ni verificó el subconjunto físico586 en esta corrida. Análisis finito readonly del JSON: filtro name selecciona24; metadata name+version exactos selecciona23. Duplicados y pins reales en failed-bootstrap-metadata.json; no nuevo test ni fix. Cierre final CIM en process-close-final.json.
