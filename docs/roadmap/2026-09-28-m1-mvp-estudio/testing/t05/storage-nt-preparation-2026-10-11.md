# Pruebas experimentales del almacenamiento Windows

ROOT verificó las entregas congeladas de dos experimentos nativos. Son evidencia de las APIs del host; **no aceptan U2, T-05 ni M1**.

| Comprobación | Resultado observado |
|---|---|
| Apertura relativa y creación exclusiva | Control02 exit0; crear sobre archivo existente rechaza sin alterarlo |
| Sharing entre lectores y escritor | Conflictos bilaterales esperados; dos lectores compatibles |
| Consulta de sectores por handle del archivo | NtQueryVolumeInformationFile, clase11, status0, Information28 |
| Geometría independiente | Logical512, atomic4096, performance65536, effective4096; SSINFO flags15, offsets0/0 |
| Buffer y transferencia sin caché | Bloque conservador65536; dirección alineada; 131072 bytes escritos exactamente |
| Barrera y relectura | FlushFileBuffers correcto; relectura por el mismo handle y tras nueva apertura idénticas |
| Identidad y cierre | Identidad intacta; handles192→203→192; cierres únicos y procesos propios restantes0 |
| Inventarios | 8 artefactos del nuevo experimento y 14 previos intactos; fuentes aceptadas sin cambios |

La consulta independiente tiene su propio contrato y flags. No se reinterpretaron los bits desconocidos de FileStorageInfo con la máscara de otra estructura. El primer intento fail-closed y sus bytes se conservan. La clase y los flags se contrastaron con [MS-FSCC](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-fscc/3e75d97f-1d0b-4e47-b435-73c513837a57) y la API user-mode con [Microsoft](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/nf-ntifs-zwqueryvolumeinformationfile).

65536 incluye el tamaño óptimo de rendimiento por una elección conservadora; no se presenta como mínimo obligatorio ni como tamaño atómico. El archivo nuevo conserva131072 bytes y SHA256 6e8717281480fcaafbd34a3da506a394a5f176c626e31f7519e3500061884667. No se acreditan capacidad completa, streams, 64slots, crash, restart ni durabilidad eléctrica.

Los instrumentos son privados y experimentales: TDD n/a, sin adopción de código de producto. La futura implementación requiere sus propios RED causales, revisión y QA. Los originales están en .cache/dev-cycle/m1/storage-nt-abi-preparation-20261011 y storage-nt-sector-probe-20261011; ROOT verificó sus sellos, raw, fixture, orden Write→Flush→Read, fuentes y procesos. Recibo ROOT: storage-journal-codec-review2-20261010/sector-probe-root.receipt.json.

ROOT eligió la política estricta S1 para producción. La creación protegida de objetos nuevos sólo aporta evidencia limitada de lease. La alternativa S3 queda aplazada por sus premisas abiertas de bootstrap y replay. La decisión documental y los descriptors por handle siguen en preparación; ninguna ACL existente se modificó. Un descriptor insuficiente debe cerrar el gate, no convertirse en un positivo simulado.

Véase el [informe global vigente](../current-validation-2026-10-10.md).


## Ampliación verificada de ROOT — 20261011T074038Z

El párrafo anterior registra el estado de preparación previo. S1 quedó incorporada documentalmente tras revisión A/B sin gaps y QA64/64exit0; [revisión](storage-nt-security-s1-review-2026-10-11.md) y [QA](storage-nt-security-s1-qa-2026-10-11.md). G2 por handle confirma los grants MODIFY de dos terceros; host completo no admitido. Creación protegida del fixture positiva limitada. Negativo con reparse real no acreditado: intento symlink1314 sin elevar privilegios.

G4 sí verifica ahora la extensión completa experimental:75563008 bytes de ceros en73writes exactas alineadas, FlushFileBuffers,73reads exactas sin diferencias. SHA256:a09d7ea396297c226ba6b6b3f9a6b81a450d91bb4c8265bf73e88f0b55dcdefe. Tres fixtures conservadas; AllocationSize82837504 no equivale a cuota exacta. Un stream::$DATA, sin sparse/compression, identidad y SD por handle iguales. Buffers propios<=3276808B; no medición RSS. Inventario25artefactos y5PIDs propios restantes0 verificados por ROOT.

Se conservan dos intentos exit1 por incremento de handles asociado causalmente a dos objetos streaming hash propios. Pruebas mínimas muestran +1 por objeto y vuelta al baseline al liberar el objeto; control03 guarda digest y libera esos objetos, baseline173→184→173exit0. No se cerraron handles opacos. Un diagnóstico de generación del informe no prueba salida de procesos; recibo válido posterior de cleanup verifica5PIDs.

Evidencias privadas congeladas:storage-nt-policy-probe-20261011 y storage-nt-capacity-probe-20261011. Recibos ROOT:qa-policy-root.receipt.json y adoption-root.receipt.json en storage-nt-security-s1-review1-20261011. No adopción de prototipos a producto, TDD n/a experimental; no journal/cabecera/commit/crash/ACK/producción/power loss ni cierreM1.


## Junction real: actualización ROOT

[Informe verificado](storage-nt-reparse-experiment-2026-10-11.md). Los párrafos anteriores conservan el estado previo: ahora hay un experimento real limitado, con éxito de apertura del alias y rechazo por metadata, sin traversal. Original exit1 por contador+1 conservado; no acredita G1 completo ni producción.
