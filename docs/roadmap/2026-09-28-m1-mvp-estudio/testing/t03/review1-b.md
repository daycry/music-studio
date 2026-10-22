**Lente B · M1/T-03 · intento 1/3:** un defecto nuevo **Minor**.

| Criterio revisado | Resultado |
|---|---|
| OpenAPI desde FastAPI, exportación y comprobación de ambos contratos | ✓ |
| Generación real de tipos mediante `pnpm gen` | ✓ |
| Parsers sobre fixtures comunes y conservación literal/UTF-16 | ✗ Paridad incompleta fuera de los fixtures |

**Minor — `apps/server/app/lyrics.py:106` y `apps/web/lib/lyrics.ts:72`.** Para la entrada literal `"[Ⅳ]\n"` (U+2163), Python devuelve anotación y aviso `UNKNOWN_TAG`, mientras TypeScript devuelve `MALFORMED_TAG`. Python admite ese carácter numérico Unicode mediante `[^\W\d_]`; TypeScript lo excluye mediante `\p{L}`. La misma letra obtiene distinta clasificación en server y web. El original y sus rangos se conservan.

**Critical:** ninguno. **Important:** ninguno.

Evidencia: revisión estática exclusiva del contenido inline; sin ejecutar herramientas ni pruebas. Los resultados de ejecución aportados no son verificaciones independientes de esta revisión. No acredita cierre de T03, QA ni aceptación UI/E2E de M1.