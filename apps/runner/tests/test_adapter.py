"""Tests del adapter de ACE-Step (T-05) que corren SIN GPU y sin torch.

Se prueba el camino mock del `AceStepAdapter` (delegacion en `_mock.py`), que es
exactamente el camino verificable en la maquina de desarrollo, y las utilidades
puras (`_slug`). El contrato nuevo de telemetria (M-3) se verifica aqui por las
dos vias: el mock directo y el adapter delegando en el.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import re

import pytest

import _timing
from _mock import MockMusicModelAdapter, make_request
from adapter import AceStepAdapter, _slug
from contracts import RunnerContext


def _ctx(**cambios):
    base = dict(
        device="mock",
        dtype="bfloat16",
        offload=False,
        weights_dir="/weights",
        max_gpu_seconds=600,
    )
    base.update(cambios)
    return RunnerContext(**base)


def _correr(corrutina):
    return asyncio.run(corrutina)


# --------------------------------------------------------------------------- #
# _slug (menor 3: sin colisiones silenciosas)
# --------------------------------------------------------------------------- #

class TestSlug:
    def test_sanea_caracteres_raros(self):
        slug = _slug("clave/con espacios y..raros!?")
        # Solo caracteres seguros para nombre de fichero.
        assert re.fullmatch(r"[A-Za-z0-9_-]+", slug)

    def test_incluye_hash_corto_del_texto_original(self):
        slug = _slug("clave-simple")
        assert re.search(r"-[0-9a-f]{8}$", slug)

    def test_trunca_pero_conserva_el_hash(self):
        slug = _slug("x" * 500, limite=64)
        assert len(slug) == 64 + 1 + 8  # parte limpia + '-' + hash
        assert re.search(r"-[0-9a-f]{8}$", slug)

    def test_texto_vacio_tiene_nombre(self):
        assert _slug("").startswith("generacion-")

    def test_claves_distintas_que_sanean_igual_no_colisionan(self):
        # "a b" y "a-b" limpian ambas a "a-b": sin el hash, el segundo WAV
        # sobrescribiria el primero en silencio.
        assert _slug("a b") != _slug("a-b")

    def test_claves_largas_con_mismo_prefijo_no_colisionan(self):
        base = "k" * 100
        assert _slug(base + "1") != _slug(base + "2")

    def test_determinista(self):
        assert _slug("misma-clave") == _slug("misma-clave")


# --------------------------------------------------------------------------- #
# Contrato de telemetria M-3 (gpu_seconds sin coste de carga)
# --------------------------------------------------------------------------- #

class TestContratoGpuSecondsMock:
    def test_generacion_no_incluye_coste_de_carga(self):
        mock = MockMusicModelAdapter()
        ctx = _ctx()

        async def flujo():
            await mock.load(ctx)
            return await mock.generate(make_request(idempotency_key="t-m3-mock"))

        resultado = _correr(flujo())
        tel = resultado.telemetry
        carga = mock.load_gpu_seconds()
        assert carga > 0.0  # el arranque simulado cuesta algo
        # gpu_seconds cubre SOLO la inferencia de esta generacion...
        assert set(tel.stage_timings) == {"inference"}
        assert tel.gpu_seconds == pytest.approx(tel.stage_timings["inference"])
        # ...y no arrastra el coste del arranque.
        assert tel.gpu_seconds < carga + tel.stage_timings["inference"]

    def test_coste_de_carga_reportado_una_vez_en_metadata(self):
        mock = MockMusicModelAdapter()
        ctx = _ctx()

        async def flujo():
            await mock.load(ctx)
            await mock.generate(make_request(idempotency_key="a"))
            await mock.generate(make_request(idempotency_key="b"))

        _correr(flujo())
        meta = mock.report_metadata()
        assert meta["source"] == "mock"
        assert meta["load_gpu_seconds"] == pytest.approx(mock.load_gpu_seconds(), abs=1e-3)
        # Las etapas de carga viven en la cabecera, no en cada generacion.
        assert set(meta["load_stage_timings_s"]) >= {"vram_load", "warmup"}
        # Y solo cuentan las etapas que retienen GPU.
        esperado = sum(
            v
            for k, v in mock.load_stage_timings().items()
            if k in _timing.GPU_STAGES and k != "inference"
        )
        assert mock.load_gpu_seconds() == pytest.approx(esperado)


class TestContratoGpuSecondsAdapter:
    def test_adapter_en_modo_mock_cumple_el_contrato(self):
        adapter = AceStepAdapter(mock=True, output_dir=None)
        ctx = _ctx()

        async def flujo():
            await adapter.load(ctx)
            r1 = await adapter.generate(make_request(idempotency_key="t-m3-1"))
            r2 = await adapter.generate(make_request(idempotency_key="t-m3-2"))
            return r1, r2

        r1, r2 = _correr(flujo())
        for resultado in (r1, r2):
            tel = resultado.telemetry
            assert set(tel.stage_timings) == {"inference"}
            assert tel.gpu_seconds == pytest.approx(tel.stage_timings["inference"])
        describe = adapter.describe()
        assert describe["source"] == "mock"
        assert describe["load_gpu_seconds"] > 0.0
        assert set(describe["load_stage_timings_s"]) >= {"vram_load", "warmup"}

    def test_generate_sin_load_es_error(self):
        adapter = AceStepAdapter(mock=True)
        with pytest.raises(RuntimeError):
            _correr(adapter.generate(make_request(idempotency_key="sin-load")))

    def test_load_idempotente_y_unload_reutilizable(self):
        adapter = AceStepAdapter(mock=True)
        ctx = _ctx()

        async def flujo():
            await adapter.load(ctx)
            await adapter.load(ctx)  # segunda llamada: no recarga (M-1)
            salud = await adapter.health()
            assert salud.ready
            await adapter.unload()
            salud = await adapter.health()
            assert not salud.ready
            await adapter.load(ctx)  # tras unload, load vuelve a funcionar
            return await adapter.health()

        assert _correr(flujo()).ready

    def test_unload_espera_a_las_generaciones_en_vuelo(self):
        # M-1: un unload lanzado con una generacion en vuelo no libera nada
        # hasta que esta termina; la generacion no ve el estado a medias.
        adapter = AceStepAdapter(mock=True, mock_time_scale=0.001)
        ctx = _ctx()

        async def flujo():
            await adapter.load(ctx)
            tarea = asyncio.create_task(
                adapter.generate(make_request(idempotency_key="en-vuelo"))
            )
            await asyncio.sleep(0)  # deja que la generacion se registre
            await adapter.unload()  # debe esperar, no romper la generacion
            return await tarea

        resultado = _correr(flujo())
        assert resultado.artifacts


# --------------------------------------------------------------------------- #
# Integridad de los pesos (revision 2026-09-03, hallazgo I-1)
# --------------------------------------------------------------------------- #

class TestIntegridadDePesos:
    """`_verificar_integridad` no puede depender de que el lanzador se acuerde de
    exportar `ACE_STEP_WEIGHTS_SHA256`: `generar.cmd` no lo hacia y las pistas
    salian sin contrastar el artefacto con el hash que el fusor escribio en el
    `.provenance.json` hermano. Ahora ese fichero es la fuente por defecto, la
    variable manda si esta, y saltarse la comprobacion exige decirlo y avisa.
    """

    @staticmethod
    def _pesos(tmp_path, contenido: bytes = b"pesos de juguete"):
        ruta = tmp_path / "juguete.safetensors"
        ruta.write_bytes(contenido)
        return ruta, hashlib.sha256(contenido).hexdigest()

    @staticmethod
    def _provenance(ruta, sha: str) -> None:
        ruta.with_suffix(".provenance.json").write_text(
            json.dumps({"artifact": {"sha256": sha}}), encoding="utf-8"
        )

    @staticmethod
    def _adapter():
        return AceStepAdapter(mock=None, require_gpu=False)

    @pytest.fixture(autouse=True)
    def _entorno_limpio(self, monkeypatch):
        monkeypatch.delenv("ACE_STEP_WEIGHTS_SHA256", raising=False)
        monkeypatch.delenv("ACE_STEP_SKIP_INTEGRITY", raising=False)

    def test_sin_variable_usa_el_provenance_hermano(self, tmp_path, caplog):
        ruta, sha = self._pesos(tmp_path)
        self._provenance(ruta, sha)
        with caplog.at_level("INFO"):
            self._adapter()._verificar_integridad(str(ruta))
        assert "verificada" in caplog.text
        assert "provenance" in caplog.text

    def test_provenance_hermano_con_hash_distinto_aborta(self, tmp_path):
        ruta, _ = self._pesos(tmp_path)
        self._provenance(ruta, "0" * 64)
        with pytest.raises(RuntimeError, match="Integridad de pesos fallida"):
            self._adapter()._verificar_integridad(str(ruta))

    def test_sin_variable_ni_provenance_avisa_de_que_no_verifica(self, tmp_path, caplog):
        ruta, _ = self._pesos(tmp_path)
        with caplog.at_level("WARNING"):
            self._adapter()._verificar_integridad(str(ruta))
        assert "NO verificada" in caplog.text

    def test_un_provenance_ilegible_no_se_confunde_con_ausente(self, tmp_path):
        ruta, _ = self._pesos(tmp_path)
        ruta.with_suffix(".provenance.json").write_text("{esto no es json", encoding="utf-8")
        with pytest.raises(RuntimeError, match="provenance"):
            self._adapter()._verificar_integridad(str(ruta))

    def test_la_variable_de_entorno_manda_sobre_el_provenance(self, tmp_path, monkeypatch):
        ruta, sha = self._pesos(tmp_path)
        self._provenance(ruta, sha)
        monkeypatch.setenv("ACE_STEP_WEIGHTS_SHA256", "1" * 64)
        with pytest.raises(RuntimeError, match="Integridad de pesos fallida"):
            self._adapter()._verificar_integridad(str(ruta))

    def test_saltarse_la_comprobacion_exige_decirlo_y_avisa(self, tmp_path, monkeypatch, caplog):
        ruta, _ = self._pesos(tmp_path)
        self._provenance(ruta, "0" * 64)
        monkeypatch.setenv("ACE_STEP_SKIP_INTEGRITY", "1")
        with caplog.at_level("WARNING"):
            self._adapter()._verificar_integridad(str(ruta))  # no aborta
        assert "NO verificada" in caplog.text
        assert "ACE_STEP_SKIP_INTEGRITY" in caplog.text
