# Captura inicial de Edge en blanco

Las dos capturas autorizadas por el propietario están guardadas. La captura del [panel GPU](gpu-baseline-capture-report.md) se obtuvo antes. La de Edge se obtuvo a **2026-10-06T19:26:32.851Z** mediante la API soportada de la extensión del navegador. [Recibo](browser-baseline-capture-receipt.json).

La imagen privada `edge-blank-tab.jpg` contiene el viewport blanco de `about:blank`: JPEG921×873,5069bytes, SHA-256 `40f12d76e257355783e1a3ca87d192724e04289b2158cf2be16cd4b263f7ced7`. La selección partió de la pestaña nueva2032699336 del navegador1; la API devolvió esa misma identidad conURLabout:blank, sin llamada explícita de navegación. La lectura posterior de `document.visibilityState` devolvió `visible`. La captura no incluye el chrome del navegador.

La identidad se correlacionó por metadatos nativos de proceso: **PID6932/HWND8062574**, títuloabout:blank, ejecutablemsedge.exe, heartbeatvisibletrue. Esta ventana sustituye para el benchmark la identidad histórica6532/330702; no se cerró la ventana anterior ni se asumió que fuese la misma. Antes, la captura nativa había fallado por ventana minimizada; después cambió el estado y apareció una nueva pestaña. Se conserva aquella evidencia, no se reescribe como éxito.

El primer nombre de persistencia terminaba en.png antes de inspeccionar los bytes. La cabecera real esJPEG; se renombró únicamente el artefacto propio a.jpg, sin conversión ni cambios de contenido. La identidad y visibilidad posteriores son observaciones separadas del instante de captura. Deben comprobarse otra vez durante el benchmark.

No se accedió al contenido de8768, ni se activaron, navegaron o cerraron ventanas. No hubo carga de modelo ni inferencia. **Sigue pendiente la calibración del sensor durante una carga representativa**; disponer de las dos capturas iniciales no completa T09 ni la matriz160. TDDn/a: observación operativa y documentación.
