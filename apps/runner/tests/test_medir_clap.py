"""Tests del arnes de medicion de CLAP (`spikes/medir_clap.py`).

Que se prueba aqui, y por que estos y no otros
==============================================
`medir_clap.py` produce el **criterio 3** de G1 (`g1-protocolo.md` §2): en
cuantos de los 10 briefs la pista propia alcanza o supera a la de libreria en
similitud audio-texto. El modelo que lo mide **no esta decidido** (HeartCLAP no
esta publicado, hallazgo A-3), asi que lo unico que hoy se puede probar es lo
que es nuestro: **la mecanica de la medida** y **las puertas** que impiden usar
un modelo sin ficha de licencia comprobada.

Por eso el modelo llega **inyectado** y aqui se usa uno de juguete: estos tests
no descargan nada, no tocan la red y no necesitan GPU.

Las cuatro cosas que fallarian en silencio, que son las que se prueban:

1. **La mecanica** — un coseno mal normalizado o una media mal hecha siguen
   dando un numero plausible entre 0 y 1. Se comprueba con vectores cuyo coseno
   se conoce a mano.
2. **El troceado** — si la ultima ventana corta se cayera, la medida ignoraria
   el final de cada pista sin decirlo. §6.1 exige ventanas que **cubren la pista
   entera**.
3. **La puerta de licencia** — sin ella el script mediria con cualquier peso que
   apareciera en disco, que es exactamente lo que la regla 5 del registry
   (I-13b) prohibe. Y la puerta de formato: solo `safetensors` (D-14).
4. **La advertencia A-14** — si desaparece del informe, un 10 de 10 en CLAP se
   lee en el acta como prueba objetiva de calidad, que es justo lo que no es.

Sin torch y sin GPU, como el resto de la suite.
"""

from __future__ import annotations

import hashlib
import json
import struct
import wave
from pathlib import Path

import numpy as np
import pytest

import medir_clap as mc


# --------------------------------------------------------------------------- #
# Utilidades de los tests
# --------------------------------------------------------------------------- #

class ModeloJuguete:
    """Modelo CLAP de juguete: determinista, sin pesos y sin red.

    `embed_texto` devuelve siempre el mismo eje y `embed_audio` devuelve
    `[media, 1 - media]` de la ventana. Con el eje del texto en `[1, 0]`:

    * ventana de unos  -> `[1, 0]` -> coseno **1,0**
    * ventana de ceros -> `[0, 1]` -> coseno **0,0**

    Asi la similitud de cada ventana se elige desde el audio y se conoce de
    antemano, que es lo que hace comprobable la aritmetica de la media.
    """

    def __init__(self, vector_texto: tuple[float, float] = (1.0, 0.0)) -> None:
        self.vector_texto = np.asarray(vector_texto, dtype=np.float64)
        self.ventanas_vistas: list[tuple[int, int]] = []
        self.textos_vistos: list[str] = []

    def embed_texto(self, texto: str) -> np.ndarray:
        self.textos_vistos.append(texto)
        return self.vector_texto

    def embed_audio(self, ventana: np.ndarray, tasa: int) -> np.ndarray:
        self.ventanas_vistas.append((len(ventana), tasa))
        media = float(np.mean(ventana))
        return np.asarray([media, 1.0 - media], dtype=np.float64)


def _audio(*bloques: tuple[float, float], tasa: int = 100) -> mc.Audio:
    """Construye un audio por bloques `(valor, segundos)` a `tasa` Hz."""
    trozos = [np.full(int(round(seg * tasa)), valor, dtype=np.float64) for valor, seg in bloques]
    return mc.Audio(np.concatenate(trozos), tasa)


def _escribir_pesos(ruta: Path) -> str:
    """Escribe un `safetensors` minimo pero **real** y devuelve su SHA-256.

    Formato: 8 bytes little-endian con la longitud de la cabecera JSON, la
    cabecera (que tiene que parsear a objeto) y los datos. No se deserializa
    nada: es exactamente lo que la puerta de formato comprueba.
    """
    cabecera = json.dumps({"__metadata__": {"origen": "juguete"}}).encode("utf-8")
    ruta.write_bytes(struct.pack("<Q", len(cabecera)) + cabecera + b"\x00" * 16)
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def _documento_ficha(sha256: str, nombre_pesos: str = "modelo.safetensors") -> dict:
    """Ficha valida de referencia. Los tests la degradan campo a campo."""
    return {
        "schema": mc.SCHEMA_FICHA,
        "id": "modelo-clap-de-juguete",
        "version": "0.0.0-test",
        "backend": "backend-de-juguete",
        "pesos": nombre_pesos,
        "sha256": sha256,
        "tasa_entrada_hz": 100,
        "ventana_s": 10.0,
        "licencia": {
            "spdx": "Apache-2.0",
            "uso_comercial": True,
            "verificada_por": "Daycry",
            "verificada_el": "2026-09-03",
            "fuente": "https://ejemplo.invalido/LICENSE",
        },
    }


#: Centinela para pedir que un campo **falte**, distinto de que valga `None`.
mc_BORRAR = object()


def _escribir_ficha(tmp_path: Path, cambios: dict | None = None, *, nombre_pesos: str = "modelo.safetensors") -> Path:
    sha = _escribir_pesos(tmp_path / nombre_pesos)
    documento = _documento_ficha(sha, nombre_pesos)
    if cambios:
        for clave, valor in cambios.items():
            if valor is mc_BORRAR:
                documento.pop(clave, None)
            else:
                documento[clave] = valor
    ruta = tmp_path / "clap.model.json"
    ruta.write_text(json.dumps(documento), encoding="utf-8")
    return ruta


@pytest.fixture()
def ficha(tmp_path: Path) -> mc.FichaClap:
    return mc.cargar_ficha(_escribir_ficha(tmp_path))


# --------------------------------------------------------------------------- #
# 1. Mecanica: coseno y media de ventanas
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    ("a", "b", "esperado"),
    [
        ((1.0, 0.0), (1.0, 0.0), 1.0),
        ((1.0, 0.0), (0.0, 1.0), 0.0),
        ((1.0, 0.0), (-1.0, 0.0), -1.0),
        ((1.0, 1.0), (1.0, 0.0), 0.7071067811865475),
        ((2.0, 0.0), (1.0, 0.0), 1.0),   # el coseno ignora la escala
        ((0.0, 3.0), (0.0, 9.0), 1.0),
    ],
)
def test_similitud_coseno_con_valores_conocidos(a, b, esperado):
    obtenido = mc.similitud_coseno(np.asarray(a), np.asarray(b))
    assert obtenido == pytest.approx(esperado, abs=1e-12)


def test_similitud_coseno_rechaza_el_vector_nulo():
    """Un vector nulo no tiene direccion: normalizarlo daria `nan` o un 0 que se
    leeria como «no se parece». Los dos son mentiras; mejor que falle."""
    with pytest.raises(ValueError, match="nulo"):
        mc.similitud_coseno(np.asarray([0.0, 0.0]), np.asarray([1.0, 0.0]))


def test_similitud_coseno_exige_la_misma_dimension():
    with pytest.raises(ValueError, match="dimension"):
        mc.similitud_coseno(np.asarray([1.0, 0.0]), np.asarray([1.0, 0.0, 0.0]))


def test_la_medida_de_una_pista_es_la_media_de_las_ventanas():
    """20 s = dos ventanas de 10 s con similitud 1,0 y 0,0 -> media 0,5."""
    modelo = ModeloJuguete()
    audio = _audio((1.0, 10.0), (0.0, 10.0))

    medida = mc.medir_pista(audio, "indie-rock luminoso a 112 BPM", modelo)

    assert medida.similitudes == pytest.approx([1.0, 0.0])
    assert medida.media == pytest.approx(0.5)
    assert medida.n_ventanas == 2


def test_el_texto_se_embebe_una_vez_por_pista():
    """El texto no cambia entre ventanas. Re-embeberlo por ventana no cambia el
    numero, pero multiplica el coste y abre la puerta a que un modelo con
    aleatoriedad interna devuelva vectores distintos dentro de la misma pista."""
    modelo = ModeloJuguete()
    mc.medir_pista(_audio((1.0, 30.0)), "un texto", modelo)
    assert modelo.textos_vistos == ["un texto"]


def test_la_media_no_pondera_por_duracion_de_ventana():
    """Politica declarada de §6.1: **media** de las similitudes, una por ventana.
    25 s dan tres ventanas (10 + 10 + 5) y la corta pesa igual que las largas:
    (1 + 1 + 0) / 3, no una media ponderada por muestras."""
    modelo = ModeloJuguete()
    medida = mc.medir_pista(_audio((1.0, 20.0), (0.0, 5.0)), "t", modelo)
    assert medida.similitudes == pytest.approx([1.0, 1.0, 0.0])
    assert medida.media == pytest.approx(2.0 / 3.0)


# --------------------------------------------------------------------------- #
# 2. Troceado en ventanas
# --------------------------------------------------------------------------- #

def test_ventanas_no_solapadas_cubren_la_pista_entera():
    audio = np.arange(2500, dtype=np.float64)   # 25 s a 100 Hz
    trozos = mc.ventanas(audio, tasa=100, ventana_s=10.0)

    assert [len(t) for t in trozos] == [1000, 1000, 500]
    assert np.array_equal(np.concatenate(trozos), audio)


def test_la_ultima_ventana_corta_se_incluye():
    """Descartar el resto es descartar el final de la pista — justo donde el
    protocolo mira el cierre. §6.1 pide cubrir la pista entera."""
    trozos = mc.ventanas(np.zeros(1200), tasa=100, ventana_s=10.0)
    assert len(trozos) == 2
    assert len(trozos[-1]) == 200


def test_una_pista_mas_corta_que_la_ventana_da_una_sola_ventana():
    """Hay briefs de 30 s y de 45 s, pero tambien podria haber material mas
    corto que la ventana: no puede quedarse sin medir."""
    trozos = mc.ventanas(np.zeros(400), tasa=100, ventana_s=10.0)
    assert len(trozos) == 1
    assert len(trozos[0]) == 400


def test_una_pista_multiplo_exacto_no_deja_ventana_vacia():
    trozos = mc.ventanas(np.zeros(2000), tasa=100, ventana_s=10.0)
    assert [len(t) for t in trozos] == [1000, 1000]


def test_audio_vacio_es_un_error_no_una_medida_de_cero():
    with pytest.raises(ValueError, match="vacio"):
        mc.ventanas(np.zeros(0), tasa=100, ventana_s=10.0)


def test_las_ventanas_llegan_al_modelo_con_su_tasa():
    modelo = ModeloJuguete()
    mc.medir_pista(_audio((1.0, 25.0), tasa=100), "t", modelo)
    assert modelo.ventanas_vistas == [(1000, 100), (1000, 100), (500, 100)]


# --------------------------------------------------------------------------- #
# 3. Puerta de licencia y de formato de pesos
# --------------------------------------------------------------------------- #

def test_una_ficha_valida_se_carga_con_su_identidad_completa(tmp_path: Path):
    ruta = _escribir_ficha(tmp_path)
    f = mc.cargar_ficha(ruta)

    assert f.id == "modelo-clap-de-juguete"
    assert f.version == "0.0.0-test"
    assert f.licencia_spdx == "Apache-2.0"
    assert f.sha256 == hashlib.sha256((tmp_path / "modelo.safetensors").read_bytes()).hexdigest()
    assert f.ruta_pesos == tmp_path / "modelo.safetensors"
    assert f.tasa_entrada_hz == 100
    assert f.ventana_s == 10.0


def test_sin_ficha_no_se_mide(tmp_path: Path):
    """El fichero de ficha no existe: el script se niega y dice que falta."""
    with pytest.raises(mc.FichaInvalida, match="no existe|no se encontro|ilegible"):
        mc.cargar_ficha(tmp_path / "no-esta.model.json")


@pytest.mark.parametrize(
    "campo", ["id", "version", "backend", "pesos", "sha256", "licencia", "tasa_entrada_hz"],
)
def test_una_ficha_a_la_que_le_falta_un_campo_obligatorio_se_rechaza(tmp_path: Path, campo: str):
    ruta = _escribir_ficha(tmp_path, {campo: mc_BORRAR})
    with pytest.raises(mc.FichaInvalida, match=campo):
        mc.cargar_ficha(ruta)


@pytest.mark.parametrize("campo", ["spdx", "uso_comercial", "verificada_por", "verificada_el"])
def test_una_licencia_sin_declarar_del_todo_se_rechaza(tmp_path: Path, campo: str):
    """«Verificada» quiere decir con nombre y fecha. Una licencia sin quien la
    comprobo y cuando no es una verificacion: es una afirmacion."""
    licencia = dict(_documento_ficha("x")["licencia"])
    licencia.pop(campo)
    ruta = _escribir_ficha(tmp_path, {"licencia": licencia})
    with pytest.raises(mc.FichaInvalida, match=campo):
        mc.cargar_ficha(ruta)


@pytest.mark.parametrize(
    "spdx", ["CC-BY-NC-4.0", "CC-BY-NC-SA-4.0", "CC-BY-NC-ND-4.0"],
)
def test_una_licencia_no_comercial_se_rechaza(tmp_path: Path, spdx: str):
    """El mismo motivo que descarto MusicGen y que dejo a Demucs en revision: la
    regla vale para las herramientas de medicion igual que para los generadores."""
    licencia = dict(_documento_ficha("x")["licencia"], spdx=spdx)
    ruta = _escribir_ficha(tmp_path, {"licencia": licencia})
    with pytest.raises(mc.FichaInvalida, match="comercial"):
        mc.cargar_ficha(ruta)


def test_una_licencia_desconocida_se_rechaza(tmp_path: Path):
    """Lista CERRADA: lo que no esta verificado en este repositorio no se usa.
    Anadir una licencia exige un commit, que es el punto de control que se busca."""
    licencia = dict(_documento_ficha("x")["licencia"], spdx="LicenseRef-Cualquiera")
    ruta = _escribir_ficha(tmp_path, {"licencia": licencia})
    with pytest.raises(mc.FichaInvalida, match="LicenseRef-Cualquiera"):
        mc.cargar_ficha(ruta)


def test_una_licencia_permisiva_pero_declarada_sin_uso_comercial_se_rechaza(tmp_path: Path):
    """Contradiccion entre el SPDX y lo que declara quien la verifico. Ante la
    duda no se elige la lectura conveniente: se para."""
    licencia = dict(_documento_ficha("x")["licencia"], uso_comercial=False)
    ruta = _escribir_ficha(tmp_path, {"licencia": licencia})
    with pytest.raises(mc.FichaInvalida, match="uso_comercial"):
        mc.cargar_ficha(ruta)


@pytest.mark.parametrize("nombre", ["modelo.bin", "modelo.pt", "modelo.ckpt", "modelo.pth"])
def test_unos_pesos_que_no_son_safetensors_se_rechazan(tmp_path: Path, nombre: str):
    """D-14: cargar un checkpoint en pickle ejecuta codigo arbitrario. La puerta
    mira el NOMBRE antes de abrir el fichero."""
    ruta = _escribir_ficha(tmp_path, {"pesos": nombre}, nombre_pesos=nombre)
    with pytest.raises(mc.FichaInvalida, match="safetensors"):
        mc.cargar_ficha(ruta)


def test_un_pickle_renombrado_a_safetensors_se_rechaza_por_la_cabecera(tmp_path: Path):
    """Defensa en profundidad: el nombre pasa, el contenido no. Los dos primeros
    bytes son el protocolo 4 de pickle."""
    ruta = _escribir_ficha(tmp_path)
    (tmp_path / "modelo.safetensors").write_bytes(b"\x80\x04\x95" + b"\x00" * 32)
    with pytest.raises(mc.FichaInvalida, match="cabecera|safetensors"):
        mc.cargar_ficha(ruta)


def test_unos_pesos_que_no_estan_en_disco_se_rechazan(tmp_path: Path):
    ruta = _escribir_ficha(tmp_path)
    (tmp_path / "modelo.safetensors").unlink()
    with pytest.raises(mc.FichaInvalida, match="no existe|no esta"):
        mc.cargar_ficha(ruta)


def test_un_sha256_que_no_cuadra_se_rechaza(tmp_path: Path):
    ruta = _escribir_ficha(tmp_path, {"sha256": "0" * 64})
    with pytest.raises(mc.FichaInvalida, match="sha256|integridad"):
        mc.cargar_ficha(ruta)


def test_un_sha256_mal_formado_se_rechaza(tmp_path: Path):
    ruta = _escribir_ficha(tmp_path, {"sha256": "no-es-un-hash"})
    with pytest.raises(mc.FichaInvalida, match="sha256"):
        mc.cargar_ficha(ruta)


def test_un_esquema_de_ficha_desconocido_se_rechaza(tmp_path: Path):
    ruta = _escribir_ficha(tmp_path, {"schema": mc.SCHEMA_FICHA + 1})
    with pytest.raises(mc.FichaInvalida, match="schema"):
        mc.cargar_ficha(ruta)


# --------------------------------------------------------------------------- #
# 4. El backend: hoy no hay ninguno, y eso se dice
# --------------------------------------------------------------------------- #

def test_hoy_no_hay_ningun_backend_de_clap_implementado():
    """A-3: HeartCLAP no esta publicado y no hay suplente designado. Si este
    test falla es porque alguien anadio un backend: entonces hay que comprobar
    que llego con su ficha de licencia verificada (I-13b) y actualizar el test
    en el mismo commit."""
    assert mc.BACKENDS_CLAP == frozenset()


def test_un_backend_que_este_repositorio_no_sabe_ejecutar_no_se_resuelve(ficha):
    """La ficha NOMBRA el backend; no lo resuelve. Nada se importa por nombre."""
    with pytest.raises(mc.BackendNoDisponible, match="backend-de-juguete"):
        mc.construir_modelo(ficha)


def test_el_modulo_no_importa_nada_por_nombre():
    """Una ficha es un dato del disco. Si `importlib` o `__import__` aparecieran
    aqui, una ficha hostil elegiria que codigo se ejecuta.

    (D-14 —nada de `pickle`— lo cubren los tests de la puerta de pesos, no este:
    aqui solo se mira que no haya resolucion dinamica de codigo.)"""
    fuente = Path(mc.__file__).read_text(encoding="utf-8")
    for prohibido in ("importlib", "__import__(", "eval(", "exec("):
        assert prohibido not in fuente, prohibido


# --------------------------------------------------------------------------- #
# 5. La medida de un brief y la salida en bruto
# --------------------------------------------------------------------------- #

def test_un_brief_publica_los_dos_valores_brutos_y_su_diferencia(ficha):
    modelo = ModeloJuguete()
    par = mc.medir_brief(
        "B-01",
        "indie-rock luminoso, 112 BPM",
        propia=_audio((1.0, 20.0)),
        libreria=_audio((1.0, 10.0), (0.0, 10.0)),
        modelo=modelo,
        ficha=ficha,
    )

    assert par.clap_propia == pytest.approx(1.0)
    assert par.clap_libreria == pytest.approx(0.5)
    assert par.diferencia == pytest.approx(0.5)
    assert par.propia_gana_o_empata is True


def test_el_empate_cuenta_como_cumplido(ficha):
    """§2, criterio 3: la comparacion es `propia >= libreria`."""
    modelo = ModeloJuguete()
    par = mc.medir_brief(
        "B-02", "t", propia=_audio((1.0, 10.0)), libreria=_audio((1.0, 10.0)),
        modelo=modelo, ficha=ficha,
    )
    assert par.clap_propia == pytest.approx(par.clap_libreria)
    assert par.propia_gana_o_empata is True


def test_un_brief_sin_linea_base_cuenta_como_no_cumplido(ficha):
    """§2.1: «un brief sin linea base es un brief sin evidencia, y la carga de la
    prueba la tiene el modelo propio, no la libreria»."""
    modelo = ModeloJuguete()
    par = mc.medir_brief(
        "B-03", "t", propia=_audio((1.0, 10.0)), libreria=None, modelo=modelo, ficha=ficha,
    )

    assert par.clap_libreria is None
    assert par.diferencia is None
    assert par.propia_gana_o_empata is False
    assert "linea base" in par.nota


def test_una_tasa_de_muestreo_distinta_de_la_declarada_se_rechaza(ficha):
    """§6.1 obliga a anotar la frecuencia de entrada. Remuestrear en silencio
    cambiaria la medida sin dejar rastro, y la politica tiene que ser identica
    para las tres series."""
    modelo = ModeloJuguete()
    with pytest.raises(ValueError, match="tasa|muestreo"):
        mc.medir_brief(
            "B-04", "t", propia=_audio((1.0, 10.0), tasa=48000), libreria=None,
            modelo=modelo, ficha=ficha,
        )


# --------------------------------------------------------------------------- #
# 6. El informe: advertencia A-14, valores brutos y reproducibilidad
# --------------------------------------------------------------------------- #

@pytest.fixture()
def informe(ficha) -> dict:
    modelo = ModeloJuguete()
    pares = [
        mc.medir_brief(
            f"B-{i:02d}", f"prompt {i}",
            propia=_audio((1.0, 10.0)),
            libreria=_audio((0.0, 10.0)) if i != 3 else None,
            modelo=modelo, ficha=ficha,
        )
        for i in range(1, 5)
    ]
    return mc.informe(pares, ficha)


def test_el_informe_lleva_la_advertencia_del_sesgo_estructural(informe):
    """A-14. Va en el informe que emite el script, no solo en el acta: si el
    numero viaja sin la advertencia, un 10 de 10 se lee como prueba de calidad."""
    assert informe["advertencia"] == mc.ADVERTENCIA_CRITERIO_3
    assert "favorece estructuralmente a la serie propia" in mc.ADVERTENCIA_CRITERIO_3


def test_la_advertencia_tambien_sale_en_el_texto_para_consola(informe):
    assert mc.ADVERTENCIA_CRITERIO_3 in mc.formatear(informe)


def test_el_informe_publica_los_pares_en_bruto_no_solo_el_recuento(informe):
    """§6.1: «los valores brutos de los 20 (o 30) pares, no solo la cuenta». Un
    7 de 10 con diferencias de 0,001 y otro con diferencias de 0,15 son
    resultados distintos."""
    assert [b["brief"] for b in informe["briefs"]] == ["B-01", "B-02", "B-03", "B-04"]
    for fila in informe["briefs"]:
        assert "clap_propia" in fila
        assert "clap_libreria" in fila
        assert "diferencia" in fila
        assert "similitudes_propia" in fila   # una por ventana


def test_el_informe_da_el_recuento_y_el_tamano_del_efecto(informe):
    """A-14 pide publicar tambien la diferencia media y la mediana."""
    assert informe["resumen"]["briefs_medidos"] == 4
    assert informe["resumen"]["propia_gana_o_empata"] == 3
    assert informe["resumen"]["sin_linea_base"] == 1
    assert informe["resumen"]["diferencia_media"] == pytest.approx(1.0)
    assert informe["resumen"]["diferencia_mediana"] == pytest.approx(1.0)


def test_el_informe_registra_lo_que_exige_la_reproducibilidad(informe):
    """§6.1: modelo, version, SHA-256 de los pesos, frecuencia de muestreo,
    politica de ventanas y politica de agregacion. Sin eso la cifra no se puede
    repetir en G1-bis."""
    m = informe["modelo"]
    assert m["id"] == "modelo-clap-de-juguete"
    assert m["version"] == "0.0.0-test"
    assert len(m["sha256"]) == 64
    assert m["licencia_spdx"] == "Apache-2.0"
    assert m["licencia_verificada_por"] == "Daycry"
    assert m["tasa_entrada_hz"] == 100
    assert informe["politica"]["ventanas"]
    assert informe["politica"]["agregacion"]


def test_el_informe_no_dicta_veredicto(informe):
    """Este script mide; no cierra el gate. Los cinco umbrales del §2 no viven
    aqui, igual que no viven en `g1_generar.py`."""
    texto = json.dumps(informe, ensure_ascii=False)
    for prohibido in ("veredicto", "GO", "NO-GO", "cumple_criterio", "umbral"):
        assert prohibido not in texto, prohibido


def test_el_informe_es_json_serializable_sin_nan(informe):
    json.dumps(informe, allow_nan=False)


# --------------------------------------------------------------------------- #
# 7. Lectura de WAV y linea de comandos
# --------------------------------------------------------------------------- #

def _escribir_wav(ruta: Path, valor: float, segundos: float, tasa: int = 100) -> None:
    muestras = np.full(int(round(segundos * tasa)), valor, dtype=np.float64)
    with wave.open(str(ruta), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(tasa)
        w.writeframes((muestras * 32767.0).astype("<i2").tobytes())


def test_leer_wav_devuelve_mono_normalizado(tmp_path: Path):
    ruta = tmp_path / "p.wav"
    _escribir_wav(ruta, 0.5, 2.0)
    audio = mc.leer_wav(ruta)

    assert audio.tasa == 100
    assert len(audio.muestras) == 200
    assert audio.muestras.max() == pytest.approx(0.5, abs=1e-4)


def test_la_cli_sin_ficha_valida_no_mide_y_dice_que_falta(tmp_path: Path, capsys):
    """La puerta tambien esta en la linea de comandos, no solo en la API."""
    codigo = mc.main(["--ficha", str(tmp_path / "no-esta.json"), "--directorio", str(tmp_path)])
    capturado = capsys.readouterr()
    salida = (capturado.out + capturado.err).lower()

    assert codigo != 0
    assert "ficha" in salida


def test_la_cli_con_ficha_valida_se_para_en_el_backend(tmp_path: Path, capsys):
    """Con ficha buena, lo que falta es el modelo. El mensaje tiene que decir eso
    y no un error generico: es el estado real del instrumento (A-3)."""
    ruta = _escribir_ficha(tmp_path)
    codigo = mc.main(["--ficha", str(ruta), "--directorio", str(tmp_path)])
    salida = capsys.readouterr().out

    assert codigo != 0
    assert "backend" in salida.lower()


class TestLaFichaSeValidaDondeSeUsa:
    """Fiarse de que «solo se puede construir por la puerta» no es una puerta.

    `FichaClap` es un NamedTuple publico: cualquiera lo construye a mano con una
    licencia propietaria y una ruta a un `.bin`, y se salta `cargar_ficha()`
    entera. La validacion tiene que repetirse **donde se usa**, que es lo unico
    que no se puede rodear. Lo contrario deja el invariante de licencias de
    CLAUDE.md apoyado en una convencion de estilo.
    """

    @staticmethod
    def _ficha_falsa(**cambios):
        from pathlib import Path

        base = dict(
            id="modelo-falso", version="0", backend="juguete",
            ruta_pesos=Path("malicioso.bin"), sha256="0" * 64,
            licencia_spdx="Propietaria-sin-uso-comercial",
            licencia_verificada_por="nadie", licencia_verificada_el="2026-01-01",
            licencia_fuente="inventada", tasa_entrada_hz=48000, ventana_s=10.0,
            ruta_ficha=Path("ficha.json"),
        )
        base.update(cambios)
        return mc.FichaClap(**base)

    def test_una_licencia_no_comercial_se_rechaza_aunque_la_ficha_este_construida_a_mano(self):
        with pytest.raises(ValueError, match="licencia"):
            mc.exigir_ficha_valida(self._ficha_falsa())

    def test_unos_pesos_que_no_son_safetensors_se_rechazan(self):
        from pathlib import Path

        with pytest.raises(ValueError, match="safetensors"):
            mc.exigir_ficha_valida(
                self._ficha_falsa(licencia_spdx="MIT", ruta_pesos=Path("pesos.bin"))
            )

    def test_un_hash_que_no_es_sha256_se_rechaza(self):
        from pathlib import Path

        with pytest.raises(ValueError, match="[Ss][Hh][Aa]"):
            mc.exigir_ficha_valida(
                self._ficha_falsa(
                    licencia_spdx="MIT", ruta_pesos=Path("pesos.safetensors"), sha256="corto"
                )
            )

    def test_una_ficha_legitima_pasa(self):
        from pathlib import Path

        buena = self._ficha_falsa(
            licencia_spdx="Apache-2.0", ruta_pesos=Path("pesos.safetensors")
        )
        assert mc.exigir_ficha_valida(buena) is buena

    def test_la_medida_no_se_puede_hacer_con_una_ficha_no_validada(self):
        # El punto entero: que la puerta este en el camino de medir, no solo en
        # el de cargar. Si esto pasa, el invariante de licencias es decorativo.
        import inspect

        # `medir_pista` recibe el MODELO, no la ficha, asi que su puerta es la
        # construccion del modelo. Los tres que reciben `FichaClap` la revalidan.
        for nombre in ("construir_modelo", "medir_brief", "informe"):
            fuente = inspect.getsource(getattr(mc, nombre))
            assert "exigir_ficha_valida" in fuente, (
                f"{nombre} usa la ficha sin revalidarla: una ficha construida a "
                "mano llegaria hasta la medida"
            )


class TestLaVentanaFinalNoDecideLaMedida:
    """Con media sin ponderar, la cifra depende de la duracion modulo 10 s.

    Una pista de 40,00 s da 4 ventanas de 10 s. La misma con 0,02 s mas da 5, y
    la quinta —de 960 muestras— pesa lo mismo que las otras cuatro en la media.
    Reproducido. Dos consecuencias, las dos malas: la cifra salta segun donde
    acabe la pista, y un fragmento de 20 ms no lleva contenido musical que ningun
    modelo pueda juzgar, asi que lo que aporta es ruido con voto.
    """

    def test_una_cola_diminuta_no_se_cuenta_como_una_ventana_entera(self):
        import numpy as np

        largas = mc.ventanas(np.zeros(int(40.0 * 48000)), 48000, 10.0)
        con_cola = mc.ventanas(np.zeros(int(40.02 * 48000)), 48000, 10.0)
        assert len(largas) == 4
        assert len(con_cola) == 4, (
            "la cola de 0,02 s no puede entrar como ventana: mide 960 muestras"
        )

    def test_una_cola_con_contenido_si_se_cuenta(self):
        import numpy as np

        # 5 s de cola son media ventana: eso si es musica que se puede juzgar.
        assert len(mc.ventanas(np.zeros(int(45.0 * 48000)), 48000, 10.0)) == 5

    def test_una_pista_mas_corta_que_el_minimo_no_es_medible(self):
        import numpy as np

        with pytest.raises(ValueError, match="corta|minim"):
            mc.ventanas(np.zeros(int(0.5 * 48000)), 48000, 10.0)

    def test_una_pista_entre_el_minimo_y_la_ventana_da_una_ventana(self):
        import numpy as np

        assert len(mc.ventanas(np.zeros(int(6.0 * 48000)), 48000, 10.0)) == 1

    def test_la_media_sigue_siendo_simple_porque_lo_manda_el_protocolo(self):
        # §6.1: «ventanas no solapadas que cubren la pista entera, y MEDIA de las
        # similitudes». Ponderar por duracion seria mas defendible en abstracto,
        # pero cambiar como se agrega es cambiar la aritmetica de un criterio, y
        # eso lo firma el propietario. El artefacto de las colas diminutas se
        # resuelve descartandolas, que no toca la formula.
        import inspect

        fuente = inspect.getsource(mc.medir_pista)
        assert "fmean" in fuente
        assert "weights" not in fuente
