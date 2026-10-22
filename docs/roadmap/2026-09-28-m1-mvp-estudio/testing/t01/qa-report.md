# QA técnica independiente — M1/T-01

Conforme:86pruebas CPU/2skip Windows, cobertura completa siete módulos201/202=99,50%, sin exclusiones. Verificación declarada80pass/8deselected y curl403. Las dos sondas Linux de symlink complementan los skips; no se cuentan como pytest adicionales.

Docker real reconstruido: paridad siete fuentes, sin torch, token interno200/401, puertos loopback, recursos limitados, datos persistentes privados, modelos solo lectura y cleanup propio vacío. Imagen `sha256:c51aaf2252297df6232d9efc67bfddacb169a17750c2f17a41015589613834e4`.

QA original:21casos HTTP/19conformes/2gaps por exigir403 a Host duplicado. [ADR-0040](../../../../decisiones/ADR-0040-frontera-parser-http-y-aplicacion.md) distingue el400 obligatorio del parser y el403 de aplicación; el suplemento independiente valida21/21 desde los originales sin repetir solicitudes ni alterar expectativas anteriores.444comprobaciones offline/105enlaces conformes; rebate A/B y revisión completa A/B/C sin gaps. [Recibo](qa-receipt.json).

Criterios técnicos de T-01 acreditados; integración Git pendiente. No acepta UI, manuales ni M1 completo, calidad musical o M0. Precio/modelo CLI reales desconocidos. Los fallos de caché Docker, sondeo httpx y comparación inicial SecretStr permanecen preservados con sus correcciones privadas.
