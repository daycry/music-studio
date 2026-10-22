# Adquisición de FFmpeg Linux — revisión 1

Tres revisores de contexto fresco terminaron con exit 0. A y C no señalaron defectos nuevos; B señaló dos defectos Important. Scope: dos archivos nuevos, cero fuera de alcance. No se acepta la unidad ni se cierra T-05.

| Hallazgo | Escenario | Evidencia |
|---|---|---|
| B-01 · Important | Falla la escritura de `.owner` después de crear `.acquisition-lock`, antes de entrar en el `finally`; el lock queda huérfano y bloquea nuevos intentos. | `fetch_ffmpeg_linux.py:432`; root confirmó el caso mediante un fallo de escritura controlado en su directorio temporal, sin red ni cambios en la carga real. |
| B-02 · Important | En Linux se eliminan los bits de ejecución de `bin/ffmpeg` o `bin/ffprobe`; los hashes siguen iguales y `--check` no exige esos bits. | `fetch_ffmpeg_linux.py:357`; confirmado por lectura del código. La regresión necesita RED funcional; aún no hay prueba nativa Linux. |

Se autoriza corregir ambos casos con TDD, preservar cargas y locks ajenos, revalidar la fuente actual y pasar revisión 2 y QA. La limpieza de un lock sin marker sólo puede hacerse con nacimiento e identidad propios comprobados y contenido vacío.

Evidencia anterior leída: 45 PASS, cobertura individual actual 87,32394 %, sin exclusiones; descarga y comprobación reales exit 0 con pin/tamaño acreditados antes de TAR. Los revisores no repitieron suites. TAR sintéticos y modos modelados siguen siendo TESTDOUBLE, sin acreditar `renameat2`, licencia binaria, ABI ni ejecución Linux.

Originales: `.cache/dev-cycle/m1/t05-ffmpeg-linux-acquisition-inspection1/{a,b,c}/`, incluido el recibo de cada proceso CLI. La adjudicación no modifica esos retornos.
