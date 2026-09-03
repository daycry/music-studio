"""Tests de `contracts.py`: la puerta anti-RCE (D-14), D-17 y la validacion de peticiones.

`assert_safetensors` es la UNICA puerta de entrada de pesos del runner: un fallo
aqui es ejecucion remota de codigo, no un bug cosmetico. Por eso su cobertura es
exhaustiva a proposito.
"""

from __future__ import annotations

import json
import pickle
import struct

import pytest

from contracts import (
    GenerationRequest,
    GpuBudgetExceeded,
    UnsafeWeightsFormat,
    assert_safetensors,
    assert_safetensors_header,
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

    def test_no_toca_el_disco(self, tmp_path):
        # Contrato deliberado: es la puerta que se cruza ANTES de abrir el
        # fichero, y la llaman sitios que no lo abren nunca (spikes/_mock.py).
        # Una ruta inexistente pasa: el formato del nombre es correcto.
        inexistente = tmp_path / "ni-existe-ni-hace-falta.safetensors"
        assert not inexistente.exists()
        assert assert_safetensors(inexistente) == str(inexistente)


# --------------------------------------------------------------------------- #
# assert_safetensors_header (D-14, al ABRIR el fichero)
# --------------------------------------------------------------------------- #

def _safetensors_de_juguete(destino, cabecera=None, datos=bytes(4)):
    """Escribe un `.safetensors` minimo pero con la disposicion real del formato."""
    if cabecera is None:
        cabecera = {"t": {"dtype": "F32", "shape": [1], "data_offsets": [0, 4]}}
    crudo = json.dumps(cabecera).encode("utf-8")
    destino.write_bytes(struct.pack("<Q", len(crudo)) + crudo + datos)
    return destino


class TestAssertSafetensorsHeader:
    """La cabecera se comprueba AL ABRIR; la extension, ANTES (`assert_safetensors`).

    Defensa en profundidad, dicho sin inflarlo: los dos cargadores del runner
    (`carga_contigua` y `safetensors.torch.load_file`) ya rechazan un pickle
    renombrado. Esto no cierra un agujero abierto; adelanta el fallo al momento de
    abrir el fichero y con un mensaje que dice que pasa.
    """

    def test_acepta_un_safetensors_valido(self, tmp_path):
        ruta = _safetensors_de_juguete(tmp_path / "pesos.safetensors")
        assert assert_safetensors_header(ruta) == str(ruta)

    def test_rechaza_un_pickle_renombrado(self, tmp_path):
        # El caso que importa: extension buena, contenido de pickle. Cargarlo con
        # torch.load/joblib seria ejecucion remota de codigo (D-14). Aqui se
        # SERIALIZA un pickle para tener bytes realistas; no se deserializa
        # ninguno, ni aqui ni en ningun otro punto del runner.
        ruta = tmp_path / "pesos.safetensors"
        ruta.write_bytes(pickle.dumps({"truco": "sorpresa"}))
        with pytest.raises(UnsafeWeightsFormat):
            assert_safetensors_header(ruta)

    def test_rechaza_un_checkpoint_zip_de_torch(self, tmp_path):
        # Un .pt moderno es un ZIP: empieza por 'PK' y dos bytes de firma.
        ruta = tmp_path / "pesos.safetensors"
        ruta.write_bytes(b"PK" + bytes([3, 4, 20, 0, 0, 0]) + b"relleno" * 64)
        with pytest.raises(UnsafeWeightsFormat):
            assert_safetensors_header(ruta)

    def test_rechaza_fichero_vacio(self, tmp_path):
        ruta = tmp_path / "pesos.safetensors"
        ruta.write_bytes(b"")
        with pytest.raises(UnsafeWeightsFormat):
            assert_safetensors_header(ruta)

    def test_rechaza_longitud_de_cabecera_cero(self, tmp_path):
        ruta = tmp_path / "pesos.safetensors"
        ruta.write_bytes(struct.pack("<Q", 0))
        with pytest.raises(UnsafeWeightsFormat):
            assert_safetensors_header(ruta)

    def test_rechaza_cabecera_truncada(self, tmp_path):
        ruta = tmp_path / "pesos.safetensors"
        ruta.write_bytes(struct.pack("<Q", 4096) + b'{"t": 1}')
        with pytest.raises(UnsafeWeightsFormat):
            assert_safetensors_header(ruta)

    def test_rechaza_cabecera_que_no_es_json(self, tmp_path):
        ruta = tmp_path / "pesos.safetensors"
        basura = b"esto no es json"
        ruta.write_bytes(struct.pack("<Q", len(basura)) + basura)
        with pytest.raises(UnsafeWeightsFormat):
            assert_safetensors_header(ruta)

    def test_rechaza_cabecera_json_que_no_es_objeto(self, tmp_path):
        # JSON valido pero una lista: el formato exige un objeto con los tensores.
        ruta = _safetensors_de_juguete(tmp_path / "pesos.safetensors", cabecera=[1, 2, 3])
        with pytest.raises(UnsafeWeightsFormat):
            assert_safetensors_header(ruta)

    def test_un_fichero_que_no_existe_es_error_de_e_s_no_de_formato(self, tmp_path):
        # Que falte el fichero no es un problema de formato: se propaga el OSError
        # en vez de disfrazarlo de UnsafeWeightsFormat, que enganaria al operador.
        with pytest.raises(OSError):
            assert_safetensors_header(tmp_path / "no-existe.safetensors")

    def test_no_sustituye_a_la_puerta_por_nombre(self, tmp_path):
        # Las dos puertas son independientes y complementarias: esta NO mira la
        # extension (la mira `assert_safetensors`, antes de abrir nada).
        ruta = _safetensors_de_juguete(tmp_path / "pesos.pt")
        assert assert_safetensors_header(ruta) == str(ruta)
        with pytest.raises(UnsafeWeightsFormat):
            assert_safetensors(ruta)


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
