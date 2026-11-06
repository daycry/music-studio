# Captura de condicionamiento y publicación Windows — verificación CPU

Fecha: 2026-11-06. **Entrega software aceptada en CPU; M0/T-16 sigue en-progreso.**
Base de código: `3dede62`. Rama: `m0/t-16-verificacion-cpu-tomas`.

## Qué se implementó

El adapter registra la huella tipada del argumento real `audio_code_string`
que recibe el resolver DiT y el backend LM observado durante su llamada.
Los campos son opcionales dentro de las cinco etapas v2; los códigos no
se guardan en claro. El lector conserva los recibos históricos y ofrece
`require_conditioning=True` para exigir ambas observaciones válidas en v2.
Ese modo valida un recibo; comparar dos tomas exige contrastar también
sus huellas y los controles existentes.

QA detectó además un falso cambio de identidad de directorios Windows.
La función actual y la de la base reprodujeron el mismo defecto ante
PINNED/UNPINNED con identidad estable. La corrección excluye sólo esos
bits de residencia y el bit que ya se excluía. Conserva dev/ino/mode,
los demás atributos y el rechazo de reparse/tag. Las
[constantes oficiales](https://learn.microsoft.com/en-us/windows/win32/fileio/file-attribute-constants)
distinguen esos metadatos del bit de reparse. El productor externo de
las transiciones sigue desconocido; no se atribuye a ningún proveedor.

## Verificación ejecutada

Una única corrida final ampliada: **437 pass, 9 skip, 0 fail; 446 casos,
23,11 s, exit 0**. Incluye los 41 casos canónicos, las dos pruebas
nativas Windows que fallaban y las 13 regresiones nuevas de identidad.

```powershell
. .\scripts\env.ps1
uv run pytest packages/audio-post/tests apps/engines/acestep/tests/test_dit_resolution.py apps/engines/acestep/tests/test_preflight.py tests/test_generate_preparation.py tests/test_generate_inference.py apps/engines/acestep/tests/test_inference_controls.py -m "not gpu"
```

La ejecución independiente añadió únicamente el plugin de bloqueo de
Torch, cobertura oficial por directorios, JUnit y cachés/temporales
locales. Comando exacto y salidas en
[qa-fixed2/report.md](../../../../.cache/dev-cycle/20261106-m0-t16/qa-fixed2/report.md).
No se ejecutaron GPU, Ollama, SQLite viva ni Claude CLI.

Los nueve omitidos conservan sus motivos anteriores: cuatro symlinks
nativos sin privilegio Windows y cinco casos FIFO POSIX. No hay nuevas
exclusiones ni repeticiones para obtener un pase.

| Puerta | Resultado |
|---|---|
| Revisión A/B, intentos 1 y 2 | Sin gaps; C/D no activadas por el selector |
| Ruff, ocho archivos propios | Exit 0 |
| Ledger | 0 incoherencias, 25 avisos históricos |
| Alcance del candidato congelado | 14 archivos, exit 0, sin exclusiones ni avisos |
| Cobertura del delta frente a `3dede62` | 18/18 sentencias afectadas, 100 % |
| Fuentes durante QA | 14/14 SHA iguales antes y después |
| Activos privados | Seis copias y seis fuentes válidas; 18 salidas fuente verificadas |
| Recibos históricos | Seis válidos en modo compatible; seis rechazados en modo fuerte por ausencia de observaciones |

La cobertura incluye la expresión modificada de `pipeline.py:38` mediante
su `Return` registrado en línea 32. El total de los dos directorios
medidos es **74,56 % combinado**: el 100 % del delta no es cobertura
global ni un porcentaje de ramas modificadas. No se añadieron exclusiones.

## Evidencia conservada y límites

Los RED precedieron al código: campos ausentes, contradicción de backend,
malformados, modo fuerte y regresión Windows `[pinned]` (`524304 != 16`).
La primera QA ampliada quedó **roja: 422 pass / 9 skip / 2 fail**. Se
conserva junto al diagnóstico y el resultado posterior, sin reescribirla.

Evidencias privadas bajo `.cache/dev-cycle/20261106-m0-t16/`:
`fix1/`, `review-1/`, `qa-final/`, `windows-diagnosis/`, `fix2/`,
`review-2/` y `qa-fixed2/`. No se publica el mapa de escucha a modelos,
texto privado, audio ni secretos. Los 71 archivos ajenos coinciden con
el estado preservado al retomar; dos journals ya diferían del baseline
original y se conservaron tal como se encontraron.

M0 no tiene UI; el plan declara `test-plan: n/a (sin UI)`.
`coverage-check` devuelve `applies:false` y conserva su aviso de diff
degradado. La inspección del checkout compartido completo detecta cambios
ajenos fuera del alcance; el candidato aislado y sus fuentes verificadas
son los que pasaron la puerta. No se fabrica un gate Playwright o PDF.

Los seis audios antiguos permanecen íntegros, pero sus recibos no permiten
recuperar la identidad de los códigos LM ni el backend observado que falta.
Las futuras tomas GPU deberán aportar esa evidencia. No se acredita
inicialización histórica PT, ejecución CUDA, calidad musical, ganador
SFT/Turbo ni cierre de M0 o M1. La entrega permanece en su rama hasta
cumplir las puertas pendientes de T-16.
