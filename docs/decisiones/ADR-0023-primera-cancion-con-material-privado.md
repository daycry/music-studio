# ADR-0023 · Primera canción de M0 con material propio privado

- **Estado:** aceptada · **Fecha:** 2026-10-05

## Contexto

T-07 preveía usar B-02, un brief fijo de folk-pop de 180 segundos, para generar la primera canción.
El propietario ha entregado «Libre» con la letra, el prompt y las notas que usaba en Suno:
hip hop con orquesta y electrónica, dueto en castellano, 94 BPM y una duración de 240–270 segundos.

El primer uso del motor debe servir para probar ese material. B-02 sigue siendo uno de los diez
casos fijos del protocolo de evaluación; cambiar su género y duración alteraría la comparación.

## Decisión

- La primera canción de T-07 usa «Libre» mediante la entrada explícita del CLI:
  `--lyrics … --style … --duration 255 --language es`. Los 255 segundos son el punto medio
  del intervalo pedido; se registrarán la duración solicitada y la duración real.
- El material del propietario se guarda en `data/inputs/libre/`, excluido de Git. Se conserva
  el original y una entrada preparada para ACE-Step; la adaptación cambia etiquetas y separa
  la descripción musical, manteniendo todos los versos y el outro.
- La letra, el prompt y las notas personales no se copian a los fixtures ni a la documentación pública.
- B-02 conserva su definición en [el protocolo](../calidad/evaluacion-escucha.md).
  El CLI mantiene `--brief <ID>` y T-11 sigue requiriendo los diez briefs con sus letras.
- La generación se hace con ACE-Step local. El formato de Suno es una referencia de entrada,
  no una integración con ese servicio.
- Antes de encolar la generación se requiere la declaración de autoría prevista en la
  [constitución](../CONSTITUTION.md). La escucha y la primera impresión las aporta el propietario.

## Consecuencias y verificación

CA-04 de la spec y T-07 aceptan la entrada privada de «Libre» para la primera canción.
Se mantienen los cuatro artefactos, los formatos, el postproceso, el manifiesto y la telemetría.
Este ajuste no acredita la calidad del dueto, la tonalidad o la orquestación: quedan para la escucha.

La entrada está preparada, con nueve secciones y los versos originales preservados.
No se ha generado ni escuchado audio al escribir este ADR. B-02 y la batería de T-11 siguen pendientes.

Fuente técnica de la preparación de etiquetas: [guía oficial de ACE-Step en el commit fijado](https://github.com/ace-step/ACE-Step-1.5/blob/dce621408bee8c31b4fcf4811682eb9359e1bc94/docs/en/Tutorial.md).
