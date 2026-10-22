# T-09: continuidad basada en fin de adquisición

## Cambio

`episode_decision` medía la continuidad desde el inicio de la muestra anterior. Cuando la consulta WDDM tardaba, ese cálculo sumaba el trabajo de la muestra anterior y podía rechazar una cadena cuyo hueco real entre adquisiciones era menor de 2,5 s. La validación ahora compara la finalización de la adquisición anterior con la finalización de la actual, en UTC y en monotónico.

La guarda sigue siendo fail-closed: una pausa superior a 2,5 s después del fin de la adquisición anterior continúa produciendo `auto_replayed_or_paused_sample`. No se ha aumentado el presupuesto de episodio de 2 s ni la cadencia contractual.

## TDD y regresiones

- RED: `test_episode_completion_uses_previous_acquisition_end_for_continuity` falló con `auto_replayed_or_paused_sample` antes del cambio.
- GREEN: el caso límite pasa; el control de pausa posterior al fin anterior también pasa.
- `test_benchmark_episode_v3.py`: 55 passed.
- `test_benchmark_canonical.py`: 102 passed.
- Ruff dirigido: `All checks passed`.

## Ejecución WDDM real

Las sesiones completas no se declaran verdes:

| Sesión | Resultado | Evidencia |
|---|---|---|
| `01M4KAKGKA5FEZW41XASDN7Z7G` | 746 recibos; `auto_replayed_or_paused_sample` al auditar un borde de 2,537 s desde el inicio anterior | `recovery-01M4KBAK41DJY7A06523CCXQ4S.json` |
| `01M4KBMWS4W3684HC02SA97089` | 706 recibos; `worker_deadline` durante lectura nativa WDDM | `recovery-01M4KCBFJTABK1VQYREKRSS3VK.json` |
| `01M4KCDRQWR0B3B0B15PQNQR59` | 723 recibos; `worker_deadline` con muestra WDDM parcial y cuarentena de cleanup | `recovery-01M4KD4JHJMXK9C8S01234ZBM5.json` |

Las tres recuperaciones conservaron los artefactos. Las dos últimas fueron reconciliadas y dejaron la reserva GPU libre; ninguna sesión acredita las 160 filas, calibración completa o cierre de T-09.

TDD n/a para este informe de evidencia; la aceptación GPU queda pendiente de una ejecución completa y de la revisión/QA formal.
