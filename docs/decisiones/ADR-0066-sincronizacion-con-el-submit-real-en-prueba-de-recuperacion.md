# ADR-0066 · Sincronizar la prueba de recuperación con el submit real

- **Estado:** aceptada bajo delegación del propietario; corrección de fixture, revisión y QA pendientes.
- **Fecha:** 2026-10-09.
- **Relacionadas:** [ADR-0018](ADR-0018-cola-de-jobs.md), [ADR-0043](ADR-0043-identidad-durable-de-intentos.md), [ADR-0062](ADR-0062-evidencia-sintetica-explicita-con-binding-del-server.md) y [ADR-0064](ADR-0064-verificacion-funcional-y-cobertura-con-coste-de-instrumentacion.md).

## Problema y evidencia

La QA independiente conservada falló en la aserción de un POST después de
`asyncio.sleep(0.35)`. El contador exacto de aquella ejecución es desconocido;
el fallo sólo acredita que no era uno. Las observaciones posteriores aislada,
contextual11 y prefijo225 pasaron y no explicaron su causa histórica.

Una auditoría independiente contrastó specCA09, los ADR de recuperación y
el runtime: no existe un requisito de POST antes de350ms. `start()` crea el
trabajo de recuperación sin esperar su submit; `poll_s` no es una latencia
máxima y `control_s` limita operaciones individuales, no toda la recuperación.

Una pareja controlada posterior mantuvo una respuesta `ConfirmedAbsent`
legítima pendiente durante0,45s. La copia de la prueba original observó cero
POST con status pendiente en su checkpoint y falló. El candidato esperó un
evento emitido después del submit real y conservó las cuatro aserciones:
un POST, petición exacta, contador de intento1 e identidad del mismo
`JobAttempt` en SQLite. El cierre terminó sin futuros nativos pendientes.
Root cotejó fuentes116/protegidas36/JUnit/counters. Evidencia en
`.cache/dev-cycle/m1/t05-recovery-qa-diagnosis1/causal-status-pair/root-causal-adjudication.json`.
La prueba demuestra el defecto de sincronización bajo esa condición controlada;
no prueba la causa del fallo histórico de QA.

## Alternativas y decisión

1. Conservar la espera fija y repetir la QA hasta un verde. No corrige el
   supuesto de observación que la prueba controlada refuta.
2. Aumentar la espera fija. Conserva el mismo supuesto sin observar el efecto.
3. Esperar el submit real de la fixture con un presupuesto finito. **Elegida.**

Sólo `test_absent_zero_cursor_resubmits_same_frozen_id` cambia su sincronización:
una subclase de fixture señala un evento después de `RecordedBackend.submit`
real, y la prueba espera ese evento con timeout finito de `runtime.control_s`.
Ese presupuesto es de la prueba, no una garantía nueva de recuperación global.
Se conservan literalmente las cuatro aserciones originales y el cierre en
`finally`. No se cambia `==1` por `>=1`, ni se interpreta timeout como éxito.
Los demás tests, parámetros, timers, guards y límites de query permanecen.

Se añade una regresión de respuesta de estado legítimamente retrasada que
falla antes de la corrección y pasa después. No se añade una exclusión de
cobertura ni se modifica el runtime. La composición sintética explícita y
los controles de autoridad/procedencia siguen intactos.

## Verificación y alcance

Esta excepción concreta actualiza la conservación absoluta de timers de
ADR-0062 sólo para la espera de observación mencionada. ADR-0064 conserva
su única omisión instrumentada del parámetro801 y su plazo original de10s.
Con la regresión añadida, los conjuntos esperados son601 funcionales completos
y600 instrumentados; se verifican sus IDs/orden y fuentes congeladas antes
de ejecutar. Cada uno de los ocho módulos completos debe superar80% combinado
con cero exclusiones de código. No se unen trazas ni pases históricos.

La corrección necesita revisión independiente y QA nueva. El resultado rojo
original se conserva; no se etiqueta como flake ni se acepta retrospectivamente.
Esta decisión no acepta T-05, no publica un WAV y no cierra el roadmap.
