# QA documental de la política NT S1

**64/64 comprobaciones, exit0. Aceptación documental; T-05 y M1 siguen abiertos.**

QA fresca verificó cuatro candidatos originales, cinco reemplazos exactos de metadatos y los cuatro documentos finales. Normativa y wire U1 permanecen idénticos; ocho enlaces locales resuelven. Inventarios de 91 entradas pre/post iguales durante esa ventana. ROOT verificó ocho artefactos sellados y las 91 entradas antes del CAS documental a las 07:34:48 UTC.

Comando real: `uv run --frozen --no-sync --all-packages python -B .cache/dev-cycle/m1/storage-nt-security-s1-qa-20261011/check_documentation.py`, con `scripts/env.ps1` cargado. Resultado:64/64; sin imports de producto, pytest, JUnit, Playwright o operaciones GPU/WSL. TDD/cobertura n/a:prosa. No se inventa un qa-gate UI.

Se conserva el primer exit1 del checker: patrón TODO sin frontera, dos comparaciones contra base en vez de candidato y lectura UTF-8 de un byte histórico del ledger. Se corrigió únicamente el checker; hashes siempre sobre bytes. stdout final genuino UTF-16LE; ROOT lo decodificó según BOM, sin alterar el raw. PDF no generado: dependencias ausentes y sin instalaciones autorizadas para esta unidad.

Evidencia congelada en `.cache/dev-cycle/m1/storage-nt-security-s1-qa-20261011`: checker, execution.receipt.json, raw-results.json, stdout/stderr final e inicial, report.md e inventory-seal.json. Sello SHA256:7c45a248b62f7bec8ae194399de40050115422b7acaf5c0565e098f369e2a64e. Recibos ROOT en `storage-nt-security-s1-review1-20261011`:qa-policy-root.receipt.json y adoption-root.receipt.json. El inventario previo al CAS sigue histórico; los cambios documentales posteriores autorizados no se atribuyen a sus SHA anteriores.

La política S1 rechaza grants peligrosos de terceros en toda la cadena. Dos SIDs no acreditados con MODIFY se confirmaron por handle en el host: **G2 completo sigue cerrado**. La excepción TrustedInstaller es sólo owner del root real del volumen del sistema, pendiente de bootstrap acreditado en producto. El positivo de creación protegida de un fixture no acepta producción/restart ni el resto de la cadena.

Véanse la [revisión completa](storage-nt-security-s1-review-2026-10-11.md), los [experimentos nativos](storage-nt-preparation-2026-10-11.md) y el [informe global](../current-validation-2026-10-10.md).
