# K4a — revisión documental intento1

ROOT normaliza respuestas completasA1/B1,no transcripciónliteral. P=principaldesign/C2K2norm/IO=storage_journal_windows_io/T=tasks snapshot. Source24deb33e60443B/diff609líneas5docs/base db23ec342a9dbaaf8547b0ceb1b7e16f58fffc02. Los✓sondocumentales,no native/producto.

| CriterioA | Resultado | Evidencia |
|---|---|---|
| A1estado | ✓ | T202/T32/P383 |
| A2scope | ✓ | T208/5docs/fuera0avisos0 |
| A3testsTDDcoverage | ✓ documental | P37,383,406;futurewhole80 |
| A4Constitución | ✓ | C32,43,55/P54,406/ADR84:33 |
| A4ADRdecisions | ✓ | C73/ADR84:17/C2:434/K2:754 |
| A5verification | ✓ n/a cierre | T202,210,214open |
| A6interopOpenAPI | ✓ n/a | 5MDs |
| O1choice | ✓ | P113,117/optionsd2d0e22515B |
| FiniterootS1 | ✓ | P121,123/S1:22 |
| K2consumer | ✓ | P140,161,190/K2:144,154,158,168 |
| U1U2readonly | ✓ | P373,375,379 |
| K1currentvsnew | ✓ | P184,186/IO19,202;boundaryfuture |
| Source/extraction | ✓ | 41pins/source24deb33e/prefixes/extractbyteexact |
| SDKpinning | ✓ documental | P418,422/12MDsSHAbytes memoryonly |
| K4a-01 import/platform | ✓ documental | P196,198,387 |
| K4a-02 bootstrap/latch | ✓ documental | P123,129,388 |
| K4a-03 nominalidentity | ✓ documental | P133,161,352,389 |
| K4a-04 ABI/ReturnLength | ✓ documental | P200,209,243,390 |
| K4a-05 noimpersonation | ✓ documental | P260,277,391 |
| K4a-06 SID/group/bounds | ✓ documental | P245,247,392 |
| K4a-07 freshstats | ✓ documental | P262,266,267,285,393 |
| K4a-08 pin/thread | ✓ documental | P287,289,299,394 |
| K4a-09 revocation/candidate | ✓ documental | P295,297,44,395 |
| K4a-10 CREATE/K5 | ✓ documental | P147,190,396 |
| K4a-11 cuts/custody | ✓ documental | P329,340,342,397 |
| K4a-12 poisonshared | ✓ documental | P172,176,186,398 |
| K4a-13 locks | ✓ documental | P178,180,182,289,399 |
| K4a-14 workspacequotas | ✓ documental reportadoA;acotadoB01 | P303,317,321,323,400;acotadoB01 |
| K4a-15 close/freeonce | ✓ documental | P340,342,346,401 |
| K4a-16 sanitization | ✓ documental | P251,369,402 |
| K4a-17 ownpositive | ✓ documental reportadoA;acotadoB01 | P258,270,403;acotadoB01 |
| K4a-18 retire/reap | ✓ documental | P323,325,404 |
| K4a01–18runtime | no verificable | P383,406/runtimefalse |
| T05audio-publication | no verificable | T215 |
| T05ready/songjson/analysis | no verificable | T216 |
| T05cleanup/failed | no verificable | T217 |
| A7docs-style1 | ✓ | P123,129,299 |
| A7docs-style2 | ✓ | P125,289 |
| A7docs-style3 | ✓ | P285,287,297 |
| A7docs-style4 | ✓ | P77,97,135,303,385 |
| A7docs-style5 | ✓ | P50,52,437 |
| A7docs-style6 | ✓ | P329,340 |
| A7docs-style7 | ✓ | P119,194,254,327,371 |
| A7docs-style8 | ✓ | ESprosa/ENidentificadores/sin espejo |

| CriterioB | Resultado | Evidencia |
|---|---|---|
| K4a-01 import/platform | ✓ documental | P196–198 |
| K4a-02 bootstrap/latch | ✓ documental | P119–129,174–176 |
| K4a-03 nominalidentity | ✓ documental | P133–164,287 |
| K4a-04 ABI/ReturnLength | ✓ documental | P200–219,246/12pins |
| K4a-05 noimpersonation | ✓ documental | P261,269,277–281 |
| K4a-06 SID/group/bounds | ✓ documental | P248–250 |
| K4a-07 freshstats | ✓ documental | P263–268,285 |
| K4a-08 pin/thread | ✓ documental | P275,287–295,299 |
| K4a-09 revocation/candidate | ✓ documental | P285,297 |
| K4a-10 CREATE/K5 | ✓ documental | P149,190 |
| K4a-11 cuts/custody | ✓ documental | P329–348 |
| K4a-12 poisonshared | ✓ documental | P172–186 |
| K4a-13 locks | ✓ documental | P178–184,289–293 |
| K4a-14 workspacequotas | ✗B01 | P225,306/IO308–314 |
| K4a-15 close/freeonce | ✓ documental | P273,340–348 |
| K4a-16 sanitization | ✓ documental | P252,369 |
| K4a-17 ownpositive | ✗B01 | P125,225,403 |
| K4a-18 retire/reap | ✓ documental | P305–325 |

| ID | Grado | Gap | Escenario | Estado |
|---|---|---|---|---|
| B01 | Important | Workspace viola APIK1allocator | P225 pide length131328/alignment8; IO308–314/C2:194–196 exigenB≥512 y n%m=0. 8rechaza;131328con512tambiénrechaza. BootstrapnopasaQ0, quotas/positiveinviables | confirmadoROOT; FIX1fresh |

0Critical/1Important/0Minor, sinrebates. A44criteriosconformes reportados; ROOTacota K4a14/17 anteevidenciaB, no finge✓runtime nireescribeA. B18criterios completos. Estrictacustodia/Principal/SDK/locks/capabilities yscopesrestoconforme documentalmente. DoctrinaS1/C2/O2/Constituciónpreservada, ADR84propuesta nueva decoordinationprivada, no canon.

A/Bauditoresstdlibstdin managedPythonreadonly:41pins/source60443byteexact/options22515d2d0e/prefixesC2K2/coordinationextractexacta/diffentero/12SDKMDpinsSHAbytesmemoryonly. BPREFIJOASTREAL_allocate_aligned sinimport/nativereproduce131328/8ALIGNMENT_INVALID backend0,131328/512reject backend0,control131584/512validationpassed/backend0. PrimerselecciónASTauditorBerrócorrigido/no producto. Ledger0/1avisoUTF8histórico;scope5/fuera0excl0avisos0/CfalseDfalse. Noescrituras/SQL/ORM/DB/native/GPU/DockerWSL/services/install/QAreal.

ROOTeligeFIX1 compatible conC2 sinrelajarlo: logicalSDKworkspace131328B, arenaK1 length131584 (=ceil(131328/512)*512), alignment512; requestedN+B−1=132095B. SDKoffsets/fields continúanalign8dentro de base512;256Btailpaddingexplícito no apuntable comoSDKoutput, no counted twicesharedbacking. Actualizartodosbudgets/limits/preentry/closewhole/matriz/readers/ejemplos/apéndices yguardC2/newABIproof antesreview2/QA/RED. Prosa no nativecallvalidado; actualK1source sin cambios. 2026-10-11T20:25:28.516338+00:00
