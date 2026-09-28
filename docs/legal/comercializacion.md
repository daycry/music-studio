---
documento: comercializacion
titulo: Checklist antes de comercializar (gate GC)
estado: vigente — no bloquea el uso personal
fecha: 2026-09-28
actualizado: 2026-09-28
---

# Antes de comercializar — gate GC

Mientras music-studio sea **de uso personal**, nada de esta página bloquea el desarrollo. Si algún día el audio generado se usa en trabajos para terceros, se vende, o la herramienta se ofrece a otras personas, **todos** estos puntos deben cerrarse antes.

Hereda el gate GC-01 de la documentación anterior ([`../archive/roadmap-2026-07-27/2026-07-27-plataforma-musical-ia/gates/gobernanza.md`](../archive/roadmap-2026-07-27/2026-07-27-plataforma-musical-ia/gates/gobernanza.md) §8), simplificado.

## La verdad incómoda (leer primero)

Usar modelos de pesos abiertos **no hace que el audio tenga procedencia más limpia que Suno**: lo hace **mejor documentado**. La licencia de los pesos (MIT, Apache 2.0…) cubre el modelo y su código, **no** los datos con los que se entrenó. Los proveedores declaran el origen de sus datos, pero nadie lo audita. Suno y Udio fueron demandados en 2025 precisamente por los datos de entrenamiento.

Consecuencia: la única vía a derechos realmente limpios es entrenar o afinar sobre catálogo propio con licencia (fuera de alcance hoy).

## Checklist

| # | Punto | Qué hay que tener |
|---|---|---|
| GC-a | Posición legal sobre el audio generado con modelos cuyo corpus no está auditado | Consulta a un abogado de PI, por escrito |
| GC-b | ¿Es protegible / licenciable en exclusiva un audio generado sin autoría humana suficiente? (en la UE puede no serlo) | Respuesta escrita; condiciona qué se promete a un cliente |
| GC-c | Licencias de **todos** los pesos y herramientas del pipeline para uso comercial | [`licencias.md`](./licencias.md) sin ninguna fila en rojo para uso comercial |
| GC-d | Condiciones de uso de servicios de terceros usados como referencia (p. ej. Suno en comparativas) | Verificadas; nada de su salida en producto |
| GC-e | Datos personales: RGPD, retención y borrado; **imagen de personas reales** en vídeos (fotos subidas, LoRA de personaje) | Política escrita; consentimiento documentado y borrado de fotos y LoRA a petición; DPIA si hubiera voz o imagen de terceros a escala |
| GC-f | Marcas: nombre del producto, repositorio y dominio sin referencias a marcas de terceros («suno», etc.) | Renombrado hecho |
| GC-g | Multiusuario: autenticación real, aislamiento, cuotas, límites de gasto | Hito propio en el roadmap |
| GC-h | Watermarking / credenciales de contenido (C2PA) si el destino lo exige | Decisión documentada en un ADR |

## Lo que ya se hace desde el día 1 para no cerrar esta puerta

- Manifiesto de procedencia por artefacto (modelos, hashes de pesos, licencias, parámetros, semilla, linaje, entradas con derechos y consentimiento, proveedor, `commercial_use`).
- Registro de licencias de cada modelo y herramienta **antes** de integrarlo.
- Esquema de datos con `owner_id` en las entidades, aunque solo exista un usuario.
- Declaración de autoría de la letra en cada generación (propia · generada por el asistente · dominio público · con permiso).
