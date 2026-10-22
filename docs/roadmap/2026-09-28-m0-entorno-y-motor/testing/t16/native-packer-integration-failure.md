# Fallo real del empaquetado nativo T-16

Las seis tomas terminaron con exit0; ambos grupos descargados, VRAM posterior1314MiB y contenedores propios eliminados. El empaquetado CPU posterior falló antes de copiar o normalizar audio.

Comando real: `uv run --frozen --no-sync --all-packages python .cache/dev-cycle/t16/native-resolution-packing/pack-comparison.py --session 01M47Q4EJZK09RBPA0ECWC57D4` → exit1, `KeyError: 'request'` en línea89, `native['request']['model_id']`.

El validador actual `validate_input_receipt` devuelve el sobre `planned/captured`; el pedido está en `planned.request`. El empaquetador histórico esperaba request en la raíz. Las cuatro lentes revisaron que el delta de configuración no introducía cambios de lógica. La QA20 de fragmentos probó publicación y linaje, sin cubrir este acoplamiento de retorno real. Su evidencia conserva ese límite; no se acredita pack completo.

Depuración con debug-root-cause y TDD: implementer fresco `fix_t16_native_packer_contract` prepara reproducción del bloque íntegro de validación con los seis recibos reales; después derivado mínimo, revisión y QA. No se toca el validador ni se relajan comprobaciones. No regenerar GPU ni sobrescribir tomas/recibos anteriores. CA3/4, calidad y M0 siguen abiertos.
