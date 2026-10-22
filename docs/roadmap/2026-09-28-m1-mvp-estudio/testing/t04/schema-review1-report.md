# T04 relación durable — revisión1

Lentes A/B/C/D frescas, estáticas, sobre ocho fuentes. C se activa por generación SQL y D por migración/consultas. Resultado fusionado:0Critical,1Important,0Minor.

**R04-S01:** SQL admite un terminal sin ts porque el contrato wire permite default_factory; cada lectura ORM fabrica otra fecha. Root confirma la posibilidad en Event y el generador de guardas. Hace falta RED funcional y exigir timestamp durable sin modificar el contrato wire. No se acepta esta unidad ni se cierra T04. Revisión2 deberá incluir todos los veredictos originales y la corrección; QA después.
