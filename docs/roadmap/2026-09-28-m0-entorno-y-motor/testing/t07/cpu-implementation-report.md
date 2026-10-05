# Entrega de implementación T-07 — 2026-10-05

## Cambios y propiedad

- `scripts/generate.py`: CLI real M0, entradas directa y por catálogo YAML versión 1, `yaml.safe_load`, token de `.env`/entorno, resolución por capacidades locales verificadas (o `STUDIO_ALLOW_UNVERIFIED=1` explícito), modo BF16 preferido, semilla persistida y variantes con semilla base+i, eventos /v1 y progreso real. Valida índices, rutas, hashes y semilla de los artefactos antes del postproceso.
- `tests/test_generate.py`: 38 casos CPU; integración con mock real, hijo supervisor y FFmpeg/postproceso real, canciones sintéticas e instrumentales, dos variantes, manifiestos verificados por API y por `scripts/verify_manifest.py`, errores y cancelación.
- `pyproject.toml`, `uv.lock`: PyYAML añadido al grupo dev mediante `uv add --group dev pyyaml`, ampliación autorizada por root. Salida: `Resolved 63 packages in 293ms`, `Checked 62 packages in 3ms`, exit 0.
- No se modificaron ledger, docs, Git ni datos privados. No se ejecutaron builds, WSL, GPU ni material Libre.

## Comportamiento

Song requiere `--lyrics-declaration own|assistant|public_domain|licensed` antes de enviar el trabajo. El manifiesto conserva hash y declaración sin texto literal ni ruta personal. La letra se preserva (incluidos finales de línea); BOM UTF-8 se elimina solo del texto enviado, el hash es sobre el fichero original. Una declaración `licensed` no demuestra permiso comercial y se registra conservadoramente con `commercial_use: false` en la dependencia; el escritor de manifiestos recalcula el resultado.

Directo: `--lyrics <fichero> --style <estilo> --duration <s> --language <xx>`; opcionales `--seed`, `--variants`, `--task music.instrumental`, `--engine`, `--bpm` (30–300). Instrumental no acepta letra/declaración. `--brief <ID>` lee exclusivamente metadatos del catálogo y letra `<ID>.txt`; rechaza IDs inseguros, tipos/versión incorrectos, entradas inexistentes, letra ausente, declaración pendiente y conflictos con argumentos directos. No hay fallback ni letra inventada.

Salida: `data/cli/<fecha UTC>/<run_id>/` por variante, exactamente master.flac, listen.mp3, peaks.json y manifest.json. Se preparan todas las variantes bajo un staging; una excepción de postproceso impide publicar resultados parciales. Los manifiestos son inmutables. Se descarga el engine antes del postproceso CPU; en errores posteriores a la aceptación se cancela si no hubo terminal y se intenta descargar. Si el engine rechaza el trabajo/no estaba idle, el CLI no lo descarga. Error CLI sanitizado, sin cuerpos, rutas absolutas ni token.

El stream usa el presupuesto real del trabajo (20× duración + 300 s, mínimo 300 s), para no cancelar una carga/etapa ACE-Step silenciosa tras solo 30 s. El presupuesto es comprobado también durante la lectura y al reenganchar un stream que finalizó sin terminal; no se inventa progreso.

## Evidencia final CPU

Entorno: `. ./scripts/env.ps1`, Python gestionado 3.12.14, sin instalar en Python de máquina.

```
uv run --frozen ruff check scripts/generate.py tests/test_generate.py
All checks passed!
exit 0

uv run --frozen ruff format --check scripts/generate.py tests/test_generate.py
2 files already formatted
exit 0

$env:COVERAGE_FILE = '.cache/dev-cycle/t07/.coverage'
uv run --frozen --all-packages pytest tests/test_generate.py -q --tb=short -p no:cacheprovider --cov=scripts --cov-report=json:.cache/dev-cycle/t07/coverage.json --cov-report=term-missing
scripts/generate.py  253 statements  13 missing  95% (240/253 = 94.86%)
Coverage JSON written to file .cache/dev-cycle/t07/coverage.json
38 passed, 1 warning in 4.65s
exit 0

uv run --frozen scripts/generate.py --help
usage: generate.py [... --bpm BPM ... --lyrics-declaration {own,assistant,public_domain,licensed}]
exit 0
```

La cobertura global de `scripts/` incluye scripts históricos no ejercitados por esta tarea; el porcentaje válido del alcance cambiado es el de generate.py. La advertencia del test runner es `PytestConfigWarning: Unknown config option: cache_dir`, porque la configuración conserva esa opción al desactivar cacheprovider para evitar el WinError 5 previo del caché de pytest. No hay fallo de test.

`test_mock_post_and_manifest` ejecuta el verificador CLI sobre su `data/cli` sintético y afirma exit 0 y salida `all valid`; la fixture limpia después los datos temporales. Esa salida no corresponde a la verificación real de Libre.

RED/GREEN observado en `tdd-evidence.md`; cobertura detallada en `coverage.json`. Los logs no incorporan la letra privada, secretos ni rutas personales.

## Pendiente de root

La declaración `own` ya fue recibida por root mientras se implementaba; no se tomó de datos privados por este agente. El comando real acordado debe incluir `--lyrics-declaration own --bpm 94`. ACE-Step aún declara `verified:false` hasta T-10, por lo que M0 necesita `STUDIO_ALLOW_UNVERIFIED=1` explícito antes de esa generación. El CLI fuerza BF16 si el descriptor lo ofrece; PT/SDPA lo fuerza el adapter vigente.

No se ejecutó la verificación canónica de 255 s, ni `verify_manifest.py data/cli/` sobre esa canción real, ni escucha/medición del propietario. Root conserva GPU, descarga/restauración Ollama, autoría privada, Git, ledger, scope/gates/revisión y QA. No se cierra T-07 ni M0 con esta entrega CPU.

BLOCKED: generación real de 255 s, verificación de su manifiesto y escucha reservadas al orquestador; implementación CPU lista para revisión.
