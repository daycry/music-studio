# Compatibilidad sintética y fixture de recuperación — revisión2

Las lentes A/B/C/D terminaron sin nuevos gaps. Se conserva la revisión1,
con cero gaps pendientes; únicamente el archivo de recuperación cambió
después de aquella aprobación. Los revisores son actores nativos existentes,
independientes del productor y QA, con contexto reutilizado declarado.
Realizaron lectura estática y cotejo de metadatos.

| Criterio | Resultado |
|---|---|
| Registro confiado, leases, rebind y captura write-once | Aprobación anterior conservada; seis módulos runtime idénticos. |
| JSON/SHA learned y evidencia sintética explícita | Conservados sin cambios de autoridad o privacidad. |
| Evento después del submit real | La subclase espera `super().submit`, señala y devuelve su respuesta. |
| Timeout y limpieza | Presupuesto finito de prueba; timeout falla y el cierre permanece en finally. |
| Cuatro aserciones y otros tests | POST exacto, request, contador e ID durable intactos; otros dos tests completos conservados. |
| Regresión retrasada | Respuesta legítima retrasada0,45s; RED antes del fix y GREEN sobre el test canónico. |
| Selección y cobertura | Nuevas601 funcionales/600 instrumentadas, única omisión801 en cobertura, WHOLE8≥83,52% sin excluir código. |

Root comprobó2677 archivos privados, fuentes actuales16/116,51 protegidos,
16 preimágenes y8126 herramientas. Los resultados del productor no sustituyen
la QA independiente. La tabla literal anterior de B no estaba conservada;
su adjudicación de cero gaps se mantuvo sin inventar esa tabla histórica.
Las cuatro salidas nativas originales y la fusión están en
[la evidencia privada](../../../../../.cache/dev-cycle/m1/t05-synthetic-compatibility-review2/root-adjudication.json).

La demora controlada prueba el defecto de sincronización bajo esa condición;
la causa del fallo histórico de QA permanece desconocida. Los30s son un
presupuesto de prueba, no una garantía global del producto. No se acreditan
HTTP real, SQL integral, publicación WAV, Docker o T-05 completa.

Se libera QA independiente601/600 sobre las fuentes congeladas. T-05 sigue
en progreso; su estado y verificación completos permanecen en el ledger.
