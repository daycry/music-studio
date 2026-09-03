# Código upstream vendorizado — ACE-Step 1.5 turbo

Copia **fijada y verificada** del código del modelo publicado por ACE Studio / StepFun.
Está aquí, y no se descarga en tiempo de ejecución, porque `CLAUDE.md` prohíbe
`trust_remote_code` y `auto_map`: el código de terceros que se ejecuta tiene que estar en el
repositorio, fijado por hash y revisable en un diff, no resolverse contra un hub que puede cambiar
bajo nuestros pies.

## Procedencia

| Campo | Valor |
|---|---|
| Repositorio | `ACE-Step/Ace-Step1.5` (huggingface.co) |
| Revisión fijada | `19671f406d603126926c1b7e2adc169acbcade22` |
| Licencia | **MIT** — `docs/` no la incluye; la evidencia está en `D:\srv\ace-step\provenance\LICENSE.acestep.mit.txt`, recuperada de github.com/ace-step/ACE-Step-1.5 porque **el repo de HuggingFace no publica fichero `LICENSE`** (HTTP 404) |
| Copiado el | 2026-09-01 |

## Ficheros y hashes

| Fichero | Bytes | SHA-256 |
|---|---|---|
| `configuration_acestep_v15.py` | 13130 | `b89870c5c7a7ce060eb0bcdbb5ffc86b0b1a324ca325a26be552ea1b42496dc5` |
| `modeling_acestep_v15_turbo.py` | 96036 | `c1ab0dd547124fee7ada449b2b86eae8201dc7d15889932643bbb67e3c982444` |
| `config.json` | 1968 | `74745ff704ea49164c3d2d1c99fc0670f3fc635a869f0aec2d1311e6a52d400a` |
| `oobleck_decoder.py` | 39936 | `dcb80f5fac9960dec56398c98ce99258edb652654abca6dab32f6d868c1a5c3f` |

Los tres primeros están verificados idénticos a la copia upstream, que a su vez se verificó
contra la atestación del publicador (`lfs.oid` para los ficheros LFS, blob SHA-1 de git para el
resto). `oobleck_decoder.py` es distinto: es una **obra derivada modificada** de `diffusers`
v0.34.0 (Apache-2.0), y el hash de arriba es el del fichero **modificado** que se ejecuta; la
atestación del original (SHA-256 y blob SHA-1 de upstream) y la lista de cambios están en la
cabecera del propio fichero. Hasta el 2026-09-03 no tenía fila en ninguna tabla.

### Textos de licencia

Están en [`LICENSES/`](./LICENSES/), junto a este README, desde el 2026-09-03:
`ACE-Step-1.5.MIT.txt`, `ACE-Step-5Hz-LM-0.6B.MIT.txt` (que además documenta de dónde sale ese
texto y la limitación de emparejarlo con unos pesos publicados en otro repositorio) y
`Apache-2.0.txt`, que cubre tanto a `oobleck_decoder.py` (obra derivada de diffusers, modificada
— el aviso de modificación que exige §4(b) está en la cabecera del propio fichero) como a los
pesos del codificador de texto Qwen3-Embedding.

El inventario completo, con qué licencia cubre qué y qué se descartó por licencia, está en el
[`NOTICE`](../../../../../NOTICE) de la raíz del repositorio. Antes de esa fecha los avisos por
fichero estaban, pero los textos íntegros no viajaban en el repositorio: faltaba la mitad formal
de lo que exigen MIT y Apache-2.0 §4(a).

**Esta tabla la vigila `apps/runner/tests/test_vendor_hashes.py`**: recalcula el SHA-256 de cada
fichero `.py`/`.json` de `vendor/` y exige que coincida con la fila de su README, y que ningún
fichero se ejecute sin fila. Si cambias un fichero vendorizado a propósito, actualiza su fila en
el mismo commit; el test es el «criterio que exija un diff contra los hashes» que estos README
reclamaban desde el principio.

## Estado de revisión — léase antes de confiar

**Estos ficheros NO han pasado todavía una revisión de seguridad línea a línea.** Son 109 KB de
Python que se **ejecutan** al importarse. Vendorizarlos no los vuelve seguros: los vuelve
*inmutables y auditables*, que es un requisito previo distinto y necesario.

Lo que sí está garantizado hoy:

- No se resuelven por `trust_remote_code` ni `auto_map`: se importan desde esta ruta.
- Están fijados por hash, así que cualquier cambio aparece en un diff.
- No se descargan en tiempo de ejecución ni en el arranque del contenedor.

Lo que falta, y es trabajo de `T-03`:

- Revisión escrita con alcance y criterios, buscando en particular ejecución en tiempo de
  importación, red, escritura en disco y `eval`/`exec`.
- Criterio de aceptación que exija un diff contra los hashes de arriba en cada reconstrucción.

Ese trabajo es más urgente que el del pickle en cuarentena: `silence_latent.pt` nunca se
deserializa (se convierte con el auditor de opcodes de `apps/runner/tools/build_artifact.py`),
mientras que **este código sí se ejecuta**.

## Qué NO está aquí

El **pipeline de inferencia** (scheduler, bucle de difusión, CFG, preparación del
condicionamiento, decode) no está en estos ficheros: solo está la definición del modelo. Ese
pipeline vive en el repositorio de GitHub y hay que vendorizarlo aparte cuando se escriba el shim.
