"""No convertir run_s en inferencia ni importar torch en HTTP."""

import pytest
from engine_common import server


def test_direct_timing_is_propagated_and_not_invented():
    assert callable(getattr(server, "measured_telemetry", None)), (
        "Falta telemetría directa"
    )
    timing = {
        "version": 1,
        "clock": "perf_counter_ns_cuda_synchronized",
        "infer_start_ns": 1_000_000_000,
        "infer_end_ns": 3_000_000_000,
        "inference_s": 2,
        "audio_duration_s": 4,
        "rtf": 0.5,
        "scope": "upstream_generate_music",
        "cuda_sync": True,
        "output_index": 0,
    }
    rtf, extra = server.measured_telemetry({"inference_timings": [timing]})
    assert rtf == 0.5 and extra["inference_timings"] == [timing]
    assert server.measured_telemetry(None) == (None, {})
    with pytest.raises(Exception, match="INTERNAL"):
        server.measured_telemetry({"inference_timings": [{**timing, "inference_s": 9}]})
