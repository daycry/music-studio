"""Tests de `spikes/medir_wer.py`: el WER del criterio 4 de G1 y su puerta de licencia.

Dos capas, y la separacion es el objeto de estos tests
-----------------------------------------------------
* **Capa 1 — aritmetica.** Se prueba con verdad conocida a mano (10 palabras,
  una sustitucion, 10 %), no con la salida del propio codigo. Un test de WER que
  compara contra lo que el codigo devuelve hoy no prueba nada.
* **Capa 2 — puerta.** No hay transcriptor integrado y estos tests **exigen que
  no lo haya**: sin ficha de licencia verificada el modulo se niega a medir, y un
  transcriptor de prueba no puede producir un numero que vaya al acta.

Biblioteca estandar pura: ni torch, ni numpy, ni red.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
from pathlib import Path

import pytest

import medir_wer as mw

_RAIZ_REPO = Path(__file__).resolve().parents[3]
_PROTOCOLO = _RAIZ_REPO / "docs/roadmap/2026-07-27-plataforma-musical-ia/gates/g1-protocolo.md"


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

    def test_no_importa_nada_de_red_ni_de_descarga(self):
        # Se mira el AST y no el texto, para no castigar a la documentacion por
        # nombrar lo que prohibe.
        prohibidos = {
            "urllib", "urllib.request", "requests", "httpx", "http", "http.client",
            "socket", "ftplib", "huggingface_hub", "transformers", "torch", "pickle",
        }
        importados = set()
        for nodo in ast.walk(self._arbol()):
            if isinstance(nodo, ast.Import):
                importados.update(a.name.split(".")[0] for a in nodo.names)
            elif isinstance(nodo, ast.ImportFrom) and nodo.module:
                importados.add(nodo.module.split(".")[0])
        assert not (importados & {p.split(".")[0] for p in prohibidos}), (
            f"el modulo importa algo que no debe: {sorted(importados & prohibidos)}"
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
