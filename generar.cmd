@echo off
setlocal
rem ===========================================================================
rem  generar.cmd — genera una cancion con ACE-Step 1.5 en la GPU local
rem ---------------------------------------------------------------------------
rem  Envoltorio del comando de Docker, para no tener que recordarlo. Todo lo que
rem  escribas despues del nombre del script se le pasa tal cual al generador.
rem
rem  Ejemplos:
rem    generar.cmd
rem    generar.cmd --duraciones 60
rem    generar.cmd --prompt "bolero triste, guitarra espanola, voz grave" --duraciones 30
rem    generar.cmd --letra-fichero /work/spikes/mi-letra.txt --duraciones 180
rem    generar.cmd --help
rem
rem  El audio sale en D:\srv\ace-step\out\ como WAV de 48 kHz estereo, junto a
rem  un informe .json con tiempos, VRAM y las comprobaciones del fichero.
rem
rem  ACE_STEP_REQUIRE_GPU=1 es el guardarrail G-01: si el entorno esta mal
rem  configurado, el runner se niega a arrancar en vez de degradar al mock y
rem  darte audio simulado sin avisarte.
rem
rem  Aislamiento en tiempo de ejecucion (revision 2026-09-03): el contenedor corre
rem  SIN red, con el sistema de ficheros de solo lectura (salvo /outputs y un /tmp
rem  efimero), sin capacidades de Linux y sin poder ganar privilegios. Las
rem  variables *_OFFLINE de la imagen son una peticion a la libreria; esto es la
rem  barrera. El codigo vendorizado que se ejecuta no ha pasado aun revision
rem  linea a linea, asi que no tiene por que poder salir a ningun sitio.
rem
rem  Integridad de los pesos: el adapter compara el SHA-256 del artefacto con el
rem  `.provenance.json` hermano que dejo el fusor (mismo directorio). No hace
rem  falta exportar nada; si el fichero de procedencia falta, el runner lo dice.
rem ===========================================================================

set "PESOS=D:\srv\ace-step\weights"
set "SALIDA=D:\srv\ace-step\out"
set "RUNNER=%~dp0apps\runner"

if not exist "%PESOS%\ace_step_1_5.safetensors" (
  echo [ERROR] No encuentro el artefacto de pesos en %PESOS%
  echo         Deberia estar ace_step_1_5.safetensors ^(6,2 GB^).
  exit /b 1
)
if not exist "%SALIDA%" mkdir "%SALIDA%"

docker image inspect ace-step-runner:t05 >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Falta la imagen ace-step-runner:t05. Construyela con:
  echo         docker build -t ace-step-runner:t05 -f apps\runner\adapters\ace_step\Dockerfile apps\runner
  exit /b 1
)

echo Generando con ACE-Step 1.5 en la GPU local. Ctrl-C para abortar.
echo Salida: %SALIDA%
echo.

docker run --rm --gpus all ^
  --network none ^
  --read-only --tmpfs /tmp:rw,size=512m ^
  --cap-drop ALL --security-opt no-new-privileges ^
  --pids-limit 256 ^
  -e ACE_STEP_REQUIRE_GPU=1 ^
  -v "%PESOS%:/weights:ro" ^
  -v "%SALIDA%:/outputs" ^
  -v "%RUNNER%:/work:ro" ^
  --entrypoint python ace-step-runner:t05 /work/spikes/generate_smoke.py %*

if errorlevel 1 (
  echo.
  echo [FALLO] La generacion no termino bien. El traceback esta arriba.
  exit /b 1
)

echo.
echo Listo. Ficheros mas recientes en %SALIDA%:
powershell -NoProfile -Command "Get-ChildItem '%SALIDA%\*.wav' | Sort-Object LastWriteTime -Descending | Select-Object -First 3 | ForEach-Object { '  {0}  ({1:N1} MB)  {2:HH:mm:ss}' -f $_.Name, ($_.Length/1MB), $_.LastWriteTime }"
echo.
echo Para escucharlas:  explorer "%SALIDA%"
endlocal
