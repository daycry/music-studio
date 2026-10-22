# Captura inicial del panel GPU

Tras la indicación del propietario «ya», se capturó el Administrador de tareas en Rendimiento → GPU a **2026-10-06T19:16:33.980Z**. El panel identifica la **NVIDIA GeForce RTX 5070** y muestra dedicada **1,3/12,0 GB**, compartida **0,1/15,8 GB**. Imagen privada: 1920×1032, 172951 bytes, SHA-256 `1ecbc876a41320f20250feceb5a99cd98de79c9e87e4ddda5be0b78a5d7a5298`. [Recibo](gpu-baseline-capture-receipt.json).

El sensor nativo DXGI→LUID→PDH se leyó después, a19:18:23–25UTC: compartida145,61328125MiB; dedicada1342,44140625/1341,56640625/1330,1875MiB. Todas las operaciones PDH devolvieron status0. Los valores son compatibles con el redondeo0,1/1,3GiB de la interfaz, pero estas lecturas no son simultáneas con la imagen. NVML1330MiB en ese instante; Ollama vacío. Esta lectura histórica no sustituye el preflight fresco antes de cada carga.

Edge volvió a aparecer en el inventario soportado con ventana8062574. La captura y un único reintento tras actualizar su selección devolvieron exactamente: `window is minimized; call activate_window, refresh with get_window, then retry get_window_state`. No se obtuvo ni guardó imagen de Edge, no se activó ni cambió la ventana y no se accedió a8768. Esta identidad difiere del HWND330702 histórico del navegador del benchmark; no se la sustituyó silenciosamente ni se construyó un handle inventado.

Se dispone ya de evidencia visual inicial del panel GPU. Siguen pendientes su contraste temporal durante carga representativa y la captura/identidad del navegador visible. La calibración formal y los prerrequisitos completos de la matriz160 permanecen incompletos. No se cargó modelo ni se inició inferencia; T09 continúa en progreso. TDDn/a: observación operativa, imagen y documentación.
