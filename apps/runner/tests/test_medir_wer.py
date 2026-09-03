"""Tests de `spikes/medir_wer.py`: el WER del criterio 4 de G1, su puerta y el suelo.

Tres capas, y la separacion es el objeto de estos tests
------------------------------------------------------
* **Capa 1 — aritmetica.** Se prueba con verdad conocida a mano (10 palabras,
  una sustitucion, 10 %), no con la salida del propio codigo. Un test de WER que
  compara contra lo que el codigo devuelve hoy no prueba nada.
* **Capa 2 — puerta.** Sin ficha de licencia verificada el modulo se niega a
  medir, y un transcriptor de prueba no puede producir un numero que vaya al
  acta ni adjuntandole una ficha impecable.
* **Capa 3 — el transcriptor real.** Casi todo lo que hay que garantizar de el
  **no necesita los pesos**: que rechace un directorio con un `.bin` al lado o
  con un `auto_map`, que no cargue nada hasta la primera transcripcion, que
  exija el idioma. Eso se prueba con directorios de mentira de 60 bytes.

Que necesita pesos y que no
---------------------------
La mayor parte de este fichero corre con biblioteca estandar: ni torch, ni
numpy, ni red. Lo que si los necesita esta marcado con `skipif` y se salta solo,
para que la suite siga verde en una maquina sin el modelo descargado:

* `@sin_pesos` — necesita `D:/srv/whisper/ficha.json` (o `$SUNO_FICHA_TRANSCRIPTOR`)
  y torch + transformers instalados.
* los de lectura de audio — solo numpy, y scipy si hay que remuestrear.
* los del corpus del suelo — solo el `corpus.json`, sin modelo.

Los tres caminos se pueden apuntar a otro sitio con variables de entorno, para
que esto no quede clavado a una maquina concreta.
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

import medir_wer as mw

_RAIZ_REPO = Path(__file__).resolve().parents[3]
_PROTOCOLO = _RAIZ_REPO / "docs/roadmap/2026-07-27-plataforma-musical-ia/gates/g1-protocolo.md"

#: Los tres caminos al material real. Con valores por defecto porque es donde
#: estan hoy, y con variable de entorno porque clavarlos seria dejar la suite
#: atada a una maquina.
_FICHA_REAL = Path(os.environ.get("SUNO_FICHA_TRANSCRIPTOR", "D:/srv/whisper/ficha.json"))
_CORPUS_SUELO = Path(os.environ.get("SUNO_CORPUS_SUELO", "D:/srv/whisper/suelo/corpus.json"))
_AUDIO_REAL = Path(os.environ.get(
    "SUNO_AUDIO_PRUEBA",
    "D:/srv/ace-step/out/qa-final-20s-1788448061-af4ba954.wav",
))


def _hay(modulo: str) -> bool:
    try:
        return importlib.util.find_spec(modulo) is not None
    except (ImportError, ValueError):
        return False


_FALTA_PARA_TRANSCRIBIR = [
    motivo for motivo, presente in (
        (f"la ficha {_FICHA_REAL}", _FICHA_REAL.is_file()),
        (f"el audio {_AUDIO_REAL}", _AUDIO_REAL.is_file()),
        ("torch", _hay("torch")),
        ("transformers", _hay("transformers")),
    ) if not presente
]

#: Marca para lo que necesita pesos de verdad. El motivo enumera TODO lo que
#: falta, no lo primero: descubrirlo de uno en uno es la peor forma de perder
#: una tarde.
sin_pesos = pytest.mark.skipif(
    bool(_FALTA_PARA_TRANSCRIBIR),
    reason="falta " + ", ".join(_FALTA_PARA_TRANSCRIBIR),
)


# --------------------------------------------------------------------------- #
# Utilidades de los tests
# --------------------------------------------------------------------------- #

def _diez_palabras() -> str:
    return "uno dos tres cuatro cinco seis siete ocho nueve diez"


_BORRAR = object()  # centinela para quitar un campo de la ficha en un test


def _pesos_falsos(tmp_path: Path, nombre: str = "transcriptor.safetensors") -> Path:
    """Un `.safetensors` minimo pero de verdad: 8 bytes de longitud + JSON objeto.

    No es un modelo: es lo justo para que la puerta pueda comprobar formato y
    hash sin descargar nada. Que un test necesite fabricar esto a mano es la
    prueba de que el modulo no trae ningun peso consigo.
    """
    cuerpo = b'{"__metadata__":{"formato":"prueba"}}'
    ruta = tmp_path / nombre
    ruta.write_bytes(len(cuerpo).to_bytes(8, "little") + cuerpo + b"\x00" * 16)
    return ruta


def _ficha_valida(tmp_path: Path, **cambios) -> Path:
    ruta_pesos = _pesos_falsos(tmp_path)
    documento = {
        "schema": mw.SCHEMA_FICHA,
        "identificador": "HeartTranscriptor-oss",
        "version": "1.0.0",
        "ruta_pesos": str(ruta_pesos),
        "licencia_spdx": "Apache-2.0",
        "sha256_pesos": hashlib.sha256(ruta_pesos.read_bytes()).hexdigest(),
        "licencia_verificada_por": "Daycry (propietario)",
        "licencia_verificada_el": "2026-09-03",
        "fuente_licencia": "https://ejemplo.invalido/LICENSE",
    }
    documento.update(cambios)
    for clave, valor in list(documento.items()):
        if valor is _BORRAR:
            del documento[clave]
    ruta = tmp_path / "ficha.json"
    ruta.write_text(json.dumps(documento), encoding="utf-8")
    return ruta


# --------------------------------------------------------------------------- #
# CAPA 1 — aritmetica del WER con verdad conocida
# --------------------------------------------------------------------------- #

class TestWerConVerdadConocida:

    def test_identicas_dan_cero(self):
        r = mw.medir_wer(_diez_palabras(), _diez_palabras())
        assert r.wer == 0.0
        assert (r.sustituciones, r.inserciones, r.borrados) == (0, 0, 0)
        assert r.n_referencia == 10

    def test_una_sustitucion_de_diez_da_diez_por_ciento(self):
        hipotesis = _diez_palabras().replace("cinco", "quince")
        r = mw.medir_wer(_diez_palabras(), hipotesis)
        assert r.sustituciones == 1
        assert r.inserciones == 0
        assert r.borrados == 0
        assert r.wer == pytest.approx(0.10)
        assert r.wer_pct == pytest.approx(10.0)

    def test_dos_borrados_de_diez_dan_veinte_por_ciento(self):
        hipotesis = "uno dos tres cuatro cinco seis siete ocho"  # faltan nueve y diez
        r = mw.medir_wer(_diez_palabras(), hipotesis)
        assert (r.sustituciones, r.inserciones, r.borrados) == (0, 0, 2)
        assert r.wer == pytest.approx(0.20)

    def test_insercion_pura(self):
        hipotesis = _diez_palabras() + " once"
        r = mw.medir_wer(_diez_palabras(), hipotesis)
        assert (r.sustituciones, r.inserciones, r.borrados) == (0, 1, 0)
        assert r.wer == pytest.approx(0.10)

    def test_hipotesis_vacia_es_cien_por_cien(self):
        r = mw.medir_wer(_diez_palabras(), "")
        assert r.borrados == 10
        assert r.wer == pytest.approx(1.0)
        assert r.wer_pct == pytest.approx(100.0)

    def test_referencia_vacia_es_error_claro_y_no_division_por_cero(self):
        with pytest.raises(mw.ReferenciaVacia) as exc:
            mw.medir_wer("   \n  ", "lo que sea")
        # El mensaje tiene que decir por que, no solo que: el denominador del WER
        # es N, y sin referencia no hay WER — no hay un "0 %" que devolver.
        assert "referencia" in str(exc.value).lower()
        assert not isinstance(exc.value, ZeroDivisionError)

    def test_referencia_que_solo_tiene_marcas_tambien_es_error(self):
        # `[verse]` no es una palabra cantada: tras normalizar quedan cero
        # palabras y el denominador vuelve a ser 0.
        with pytest.raises(mw.ReferenciaVacia):
            mw.medir_wer("[verse]\n[chorus]\n", "algo")

    def test_wer_puede_pasar_del_cien_por_cien_y_no_se_recorta(self):
        # 10 de referencia, 30 de hipotesis: 20 inserciones -> 200 %.
        r = mw.medir_wer(_diez_palabras(), " ".join([_diez_palabras()] * 3))
        assert r.inserciones == 20
        assert r.wer == pytest.approx(2.0)

    def test_el_desglose_cuadra_con_la_alineacion(self):
        r = mw.medir_wer("uno dos tres cuatro", "uno DOS tres cuatro cinco")
        tipos = [op.tipo for op in r.alineacion]
        assert tipos.count(mw.SUSTITUCION) == r.sustituciones
        assert tipos.count(mw.INSERCION) == r.inserciones
        assert tipos.count(mw.BORRADO) == r.borrados
        assert tipos.count(mw.IGUAL) == r.aciertos
        assert r.aciertos + r.sustituciones + r.borrados == r.n_referencia

    def test_la_alineacion_dice_QUE_fallo_no_solo_cuanto(self):
        # El acta necesita poder mirar el error concreto (§6.2, "que se archiva").
        r = mw.medir_wer("la lluvia cae despacio", "la lluvia sabe despacio")
        fallos = [op for op in r.alineacion if op.tipo != mw.IGUAL]
        assert len(fallos) == 1
        assert fallos[0].tipo == mw.SUSTITUCION
        assert (fallos[0].referencia, fallos[0].hipotesis) == ("cae", "sabe")


# --------------------------------------------------------------------------- #
# CAPA 1 — normalizacion: declarada, configurable, y la decision de las tildes
# --------------------------------------------------------------------------- #

class TestNormalizacion:

    def test_minusculas_y_puntuacion_no_cuentan_como_error(self):
        r = mw.medir_wer("¿Quien canta, ahora?", "quien canta ahora")
        assert r.wer == 0.0

    def test_la_normalizacion_usada_queda_declarada_en_el_resultado(self):
        r = mw.medir_wer("uno dos", "uno dos")
        assert r.normalizacion is mw.NORMALIZACION_PROTOCOLO
        assert r.normalizacion.nombre  # tiene nombre citable en el acta

    def test_la_del_protocolo_conserva_tildes_y_enye(self):
        assert mw.NORMALIZACION_PROTOCOLO.conservar_tildes is True

    def test_sonar_y_sonyar_son_palabras_distintas(self):
        # La quemadura del proyecto, convertida en test: si el transcriptor
        # escribe "sonar" donde la letra dice "sonar" con enye, eso es un error de
        # inteligibilidad REAL y tiene que contar.
        r = mw.medir_wer("quiero soñar contigo", "quiero sonar contigo")
        assert r.sustituciones == 1
        assert r.wer == pytest.approx(1 / 3)

    def test_tilde_diacritica_tambien_cuenta(self):
        r = mw.medir_wer("el cantara manana", "el cantará manana")
        assert r.sustituciones == 1

    def test_modo_diagnostico_sin_tildes_las_iguala_pero_se_declara(self):
        r = mw.medir_wer(
            "quiero soñar contigo", "quiero sonar contigo",
            norma=mw.NORMALIZACION_SIN_TILDES,
        )
        assert r.wer == 0.0
        assert r.normalizacion.conservar_tildes is False
        assert r.normalizacion is not mw.NORMALIZACION_PROTOCOLO

    def test_la_norma_de_diagnostico_no_es_apta_para_el_acta(self):
        # Medir con otra normalizacion que la de §6.2 y llevarla al acta seria
        # cambiar la definicion del numero despues de fijar el umbral.
        assert mw.NORMALIZACION_PROTOCOLO.apta_para_acta is True
        assert mw.NORMALIZACION_SIN_TILDES.apta_para_acta is False

    def test_las_marcas_de_seccion_no_cuentan_como_palabras(self):
        r = mw.medir_wer("[verse]\nuno dos\n[chorus]\ntres", "uno dos tres")
        assert r.n_referencia == 3
        assert r.wer == 0.0

    def test_la_contraccion_inglesa_sigue_siendo_un_token(self):
        # "don't" -> "dont", NUNCA "don" + "t": partirla inventaria una insercion
        # que el cantante no cometio.
        assert mw.normalizar("don't stop", mw.NORMALIZACION_PROTOCOLO) == ("dont", "stop")

    def test_el_guion_separa_palabras(self):
        assert mw.normalizar("lo-fi", mw.NORMALIZACION_PROTOCOLO) == ("lo", "fi")

    def test_la_misma_normalizacion_se_aplica_a_las_dos_partes(self):
        r = mw.medir_wer("HOLA, MUNDO", "hola mundo")
        assert r.referencia_normalizada == r.hipotesis_normalizada == ("hola", "mundo")

    def test_avisa_si_sobreviven_digitos(self):
        # §6.2 pide "numeros escritos en palabras". El modulo NO los convierte
        # (deletrear numeros en dos idiomas es una fuente de error propia): avisa.
        r = mw.medir_wer("eran las 3 en punto", "eran las tres en punto")
        assert r.avisos
        assert any("digito" in a.lower() or "numero" in a.lower() for a in r.avisos)

    def test_sin_digitos_no_hay_aviso(self):
        r = mw.medir_wer("eran las tres en punto", "eran las tres en punto")
        assert r.avisos == ()

    def test_avisa_de_un_homoglifo_invisible(self):
        # Caso REAL, medido el 2026-09-03 sobre el corpus del suelo: el
        # transcriptor escribio «conflated» con una «е» cirilica. A la vista es la
        # misma palabra; para el WER es una sustitucion, y sin este aviso quien
        # mirase la alineacion vería 'conflated' -> 'conflated' y no entenderia nada.
        r = mw.medir_wer("usually conflated with christmas", "usually conflatеd with christmas")
        assert r.sustituciones == 1
        assert any("mezcladas" in a.lower() for a in r.avisos)
        assert any("conflat" in a for a in r.avisos)

    def test_avisa_si_la_transcripcion_se_va_a_otra_escritura(self):
        # El otro caso observado: el modelo suelta un «啊» en medio de una pista en
        # castellano pese a llevar el idioma forzado.
        r = mw.medir_wer("ah se apaga la ciudad", "ah 啊 se apaga la ciudad")
        assert any("escrituras que la referencia no usa" in a for a in r.avisos)

    def test_las_tildes_NO_son_otra_escritura(self):
        # «á» es LATIN SMALL LETTER A WITH ACUTE: si esto avisara, el aviso saltaria
        # en cada pista en castellano y dejaria de significar nada.
        r = mw.medir_wer("la canción soñada", "la canción soñada")
        assert r.avisos == ()


# --------------------------------------------------------------------------- #
# CAPA 2 — la puerta de licencia: sin ficha verificada, no se mide
# --------------------------------------------------------------------------- #

class TestPuertaDeLicencia:

    def test_sin_ficha_no_se_mide_y_dice_que_falta(self, tmp_path):
        t = mw.TranscriptorDePrueba("lo que sea")
        with pytest.raises(mw.TranscriptorNoAptoParaActa) as exc:
            mw.exigir_apto_para_acta(t)
        mensaje = str(exc.value)
        assert "ficha" in mensaje.lower()
        assert "prueba" in mensaje.lower()

    def test_la_ficha_incompleta_enumera_exactamente_los_campos_que_faltan(self, tmp_path):
        ruta = _ficha_valida(tmp_path, sha256_pesos=_BORRAR, licencia_spdx=_BORRAR)
        with pytest.raises(mw.FichaInvalida) as exc:
            mw.cargar_ficha(ruta)
        mensaje = str(exc.value)
        assert "sha256_pesos" in mensaje
        assert "licencia_spdx" in mensaje

    def test_ficha_que_no_existe_dice_donde_se_busco(self, tmp_path):
        ausente = tmp_path / "no-existe.json"
        with pytest.raises(mw.FichaAusente) as exc:
            mw.cargar_ficha(ausente)
        assert str(ausente) in str(exc.value)

    def test_licencia_no_comercial_se_rechaza(self, tmp_path):
        ruta = _ficha_valida(tmp_path, licencia_spdx="CC-BY-NC-4.0")
        with pytest.raises(mw.LicenciaNoPermitida) as exc:
            mw.cargar_ficha(ruta)
        assert "CC-BY-NC-4.0" in str(exc.value)

    def test_licencia_desconocida_se_rechaza_por_defecto(self, tmp_path):
        # Lista blanca, no lista negra: lo que no esta verificado, no pasa.
        ruta = _ficha_valida(tmp_path, licencia_spdx="LicenciaRarisima-9.9")
        with pytest.raises(mw.LicenciaNoPermitida):
            mw.cargar_ficha(ruta)

    def test_pesos_que_no_son_safetensors_se_rechazan(self, tmp_path):
        malo = tmp_path / "transcriptor.bin"
        malo.write_bytes(b"\x80\x04pickle")
        ruta = _ficha_valida(tmp_path, ruta_pesos=str(malo))
        with pytest.raises(mw.FichaInvalida) as exc:
            mw.cargar_ficha(ruta)
        assert "safetensors" in str(exc.value).lower()

    def test_hash_que_no_cuadra_se_rechaza(self, tmp_path):
        ruta = _ficha_valida(tmp_path, sha256_pesos="00" * 32)
        with pytest.raises(mw.FichaInvalida) as exc:
            mw.cargar_ficha(ruta)
        assert "sha256" in str(exc.value).lower()

    def test_una_ficha_completa_pasa_la_puerta(self, tmp_path):
        ficha = mw.cargar_ficha(_ficha_valida(tmp_path))
        assert ficha.identificador == "HeartTranscriptor-oss"
        assert ficha.licencia_spdx == "Apache-2.0"
        assert ficha.licencia_verificada_el == "2026-09-03"

    def test_la_ficha_no_puede_declarar_un_transcriptor_de_prueba(self, tmp_path):
        # Una ficha es una declaracion sobre pesos reales; no puede blanquear el
        # doble de pruebas diciendo que si.
        ficha = mw.cargar_ficha(_ficha_valida(tmp_path))
        t = mw.TranscriptorDePrueba("da igual", ficha=ficha)
        with pytest.raises(mw.TranscriptorNoAptoParaActa):
            mw.exigir_apto_para_acta(t)


class TestTranscriptorDePrueba:

    def test_devuelve_el_texto_fijo_que_se_le_dio(self, tmp_path):
        t = mw.TranscriptorDePrueba("uno dos tres")
        assert t.transcribir(tmp_path / "b01.wav", "es") == "uno dos tres"

    def test_esta_marcado_como_de_prueba(self):
        assert mw.TranscriptorDePrueba("x").es_de_prueba is True

    def test_sirve_para_medir_cuando_NO_va_al_acta(self, tmp_path):
        t = mw.TranscriptorDePrueba("uno dos tres cuatro")
        med = mw.medir_pista(
            t, tmp_path / "b01.wav", "es", "uno dos tres cuatro",
            brief="B-01", para_acta=False,
        )
        assert med.resultado.wer == 0.0
        assert med.apta_para_acta is False

    def test_NO_sirve_para_una_medida_que_va_al_acta(self, tmp_path):
        # El test que da sentido a toda la capa 2: inventarse el numero del gate
        # con un doble de pruebas es exactamente lo que no puede poder hacerse.
        t = mw.TranscriptorDePrueba("uno dos tres cuatro")
        with pytest.raises(mw.TranscriptorNoAptoParaActa):
            mw.medir_pista(
                t, tmp_path / "b01.wav", "es", "uno dos tres cuatro",
                brief="B-01", para_acta=True,
            )

    def test_para_acta_es_lo_que_se_asume_si_no_se_dice(self, tmp_path):
        # El valor por defecto tiene que ser el estricto: quien quiera un numero
        # de juguete lo pide explicitamente.
        t = mw.TranscriptorDePrueba("uno")
        with pytest.raises(mw.TranscriptorNoAptoParaActa):
            mw.medir_pista(t, tmp_path / "b01.wav", "es", "uno", brief="B-01")


# --------------------------------------------------------------------------- #
# CAPA 2 — el suelo del transcriptor: sin el, el 15 % no significa nada
# --------------------------------------------------------------------------- #

class TestSueloDelTranscriptor:

    def test_se_mide_sobre_voz_clara_de_referencia(self, tmp_path):
        # El transcriptor de prueba se equivoca en una palabra de cada cinco:
        # ese 20 % es su suelo, y no es culpa de ningun cantante.
        t = mw.TranscriptorDePrueba("uno dos tres cuatro CINCO_MAL")
        suelo = mw.medir_suelo(
            t,
            [(tmp_path / "voz.wav", "es", "uno dos tres cuatro cinco")],
            para_acta=False,
        )
        assert suelo.wer_medio == pytest.approx(0.20)
        assert suelo.n_muestras == 1

    def test_sin_suelo_el_resumen_se_declara_NO_interpretable(self, tmp_path):
        res = mw.resumir([self._medicion(tmp_path, 0.10)], suelo=None)
        assert res.interpretable is False
        assert any("suelo" in n.lower() for n in res.notas)

    def test_con_suelo_el_resumen_es_interpretable_y_publica_el_margen(self, tmp_path):
        suelo = mw.Suelo(wer_medio=0.05, n_muestras=3, detalle=())
        res = mw.resumir([self._medicion(tmp_path, 0.10)], suelo=suelo)
        assert res.interpretable is True
        assert res.media_menos_suelo == pytest.approx(0.05)

    def test_el_suelo_NO_cambia_el_veredicto_del_umbral(self, tmp_path):
        # §2 regla de inmutabilidad: el 15 % se aplica tal cual. Restar el suelo
        # es interpretacion, no aritmetica del gate.
        suelo = mw.Suelo(wer_medio=0.10, n_muestras=3, detalle=())
        res = mw.resumir([self._medicion(tmp_path, 0.20)], suelo=suelo)
        assert res.media == pytest.approx(0.20)
        assert res.media_menos_suelo == pytest.approx(0.10)  # "pasaria" restando
        assert res.cumple_media is False                      # pero NO pasa

    @staticmethod
    def _medicion(tmp_path: Path, wer_objetivo: float) -> mw.MedicionPista:
        """Una medicion con el WER que se quiera, hecha con verdad conocida."""
        n = 20
        fallos = round(wer_objetivo * n)
        ref = " ".join(f"p{i}" for i in range(n))
        hip = " ".join(("x" if i < fallos else f"p{i}") for i in range(n))
        t = mw.TranscriptorDePrueba(hip)
        return mw.medir_pista(t, tmp_path / "x.wav", "es", ref, brief="B-01", para_acta=False)


class TestResumenDelCriterio4:

    def _med(self, tmp_path, brief, wer):
        return TestSueloDelTranscriptor._medicion(tmp_path, wer)._replace(brief=brief)

    def test_media_y_peor_caso(self, tmp_path):
        res = mw.resumir(
            [self._med(tmp_path, "B-01", 0.05), self._med(tmp_path, "B-02", 0.25)],
            suelo=None,
        )
        assert res.media == pytest.approx(0.15)
        assert res.peor == pytest.approx(0.25)
        assert res.brief_peor == "B-02"

    def test_cumple_los_dos_umbrales(self, tmp_path):
        res = mw.resumir([self._med(tmp_path, "B-01", 0.10)], suelo=None)
        assert res.cumple_media is True and res.cumple_peor is True

    def test_media_buena_pero_un_peor_caso_por_encima_del_25_no_cumple(self, tmp_path):
        # Los dos umbrales son AND, no un promedio que compense.
        res = mw.resumir(
            [self._med(tmp_path, "B-01", 0.0), self._med(tmp_path, "B-02", 0.30)],
            suelo=None,
        )
        assert res.media == pytest.approx(0.15)
        assert res.cumple_media is True
        assert res.cumple_peor is False

    def test_cumple_es_un_AND_y_no_admite_compensacion(self, tmp_path):
        # §8.3: los criterios se comprueban "sin ponderaciones ni compensaciones".
        # Una media impecable NO rescata un peor caso por encima del 25 %.
        res = mw.resumir(
            [self._med(tmp_path, "B-01", 0.0), self._med(tmp_path, "B-02", 0.30)],
            suelo=None,
        )
        assert (res.cumple_media, res.cumple_peor) == (True, False)
        assert res.cumple is False

    def test_una_media_alta_tampoco_se_salva_por_un_peor_caso_decente(self, tmp_path):
        res = mw.resumir([self._med(tmp_path, "B-01", 0.20)], suelo=None)
        assert (res.cumple_media, res.cumple_peor) == (False, True)
        assert res.cumple is False

    def test_cumple_cuando_pasan_los_dos(self, tmp_path):
        res = mw.resumir([self._med(tmp_path, "B-01", 0.10)], suelo=None)
        assert res.cumple is True

    def test_resumir_sin_mediciones_es_error(self):
        with pytest.raises(ValueError):
            mw.resumir([], suelo=None)

    def test_un_resumen_del_acta_exige_que_todas_las_mediciones_lo_sean(self, tmp_path):
        with pytest.raises(mw.TranscriptorNoAptoParaActa):
            mw.resumir([self._med(tmp_path, "B-01", 0.10)], suelo=None, para_acta=True)



# --------------------------------------------------------------------------- #
# CAPA 3 — la auditoria del directorio de pesos, que corre SIN pesos
# --------------------------------------------------------------------------- #

def _cabecera_safetensors() -> bytes:
    cuerpo = b'{"__metadata__":{"formato":"prueba"}}'
    return len(cuerpo).to_bytes(8, "little") + cuerpo + b"\x00" * 16


def _modelo_falso(raiz: Path, *, config: dict | None = None, extras: dict | None = None) -> Path:
    """Un directorio con la FORMA de un modelo, sin ser uno.

    Que un test pueda fabricar esto con `write_bytes` es la prueba de que la
    auditoria mira el directorio y no el modelo: no hace falta descargar 3 GB para
    comprobar que un `.bin` al lado tumba la carga.
    """
    raiz.mkdir(parents=True, exist_ok=True)
    (raiz / "model.safetensors").write_bytes(_cabecera_safetensors())
    (raiz / "config.json").write_text(
        json.dumps(config if config is not None else {"model_type": "whisper"}), encoding="utf-8"
    )
    for nombre, contenido in (extras or {}).items():
        destino = raiz / nombre
        destino.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(contenido, bytes):
            destino.write_bytes(contenido)
        else:
            destino.write_text(contenido, encoding="utf-8")
    return raiz


class TestAuditoriaDelDirectorioDeModelo:
    """Lo ultimo que se mira antes de dejar que `transformers` abra el directorio."""

    def test_un_directorio_limpio_pasa_y_enumera_lo_que_vio(self, tmp_path):
        auditoria = mw.auditar_directorio_modelo(_modelo_falso(tmp_path / "m"))
        assert [p.name for p in auditoria.pesos] == ["model.safetensors"]
        assert auditoria.n_ficheros == 2

    def test_un_bin_al_lado_tumba_el_directorio_entero(self, tmp_path):
        # Aunque hoy se cargue con use_safetensors=True: un formato alternativo al
        # lado es un cargador esperando equivocarse, y .bin es pickle (D-14).
        raiz = _modelo_falso(tmp_path / "m", extras={"pytorch_model.bin": b"\x80\x04pickle"})
        with pytest.raises(mw.ModeloConPesosInseguros) as exc:
            mw.auditar_directorio_modelo(raiz)
        assert "pytorch_model.bin" in str(exc.value)

    @pytest.mark.parametrize("nombre", ["modeling_raro.py", "sub/otro.py", "acelerador.dll"])
    def test_el_codigo_dentro_del_modelo_se_rechaza(self, tmp_path, nombre):
        raiz = _modelo_falso(tmp_path / "m", extras={nombre: "print('hola')"})
        with pytest.raises(mw.ModeloConCodigoRemoto) as exc:
            mw.auditar_directorio_modelo(raiz)
        assert Path(nombre).name in str(exc.value)

    @pytest.mark.parametrize("clave", ["auto_map", "custom_pipelines", "custom_code"])
    def test_pedir_codigo_remoto_por_configuracion_se_rechaza(self, tmp_path, clave):
        raiz = _modelo_falso(
            tmp_path / "m",
            config={"model_type": "whisper", clave: {"AutoModel": "modeling_raro.Modelo"}},
        )
        with pytest.raises(mw.ModeloConCodigoRemoto) as exc:
            mw.auditar_directorio_modelo(raiz)
        assert clave in str(exc.value)

    def test_lo_encuentra_aunque_este_anidado_hondo(self, tmp_path):
        # `tokenizer.json` anida mucho; esconder ahi un auto_map no puede colar.
        raiz = _modelo_falso(tmp_path / "m", extras={
            "tokenizer.json": json.dumps({"a": [{"b": {"c": {"auto_map": "x"}}}]}),
        })
        with pytest.raises(mw.ModeloConCodigoRemoto):
            mw.auditar_directorio_modelo(raiz)

    def test_trust_remote_code_en_true_se_rechaza(self, tmp_path):
        raiz = _modelo_falso(tmp_path / "m", config={"trust_remote_code": True})
        with pytest.raises(mw.ModeloConCodigoRemoto):
            mw.auditar_directorio_modelo(raiz)

    def test_trust_remote_code_en_false_es_lo_correcto_y_no_molesta(self, tmp_path):
        # Declararlo apagado es la practica buena: no puede leerse como sospecha.
        raiz = _modelo_falso(tmp_path / "m", config={"trust_remote_code": False})
        assert mw.auditar_directorio_modelo(raiz).pesos

    def test_sin_safetensors_no_hay_modelo(self, tmp_path):
        raiz = tmp_path / "m"
        raiz.mkdir()
        (raiz / "config.json").write_text("{}", encoding="utf-8")
        with pytest.raises(mw.ModeloNoAuditable) as exc:
            mw.auditar_directorio_modelo(raiz)
        assert "safetensors" in str(exc.value)

    def test_un_directorio_que_no_existe_dice_que_aqui_no_se_descarga_nada(self, tmp_path):
        with pytest.raises(mw.ModeloNoAuditable) as exc:
            mw.auditar_directorio_modelo(tmp_path / "no-esta")
        assert "descarga" in str(exc.value).lower()


class TestTranscriptorLocalSinTocarLosPesos:
    """Todo lo que el transcriptor real garantiza ANTES de cargar 3 GB."""

    @staticmethod
    def _con_ficha(tmp_path):
        raiz = _modelo_falso(tmp_path / "m")
        ruta_ficha = _ficha_valida(
            tmp_path,
            ruta_pesos=str(raiz / "model.safetensors"),
            sha256_pesos=hashlib.sha256((raiz / "model.safetensors").read_bytes()).hexdigest(),
        )
        return mw.TranscriptorLocal(mw.cargar_ficha(ruta_ficha))

    def test_no_esta_marcado_como_de_prueba(self, tmp_path):
        assert self._con_ficha(tmp_path).es_de_prueba is False

    def test_cruza_la_puerta_del_acta(self, tmp_path):
        t = self._con_ficha(tmp_path)
        assert mw.exigir_apto_para_acta(t) is t.ficha

    def test_construirlo_no_carga_los_pesos(self, tmp_path):
        # El punto entero de la carga perezosa: la puerta, la auditoria y estos
        # tests corren sin gastar la RAM ni el segundo de carga del modelo.
        t = self._con_ficha(tmp_path)
        assert t.segundos_carga is None
        assert t.llamadas == 0
        assert t.rtf_medio is None

    def test_el_idioma_es_obligatorio_y_se_comprueba_antes_de_cargar_nada(self, tmp_path):
        t = self._con_ficha(tmp_path)
        with pytest.raises(ValueError, match="FUERZA"):
            t.transcribir(tmp_path / "b01.wav", "")
        assert t.segundos_carga is None  # ni ha intentado abrir el modelo

    def test_exige_una_ficha_salida_de_cargar_ficha(self, tmp_path):
        with pytest.raises(TypeError):
            mw.TranscriptorLocal({"identificador": "lo que sea"})

    def test_una_ficha_con_licencia_de_fuera_de_la_lista_no_llega_a_construir(self, tmp_path):
        # La puerta esta en el constructor: un transcriptor que no podria producir
        # una cifra del acta no deberia ni existir.
        raiz = _modelo_falso(tmp_path / "m")
        ficha = mw.FichaTranscriptor(
            identificador="x", version="0", ruta_pesos=raiz / "model.safetensors",
            licencia_spdx="Propietaria-sin-uso-comercial", sha256_pesos="0" * 64,
            licencia_verificada_por="nadie", licencia_verificada_el="2026-01-01",
            fuente_licencia="inventada", ruta_ficha=tmp_path / "ficha.json",
        )
        with pytest.raises(mw.TranscriptorNoAptoParaActa, match="licencia"):
            mw.TranscriptorLocal(ficha)

    def test_los_pesos_de_la_ficha_tienen_que_ser_los_del_directorio(self, tmp_path):
        # La ficha acredita UN fichero por su sha256. Cargar otro dejaria el acta
        # declarando un hash que no es el de los pesos que midieron.
        raiz = _modelo_falso(tmp_path / "m")
        otro = _modelo_falso(tmp_path / "otro")
        ruta_ficha = _ficha_valida(
            tmp_path,
            ruta_pesos=str(otro / "model.safetensors"),
            sha256_pesos=hashlib.sha256((otro / "model.safetensors").read_bytes()).hexdigest(),
        )
        with pytest.raises(mw.ModeloNoAuditable, match="sha256"):
            mw.TranscriptorLocal(mw.cargar_ficha(ruta_ficha), directorio=raiz)


# --------------------------------------------------------------------------- #
# CAPA 3 — lectura de audio (necesita numpy; scipy solo si hay que remuestrear)
# --------------------------------------------------------------------------- #

def _wav(ruta: Path, *, sr: int = 16000, canales: int = 1, bits: int = 16,
         segundos: float = 1.0, frames: int | None = None) -> Path:
    import wave as _wave

    n = frames if frames is not None else int(sr * segundos)
    with _wave.open(str(ruta), "wb") as w:
        w.setnchannels(canales)
        w.setsampwidth(bits // 8)
        w.setframerate(sr)
        w.writeframes(b"\x01\x00" * n * canales if bits == 16 else b"\x40" * n * canales)
    return ruta


@pytest.mark.skipif(not _hay("numpy"), reason="leer audio necesita numpy")
class TestLecturaDeAudio:

    def test_lee_un_wav_de_16_bits_y_devuelve_la_duracion_del_original(self, tmp_path):
        muestras, duracion, sr = mw.leer_wav_mono_16k(
            _wav(tmp_path / "a.wav", sr=16000, segundos=2.0)
        )
        assert sr == 16000
        assert duracion == pytest.approx(2.0)
        assert len(muestras) == 32000

    def test_mezcla_a_mono(self, tmp_path):
        muestras, _, _ = mw.leer_wav_mono_16k(
            _wav(tmp_path / "a.wav", sr=16000, canales=2, segundos=1.0)
        )
        assert len(muestras) == 16000

    @pytest.mark.skipif(not _hay("scipy"), reason="remuestrear necesita scipy")
    def test_remuestrea_a_16k_pero_la_duracion_sigue_siendo_la_real(self, tmp_path):
        # El RTF se divide por la duracion del audio, no por la del remuestreo:
        # confundirlas inflaria o desinflaria el cronometro por un factor de tres.
        muestras, duracion, sr = mw.leer_wav_mono_16k(
            _wav(tmp_path / "a.wav", sr=48000, segundos=1.0)
        )
        assert sr == 48000
        assert duracion == pytest.approx(1.0)
        assert len(muestras) == pytest.approx(16000, abs=8)

    def test_rechaza_lo_que_no_es_wav(self, tmp_path):
        mp3 = tmp_path / "a.mp3"
        mp3.write_bytes(b"ID3")
        with pytest.raises(mw.AudioNoSoportado, match="WAV"):
            mw.leer_wav_mono_16k(mp3)

    def test_rechaza_una_profundidad_que_no_sea_de_16_bits(self, tmp_path):
        with pytest.raises(mw.AudioNoSoportado, match="16 bits"):
            mw.leer_wav_mono_16k(_wav(tmp_path / "a.wav", bits=8, segundos=1.0))

    def test_rechaza_un_wav_sin_muestras(self, tmp_path):
        with pytest.raises(mw.AudioNoSoportado):
            mw.leer_wav_mono_16k(_wav(tmp_path / "a.wav", frames=0))

    def test_dice_donde_busco_el_audio_que_falta(self, tmp_path):
        with pytest.raises(mw.AudioNoSoportado) as exc:
            mw.leer_wav_mono_16k(tmp_path / "no-esta.wav")
        assert "no-esta.wav" in str(exc.value)


# --------------------------------------------------------------------------- #
# El corpus del suelo: el audio de referencia tambien declara su licencia
# --------------------------------------------------------------------------- #

def _corpus(tmp_path, *, muestras=None, **cambios) -> Path:
    (tmp_path / "es").mkdir(exist_ok=True)
    _wav(tmp_path / "es" / "v1.wav", segundos=1.0)
    documento = {
        "schema": mw.SCHEMA_CORPUS_SUELO,
        "descripcion": "voz leida clara de prueba",
        "licencia_spdx": "CC-BY-SA-4.0",
        "fuente_licencia": "https://ejemplo.invalido/LICENSE",
        "licencia_verificada_el": "2026-09-03",
        "muestras": [{"ruta": "es/v1.wav", "idioma": "es", "texto": "uno dos tres cuatro"}]
        if muestras is None else muestras,
    }
    documento.update(cambios)
    for clave, valor in list(documento.items()):
        if valor is _BORRAR:
            del documento[clave]
    ruta = tmp_path / "corpus.json"
    ruta.write_text(json.dumps(documento), encoding="utf-8")
    return ruta


class TestCorpusDelSuelo:

    def test_un_corpus_valido_carga_y_resuelve_las_rutas_contra_el_manifiesto(self, tmp_path):
        # Rutas relativas para que el corpus se pueda mover entero sin reescribirlo.
        corpus = mw.cargar_corpus_suelo(_corpus(tmp_path))
        assert corpus.licencia_spdx == "CC-BY-SA-4.0"
        assert corpus.muestras[0].ruta == (tmp_path / "es" / "v1.wav").resolve()
        assert corpus.triples() == ((corpus.muestras[0].ruta, "es", "uno dos tres cuatro"),)

    def test_sin_licencia_declarada_no_carga(self, tmp_path):
        with pytest.raises(mw.CorpusInvalido, match="licencia_spdx"):
            mw.cargar_corpus_suelo(_corpus(tmp_path, licencia_spdx=_BORRAR))

    def test_una_licencia_no_comercial_del_audio_se_rechaza(self, tmp_path):
        with pytest.raises(mw.CorpusInvalido) as exc:
            mw.cargar_corpus_suelo(_corpus(tmp_path, licencia_spdx="CC-BY-NC-4.0"))
        assert "CC-BY-NC-4.0" in str(exc.value)

    def test_sharealike_vale_para_el_CORPUS_pero_NO_para_el_pipeline(self):
        # La distincion es deliberada, no un descuido: el corpus del suelo se
        # escucha y se tira, no se integra ni se redistribuye, asi que la clausula
        # de ShareAlike no contagia nada. Unos PESOS con esa clausula si podrian
        # contagiar lo que se genere con ellos, y por eso la lista del pipeline
        # sigue sin admitirla.
        assert "CC-BY-SA-4.0" in mw.LICENCIAS_CORPUS_SUELO
        assert "CC-BY-SA-4.0" not in mw.LICENCIAS_COMERCIALES
        assert mw.LICENCIAS_COMERCIALES < mw.LICENCIAS_CORPUS_SUELO

    def test_un_audio_que_falta_se_detecta_antes_de_medir(self, tmp_path):
        with pytest.raises(mw.CorpusInvalido) as exc:
            mw.cargar_corpus_suelo(_corpus(tmp_path, muestras=[
                {"ruta": "es/no-esta.wav", "idioma": "es", "texto": "uno dos"},
            ]))
        assert "no existe" in str(exc.value)

    def test_un_corpus_sin_muestras_no_es_un_suelo_de_cero(self, tmp_path):
        with pytest.raises(mw.CorpusInvalido, match="cero muestras"):
            mw.cargar_corpus_suelo(_corpus(tmp_path, muestras=[]))

    def test_un_esquema_desconocido_no_se_interpreta_a_medias(self, tmp_path):
        with pytest.raises(mw.CorpusInvalido, match="schema"):
            mw.cargar_corpus_suelo(_corpus(tmp_path, schema=99))

    def test_una_muestra_sin_texto_se_rechaza(self, tmp_path):
        with pytest.raises(mw.CorpusInvalido, match="texto"):
            mw.cargar_corpus_suelo(_corpus(tmp_path, muestras=[
                {"ruta": "es/v1.wav", "idioma": "es", "texto": "   "},
            ]))


class TestElSueloDeclaraSuLimitacion:
    """Lo que el encargo llama «no restarlo sin decirlo»."""

    def test_el_suelo_dice_sobre_que_se_midio_y_que_es_una_cota_inferior(self, tmp_path):
        t = mw.TranscriptorDePrueba("uno dos tres cuatro cinco")
        suelo = mw.medir_suelo(
            t, [(tmp_path / "v.wav", "es", "uno dos tres cuatro cinco")], para_acta=False,
        )
        assert suelo.dominio.startswith("habla")
        assert suelo.es_cota_inferior_del_suelo_de_canto is True

    def test_la_limitacion_nombra_las_DOS_direcciones_del_sesgo(self):
        # Decir solo «es una cota inferior» invita a la lectura comoda. El aviso
        # tiene que decir a quien favorece cada uso, porque no es el mismo.
        aviso = mw.AVISO_SUELO_ES_COTA_INFERIOR.lower()
        assert "cota inferior" in aviso
        assert "favorece al transcriptor" in aviso
        assert "perjudica al generador" in aviso

    def test_el_resumen_publica_la_limitacion_junto_al_numero(self, tmp_path):
        suelo = mw.Suelo(wer_medio=0.05, n_muestras=3, detalle=())
        res = mw.resumir([TestSueloDelTranscriptor._medicion(tmp_path, 0.10)], suelo=suelo)
        assert any(mw.AVISO_SUELO_ES_COTA_INFERIOR == n for n in res.notas)

    def test_el_suelo_se_desglosa_por_idioma(self, tmp_path):
        # Un suelo global esconde que un idioma vaya mucho peor que el otro, y §4
        # mide en dos.
        perfecto = mw.TranscriptorDePrueba("uno dos tres cuatro")
        suelo = mw.medir_suelo(perfecto, [
            (tmp_path / "a.wav", "es", "uno dos tres cuatro"),
            (tmp_path / "b.wav", "en", "uno dos tres MAL"),
        ], para_acta=False)
        por_idioma = suelo.por_idioma()
        assert por_idioma["es"] == pytest.approx(0.0)
        assert por_idioma["en"] == pytest.approx(0.25)

    def test_un_corpus_cargado_deja_su_licencia_pegada_al_suelo(self, tmp_path):
        corpus = mw.cargar_corpus_suelo(_corpus(tmp_path))
        suelo = mw.medir_suelo(
            mw.TranscriptorDePrueba("uno dos tres cuatro"), corpus, para_acta=False,
        )
        assert suelo.licencia_corpus == "CC-BY-SA-4.0"
        assert suelo.corpus.endswith("corpus.json")
# --------------------------------------------------------------------------- #
# Los umbrales son del protocolo, no de este fichero
# --------------------------------------------------------------------------- #

class TestUmbralesContraElProtocolo:

    def test_las_constantes_coinciden_con_el_2_del_protocolo(self):
        texto = _PROTOCOLO.read_text(encoding="utf-8")
        media = re.search(r"≤\s*(\d+)\s*%\s*de media", texto)
        peor = re.search(r"≤\s*(\d+)\s*%\s*en el peor caso", texto)
        assert media and peor, "el §2 del protocolo ya no dice los umbrales como se esperaba"
        assert mw.UMBRAL_WER_MEDIA == pytest.approx(int(media.group(1)) / 100)
        assert mw.UMBRAL_WER_PEOR == pytest.approx(int(peor.group(1)) / 100)

    def test_la_funcion_de_verificacion_detecta_la_deriva(self, tmp_path):
        falso = tmp_path / "protocolo.md"
        falso.write_text("4. **WER**: ≤ 40 % de media y ≤ 50 % en el peor caso.", "utf-8")
        with pytest.raises(mw.UmbralesDerivados):
            mw.verificar_umbrales(falso)

    def test_la_funcion_de_verificacion_acepta_el_protocolo_real(self):
        assert mw.verificar_umbrales(_PROTOCOLO) == (mw.UMBRAL_WER_MEDIA, mw.UMBRAL_WER_PEOR)


# --------------------------------------------------------------------------- #
# Invariantes del proyecto sobre el propio modulo
# --------------------------------------------------------------------------- #

class TestInvariantesDelModulo:

    @staticmethod
    def _arbol() -> ast.Module:
        return ast.parse(Path(mw.__file__).read_text(encoding="utf-8"))

    @staticmethod
    def _importaciones() -> tuple[set[str], set[str]]:
        """`(las de nivel de modulo, las anidadas dentro de una funcion)`.

        La distincion es el invariante. Antes de la capa 3 bastaba con prohibir
        `torch` y `transformers` en todo el fichero; ahora el modulo los usa de
        verdad, y lo que hay que garantizar es mas fino: que **importarlo** no
        los arrastre. Un import perezoso dentro del metodo de carga cumple eso;
        uno arriba, no. Se mira el AST y no el texto, para no castigar a la
        documentacion por nombrar lo que regula.
        """
        modulo: set[str] = set()
        anidados: set[str] = set()

        def recorrer(nodos, dentro_de_funcion: bool) -> None:
            for nodo in nodos:
                if isinstance(nodo, ast.Import):
                    nombres = {a.name.split(".")[0] for a in nodo.names}
                elif isinstance(nodo, ast.ImportFrom):
                    nombres = {(nodo.module or "").split(".")[0]} - {""}
                else:
                    nombres = set()
                (anidados if dentro_de_funcion else modulo).update(nombres)
                recorrer(
                    ast.iter_child_nodes(nodo),
                    dentro_de_funcion or isinstance(
                        nodo, (ast.FunctionDef, ast.AsyncFunctionDef)
                    ),
                )

        recorrer(ast.iter_child_nodes(TestInvariantesDelModulo._arbol()), False)
        return modulo, anidados

    def test_importar_el_modulo_solo_cuesta_biblioteca_estandar(self):
        # Lista BLANCA y no negra: lo que aparezca arriba sin estar aqui es una
        # dependencia nueva del camino barato, y tiene que discutirse en un
        # commit, no colarse.
        permitidos = {
            "__future__", "argparse", "hashlib", "json", "math", "os", "re", "sys",
            "time", "unicodedata", "wave", "dataclasses", "pathlib", "typing",
            "contracts",  # el del propio runner: puertas D-14, tambien sin dependencias
        }
        modulo, _ = self._importaciones()
        assert modulo <= permitidos, (
            f"imports nuevos en el nivel de modulo: {sorted(modulo - permitidos)}. La capa 1 "
            "y la puerta tienen que seguir corriendo en un Python limpio."
        )

    def test_torch_y_transformers_solo_se_importan_dentro_de_una_funcion(self):
        modulo, anidados = self._importaciones()
        assert {"torch", "transformers"} & modulo == set()
        assert {"torch", "transformers"} <= anidados, (
            "si ya no se importan de forma perezosa, o se ha quitado el transcriptor real "
            "o se ha roto la carga perezosa. Las dos cosas hay que mirarlas."
        )

    def test_nada_de_red_ni_de_pickle_en_ningun_sitio(self):
        # Esto si sigue siendo absoluto: ni arriba ni dentro de una funcion. Lo
        # unico que puede traer pesos aqui es el propietario, a mano, con su ficha.
        prohibidos = {
            "urllib", "requests", "httpx", "http", "socket", "ftplib",
            "huggingface_hub", "pickle", "dill", "joblib",
        }
        modulo, anidados = self._importaciones()
        encontrados = (modulo | anidados) & prohibidos
        assert not encontrados, f"el modulo importa algo que no debe: {sorted(encontrados)}"

    def test_importar_el_modulo_no_arrastra_torch_ni_transformers(self):
        """El invariante de verdad, comprobado ejecutandolo y no leyendolo.

        En un interprete limpio: importar `medir_wer` no puede dejar `torch` ni
        `transformers` en `sys.modules`. Va en un subproceso porque en esta misma
        sesion de pytest otro test ya los habra cargado.
        """
        codigo = (
            "import sys\n"
            f"sys.path.insert(0, {str(Path(mw.__file__).parent)!r})\n"
            "import medir_wer\n"
            "print(int('torch' in sys.modules), int('transformers' in sys.modules))\n"
        )
        salida = subprocess.run(
            [sys.executable, "-c", codigo], capture_output=True, text=True, timeout=180,
        )
        assert salida.returncode == 0, salida.stderr
        assert salida.stdout.split() == ["0", "0"], (
            f"importar el modulo arrastro dependencias pesadas: {salida.stdout!r}"
        )

    def test_toda_carga_de_modelo_es_local_y_sin_codigo_remoto(self):
        # El invariante escrito donde no se puede olvidar: cada `from_pretrained`
        # del modulo tiene que llevar las dos banderas. Sin `local_files_only`,
        # un fichero que falte se busca en el hub y entrarian pesos que nadie
        # verifico; sin `trust_remote_code=False`, la bandera queda al criterio
        # de la version de transformers que haya instalada.
        llamadas = [
            n for n in ast.walk(self._arbol())
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and n.func.attr == "from_pretrained"
        ]
        assert llamadas, "ya no se carga ningun modelo: si es a proposito, borra este test"
        for llamada in llamadas:
            claves = {k.arg: k.value for k in llamada.keywords}
            for bandera, esperado in (("local_files_only", True), ("trust_remote_code", False)):
                valor = claves.get(bandera)
                assert isinstance(valor, ast.Constant) and valor.value is esperado, (
                    f"un from_pretrained sin {bandera}={esperado} (linea {llamada.lineno})"
                )
        assert any(
            isinstance(claves.get("use_safetensors"), ast.Constant)
            and claves["use_safetensors"].value is True
            for claves in ({k.arg: k.value for k in ll.keywords} for ll in llamadas)
        ), "ninguna carga pide use_safetensors=True (D-14)"

    def test_no_se_usa_ninguna_clase_Auto_de_transformers(self):
        # `Auto*` es justo lo que consulta `auto_map` para importar un .py del
        # repositorio del modelo. Usar la clase concreta cierra esa via por
        # construccion, que es mas fuerte que cerrarla con una bandera.
        traidos = set()
        for nodo in ast.walk(self._arbol()):
            if isinstance(nodo, ast.ImportFrom) and (nodo.module or "").startswith("transformers"):
                traidos.update(a.name for a in nodo.names)
        assert traidos, "el modulo ya no importa nada de transformers: revisa este test"
        assert not [n for n in traidos if n.startswith("Auto")], (
            f"se ha colado una clase Auto*: {sorted(traidos)}"
        )

    def test_no_llama_a_torch_load_ni_a_ninguna_deserializacion(self):
        peligrosos = {"load", "loads", "eval", "exec", "__import__"}
        for nodo in ast.walk(self._arbol()):
            if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute):
                if nodo.func.attr in {"load", "loads"}:
                    # json.load/loads es lo unico admitido, y sobre texto.
                    base = nodo.func.value
                    assert isinstance(base, ast.Name) and base.id == "json", (
                        f"deserializacion no permitida: {ast.dump(nodo.func)}"
                    )
            if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name):
                assert nodo.func.id not in (peligrosos - {"load", "loads"}), (
                    f"llamada prohibida: {nodo.func.id}"
                )

    def test_la_puerta_reutiliza_la_de_D14_y_no_reescribe_otra(self):
        fuente = Path(mw.__file__).read_text(encoding="utf-8")
        assert "assert_safetensors" in fuente


class TestLaFichaSeRevalidaDondeSeUsa:
    """`isinstance(ficha, FichaTranscriptor)` no comprueba nada del contenido.

    `FichaTranscriptor` es un NamedTuple publico: se construye a mano con una
    licencia propietaria y una ruta a un `.bin`, pasa el `isinstance` y cruza la
    puerta. Comprobado ejecutandolo (revision 2026-09-03). Una puerta que se
    rodea construyendo una tupla no es una puerta: los invariantes se revalidan
    sobre el CONTENIDO, no sobre el tipo.
    """

    @staticmethod
    def _ficha(**cambios):
        from pathlib import Path

        base = dict(
            identificador="falso", version="0", ruta_pesos=Path("malicioso.bin"),
            licencia_spdx="Propietaria-sin-uso-comercial", sha256_pesos="0" * 64,
            licencia_verificada_por="nadie", licencia_verificada_el="2026-01-01",
            fuente_licencia="inventada", ruta_ficha=Path("ficha.json"),
        )
        base.update(cambios)
        return mw.FichaTranscriptor(**base)

    class _Falso:
        es_de_prueba = False

        def __init__(self, ficha):
            self.ficha = ficha

        def transcribir(self, ruta, idioma):  # noqa: ARG002
            return "lo que sea"

    def test_una_licencia_no_comercial_no_cruza_la_puerta(self):
        with pytest.raises(mw.TranscriptorNoAptoParaActa, match="licencia"):
            mw.exigir_apto_para_acta(self._Falso(self._ficha()))

    def test_unos_pesos_que_no_son_safetensors_no_cruzan_la_puerta(self):
        from pathlib import Path

        ficha = self._ficha(licencia_spdx="Apache-2.0", ruta_pesos=Path("pesos.bin"))
        with pytest.raises(mw.TranscriptorNoAptoParaActa, match="safetensors"):
            mw.exigir_apto_para_acta(self._Falso(ficha))

    def test_un_hash_mal_formado_no_cruza_la_puerta(self):
        from pathlib import Path

        ficha = self._ficha(
            licencia_spdx="Apache-2.0", ruta_pesos=Path("pesos.safetensors"),
            sha256_pesos="corto",
        )
        with pytest.raises(mw.TranscriptorNoAptoParaActa):
            mw.exigir_apto_para_acta(self._Falso(ficha))

    def test_una_ficha_legitima_construida_a_mano_si_cruza(self):
        # No se trata de prohibir construirla: se trata de que su CONTENIDO valga.
        from pathlib import Path

        ficha = self._ficha(licencia_spdx="Apache-2.0", ruta_pesos=Path("pesos.safetensors"))
        assert mw.exigir_apto_para_acta(self._Falso(ficha)) is ficha

    def test_la_marca_de_doble_sigue_mandando_sobre_todo(self):
        # Regresion de lo que ya estaba bien: una ficha impecable no blanquea a
        # un transcriptor de prueba.
        from pathlib import Path

        class Doble(self._Falso):
            es_de_prueba = True

        ficha = self._ficha(licencia_spdx="Apache-2.0", ruta_pesos=Path("pesos.safetensors"))
        with pytest.raises(mw.TranscriptorNoAptoParaActa, match="PRUEBA"):
            mw.exigir_apto_para_acta(Doble(ficha))


# --------------------------------------------------------------------------- #
# Con los pesos de verdad. Se SALTAN si no estan: la suite sigue verde sin ellos.
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="module")
def transcriptor_real():
    """Un solo transcriptor para todos los tests de esta seccion.

    Ambito de modulo por una razon de peso literal: cargar son 3 GB de pesos y
    verificar el sha256 es leerlos otra vez. Hacerlo por test convertiria estos
    cinco en varios minutos sin comprobar nada mas.
    """
    return mw.transcriptor_desde_ficha(_FICHA_REAL, verificar_hash=False)


@sin_pesos
class TestTranscriptorRealSobreAudioDeVerdad:
    """La unica prueba que de verdad demuestra que el instrumento esta cableado."""

    def test_la_ficha_real_pasa_la_puerta_con_su_hash_comprobado(self):
        # Aqui SI se verifica el sha256 contra los 3 GB del disco: es el test que
        # acredita integridad, y por eso es el unico que paga esa lectura.
        ficha = mw.cargar_ficha(_FICHA_REAL, verificar_hash=True)
        assert ficha.licencia_spdx in mw.LICENCIAS_COMERCIALES
        assert ficha.ruta_pesos.name.endswith(".safetensors")

    def test_el_directorio_real_pasa_la_auditoria(self, transcriptor_real):
        auditoria = transcriptor_real.auditoria
        assert auditoria.pesos, "el modelo real tiene que traer safetensors"
        assert auditoria.configuraciones, "y sus JSON de configuracion"

    def test_transcribe_una_pista_real_y_deja_el_cronometro(self, transcriptor_real):
        texto = transcriptor_real.transcribir(_AUDIO_REAL, "es")
        assert texto.strip(), "una pista con voz no puede transcribirse a cadena vacia"
        ultima = transcriptor_real.ultima
        assert ultima["idioma"] == "es"
        assert ultima["duracion_s"] > 0
        assert ultima["rtf"] > 0
        assert ultima["ventanas_de_30s"] >= 1
        assert transcriptor_real.historial, "el cronometro tiene que guardar la pasada"
        # La cifra que se extrapola es la del coste por ventana de 30 s, no el
        # RTF: Whisper rellena hasta 30 s, asi que el RTF de una frase corta es
        # enorme y el de una pista larga, pequeno, sin que el modelo cambie.
        assert transcriptor_real.segundos_por_ventana > 0

    def test_es_apto_para_el_acta_y_medir_pista_lo_acepta(self, transcriptor_real):
        # El camino completo del §6.2 con el transcriptor real: puerta + medida.
        medida = mw.medir_pista(
            transcriptor_real, _AUDIO_REAL, "es",
            "se apaga la ciudad y enciendo la consola",
            brief="prueba-de-cableado", para_acta=True,
        )
        assert medida.apta_para_acta is True
        assert medida.ficha is not None
        assert medida.resultado.n_referencia == 8
        assert medida.resultado.normalizacion is mw.NORMALIZACION_PROTOCOLO

    def test_no_transcribe_sin_decirle_el_idioma(self, transcriptor_real):
        with pytest.raises(ValueError):
            transcriptor_real.transcribir(_AUDIO_REAL, "   ")


@pytest.mark.skipif(not _CORPUS_SUELO.is_file(), reason=f"sin corpus en {_CORPUS_SUELO}")
class TestCorpusRealDelSuelo:
    """El corpus que de verdad hay en disco, sin necesidad de cargar los pesos."""

    def test_carga_y_declara_licencia_verificada(self):
        corpus = mw.cargar_corpus_suelo(_CORPUS_SUELO)
        assert corpus.licencia_spdx in mw.LICENCIAS_CORPUS_SUELO
        assert corpus.fuente_licencia.startswith("http")
        assert corpus.muestras

    def test_cubre_los_dos_idiomas_de_los_briefs(self):
        # §4 mide en castellano y en ingles: un suelo de un solo idioma no cubre
        # la mitad de lo que se va a medir.
        por_idioma = mw.cargar_corpus_suelo(_CORPUS_SUELO).por_idioma()
        assert set(por_idioma) >= {"es", "en"}
        assert min(por_idioma.values()) >= 5

    def test_ninguna_referencia_trae_digitos(self):
        # Es el criterio de seleccion, y se comprueba aqui porque si se colara un
        # digito el suelo subiria por un problema de formato, no del transcriptor.
        for muestra in mw.cargar_corpus_suelo(_CORPUS_SUELO).muestras:
            assert not re.search(r"\d", muestra.texto), muestra.ruta


@sin_pesos
@pytest.mark.skipif(not _CORPUS_SUELO.is_file(), reason=f"sin corpus en {_CORPUS_SUELO}")
def test_el_suelo_se_puede_medir_de_punta_a_punta(transcriptor_real):
    """Dos muestras reales: no es el suelo publicado, es la prueba del cableado.

    El suelo de verdad se mide con el corpus entero desde la linea de ordenes
    (`medir_wer.py suelo ...`); aqui se comprueba que la cadena corpus ->
    transcriptor -> WER -> `Suelo` funciona con material real, en pocos segundos.
    """
    corpus = mw.cargar_corpus_suelo(_CORPUS_SUELO)
    recortado = corpus._replace(muestras=corpus.muestras[:2])
    suelo = mw.medir_suelo(transcriptor_real, recortado, para_acta=True)
    assert suelo.n_muestras == 2
    assert 0.0 <= suelo.wer_medio < 1.0
    assert suelo.licencia_corpus == corpus.licencia_spdx
    assert suelo.es_cota_inferior_del_suelo_de_canto is True
