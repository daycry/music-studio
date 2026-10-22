# ADR-0051 — Dependencias web fijadas y uso local

- **Estado:** aceptada; instalación, compatibilidad y QA pendientes
- **Fecha:** 2026-10-08
- **Decisor:** orquestador bajo mandato autónomo explícito
- **Ámbito:** M1/T08; complementa ADR-0048 y conserva producto Docker de ADR-0035

Se eligen los23 pins exactos ya revisados y el lock candidato de609 artefactos oficiales, con metadatos e integridades SRI/SHA1/SHA256 comprobados. Las declaraciones reales de package.json, textos y avisos se mantienen separados de suplementos upstream. Se acepta su uso local para desarrollo, build y runtime con sus condiciones; no se concluye que todo bundle sea MIT ni se acredita redistribución. El [registro completo](../legal/dependencias-web-m1.md) contiene las filas y [datos fijados](../legal/dependencias-web-m1.json).

Se autoriza al implementador a adoptar esos manifiestos/lock e instalar mediante Node/pnpm verificados y `--frozen-lockfile --ignore-scripts`, con store/cache/state/config/tmp dentro del proyecto y cambio automático de gestor desactivado. No usar pnpm de perfil, Corepack ni scripts lifecycle. Build/test explícitos de las dependencias fijadas están autorizados; descargar navegadores, herramientas del sistema o base Linux requiere sus pins y licencias propias antes de incorporarlos. El instalador y sus efectos deben verificarse; esta decisión no declara que ya hayan pasado.

Dos TAR oficiales contienen únicamente una pareja de nombres normalizados duplicados, con contenido idéntico comprobado. Se permite su instalación ordinaria por pnpm sólo para estos artefactos:

| Paquete | SHA256 del TAR | Alias normalizados | SHA256 de ambos miembros |
|---|---|---|---|
| agent-base@7.1.4 | 7dd4a61668a9a4e8d4e903f1a254f94d53dafd3f316f2b9b597c5ad8c79cb57e | `package/./dist/index.js` y `package/dist/index.js` | c6503bd5e007db8b73fedf07b6eaaf4a94d5541953f0d06c8a17d1644c29a0c5 |
| https-proxy-agent@7.0.6 | 960f89e8e5240882f64249d04a538421dd39d62ffacc138544647cc3251bc0e0 | `package/./dist/index.js` y `package/dist/index.js` | 30165586fac3becbc9dbf2b7b5bdaa802a77ac34af9926208f6e94a3bd87ef31 |

Los12 miembros por archivo son regulares, de tamaño acotado y rutas dentro de package; no hay otra colisión, enlace o dispositivo. La lectura fue inerte. El auditor DATA conserva su rechazo histórico de duplicados; no se lo presenta como un fallo del instalador que todavía no se ejecutó. No se modifica ni se flexibiliza el extractor de herramientas de fetch_web_tools. Cualquier otra pareja, bytes diferentes, escape o artefacto no fijado queda fuera de esta decisión.

Para redistribuir se deben conservar licencias/avisos y cumplir fuente cubierta MPL, fuentes/reemplazo/re-enlace LGPL, atribución CC-BY y condiciones OFL según componente. Uso local y distribución son gates distintos. Declaraciones publicadas no constituyen una garantía de derechos universales. Esta decisión no acredita UI/E2E, build,los seis criterios de T08, GPU, calidad musical ni cierre de M1.
