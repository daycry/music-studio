# T05 — revisión documental intento2

ROOTnormaliza respuestasA2/B2 completas, no literal. Fuente dc29562e88428B443líneas/diff98120B497líneas3docs/basea9e150063526f71d958aa81e6d85a7b2086612d0. Tabla original íntegra incluida después, no criteria omitidos. ✓ documentales,no implementación.

| CriterioA actual | Resultado | Evidencia |
|---|---|---|
| A1 cierres | ✓ | T200,214–222/C443 |
| A2scope | ✓ | T207/3docs/fuera0avisos0 |
| A3tests | ✓ documental | C334–364 |
| A3coverage | no verificable | C364/443 |
| A4SQLexception | ✓ reportadoA; acotado porB02 | C31,283,289/ADR0074;batchNULL nuevoB02 |
| A4song/parents/master | ✓ | C98,102,219,309,345 |
| A4server/v1 | ✓ | C73,100,162,299 |
| A5verification | no verificable | T210/216 |
| A6interop | ✓ n/a | 3MDs |
| A6docs | ✓ | datos441–455/iteracion168–178/C370–404 |
| A7prosa | ✓ A02corregido | C281frase21palabras |
| T05M1/backup | ✓ documental | C271–289,350–356 |
| T05inference | ✓ | C184–187,207,338 |
| T05CPUreserve | ✓ A01corr; condicionadoB02 | C98,104–118,184–205 |
| NULL | ✓ reportadoA; batchB02pendiente | C184–187,207 |
| CpuExecution | ✓ | C73,106,187,265,283 |
| Plan/receipt/package | ✓ | C75–160,215,239–267 |
| rights/tools | ✓ | C96,146–162,219,311 |
| UNKNOWN | ✓ | C166,174,231,315 |
| FKcycles | ✓ | C106–108,203–215,340 |
| CAS/unique/retry | ✓ | C170–178,203–213,342–344 |
| SQL/hashlimits | ✓ | C211–217,338–349 |
| Replay0006 | ✓ documental | C271–273,350 |
| Upgrade/backup | ✓ documental | C275–287 |
| Downgrade | ✓ | C289,356 |
| Songv1 | ✓ documental | C267,303,305–307,359 |
| Songv2closure | ✓ documental | C303–311,359–360 |
| Importnocustody | ✓ | C311–315,330,360–361 |
| APIv2four | ✓ documental | C293–297,357 |
| M1409/listwhole | ✓ | C299,358 |
| Preview | ✓ | C223–235,362 |
| T07gates | ✓ | C55,115–120,162,265,364,443 |

| CriterioB actual | Resultado | Evidencia |
|---|---|---|
| Reserva | ✗ B02; B01corregido | C98–118/219 |
| Types/SHA | ✓ | C63–69,146–160 |
| Refs/cycles/history | ✓ | C104–108,178,203–215 |
| NULL/uniqueCASowner | ✗ B02 | C170–215/219 |
| Ownsource/tools/rightsUNKNOWN | ✓ | C146–168,219 |
| M1replay0006 | ✓ | C271–273 |
| UpgradebackupFKrollback | ✓ | C275–289 |
| APIv2/409 | ✓ | C293–299 |
| Songv1/v2/import | ✓ | C303–330 |
| Preview/hashes | ✓ | C223–235 |
| RuntimeSQL/ORM/API/render | no verificable | C364/443 |

| ID | Grado | Estadoactual | Evidencia |
|---|---|---|---|
| A01=B01 | Importantprevio | corregidodocumentalmente | C104–118/156/168–178/211–215;PRErenderaditiva/noPUBfuturo, finalrawrealNOTNULL |
| A02 | Minorprevio | corregido | C281frase21palabras, inventarioidéntico |
| B02 | Importantnuevo | pendiente confirmadoROOT | C219batch_idNULL contra0001:106NOTNULL/CHECKULID141/models155Mappedstr. ReservaCPU no insertable; relaxfueraADR74 |

0Critical/1Importantpendiente/0Minorpendiente. B02 reabre ✓ anterior por nuevaevidencia directaAST/baseline, no simpleopinión. A2 no detectóB02; ROOTacota ese ✓ deexcepciónSQL/NULL/reserva, no reescribe elveredictoA ni declara QAgreen. NODEBATE. RootAST/textolocalverifica batchidString26NOTNULLsinFK yNOtablaBatch; propiaagrupaciónCPUULIDsoluciónrutina sininferenciafake.

A2 yB2:120/120pins, sourceexactFIX1,497diff3docs y443sourceaddedlines; apéndices DATOS4126B/ITERACION2705B exactos/prefijos raw. AASTsourceSHA NOTNULL/metadata0006frozen; dosauditorfailpropiosCRLFblob/nullableORMimplicitcorregidos. BASTbatchNOTNULL/ORMMappedstr ytopologíaabstractapre/final(ciclofaltanterechaza), sinSQLreal; primerstdoutliteralacentuadostdinerrorcorregido. Noescrituras/SQL/ORM/app/DB/native/GPU/DockerWSL/services/install. Gatesruntime/T07siguenfuture.

ROOTeligeFIX2 mínimo: `Take.batch_id = cpu_pre_render_reservation.id` (ULIDrealpropio) como agrupacióndeestaoperaciónCPU, noBatchentity/inferenceniidpadre. MantenerNOTNULL/CHECK/index/históricos; columna noFK. Refs/plan/DTO/SQLdirect/portable/casos/adenda debenpropagarcoherenciafinitayrechazarNULL/parent/arbitrarygroup. No ampliar excepciónADR74. 2026-10-11T20:20:02.270160+00:00

## Tabla y gaps completos del intento1 preservados

# T05 — revisión documental O1, intento1

ROOT normaliza explícitamente las respuestas completas A1/B1 recibidas; no transcripción literal ni reconstrucción de ficheros de los revisores. C=creative-persistence-contract.md, T=tasks.md, ADR=ADR0074, relativos al snapshot fijado. C377líneas/SHA5f695a6d; diff425líneas/3docs, base484b83fd9fa2df9ed8abecf598983a63e29b66df. Todos ✓ son documentales, no ejecución.

| Criterio A | Resultado | Evidencia |
|---|---|---|
| A1 cierres | ✓ | T200–222/C377: T05 abierto, sin resultado producto |
| A2 alcance | ✓ | T207;3docs/fuera0/avisos0 |
| A3 tests requeridos | ✓ | C277–305 y T210 |
| A3 cobertura real | no verificable | C305/377: prosa antes RED |
| A4 excepción SQL | ✓ | Constitución39/ADR27–43/C31,159–168,230 |
| A4 canción/padres/maestro | ✓ | Constitución17,19/C98,149,170,256 |
| A4 server local/v1 | ✓ | Constitución31–35/C73,143,244–246 |
| A5 verificación tarea | no verificable | T216 pendiente, sin cierre |
| A6 interop/OpenAPI | ✓ n/a | ningún cambio spec/código/plugin |
| A6 docs afectadas | ✓ | datos441–451/iteración168–176/C311–339 |
| A7 guía prosa | ✗ | docs-style15/C228; A02Minor |
| T05 conservación/backup | ✓ documental | C218–236,291–297; runtime no verificado |
| T05 inferencia obligatoria | ✓ | C159–166,281 |
| T05 reserva CPU | ✗ | C104,106,151,161/models585/DDL0006;A01=B01 |
| DiscriminaciónNULL | ✓ | C159–166/ADR31–35 |
| CpuExecution aditivo/dispatch | ✓ | C73,106,162,201–214 |
| Plan/receipt/package | ✓ salvoA01 | C69,75–143 |
| Derechos/tools | ✓ | C96,129–143,170 |
| UNKNOWN | ✓ | C147–149,182,258/ADR51 |
| CiclosFK | ✓ salvoA01 | C104–106,283;no committrigger inventado |
| CAS/unique/retry | ✓ salvoA01 | C151–166 |
| SQLdirect/límitesSHA | ✓ | C164,168,281–290;SQL no certifica ejecución |
| Replay0006 | ✓ documental | C218–220/invariants671/0006:5,47 |
| Upgradeexclusive/backup | ✓ documental | C222–234 |
| Downgradepreffects | ✓ | C236,297 |
| Songv1bytes/digests | ✓ documental | C250–256,300 |
| Songv2closure | ✓ documental | C256–273 |
| Importnocustodia | ✓ | C258,302 |
| APIv2cuatro | ✓ documental | C240–244,298 |
| M1409beforeeffects/listwhole | ✓ | C246,299 |
| Previewnonefake | ✓ | C174–184,303 |
| T07gates | ✓ | C55,143,182,305,377 |

| Criterio B | Resultado | Evidencia |
|---|---|---|
| Reserva antesrender | ✗ | C104/151/161;B01=A01 |
| Tipos/dominiosSHA | ✓ | C63–69,188–214 |
| Refs/ciclos/activo-histórico | ✓ | C106,153;salvoB01 |
| NULL/unique/CAS/owner | ✓ | C159–170 |
| Fuente/tool/rights/UNKNOWN | ✓ | C129–149;T07gates |
| M1/replay0006 | ✓ | C218–220 |
| Upgrade/backup/FK/rollback | ✓ | C222–236 |
| APIv2/409 | ✓ | C240–246 |
| Songv1/v2/import | ✓ | C250–273 |
| Preview/cicloshash | ✓ | C174–186 |
| RuntimeSQL/ORM/API/render | no verificable | prosa antesRED |

| ID | Grado | Gap | Escenario | Estado |
|---|---|---|---|---|
| A01/B01 | Important | Source SHA imposible en reserva antes render | C104/106 reserva revision. SourceSHArawreal C69/161; models585 yDDL0006 NOTNULL. NULL violaDDL; marcador/padre falsea dominio; C151 impide fijarSHAdespués (sólo package/errorwriteonce). Trim/crossfade nuevo no tiene source propia aún | confirmado; FIX1 fresco |
| A02 | Minor | Frase63palabras | C228 primerafrase, docs-style15 regla1 unas25palabras orientativas | corregir duranteFIX1; no bloquea por sísolo |

0Critical/1Importantdeduplicado/1Minor, ningún rebate. A120/120SHA ydiffentero377líneas/425diff/3docs; ASTpuro0006source_sha NOTNULL con intérprete gestionado/stdin exit0, primerstdoutcp1252exit1 corregidoUTF8. B120/120SHA/diffbyteexact/ASTDDL ycontrasteNULL/padre/marker/inmutabilidad exit0. Ninguna escritura/SQL/ORM/appimport/DB/tests/servicios/GPU/native/DockerWSL/install porlentes; noQA niT05/M2green. Scope0/selectorCfalseDfalse/ledger0 con27avisosChangelog conservados.

ROOT elige corregir secuencia dentroO1/ADR0074: reserva CPU pre-render propia, aditiva y durable separada; PublicationIntentRevision final inmutable nace sólo después de fuente/recibo reales acreditados. No ampliarNULL de source_sha poranalogía ni placeholder ni nuevoganador. FIX1 debe cerrar IDs/refs/FK/estado/CAS/linaje/retry/publish/portable en toda matriz y apéndices, sin difundir defecto a otrocampo. Código/RED/schema aún no liberados; T05/M2abiertos. 2026-10-11T19:57:27.450769+00:00
