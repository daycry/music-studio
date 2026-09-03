"""Tests del cableado del planificador de 5 Hz en el shim (sin GPU y sin pesos).

Lo que se prueba aqui es exactamente lo que se puede probar sin 7,5 GB de pesos:
la aritmetica entre tramas latentes (25 Hz) y codigos (5 Hz), la lista blanca de
`model_params` y —lo mas importante— **la perilla `usar_lm` en sus cuatro
casos**, porque esa perilla es el entregable: sin ella no hay A/B.

El resto de la cadena (planificar -> codigos -> quantizer -> detokenizer ->
hints) necesita los pesos reales y se verifica en la maquina con GPU; no se
simula aqui, que seria probar el simulacro.

La suite base corre sin torch a proposito (ver `conftest.py`), asi que si torch
no esta instalado estos tests se saltan en vez de romper la suite.
"""

from __future__ import annotations

import threading
import time

import pytest

torch = pytest.importorskip("torch", reason="el shim necesita torch")

import ace_step_shim as shim  # noqa: E402
from vendor.lm.constants import VENTANA_AGRUPACION, codigos_para_duracion  # noqa: E402
from vendor.pipeline.conditioning import longitud_latente  # noqa: E402


# --------------------------------------------------------------------------- #
# Tramas latentes (25 Hz) <-> codigos del planificador (5 Hz)
# --------------------------------------------------------------------------- #

class TestCodigosYTramas:
    @pytest.mark.parametrize("duracion", [6, 8, 25, 30, 60, 120, 180, 300, 420])
    def test_los_codigos_cubren_siempre_la_pista_entera(self, duracion):
        # Quedarse corto dejaria el final sin plan, y el condicionamiento lo
        # rechaza; este es el invariante que lo impide.
        tramas, _ = longitud_latente(duracion)
        codigos = shim._codigos_para_tramas(tramas)
        assert codigos * VENTANA_AGRUPACION >= tramas

    @pytest.mark.parametrize("duracion", [6, 8, 25, 30, 60, 120, 180, 300, 420])
    def test_no_se_pide_mas_de_un_codigo_de_sobra(self, duracion):
        tramas, _ = longitud_latente(duracion)
        codigos = shim._codigos_para_tramas(tramas)
        assert (codigos - 1) * VENTANA_AGRUPACION < tramas

    def test_el_suelo_de_128_tramas_necesita_redondeo_hacia_arriba(self):
        # Upstream impone `max(128, ...)`: 128 tramas no son multiplo de 5, asi
        # que hacen falta 26 codigos (130 fotogramas) y sobran 2.
        tramas, _ = longitud_latente(5)
        assert tramas == 128
        assert shim._codigos_para_tramas(tramas) == 26

    @pytest.mark.parametrize("codigos", list(range(1, 200)) + [900, 2100])
    def test_la_duracion_pedida_rinde_exactamente_esos_codigos(self, codigos):
        # `codigos_para_duracion` es `int(duracion * 5)` y el redondeo binario
        # puede quedarse corto: la decodificacion restringida fuerza el EOS en
        # ese entero exacto, asi que un codigo de menos aborta la generacion.
        duracion = shim._duracion_para_codigos(codigos)
        assert codigos_para_duracion(duracion) == codigos

    @pytest.mark.parametrize("duracion", [6, 25, 30, 180])
    def test_para_duraciones_enteras_la_ida_y_vuelta_es_exacta(self, duracion):
        tramas, _ = longitud_latente(duracion)
        codigos = shim._codigos_para_tramas(tramas)
        assert shim._duracion_para_codigos(codigos) == pytest.approx(duracion)
        assert codigos * VENTANA_AGRUPACION == tramas


# --------------------------------------------------------------------------- #
# Lista blanca de model_params
# --------------------------------------------------------------------------- #

class TestParams:
    def test_las_perillas_del_lm_estan_admitidas(self):
        assert {"usar_lm", "lm_cfg", "lm_temperatura"} <= shim._PARAMS_ADMITIDOS

    def test_sin_decir_nada_usar_lm_queda_indeciso(self):
        # None NO es True: significa "el llamante no dijo nada" y lo resuelve
        # render() sabiendo si el artefacto trae planificador.
        assert shim.PipelineAceStep._validar_params({})["usar_lm"] is None

    @pytest.mark.parametrize("valor", [True, False])
    def test_usar_lm_explicito_se_respeta(self, valor):
        assert shim.PipelineAceStep._validar_params({"usar_lm": valor})["usar_lm"] is valor

    def test_defectos_de_muestreo_son_los_de_upstream(self):
        opciones = shim.PipelineAceStep._validar_params({})
        assert opciones["lm_cfg"] == 2.0
        assert opciones["lm_temperatura"] == 0.85

    @pytest.mark.parametrize("malos", [{"lm_cfg": 0.5}, {"lm_temperatura": 0.0}, {"usar_lmm": 1}])
    def test_valores_invalidos_se_rechazan(self, malos):
        with pytest.raises(ValueError):
            shim.PipelineAceStep._validar_params(malos)


# --------------------------------------------------------------------------- #
# La perilla, en sus cuatro casos
# --------------------------------------------------------------------------- #

class _Corte(Exception):
    """Corta render() en el punto donde ya se sabe si hay plan."""


class _ResidenciaFalsa:
    """Residencia que no sube ni baja nada: aqui no hay pesos ni VRAM."""

    nombre = "falsa"
    modulo = None

    def subir(self, extra_bytes: int = 0) -> None:
        pass

    def bajar(self) -> None:
        pass


def _pipeline(con_planificador: bool):
    """PipelineAceStep hueco: solo lo que `render()` toca antes de condicionar."""
    pipe = shim.PipelineAceStep.__new__(shim.PipelineAceStep)
    pipe._liberado = False
    pipe._render_lock = threading.Lock()
    pipe._dir_tokenizer_lm = None
    pipe._planificador = object() if con_planificador else None
    pipe._dispositivo = torch.device("cpu")
    pipe._dtype = torch.float16
    pipe._modelo = None
    pipe._tokenizador = None
    pipe._silence_latent = torch.zeros(1, 64, 15000)
    pipe._audio_tokenizer = None
    pipe._detokenizer = None
    pipe._text_encoder = _ResidenciaFalsa()
    pipe._dit_encoder = _ResidenciaFalsa()
    pipe._vae = _ResidenciaFalsa()
    pipe._planificar = lambda **kw: (_ for _ in ()).throw(_Corte("planifico"))
    return pipe


def _render(pipe, params, monkeypatch):
    def cond(**kw):
        raise _Corte("condiciono CON plan" if kw.get("lm_hints_25Hz") is not None
                     else "condiciono SIN plan")

    monkeypatch.setattr(shim, "preparar_condicionamiento_text2music", cond)
    with pytest.raises(_Corte) as info:
        pipe.render(style_prompt="x", lyrics="y", duration_s=25, instrumental=False,
                    seed=1, params=params, on_step=lambda *a: None)
    return str(info.value)


class TestPerillaUsarLm:
    def test_con_planificador_y_sin_decir_nada_se_planifica(self, monkeypatch):
        assert _render(_pipeline(True), {}, monkeypatch) == "planifico"

    def test_con_planificador_y_usar_lm_true_se_planifica(self, monkeypatch):
        assert _render(_pipeline(True), {"usar_lm": True}, monkeypatch) == "planifico"

    def test_con_planificador_y_usar_lm_false_no_se_planifica(self, monkeypatch):
        # La rama de CONTROL del A/B: mismo artefacto, sin plan.
        assert _render(_pipeline(True), {"usar_lm": False}, monkeypatch) == "condiciono SIN plan"

    def test_sin_planificador_y_sin_decir_nada_se_genera_como_siempre(self, monkeypatch):
        # Un artefacto anterior (sin `lm.*`) tiene que seguir cargando y
        # generando; si esto fallara, ni siquiera se podria hacer el warm-up.
        assert _render(_pipeline(False), {}, monkeypatch) == "condiciono SIN plan"

    def test_sin_planificador_y_usar_lm_true_es_error_duro(self, monkeypatch):
        # Pedir el plan explicitamente y no tenerlo NO se degrada en silencio:
        # una pista con plan y otra sin el no son comparables.
        monkeypatch.setattr(shim, "preparar_condicionamiento_text2music",
                            lambda **kw: (_ for _ in ()).throw(_Corte("no deberia llegar")))
        with pytest.raises(RuntimeError, match="no trae el planificador"):
            _pipeline(False).render(style_prompt="x", lyrics="y", duration_s=25,
                                    instrumental=False, seed=1, params={"usar_lm": True},
                                    on_step=lambda *a: None)

    def test_sin_planificador_y_usar_lm_false_no_se_planifica(self, monkeypatch):
        assert _render(_pipeline(False), {"usar_lm": False}, monkeypatch) == "condiciono SIN plan"


# --------------------------------------------------------------------------- #
# render() no es reentrante
# --------------------------------------------------------------------------- #

class TestRenderNoReentrante:
    """Dos `render()` a la vez sobre el mismo pipeline comparten residencias,
    ganchos fp32 y `empty_cache()`: el resultado es un error de dispositivo o,
    peor, audio incorrecto en silencio. El adapter permite `--max-concurrency`
    > 1 (T-04 lo mide en la L40S), asi que el shim tiene que serializar y decirlo.
    """

    @staticmethod
    def _dos_renders_solapados(pipe, monkeypatch):
        dentro = threading.Event()
        suelta = threading.Event()
        en_curso = [0]
        vistos: list[int] = []

        def cond(**kw):
            en_curso[0] += 1
            vistos.append(en_curso[0])
            dentro.set()
            suelta.wait(5)
            en_curso[0] -= 1
            raise _Corte("fin")

        monkeypatch.setattr(shim, "preparar_condicionamiento_text2music", cond)

        def llamar():
            try:
                pipe.render(style_prompt="x", lyrics="y", duration_s=25, instrumental=False,
                            seed=1, params={"usar_lm": False}, on_step=lambda *a: None)
            except _Corte:
                pass

        h1 = threading.Thread(target=llamar)
        h1.start()
        assert dentro.wait(5), "el primer render no llego a condicionar"
        h2 = threading.Thread(target=llamar)
        h2.start()
        time.sleep(0.3)  # tiempo de sobra para que h2 entre si nadie lo frena
        suelta.set()
        h1.join(5)
        h2.join(5)
        assert not h1.is_alive() and not h2.is_alive()
        return vistos

    def test_dos_renders_a_la_vez_se_serializan(self, monkeypatch):
        vistos = self._dos_renders_solapados(_pipeline(False), monkeypatch)
        assert vistos == [1, 1], f"hubo {max(vistos)} render(s) dentro a la vez: {vistos}"

    def test_la_serializacion_no_es_silenciosa(self, monkeypatch, caplog):
        with caplog.at_level("WARNING"):
            self._dos_renders_solapados(_pipeline(False), monkeypatch)
        assert "no es reentrante" in caplog.text

    def test_release_espera_a_que_termine_el_render_en_curso(self, monkeypatch):
        # Soltar residencias bajo un forward en curso daria audio corrupto o un
        # error de dispositivo: release() tiene que esperar al lock del render.
        pipe = _pipeline(False)
        dentro = threading.Event()
        suelta = threading.Event()

        def cond(**kw):
            dentro.set()
            suelta.wait(5)
            raise _Corte("fin")

        monkeypatch.setattr(shim, "preparar_condicionamiento_text2music", cond)

        def renderizar():
            try:
                pipe.render(style_prompt="x", lyrics="y", duration_s=25, instrumental=False,
                            seed=1, params={"usar_lm": False}, on_step=lambda *a: None)
            except _Corte:
                pass

        h_render = threading.Thread(target=renderizar)
        h_render.start()
        assert dentro.wait(5)
        h_release = threading.Thread(target=pipe.release)
        h_release.start()
        time.sleep(0.3)
        assert h_release.is_alive(), "release() no ha esperado al render en curso"
        assert pipe._liberado is False
        suelta.set()
        h_render.join(5)
        h_release.join(5)
        assert pipe._liberado is True


# --------------------------------------------------------------------------- #
# Validacion del punto de sustitucion
# --------------------------------------------------------------------------- #

class TestSustitucionDeSrcLatents:
    """`preparar_condicionamiento_text2music` rechaza hints mal formados.

    Solo los casos que fallan ANTES de tocar el modelo: el camino feliz necesita
    el codificador de texto real y se verifica en la maquina con GPU.
    """

    @staticmethod
    def _llamar(hints):
        from vendor.pipeline.conditioning import preparar_condicionamiento_text2music

        class _Tok:
            def __call__(self, texto, **kw):
                ids = torch.tensor([[1, 2, 3]])
                return {"input_ids": ids, "attention_mask": torch.ones_like(ids)}

        preparar_condicionamiento_text2music(
            model=None, text_encoder=None, text_tokenizer=_Tok(),
            silence_latent=torch.zeros(1, 64, 15000), style_prompt="x", lyrics=None,
            duracion_s=25.0, device=torch.device("cpu"), dtype=torch.float16,
            lm_hints_25Hz=hints,
        )

    def test_hints_demasiado_cortos_se_rechazan(self):
        with pytest.raises(ValueError, match="hacen falta"):
            self._llamar(torch.zeros(1, 10, 64))

    def test_numero_de_canales_erroneo_se_rechaza(self):
        with pytest.raises(ValueError, match="canales"):
            self._llamar(torch.zeros(1, 625, 32))

    def test_falta_el_eje_de_lote(self):
        with pytest.raises(ValueError, match=r"\[1, T', 64\]"):
            self._llamar(torch.zeros(625, 64))


class TestTipadoDeLosMetadatos:
    """bpm, keyscale y timesignature pasaban sin tipar hasta el codigo vendorizado.

    Ahi el condicionamiento hace `.strip()` sobre el valor, asi que un
    `keyscale=5` daba un AttributeError dentro del vendor: un 500 del runner
    (fallo nuestro) donde correspondia un 400 de peticion mal formada. Es el mismo
    patron que ya se arreglo en `contracts.GenerationRequest`, un nivel mas abajo.
    """

    @staticmethod
    def _validar(**params):
        pipe = _pipeline(False)
        return pipe._validar_params(params)

    def test_los_valores_bien_formados_pasan(self):
        opciones = self._validar(bpm="120", keyscale="A minor", timesignature="4/4")
        assert opciones["keyscale"] == "A minor"
        assert opciones["timesignature"] == "4/4"

    def test_los_tres_pueden_faltar(self):
        # Son opcionales: el modelo tiene sus propios defectos.
        opciones = self._validar()
        assert opciones["bpm"] is None
        assert opciones["keyscale"] is None

    @pytest.mark.parametrize("clave", ["keyscale", "timesignature"])
    def test_un_texto_esperado_que_llega_como_numero_es_error_de_validacion(self, clave):
        with pytest.raises(ValueError, match=clave):
            self._validar(**{clave: 5})

    def test_un_compas_con_forma_imposible_se_rechaza(self):
        with pytest.raises(ValueError, match="timesignature"):
            self._validar(timesignature="cuatro por cuatro")

    def test_no_se_inventa_un_vocabulario_de_tonalidades(self):
        # Que sea una cadena es nuestro asunto; QUE tonalidades entiende el modelo
        # es del modelo. Rechazar aqui una tonalidad rara seria decidir por el.
        assert self._validar(keyscale="F# dorian")["keyscale"] == "F# dorian"

    def test_un_bpm_que_no_es_numero_ni_texto_numerico_se_rechaza(self):
        with pytest.raises(ValueError, match="bpm"):
            self._validar(bpm="rapido")

    def test_un_bpm_numerico_se_acepta_en_las_dos_formas(self):
        assert self._validar(bpm=120)["bpm"] is not None
        assert self._validar(bpm="120")["bpm"] is not None
