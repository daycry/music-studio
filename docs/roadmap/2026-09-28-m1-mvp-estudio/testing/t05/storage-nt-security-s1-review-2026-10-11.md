# Revisión de dos lentes — intento 1: política NT S1

Revisión fresca A/B exclusivamente documental de cuatro archivos, base privada `6b6dc1f5526a2d7068a1aad5d8a926981efdf022`. Scope:4 archivos,0 fuera,0 avisos,0 exclusiones de usuario. Selector:Cfalse/Dfalse, prosa. Resultado:0Critical/0Important/0Minor. No se acepta G2 nativo, U2 ni M1.

`P` identifica `docs/roadmap/2026-09-28-m1-mvp-estudio/storage-nt-security-policy.md`; `D` el diseño durable en esa carpeta; `ADR` identifica ADR-0076. Líneas del candidato original revisado.

## Lente A: tabla completa

| Criterio | Veredicto | Evidencia |
|---|---|---|
| T05/G2 alcance documental declarado | ✓ | tasks:208; scope4/0/0, sin exclusiones |
| Elección S1 de ROOT bajo delegación | ✓ | tasks:4705; P:6,16; ADR:24; no aprobación humana nueva |
| Principal previo y allowlist cerrada | ✓ | P:24,26; no confianza desde owner/grupos/nombre/prefijo |
| Owner por papel | ✓ | P:30; dominio/journal nuevos requieren principal |
| TrustedInstaller owner exclusivo root real del volumen sistema | ✓ | P:34,36; ADR:26; SID exacto y papel, no trustees mutación ni otros roots/servicios |
| OWNER/GROUP/DACL por handle; desconocidos rechazan | ✓ | P:44; READ_CONTROL/liberación según GetSecurityInfo |
| Control implícito owner | ✓ | P:38; Owner of a New Object |
| ACE estándar, orden, flags y tipos desconocidos | ✓ | P:46; unknown también IO rechaza, sin reparación |
| IO/herencia por componente | ✓ | P:50,61; efecto actual/propagación separados |
| Generic rights/trustees no conceden confianza | ✓ | P:46,54; mapping por papel/unknown rechaza |
| ALLOW outsider no compensado mediante DENY | ✓ | P:55,56,59; condición suficiente conservadora |
| Derechos journal/dominio/todos padres | ✓ | P:65; DELETE/DC/WDAC/WO/atributos/EA |
| Siblings no reemplazo | ✓ | P:71; hijo retenido/owner/ausencia peligros/NOREPLACE |
| DACL hijo no neutraliza DC padre | ✓ | P:73; DeleteFileW |
| Sharing/revalidación/seguridad complementarios | ✓ | P:75,83; no pre/post como protección ABA |
| Ancla/recorrido por handles, no path/hash como autoridad | ✓ | P:81,89; G1 pendiente |
| Creación cerrada NtCreateFile/no adopción | ✓ | P:85,87; FILE_CREATE/CREATED/protectedDACL/OPENno crea |
| ACL existentes sin cambios | ✓ | P:18,46,93,97; sólo nuevos fixtures liberados |
| S2 experimental/S3 aplazada | ✓ | P:97,99; ADR:32,33; sin binding/controller nuevo |
| Host/diagnóstico sin acreditar resultado nativo | ✓ | P:93,95; name-only no handle, desconocido no inexistente |
| O2/ADR75/U1/wire W1–W6 preservados | ✓ | P:16,89; ADR:40; D sólo enlace/callout |
| Descriptivos/índice actualizados | ✓ | D:9,164; índice:109;8 links/0rotos |
| Constitución explícita respetada | ✓ | Constitución:43,65,69,73; ADR/diseño, sin runtime/BD/contracts |
| Estados/verificación/release preservados | ✓ | tasks:202,210,215,216,217; P:101/ADR:40; T05 abierta |
| TDD/cobertura | n/a prosa | Cuatro documentos, sin código/tests/cobertura atribuida |
| Generados/interoperabilidad | n/a | No commands/agents/hooks tocados |
| Reglas explícitas docs-style | ✓ | Lectura completa; tablas por roles/derechos/ACE y límites concretos |
| CA globales T05 publicación/ready/análisis/limpieza/fallo | no verificable en esta unidad | tasks:215–217 siguen pendientes |
| G1/G2 nativo/U2/persistencia/M1 | no verificable en esta unidad | P:101/ADR:40; ROOTreleasefalse/M1false |

A ejecutó lectura íntegra literal/diff/autoridades, hash4 candidatos+8 entradas sin discrepancias, links8/8, knowledge-find gestionadoexit0 sin aciertos y git status readonly. Consulta Microsoft documental. Ninguna operación nativa o escritura.

## Lente B: tabla completa

| Criterio | Veredicto | Evidencia |
|---|---|---|
| Contrato/confianza | ✓ | P:16,22,24; O2/ADR75/principal independiente |
| Descriptor/owner/ACEIO | ✓ | P:40,44,46,50,61; handle/unknown/herencia, primarias GetSecurityInfo/ACEInheritance |
| Padres/creación | ✓ | P:69,73,75,81,85,87; siblings/exclusivo/protected/noadopción, DeleteFileW/NtCreateFile |
| TrustedInstaller excepción exacta | ✓ | P:34,36,38; sólo owner root real, SID/papel; SERVICE_SID_INFO |
| Límites runtime/restart | ✓ | P:83,89,95,97,99,101; reacreditación/fixtureparcial/S3/U2QA pendientes |
| Referencias/wire/datos personales | ✓ | P:16,93,95; D:164; ADR:40;8 links/0ausentes/0personalliterals |

B ejecutó lectura completa del diff/autoridades, status readonly, hash4/4, links8/8, knowledge-find docs/backendexit0 sin aciertos y primarias Microsoft. Sin runtime ni mutaciones.

## Fusión y metadatos de aceptación

Sin gaps, deuda o rebates. TDD/cobertura/Playwrightqa-gate n/a prosa, no resultado simulado. Revisión no sustituye QA independiente.

Tras el veredicto, ROOT generó un candidato final separado que sólo cambia los metadatos de revisión/aceptación, la frase de estado del ADR y su fila de índice. Las sustituciones exactas y hashes están en `metadata-transform-root.receipt.json` del namespace `storage-nt-security-s1-final-20261011`. Ningún cuerpo normativo ni wire cambia. Snapshot de revisión fue transitoriamente finalizado y restaurado a los cuatro bytes revisados originales; el candidato original y `source.diff` permanecen congelados. QA debe verificar tanto los originales como las sustituciones y el final antes de CAS. No se atribuye identidad de SHA entre original revisado y metadatos finales distintos.

Elección ROOT:S1 estricta, TrustedInstaller sólo owner del ancla del sistema acreditada, S2 experimental, S3 aplazada. Estado de producto y del hito permanece abierto.

ROOT incorporó los cuatro documentos a las 07:34:48 UTC tras QA independiente64/64exit0 y verificación de los reemplazos exclusivamente de metadatos. Las líneas de las tablas corresponden al candidato original; los SHA finales se distinguen en adoption-root.receipt.json. No cambió normativa ni wire.
