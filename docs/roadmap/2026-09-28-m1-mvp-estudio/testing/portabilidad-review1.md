# Revisión de portabilidad y entradas web — intento 1

Revisión adversarial con cuatro contextos frescos. El diff acotado comprende nueve archivos de T-05 U1 y T-08 U1/U2; la preparación corregida dio cero archivos fuera de alcance y ningún aviso. No acredita tareas completas, Docker ni E2E.

| Lente | Resultado | Evidencia y límites |
|---|---|---|
| A · requisitos | 0 Critical / 0 Important / 0 Minor | Recorrió los nueve archivos, RED conductuales, JUnit y coberturas individuales. Raíz opcional, esquema idéntico, paquete instalado e importación opaca/contexto cumplen el alcance. CA completos de T-05/T-08 siguen abiertos. |
| B · corrección | 0 Critical / 0 Important / 1 Minor | Reprodujo en memoria `integrity=null` y `1`: `fetch_web_dependencies.py:230` lanza `AttributeError` en lugar del error tipado y retorno CLI 2. Rechaza antes de publicar. |
| C · seguridad | 0 Critical / 0 Important / 0 Minor | Comprobó autoridad ROOT, pins, aliases, escapes y preservación de destinos. Las pruebas con callbacks y revalidaciones no certifican custodia universal frente a sustitución concurrente. |
| D · rendimiento | 0 Critical / 0 Important / 0 Minor | Sondas AST muestran coste lineal en 609 archivos y 1562 entradas. Observó reserva transitoria de unos 256 MiB en una lectura limitada; no midió RSS/commit ni una degradación material. Los 1156 s son duración de suite. |

Los revisores leyeron las baselines actuales de audio (228 PASS, 4 omisiones de symlink Windows) y web (59 PASS, sin omisiones); no repitieron suites. Cobertura individual: manifiesto 92,40 %, pipeline 96,24 %, importador 93,41 % y contexto 90,91 %, sin exclusiones ni unión de trazas históricas. Los nueve tamaños/SHA actuales se cotejaron.

## Adjudicación adicional del orquestador

**ROOT1-02 · Important · T-08:** las fixtures permanentes contienen rutas fijas a `t08-stable-build-inputs-unit1/source-copies` y `fixtures/archives609`. Sin esa historia privada, ambas fixtures reproducen `FileNotFoundError`. La sonda se hizo en un directorio propio, sin borrar la historia existente. Deben usar fuentes actuales del proyecto y herramientas preparadas en sus rutas estables, con prerrequisitos explícitos.

Se autoriza corregir ROOT1-02 y el Minor B1-01 antes de la QA de web. T-05 U1 queda disponible para QA independiente porque sus fuentes no necesitan esa corrección. Las siguientes revisiones conservan el contador de estas unidades y los contadores históricos del frontend.

## Custodia

La primera preparación falló antes del despacho: el ledger no expresaba todas las rutas con el formato que reconoce el parser, y el snapshot posterior de audio se usó indebidamente como preimagen de los nuevos módulos web. Se preservó esa preparación y se corrigió: el diff efectivo incluye los nueve cambios reales.

Después del preflight, el orquestador añadió únicamente una fila legal de FFmpeg Linux al corpus congelado de 1885 archivos. Ese cambio documental se registró por separado; las nueve fuentes de producción y tests permanecieron intactas. Descendientes de FFmpeg/build no inventariados individualmente siguen UNKNOWN; los archivos de distribuciones conservados tras otro build no se atribuyen a la fixture anterior.

La evidencia privada está en `.cache/dev-cycle/m1/portable-audio-web-inputs-inspection1-preflight-repair1/`. Los resultados aquí son un resumen de los retornos nativos, no logs CLI fabricados.
