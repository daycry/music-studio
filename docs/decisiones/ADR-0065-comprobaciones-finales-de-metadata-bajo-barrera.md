# ADR-0065 · Comprobaciones finales de metadata bajo la barrera

- **Estado:** aceptada bajo delegación del propietario; integración y QA pendientes.
- **Fecha:** 2026-10-09.
- **Relacionadas:** [ADR-0056](ADR-0056-sse-con-buffer-y-recuperacion-de-estado.md), [ADR-0061](ADR-0061-rechazo-con-rollback-confirmado-sin-invalidar-el-feed.md).

## Contexto y alternativas

La integración de escritores adquiere el coordinador antes del writer SQLite.
La reserva actual realiza dentro del writer sus comprobaciones finales:
`resolve_references(..., verify=False)`, `StagedInputs.check` y `proof.check`
de retry. Inspeccionan paths, enlaces e identidad de fichero. Envolverlas bajo
la barrera conservando una prohibición absoluta de filesystem sería incoherente;
moverlas fuera eliminaría la comprobación final que protege hoy la reserva.

Se compararon permitir esas comprobaciones de metadata (M1) y sustituirlas por
una lease de custodia pura (M2). M2 puede impedir cambios de otros mutadores
del servidor, pero no congela por sí sola el filesystem externo ni reemplaza
la detección actual de enlaces o reemplazos. Se elige **M1**.

## Decisión

Bajo el orden coordinador → writer SQLite → bus se permiten únicamente las
comprobaciones finales existentes de metadata sobre entradas resueltas por
referencias vigentes de SQLite, autorizadas para el owner y canción actuales
y confinadas a `data/`, y sobre staging propio en `tmp/_server_inputs/`, con
identidad y bytes previamente verificados fuera de la barrera.

La excepción incluye confinamiento/resolución de path, tipo de fichero,
enlaces/junctions, número de enlaces e identidad `stat`. No abarca sólo la
copia staged: `resolve_references(..., verify=False)` también comprueba las
entradas autorizadas originales. Se conservan la igualdad de referencias
actuales y todos los controles finales; una prueba anterior no sustituye
la autoridad vigente del writer.

Lectura de bytes, hashes, copia/staging, permisos, rename, cleanup, carga de
modelos y red ocurren fuera de la barrera. No hay awaits ni yields bajo ella.
Cada transacción o página participante la libera antes de devolver o producir
una página del iterador.

SQLite y metadata se ejecutan en un hilo nativo, nunca bloqueando el event
loop. El timeout de adquisición limita la espera para entrar; no garantiza
un plazo absoluto de las syscalls ni permite abandonar un actor todavía
activo como si hubiera terminado. Cancelación y shutdown conservan su
supervisión hasta el retorno real.

Sólo rollback y cierre confirmados anteriores al commit conservan el feed
según ADR-0061. La incertidumbre durable lo invalida; una notificación fallida
posterior no reenvía la generación.

## Verificación

La integración debe cubrir todos los escritores, snapshot WAL y alta del
suscriptor bajo la misma instancia. Sus pruebas comprueban orden de locks,
rechazo de referencias/staging cambiados, ausencia de hashes/copia/red bajo
la barrera y retención de un actor nativo bloqueado. Conservan los casos de
reserva, retry, rollback e incertidumbre.

Esta decisión no modifica las fuentes de cola congeladas en revisión T-05.
El comentario de `publication.py` se actualizará al implementar la integración
bajo su ownership y revisión. No acredita el endpoint ni el cierre de T-06.
