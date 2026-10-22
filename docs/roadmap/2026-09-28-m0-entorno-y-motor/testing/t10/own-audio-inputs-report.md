# Recursos de audio propios para T-10

Preparados tres WAV FLOAT estéreo a 48 kHz: fuente de 60 s y referencias A/B de 30 s, en `data/inputs/t10-capabilities/own-audio-v1/`. No se han ejecutado nuevas generaciones ni instalado herramientas.

Los padres son las dos tomas originales T-10 ya generadas y preservadas: song60 segunda e instrumental60. No proceden de T-16 ni de los MP3/stems externos de Suno. Se registra la procedencia de generación original autorizada con texto declarado assistant; no se usa una grabación de una persona real.

Transformación explícita: intervalo inicial de cada padre, ganancia fija float32 de 0,75 y escritura FLOAT. Sin resample, ajuste temporal, normalización de loudness ni limitador. Todos los derivados son finitos, tienen pico ≤0,8 y su PCM coincide bit a bit tras escritura/lectura. Los hashes de ambos padres permanecen intactos. Cualquier comparación de preservación posterior debe usar el nuevo WAV de entrada, no confundirlo con el padre sin atenuar.

`resources.json` pasa el validador real de permisos, procedencia y sellos de recursos del harness. Las referencias contrastan tomas concebidas como canción e instrumental; no se acredita identidad vocal, timbre concreto ni calidad por esta preparación.

No se aporta voz aislada ni ground truth multipista. Tampoco se aportan LoRA ni evaluador tonal: sus prerrequisitos siguen pendientes. Estos archivos habilitan la preparación técnica de fuentes y referencias, no declaran ninguna capacidad verificada. [Recibo](own-audio-inputs-receipt.json).

Incidencia de orquestación: primera invocación falló al importar scripts por ausencia de la raíz del repo en sys.path, antes de crear el bundle. Se corrigió sólo el helper privado y la segunda invocación terminó exit0. Originales sin cambios. TDD n/a: preparación de datos derivados.
