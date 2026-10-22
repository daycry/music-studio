# M2/T05 codecs — revisión2 completa y FIX2

ROOT normaliza FULL37A/14B;no transcripción literal. Base6e76c305/original126bea1b/71a4ea38→FIX1source2f49f5ec/tests908195df,diff2files1516+/8−. D1/T1referenciashistóricasconservadas;D2/T2fixed. A2no nuevosgaps,A01corregido/B01respaldado; B2B01corregido+B02nuevoImportant. ROOTacotaA2conformidaddispatchanteB02 real; noreescribepasado.

| CriterioA | Resultado | Evidencia |
|---|---|---|
| scope | ✓ | 2files/T207/C427,436 |
| contractADR74 | ✓ | a608b81f/ADR74 |
| strict/frozen/extra/numbers | ✓ funcional reportadoA | D39,44,92/T755,801,852,888 |
| refs/fieldsets | ✓ | D118–173,340–426,482–635,682–968,1010–1048 |
| canonical/limits | ✓ B01corregido/A2B2 | D2:69–119/contextencoderdecoder;8192/8193/32768NFDCRLFpositivos,extrasdepthsecrets32769negativos |
| wrappers3fields | ✓ | D267,430,632,767,965/T127,240,402,480,587 |
| planSHAown | ✓ | D195,273/T127,755 |
| capturewrappers/preflight | ✓ | D283/T142/REDcapture |
| CPU3ops/noinference | ✓ | D195–263/T127,975 |
| PREreservaNoPUB | ✓ | D139–150/T402,777 |
| batchderived | ✓ | D139,391,500,524/T127,777,1005 |
| root/paths/parents/maps | ✓ | D232–262/T755,1005 |
| parentslyricsrights/tools | ✓ B01corregido/A2B2 | D2:69–119/contextencoderdecoder;8192/8193/32768NFDCRLFpositivos,extrasdepthsecrets32769negativos |
| receiptown | ✓ | D443–479/T240,297,1005 |
| sourceframesduration | ✓ | D356–362,476–478/T240,297 |
| effectiveclaims | ✓ | D371,383,470–474/T297 |
| closurebindingauthorityclaims | ✓ | D482–552/T402,852 |
| packagefinalbinding | ✓ | D587–628,638–679/T402,424,852/REDbinding |
| finalfilesmasterdomains | ✓ | D555–628/T402,852 |
| previewnamespace | ✓ | D693–801/T480,1061 |
| previewcontext | ✓ | D709–740,971–991/T888,633 |
| previewpasses/outputs | ✓ | D813–961/T587,633,1033 claimsnotmeasure |
| outcomes | ✓ | D1019,1039/T646/REDoutcome |
| dispatchtuple/branch | ✗ acotado B02nuevo | D2:80 kindlist/dict→TypeErrorantesdominio;baselineCPU_CONTRACT_UNSUPPORTED |
| unknownversions | ✓ | D81,1058,1076,1123/T956/REDunsupported |
| M1bytes/seed0 | ✓ | D1074–1084,1116–1129/T899–953 |
| noVerifiedwriter | ✓ | Dwhole/reportpending |
| Constitutionlocal/song/server | ✓ | C17–20,33–44,81–87 |
| 11REDauthentic | ✓ | 11JUnit1FAIL0ERROR/preimagepinssame |
| TDDpercriterion | ✓ A01corregidoA2 | A2verificó87/87guardaypredicadoretirados/reescritos;XMLnodeid/argv/UTC/rawpreimage/imports7482pins |
| gatewholecoverage | ✓ candidatoFIX1histórico | 748PASS601/601lines61/62branches99.8492%0omit/excl;ROOT4085payload+87causal;A2confirma |
| M1librarybackup | no verificable | T215unchecked |
| schemaSQLORMmigration | no verificable | fullT05pending |
| rowIndexrealbindings | no verificable | unreleased |
| APIv2Songv2import | no verificable | fullT05pending |
| VerificationT05QA | no verificable | T210,217open/testschema notexecuted |
| interopOpenAPIdocsstyle | ✓ n/a | 2PYprivate |

| CriterioB | Resultado | Evidencia |
|---|---|---|
| strictclosedarraysnums | ✓ | D2:37–57,145/directnumbersliteralarrays |
| canonicalSHAdupeUTF8limits | ✓ | D2:60–137/12damagedJSONnegatives |
| exactT02lyricscapture | ✓B01corregido | D2:69–112/T2:1082,1108,1138,1166/context32k/NFDCRLF |
| CPUopsrootreplay | ✓ | D2:243/T2:128,143/validinferenceadmissionnegative |
| reserveparentsmapspathsbatch | ✓ | D2:282–307/cardinalityedgesunique |
| receiptSHAframesformat | ✓ | T2:241,298/29mutations |
| packagebindingclosure | ✓ | T2:403,425,853/14mutations |
| previewnamespace | ✓ | T2:481,889/11mutations |
| previewpassesgainoutputclose | ✓ | T2:588,634,1034/25mutations/secondpass |
| outcomes | ✓ | T2:647,2417/8negatives |
| dispatchmixedunknown | ✗B02nuevo | D2:80 nonhashablekind[]/{}beforetypedguard |
| M1byteslearnedseed0 | ✓conservado | goldenPostPlanv1/seed0direct+paststates |
| historynorebind | ✓ | T2:1006 |
| authoritySQLfullT05 | no verificable | scopepurecodec/noSQLORMpublicationreal |

| ID | Grado | Gap | Estado/evidenciaactual |
|---|---|---|---|
| A01 | Importantprevio | GuardasnuevasantesRED | corregidoA2;87literalesguardapredicadoborrados/reescritos/JUnit1FAIL0ERROR→1PASS,tests87byteidenticos,7482importsverificados |
| B01 | Importantprevio | LyricsContextanidado32k→8k | corregidoA2B2;encoderdecodercontextualexacto,330directinvocacionesB/positivos8192/8193/32768+8negativos |
| B02 | Importantnuevo | D2:80 dict.get(kind) nohashableescapaTypeError | B2 público/ASTkind[]y{}canonical/SHAcorrecto:oldCPU_CONTRACT_UNSUPPORTED→newTypeError;ROOTfunciónASTreal2casosantesr/lyricslookupconfirma |

0Critical/1Importantnuevo/0Minor,sinrebate/deuda. Scope2fuera0avisos0,C/Dauto false. FULLA2/R1estadosconservados, T05abierto/M2=4/30/fullSQL/API/library/nativepublishpending. AuditorAinicialsupusoLFvsCRLF, luego87correctobytesshaintactos; auditorBinitialParameterSet/helperSQLerrorescorregidosyhelperlegacyomitido, nofallosproducto/QA. Verdes330invocacionesAST noofficialpytest;748actorPASSauditednocuentaQAindependiente.

FIX2sólo2filesprivados: testREDfuncionalinvalidkindlist/dict enlectorpúblico/encoderdecoded noexceptionuntyped; validartipoexactoantesusarloclavedictionary, sincoerción/suffixmatches/recursosecretsdepthsizebypass ni cambiarwire/fieldsets/readersemánticabaseline. Guardcentralmínimo, casosextrasmalformedunknown/versions yregresiones32k+748/whole80. ScopeSQL/ORM/migration/api/importfullT05seconserva;revisión3FULL37A14B+A01B01B02yQAposterior. 2026-10-11T22:00:14.958411+00:00
