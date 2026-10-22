# T04 — relación durable de intentos, unidad parcial

Siete fuentes custodiadas tras salida real0. La migración0005 añade JobAttempt sin modificar0001–0004; snapshots incorporan intentos y aceptan históricos sin inventar identidades. 89 pruebas nuevas pasan. Cuatro módulos completos superan93% de cobertura, sin exclusiones.

La suite de BD conserva212 pases,1skip Windows y8 fallos por una expectativa histórica de head0004 frente al head0005 actual. Se conservan los originales. Root rechaza simular head mediante monkeypatch: la migración de pruebas deberá separar explícitamente el ciclo histórico0004 del ciclo actual0005. Revisión independiente y QA pendientes. Dispatcher, backends, recuperación ejecutable y ocho criterios de T04 permanecen abiertos.
