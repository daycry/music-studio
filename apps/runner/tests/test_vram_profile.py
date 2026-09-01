"""Tests de la proteccion C1 de `vram_profile.py` (T-03).

Se prueba la funcion de decision factorizada (`es_adapter_degradado_a_mock`) y
su materia prima (`_meta_backend_adapter`), no el script entero: la regla es que
un adapter 'real' degradado al mock obliga a etiquetar TODO el informe como
mock, y esa decision tiene que ser correcta de forma aislada.
"""

from __future__ import annotations

import pytest

import vram_profile
from adapter import AceStepAdapter


class TestEsAdapterDegradadoAMock:
    @pytest.mark.parametrize(
        "meta",
        [
            {"backend": "mock", "source": None},
            {"backend": "unavailable", "source": None},
            {"backend": "gpu", "source": "mock"},   # describe() delata la simulacion
            {"backend": None, "source": "mock"},
            {"backend": "mock", "source": "mock"},
        ],
    )
    def test_detecta_degradacion(self, meta):
        assert vram_profile.es_adapter_degradado_a_mock(meta) is True

    @pytest.mark.parametrize(
        "meta",
        [
            {"backend": "gpu", "source": "gpu"},
            {"backend": "gpu", "source": None},
            {},  # sin datos no se acusa: la degradacion exige evidencia
        ],
    )
    def test_no_acusa_sin_evidencia(self, meta):
        assert vram_profile.es_adapter_degradado_a_mock(meta) is False


class TestMetaBackendAdapter:
    def test_lee_backend_y_source_de_un_adapter_real_degradado(self):
        # En esta maquina no hay CUDA: AceStepAdapter sin require_gpu cae al
        # mock, que es EXACTAMENTE el escenario del defecto C1.
        adapter = AceStepAdapter(mock=None, require_gpu=False)
        meta = vram_profile._meta_backend_adapter(adapter)
        assert meta["backend"] == "mock"
        assert meta["source"] == "mock"
        assert vram_profile.es_adapter_degradado_a_mock(meta) is True

    def test_adapter_con_require_gpu_queda_unavailable_y_degrada(self):
        adapter = AceStepAdapter(mock=None, require_gpu=True)
        meta = vram_profile._meta_backend_adapter(adapter)
        assert meta["backend"] == "unavailable"
        assert vram_profile.es_adapter_degradado_a_mock(meta) is True

    def test_objeto_sin_describe_no_revienta(self):
        class Pelado:
            backend = "gpu"

        meta = vram_profile._meta_backend_adapter(Pelado())
        assert meta["source"] is None
        assert vram_profile.es_adapter_degradado_a_mock(meta) is False


class TestLoadStageTimingsAdapter:
    def test_lee_las_etapas_de_carga_del_contrato_m3(self):
        class ConCabecera:
            def describe(self):
                return {"load_stage_timings_s": {"vram_load": 12.5, "warmup": 3.0}}

        etapas = vram_profile._load_stage_timings_adapter(ConCabecera())
        assert etapas == {"vram_load": 12.5, "warmup": 3.0}

    def test_sin_cabecera_devuelve_vacio(self):
        assert vram_profile._load_stage_timings_adapter(object()) == {}
