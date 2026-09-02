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
