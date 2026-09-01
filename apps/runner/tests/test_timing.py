"""Tests de `spikes/_timing.py`: estadisticas, decision de offloading e informes."""

from __future__ import annotations

import json

import pytest

import _timing


# --------------------------------------------------------------------------- #
# _percentile / summarize
# --------------------------------------------------------------------------- #

class TestPercentileYSummarize:
    def test_percentile_una_muestra(self):
        assert _timing._percentile([7.0], 0.95) == 7.0

    def test_percentile_interpola(self):
        # p50 de [0, 10] interpola al punto medio.
        assert _timing._percentile([0.0, 10.0], 0.5) == pytest.approx(5.0)

    def test_percentile_extremos(self):
        datos = [1.0, 2.0, 3.0, 4.0]
        assert _timing._percentile(datos, 0.0) == 1.0
        assert _timing._percentile(datos, 1.0) == 4.0

    def test_summarize_valores_conocidos(self):
        stats = _timing.summarize([1.0, 2.0, 3.0, 4.0, 5.0])
        assert stats.n == 5
        assert stats.mean == pytest.approx(3.0)
        assert stats.median == pytest.approx(3.0)
        assert stats.min == 1.0
        assert stats.max == 5.0
        # p95 de 5 muestras: interpolacion entre las dos ultimas.
        assert stats.p95 == pytest.approx(4.8)

    def test_summarize_serie_vacia_es_error(self):
        # Devolver ceros enmascararia "no se midio nada" como resultado.
        with pytest.raises(ValueError):
            _timing.summarize([])

    @pytest.mark.parametrize("q", [-0.1, 1.1])
    def test_summarize_percentil_fuera_de_rango(self, q):
        with pytest.raises(ValueError):
            _timing.summarize([1.0], percentile=q)


# --------------------------------------------------------------------------- #
# decide_offloading (D-06)
# --------------------------------------------------------------------------- #

class TestDecideOffloading:
    def test_por_debajo_del_suelo_no_viable(self):
        offload, motivo = _timing.decide_offloading(4 * 1024)
        assert offload is True
        assert motivo.startswith(_timing.NOT_VIABLE_PREFIX)

    def test_entre_suelo_y_confort_activa_offloading(self):
        offload, motivo = _timing.decide_offloading(16 * 1024)
        assert offload is True
        assert not motivo.startswith(_timing.NOT_VIABLE_PREFIX)
        assert "DEGRADADOS" in motivo  # aviso explicito de tiempos degradados (D-29)

    def test_en_el_suelo_exacto_es_viable_con_offloading(self):
        offload, motivo = _timing.decide_offloading(_timing.VRAM_FLOOR_MB)
        assert offload is True
        assert not motivo.startswith(_timing.NOT_VIABLE_PREFIX)

    def test_por_encima_del_confort_sin_offloading(self):
        offload, motivo = _timing.decide_offloading(48 * 1024)
        assert offload is False
        assert not motivo.startswith(_timing.NOT_VIABLE_PREFIX)

    def test_vram_desconocida_es_conservador(self):
        offload, motivo = _timing.decide_offloading(None)
        assert offload is True
        assert not motivo.startswith(_timing.NOT_VIABLE_PREFIX)


# --------------------------------------------------------------------------- #
# write_json_report (escritura atomica, menor 9)
# --------------------------------------------------------------------------- #

class TestWriteJsonReport:
    def test_escribe_json_valido_y_sin_temporales(self, tmp_path):
        destino = tmp_path / "sub" / "informe.json"
        payload = {"tarea": "T-03", "acentos": "medición", "n": 3}
        ruta = _timing.write_json_report(destino, payload)
        assert ruta == destino
        leido = json.loads(destino.read_text(encoding="utf-8"))
        assert leido == payload
        # El temporal de la escritura atomica no queda al lado del informe.
        assert [p.name for p in destino.parent.iterdir()] == ["informe.json"]

    def test_payload_no_serializable_no_toca_el_fichero_existente(self, tmp_path):
        destino = tmp_path / "informe.json"
        _timing.write_json_report(destino, {"ok": True})
        with pytest.raises(TypeError):
            _timing.write_json_report(destino, {"malo": object()})
        # La serializacion fallida no debe dejar el informe anterior truncado.
        assert json.loads(destino.read_text(encoding="utf-8")) == {"ok": True}
        assert [p.name for p in tmp_path.iterdir()] == ["informe.json"]

    def test_reemplaza_contenido_anterior(self, tmp_path):
        destino = tmp_path / "informe.json"
        _timing.write_json_report(destino, {"v": 1})
        _timing.write_json_report(destino, {"v": 2})
        assert json.loads(destino.read_text(encoding="utf-8")) == {"v": 2}
