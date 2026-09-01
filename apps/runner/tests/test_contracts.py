"""Tests de `contracts.py`: la puerta anti-RCE (D-14), D-17 y la validacion de peticiones.

`assert_safetensors` es la UNICA puerta de entrada de pesos del runner: un fallo
aqui es ejecucion remota de codigo, no un bug cosmetico. Por eso su cobertura es
exhaustiva a proposito.
"""

from __future__ import annotations

import pytest

from contracts import (
    GenerationRequest,
    GpuBudgetExceeded,
    UnsafeWeightsFormat,
    assert_safetensors,
    assert_within_gpu_budget,
)


# --------------------------------------------------------------------------- #
# assert_safetensors (D-14)
# --------------------------------------------------------------------------- #

class TestAssertSafetensors:
    def test_acepta_safetensors(self):
        assert assert_safetensors("pesos.safetensors") == "pesos.safetensors"

    def test_acepta_ruta_absoluta(self):
        ruta = "/weights/ace_step_1_5.safetensors"
        assert assert_safetensors(ruta) == ruta

    def test_insensible_a_mayusculas(self):
        # La comprobacion es de FORMATO, no de estetica: '.SAFETENSORS' es el
        # mismo formato en un sistema de ficheros insensible a mayusculas.
        assert assert_safetensors("PESOS.SAFETENSORS")
        assert assert_safetensors("pesos.SafeTensors")

    @pytest.mark.parametrize(
        "ruta",
        [
            "pesos.pt",
            "pesos.pth",
            "pesos.bin",
            "pesos.ckpt",
            "pesos.pkl",
            "pesos.joblib",
            "pesos.safetensors.pt",   # la extension REAL es .pt
            "pesos",                   # sin extension
            "pesos.wav",
        ],
    )
    def test_rechaza_extension_distinta(self, ruta):
        with pytest.raises(UnsafeWeightsFormat):
            assert_safetensors(ruta)

    @pytest.mark.parametrize("ruta", ["", "   "])
    def test_rechaza_vacio(self, ruta):
        with pytest.raises(UnsafeWeightsFormat):
            assert_safetensors(ruta)

    @pytest.mark.parametrize("ruta", ["pesos.safetensors/", "pesos.safetensors\\"])
    def test_rechaza_directorio(self, ruta):
        # Un directorio no es un fichero de pesos: dentro puede haber cualquier cosa.
        with pytest.raises(UnsafeWeightsFormat):
            assert_safetensors(ruta)

    @pytest.mark.parametrize("ruta", [".safetensors", "/weights/.safetensors"])
    def test_rechaza_nombre_solo_extension(self, ruta):
        with pytest.raises(UnsafeWeightsFormat):
            assert_safetensors(ruta)

    def test_mira_el_nombre_no_el_directorio(self):
        # Un directorio llamado *.safetensors no legitima un fichero pickle.
        with pytest.raises(UnsafeWeightsFormat):
            assert_safetensors("/malicioso.safetensors/pesos.pt")


# --------------------------------------------------------------------------- #
# assert_within_gpu_budget (D-17)
# --------------------------------------------------------------------------- #

class TestAssertWithinGpuBudget:
    def test_dentro_de_presupuesto_no_lanza(self):
        assert_within_gpu_budget(10.0, 600)
        assert_within_gpu_budget(600.0, 600)  # el limite exacto no aborta

    def test_fuera_de_presupuesto_lanza_con_cifras(self):
        with pytest.raises(GpuBudgetExceeded) as exc:
            assert_within_gpu_budget(601.5, 600, detail="prueba")
        assert exc.value.elapsed_s == pytest.approx(601.5)
        assert exc.value.max_gpu_seconds == 600
        assert "prueba" in str(exc.value)

    @pytest.mark.parametrize("tope", [0, -1])
    def test_presupuesto_no_positivo_es_error(self, tope):
        with pytest.raises(ValueError):
            assert_within_gpu_budget(1.0, tope)


# --------------------------------------------------------------------------- #
# GenerationRequest.__post_init__
# --------------------------------------------------------------------------- #

def _req(**cambios):
    base = dict(
        style_prompt="pop electronico",
        duration_s=180,
        max_gpu_seconds=600,
        idempotency_key="test-0001",
    )
    base.update(cambios)
    return GenerationRequest(**base)


class TestGenerationRequest:
    def test_peticion_valida(self):
        req = _req(lyrics="letra", seed=42)
        assert req.duration_s == 180

    def test_campos_obligatorios(self):
        # Construccion solo por palabra clave y sin valores por defecto para los
        # cuatro campos obligatorios: omitir uno es TypeError del dataclass.
        with pytest.raises(TypeError):
            GenerationRequest(style_prompt="x", duration_s=1, max_gpu_seconds=1)  # type: ignore[call-arg]

    @pytest.mark.parametrize("duracion", [0, -10])
    def test_duracion_invalida(self, duracion):
        with pytest.raises(ValueError):
            _req(duration_s=duracion)

    def test_prompt_vacio(self):
        with pytest.raises(ValueError):
            _req(style_prompt="   ")

    def test_presupuesto_obligatorio(self):
        with pytest.raises(ValueError):
            _req(max_gpu_seconds=0)

    def test_clave_idempotencia_vacia(self):
        with pytest.raises(ValueError):
            _req(idempotency_key=" ")

    def test_instrumental_con_letra_es_contradiccion(self):
        with pytest.raises(ValueError):
            _req(instrumental=True, lyrics="no deberia cantarse")
