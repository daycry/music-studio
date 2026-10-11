---
id: ADR-0084
titulo: Frontera nativa común y admisión del principal Windows
estado: aceptada
fecha: 2026-10-11
opcion_elegida: O1
validacion: elección ROOT delegada; revisión y adopción pendientes
---

# ADR-0084 — coordinación y admisión del principal Windows

## Contexto

ADR0081/C2/K2 separan memoria propia y adquisición candidata. K4a necesita observar el token efectivo del controller confiable antes de adquirir candidatos sin requerir RootContext. El diseño seleccionado O1 conserva ese bootstrap privado y la frontera S1 existente. O2, supervisor como emisor, añade transporte de autoridad sin necesidad acreditada; la retirada/reap sigue siendo responsabilidad de procesos propios posteriores.

## Decisión propuesta

El [contrato K4a](../roadmap/2026-09-28-m1-mvp-estudio/storage-journal-principal-design.md) define raíces nominales finitas, PID/thread/provenance/epochs y consultas acotadas de tokens propios. Los SID observados no autentican por sí solos capacidades ni conceden confianza de archivos. Impersonación no ratificada, pins stale, CPUassemblies o DTOs nunca son admisión nativa. CREATE sigue guardParentS1 deK4b; G1/K3/K4b/K5 y fullchainS1 son puertas distintas.

Se propone una frontera nativa común junto al registry K1. Su orden es boundary→ownerK2→sessionK4a→contextK1. Registry sólo breve y suelto antes de esperarRLock. _pin consume una lease genuina con owner ya bloqueado y no toma boundary/owner posteriores. Bootstrap/revoke no esperanowner desde session. Registrosidentity y memory comparten poison y custodia del mismo módulo importado, sin globals sanos alternativos o callbacks de caller como validación.

Los apéndices candidatos C2/K2 extraen byteexactamente la coordinación de la fuente3c20d078. El runtime K1 vigente no contiene ese preludio; su QA anterior acredita su propio SHA. La futura implementación debe conservar TDD, regresión whole y QA nativa actual con PID real/reap, sin atribuir resultados antiguos al código cambiado.

## Alternativas

- O1, elegida: bootstrap privado del controller actual. Menor complejidad y ninguna serialización de autoridad entre procesos.
- O2, descartada: emisor supervisor/atestación de hijo propio. Más custodia y protocolo sin necesidad actual para esta frontera. No fortalece por sí solo la amenaza frente al mismoSID/admin ni repara ancestros.

## Consecuencias

Se ajustan interfaces privadas y coordinación documentada C2/K2 mediante esta ADR nueva; S1/O2/Constitución permanecen. Controller/threads confiables es supuesto explícito, no protección frente a RCE interna/admin. NativeMemory no necesita principalK4a, pero participa en la misma frontera/poison al integrarse. Después de incertidumbre no se inventan cierres; custodia se retiene hasta retirada/reap propios.

Esta propuesta no ratifica ACL, no remedia ancestros, no publica RootContext/WriterLease/store/ACK ni prueba I/O/SQLite/ext4. Sólo tras revisión, QA y adopción ROOT se libera RED dependiente; las pruebas nativas propias requieren release específica dentro del alcance autorizado. Fecha2026-10-11T20:15:37.285638+00:00. Uso realnull.


## Ratificación ROOT — 2026-10-11T20:45:39.188502+00:00

Decisión documental aceptada tras revisión2 A/B sin defectos y QA documental232/232. Esta ratificación no acredita implementación ni concede admisión nativa. El código K1 vigente conserva su propio alcance y SHA; la coordinación nueva necesita TDD, regresión y pruebas actuales antes de aceptarse.
