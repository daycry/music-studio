# ADR-0022 · Memoria técnica en Kwipu y Graphiti (herramienta de desarrollo, no de la app)

- **Estado:** aceptada · **Fecha:** 2026-09-28

## Contexto
El propietario tiene un stack Docker local, `knowledge-graphs`, definido fuera de este repositorio. Incluye:
- Kwipu, con su bridge en `127.0.0.1:8765` y un MCP por stdio;
- Graphiti MCP en `127.0.0.1:8001`, sobre FalkorDB;
- Ollama, con `qwen3.5:9b` y `nomic-embed-text`.

El plugin custom-agents puede publicar allí la memoria técnica curada (`docs/knowledge/approved/`).

## Decisión
- **Plugin** (`.claude/knowledge-services/taxonomy.json`):
  - `kwipu`: `markdown-export`, **activado**. Solo escribe: exporta Markdown y el plugin nunca lee de él.
  - `graphiti`: **activado en `mode: shadow`** (sincroniza, no lee) con `group_id: music-studio`, un grupo propio que no comparte el `knowledge-graphs` del stack. Pasará a `read` cuando `/doctor` lo dé por sano y `knowledge-sync.py --check` no muestre desfase.
- **Claude Code:** los dos se registran como servidores MCP con **alcance local**, en `~/.claude.json` del proyecto y no en `.mcp.json`. El repo es público y los servidores dependen de un stack que vive fuera de la carpeta.
  - `graphiti` → HTTP `http://127.0.0.1:8001/mcp`
  - `kwipu` → stdio `docker exec -i knowledge-graphs-kwipu-mcp-1 python kwipu_mcp_server.py`
- **Es una herramienta de desarrollo, no parte de la aplicación.** music-studio no depende de ella para funcionar, y esto no contradice [ADR-0005](ADR-0005-todo-en-la-carpeta.md): el stack no guarda nada del producto. Si el stack está apagado, el Knowledge Gate sigue funcionando en git y la exportación se reanuda más tarde.

## Consecuencia crítica: VRAM
Ollama carga `qwen3.5:9b` en la GPU (≈ 8,9 GB) cada vez que Kwipu indexa o responde. En la 5070 eso deja sin sitio a ACE-Step y, en WSL2, la GPU desborda a RAM sin avisar ([ADR-0007](ADR-0007-gpu-local-12gb.md)).

- **Regla de medición:** antes de cualquier trabajo real con GPU (M0 T-05 en adelante, y **siempre** antes del benchmark de T-09 y de la escucha), hay que:
  1. descargar de la VRAM el modelo de Ollama con `ollama stop <modelo>` (sin parar el servicio ni borrar el modelo);
  2. comprobar con `nvidia-smi` que la VRAM usada es ≤ ~1,6 GB (solo el escritorio).
- **Sincronizaciones:** no se lanzan (`knowledge-sync.py`) mientras haya un trabajo GPU en marcha.
- **Cómo liberarla (procedimiento del propietario, 2026-09-28).** Ollama es un **servicio systemd de la distro `Ubuntu` de WSL**: el contenedor `knowledge-graphs-ollama-1` es solo un nginx que hace de proxy hacia `host.docker.internal:11434`. **No se para el servicio ni se borra ningún modelo**: solo se **descarga de la VRAM** el que esté cargado.
  1. Ver qué hay cargado: `wsl -d Ubuntu -e ollama ps`
  2. Descargarlo: `wsl -d Ubuntu -e ollama stop <modelo>` (hoy `mimo:9b-q5`; el nombre exacto sale de `ollama ps` u `ollama list`)
  3. Comprobar: `nvidia-smi` → ≲ 1,6 GB usados
  4. Al terminar el trabajo con GPU, volver a cargar el que haga falta: `wsl -d Ubuntu -e ollama run <modelo>`

  Ojo: una petición de Kwipu vuelve a cargar el modelo en la VRAM. Durante una medición o generación larga no se usa Kwipu.
