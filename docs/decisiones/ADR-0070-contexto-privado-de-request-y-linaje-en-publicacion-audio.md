# ADR-0070 · Contexto privado de request y linaje en publicación de audio

- **Estado:** aceptada bajo delegación; implementación, revisión y QA pendientes.
- **Fecha:** 2026-10-09.
- **Relacionadas:** ADR-0055, ADR-0060, ADR-0062 y ADR-0065.

## Problema

La primera implementación del paquete escribía params vacíos y derivación
original aunque el ganador y la toma tuvieran otros valores. El RED real
de contexto y su GREEN posterior acreditan la captura exacta parent-owned
de request y linaje, sin modificar contratos de ejecución ni tablas.

La request musical puede contener letra y estilo. Copiarlos completos al
manifiesto contradice la privacidad vigente. La preparación ACE de M0
tiene sus propios controles efectivos y formato: no se fabrica una de esas
preparaciones para representar un contexto genérico del server.

## Decisión

El padre captura desde SQLite la request exacta del intento ganador y el
linaje/derivación de la toma. El contexto privado es JSON cerrado, versionado,
canónico, write-once y content-addressed; reside en
`data/private-contexts/<sha256>.json`. Contiene datos solicitados, no certifica
controles efectivos de un engine ni otorga autoridad por sí mismo.

El hijo recibe únicamente la referencia fija parent-owned y su SHA/tamaño,
dentro del presupuesto conjunto de 16 MiB de plan y contexto. No lee SQLite,
no interpreta entrypoints y no recibe tokens. Antes de preparar/publicar o
reconciliar, el padre coteja la autoridad vigente y el contenido capturado.
El manifiesto y el package SHA anclan ese contexto en la revisión durable
existente de la intención; no se añade una tabla por este cambio.

El manifiesto v1 añade sólo el campo opcional cerrado
`private_context: {sha256}`. Sus params públicos conservan la proyección
segura vigente: se excluyen letra y estilo privados, se mantienen los demás
valores solicitados admitidos y se conservan hash/declaración de la letra
cuando corresponde. No se silencian params inventando un objeto vacío.
Los datos privados prohibidos, tokens y fotos no se incluyen en el manifiesto.
El linaje declarado refleja la toma real; no se fuerza original por defecto.

El verificador común resuelve únicamente el basename derivado del hash
dentro de la raíz privada fija. Exige archivo regular propio, confinamiento,
no enlaces/hardlinks, tamaño acotado, SHA, JSON cerrado/finito y correspondencia
con el sujeto/request/proyección/linaje del manifiesto. Falta, mutación,
hash incorrecto o discrepancia falla explícitamente. El contenido privado
no se devuelve en mensajes de error ni logs.

Los manifiestos anteriores sin referencia privada siguen verificándose con
sus reglas anteriores. El nuevo recibo no sustituye input_receipts o
preparation de ACE, y la evidencia sintética no se presenta como learned.
La importación/restauración que pretenda verificar toda la causalidad debe
conservar los recibos privados necesarios; un export público de audio no
los incluye automáticamente ni se declara verificado como biblioteca completa.

## Alcance y gates

Extensión compatible de schema v1 y helper audio-post; no se relaja
`_privacy` ni se reescriben manifiestos emitidos. Worker y verificador usan
la misma definición. Tests primero: request con letra/estilo exactos en
privado, ausencia pública, hashes/declaración y linaje, rechazo de missing/
mutation/alias/subject/proyección, y compatibilidad M0 sin referencia nueva.
Cobertura de cada módulo Python completo >=80 % sin exclusiones, revisión
fresca y QA independiente. Integración real WAV/FFmpeg y despliegue
persistente de ADR-0069 siguen gates separados; T-05 continúa abierto.
