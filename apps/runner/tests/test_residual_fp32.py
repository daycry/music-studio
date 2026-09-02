"""Tests de `_ResidualDitFp32` — la corriente residual del DiT en fp32.

Que se prueba, y por que estas cosas y no otras:

1. **Que la enfermedad existe.** El montaje falso reproduce el patron pre-norm
   real (norma -> subcapa -> suma residual con puerta) con contribuciones que
   caben de sobra en fp16 pero cuya SUMA no. Sin la promocion, la salida sale no
   finita. Si algun dia este test dejara de fallar sin el remedio, el remedio
   sobra y hay que borrarlo.
2. **Que el remedio cura**: con la promocion la salida es finita y coincide con
   la referencia calculada entera en fp32.
3. **Que los PESOS no se tocan.** Es toda la gracia del enfoque: promover el
   decoder entero son 9,6 GiB y la tarjeta tiene 8. Aqui se exige que despues del
   paso por los ganchos todos los parametros sigan en fp16 y que lo que entra a
   cada subcapa sea fp16, o sea que los `matmul` no se han encarecido.
4. **Que el turbo no se entera**: `para_variante` lo deja inactivo y no instala ni
   un gancho. Si se le instalasen, el turbo dejaria de ser el control del A/B.
5. **Que se rompe ruidosamente** si la arquitectura vendorizada cambia de nombres,
   en vez de convertirse en un no-op silencioso.

El DiT real no aparece: son 2,4 GB de pesos, una GPU y `einops`. Lo que se
verifica es el CONTRATO DE DTYPES de los ganchos, que es lo unico que este codigo
aporta; la aritmetica de la difusion es de `test_diffusion_guia.py`.
"""

from __future__ import annotations

import pytest

torch = pytest.importorskip("torch", reason="la promocion a fp32 manipula tensores")

from ace_step_shim import _ResidualDitFp32  # noqa: E402

HIDDEN = 16
CAPAS = 6
TRAMAS = 8

#: Magnitud de la corriente al entrar en la pila. Elegida junto a `APORTE` para
#: que la suma se salga de fp16 (65.504) pero cada sumando quepa: es exactamente
#: el caso medido en `layers.20` del `sft` (entrada 6.000, aportes finitos, suma
#: 6,4e4 con diez `inf`).
ENTRADA = 2.0e4
#: Lo que aporta cada subcapa. 3 subcapas x 6 capas x 1,5e4 = 2,7e5 acumulado.
APORTE = 1.5e4

#: Error relativo admitido entre la ruta promovida (matmul en fp16) y la
#: referencia entera en fp32. No es cero y no puede serlo: los productos siguen
#: siendo fp16 a proposito. fp16 tiene 10 bits de mantisa -> ~1e-3 relativo.
TOL_RELATIVA = 5e-3


class _RMSNormFalsa(torch.nn.Module):
    """Como `Qwen3RMSNorm`: calcula en fp32 y devuelve al dtype de la entrada.

    Ese detalle es el que hace que la promocion sea gratis: con la corriente ya en
    fp32 la norma devuelve fp32, y el gancho de entrada de la subcapa la baja a
    fp16 cuando los valores ya son del orden de la unidad.
    """

    def __init__(self, hidden: int) -> None:
        super().__init__()
        self.weight = torch.nn.Parameter(torch.ones(hidden))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        dtype_entrada = x.dtype
        y = x.to(torch.float32)
        y = y * torch.rsqrt(y.pow(2).mean(-1, keepdim=True) + 1e-6)
        return self.weight * y.to(dtype_entrada)


class _AtencionFalsa(torch.nn.Module):
    """Devuelve `(salida, pesos)` como `AceStepAttention`, y se llama por kwargs."""

    def __init__(self, hidden: int, ganancia: float) -> None:
        super().__init__()
        self.o_proj = torch.nn.Linear(hidden, hidden, bias=False)
        with torch.no_grad():
            self.o_proj.weight.copy_(torch.eye(hidden) * ganancia)
        self.dtypes_vistos: list[torch.dtype] = []

    def forward(self, hidden_states=None, **_kwargs):  # noqa: ANN001, ANN201
        self.dtypes_vistos.append(hidden_states.dtype)
        # El segundo elemento imita `attn_weights`: el gancho de salida NO debe
        # tocarlo (en el modelo real es `[1, 16, L, L]` y promoverlo seria tirar
        # ~140 MiB de VRAM).
        return self.o_proj(hidden_states), torch.zeros(1, dtype=hidden_states.dtype)


class _MlpFalso(torch.nn.Module):
    """Se llama POSICIONALMENTE, como `Qwen3MLP`, y devuelve un tensor pelado."""

    def __init__(self, hidden: int, ganancia: float) -> None:
        super().__init__()
        self.down_proj = torch.nn.Linear(hidden, hidden, bias=False)
        with torch.no_grad():
            self.down_proj.weight.copy_(torch.eye(hidden) * ganancia)
        self.dtypes_vistos: list[torch.dtype] = []

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        self.dtypes_vistos.append(x.dtype)
        return self.down_proj(x)


class _CapaFalsa(torch.nn.Module):
    """Replica el patron de `AceStepDiTLayer`, incluidos los `.type_as()`.

    Los `.type_as(hidden_states)` no son decorado: son justamente lo que impide
    que baste con promover la entrada de la pila, porque devuelven cada
    intermedio al dtype de la corriente.
    """

    def __init__(self, hidden: int, aporte: float) -> None:
        super().__init__()
        self.self_attn_norm = _RMSNormFalsa(hidden)
        self.self_attn = _AtencionFalsa(hidden, aporte)
        self.cross_attn_norm = _RMSNormFalsa(hidden)
        self.cross_attn = _AtencionFalsa(hidden, aporte)
        self.mlp_norm = _RMSNormFalsa(hidden)
        self.mlp = _MlpFalso(hidden, aporte)

    def forward(self, hidden_states: torch.Tensor, *_resto):  # noqa: ANN201
        norm = self.self_attn_norm(hidden_states).type_as(hidden_states)
        salida, _ = self.self_attn(hidden_states=norm, attention_mask=None)
        hidden_states = (hidden_states + salida).type_as(hidden_states)

        norm = self.cross_attn_norm(hidden_states).type_as(hidden_states)
        salida, _ = self.cross_attn(hidden_states=norm, encoder_hidden_states=None)
        hidden_states = hidden_states + salida

        norm = self.mlp_norm(hidden_states).type_as(hidden_states)
        hidden_states = (hidden_states + self.mlp(norm)).type_as(hidden_states)
        return (hidden_states,)


class _DecoderFalso(torch.nn.Module):
    """`layers` + `norm_out` + `proj_out`, los tres nombres de los que cuelgan los ganchos."""

    def __init__(self, hidden: int, capas: int, aporte: float) -> None:
        super().__init__()
        self.layers = torch.nn.ModuleList(_CapaFalsa(hidden, aporte) for _ in range(capas))
        self.norm_out = _RMSNormFalsa(hidden)
        self.proj_out = torch.nn.Linear(hidden, hidden, bias=False)
        with torch.no_grad():
            self.proj_out.weight.copy_(torch.eye(hidden))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        hidden_states = x
        for capa in self.layers:
            hidden_states = capa(hidden_states)[0]
        hidden_states = self.norm_out(hidden_states).type_as(hidden_states)
        return self.proj_out(hidden_states)


def _decoder(dtype: torch.dtype) -> _DecoderFalso:
    torch.manual_seed(20260902)
    return _DecoderFalso(HIDDEN, CAPAS, APORTE).to(dtype).eval()


def _entrada(dtype: torch.dtype) -> torch.Tensor:
    torch.manual_seed(20260902)
    return (torch.randn(1, TRAMAS, HIDDEN) * ENTRADA).to(dtype)


# --------------------------------------------------------------------------- #
# 1. La enfermedad
# --------------------------------------------------------------------------- #

def test_sin_promocion_la_corriente_fp16_desborda():
    """El montaje reproduce el fallo medido: aportes finitos, suma no finita."""
    modelo = _decoder(torch.float16)
    with torch.no_grad():
        salida = modelo(_entrada(torch.float16))
    assert not torch.isfinite(salida).all(), (
        "El montaje ya no desborda en fp16, asi que ha dejado de probar nada. "
        "Sube ENTRADA/APORTE o borra el remedio."
    )


def test_los_aportes_de_cada_subcapa_si_caben_en_fp16():
    """Confirma que lo que desborda es la SUMA, no las subcapas.

    Es la premisa de todo el diseno: si desbordase dentro de la subcapa, promover
    las activaciones no bastaria y habria que promover pesos.
    """
    techo = torch.finfo(torch.float16).max
    assert APORTE < techo
    assert ENTRADA < techo
    assert ENTRADA + CAPAS * 3 * APORTE > techo


# --------------------------------------------------------------------------- #
# 2. El remedio
# --------------------------------------------------------------------------- #

def test_con_promocion_la_salida_es_finita_y_coincide_con_fp32():
    modelo = _decoder(torch.float16)
    with _ResidualDitFp32(modelo, torch.float16) as promocion, torch.no_grad():
        salida = modelo(_entrada(torch.float16))
    assert promocion.activo
    assert torch.isfinite(salida).all(), "La promocion no ha evitado el desbordamiento."

    referencia = _decoder(torch.float32)
    with torch.no_grad():
        esperada = referencia(_entrada(torch.float32))

    obtenida = salida.to(torch.float32)
    error = torch.linalg.vector_norm(obtenida - esperada) / torch.linalg.vector_norm(esperada)
    assert float(error) < TOL_RELATIVA, f"error relativo {float(error):.3g}"


def test_la_salida_del_decoder_vuelve_a_fp16():
    """`proj_out` tiene pesos fp16: si la corriente llegase en fp32, reventaria."""
    modelo = _decoder(torch.float16)
    with _ResidualDitFp32(modelo, torch.float16), torch.no_grad():
        salida = modelo(_entrada(torch.float16))
    assert salida.dtype is torch.float16


def test_los_pesos_no_se_promueven_y_las_subcapas_reciben_fp16():
    """La razon de ser del enfoque: 0 bytes de VRAM extra en parametros."""
    modelo = _decoder(torch.float16)
    with _ResidualDitFp32(modelo, torch.float16), torch.no_grad():
        modelo(_entrada(torch.float16))

    assert all(p.dtype is torch.float16 for p in modelo.parameters()), (
        "Algun parametro se ha promovido a fp32: eso es justo lo que no cabe en 8 GB."
    )
    for capa in modelo.layers:
        assert capa.self_attn.dtypes_vistos == [torch.float16]
        assert capa.cross_attn.dtypes_vistos == [torch.float16]
        assert capa.mlp.dtypes_vistos == [torch.float16]


def test_los_pesos_de_atencion_no_se_promueven():
    """El gancho de salida solo toca el elemento 0 de la tupla."""
    registradas: list[torch.dtype] = []
    modelo = _decoder(torch.float16)

    original = modelo.layers[0].self_attn.forward

    def _espia(**kwargs):  # noqa: ANN202
        salida, pesos = original(**kwargs)
        registradas.append(pesos.dtype)
        return salida, pesos

    modelo.layers[0].self_attn.forward = _espia
    with _ResidualDitFp32(modelo, torch.float16), torch.no_grad():
        modelo(_entrada(torch.float16))
    assert registradas == [torch.float16]


# --------------------------------------------------------------------------- #
# 3. Alcance: solo el sft
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    ("variante", "esperado"),
    [("sft", True), ("turbo", False)],
)
def test_solo_se_activa_para_el_sft(variante, esperado):
    modelo = _decoder(torch.float16)
    promocion = _ResidualDitFp32.para_variante(modelo, variante, torch.float16)
    assert promocion.activo is esperado


def test_para_el_turbo_no_instala_ni_un_gancho():
    """Si se le instalasen, el turbo dejaria de ser comparable con lo ya escuchado."""
    modelo = _decoder(torch.float16)
    with _ResidualDitFp32.para_variante(modelo, "turbo", torch.float16), torch.no_grad():
        salida = modelo(_entrada(torch.float16))
    for modulo in modelo.modules():
        assert not modulo._forward_hooks
        assert not modulo._forward_pre_hooks
    # Y sigue haciendo exactamente lo de siempre, desbordamiento incluido.
    assert not torch.isfinite(salida).all()


@pytest.mark.parametrize("dtype", [torch.float32, torch.bfloat16])
def test_con_otros_dtypes_es_un_no_op(dtype):
    """Solo fp16 pierde rango: en fp32 y bf16 no hay nada que arreglar."""
    modelo = _decoder(dtype)
    assert _ResidualDitFp32(modelo, dtype).activo is False


# --------------------------------------------------------------------------- #
# 4. Instrumentacion y guardarrailes
# --------------------------------------------------------------------------- #

def test_solo_anota_la_primera_pasada():
    """9.600 sincronizaciones por pista si anotase todas; aqui se exige que no."""
    modelo = _decoder(torch.float16)
    with _ResidualDitFp32(modelo, torch.float16) as promocion, torch.no_grad():
        modelo(_entrada(torch.float16))
        anotadas = len(promocion.picos)
        modelo(_entrada(torch.float16))
        modelo(_entrada(torch.float16))
    assert len(promocion.picos) == anotadas > 0


def test_el_resumen_traza_el_crecimiento_capa_a_capa():
    modelo = _decoder(torch.float16)
    with _ResidualDitFp32(modelo, torch.float16) as promocion, torch.no_grad():
        modelo(_entrada(torch.float16))
    resumen = promocion.resumen(cada=2)
    assert "entrada=" in resumen and "proj_out=" in resumen
    picos = {nombre: pico for nombre, pico, _ in promocion.picos}
    assert picos["layers.0"] < picos[f"layers.{CAPAS - 1}"], "la corriente deberia crecer"
    assert picos[f"layers.{CAPAS - 1}"] > torch.finfo(torch.float16).max, (
        "la corriente promovida deberia superar el techo de fp16: es el desbordamiento evitado"
    )


def test_los_ganchos_se_retiran_al_salir():
    modelo = _decoder(torch.float16)
    with _ResidualDitFp32(modelo, torch.float16), torch.no_grad():
        modelo(_entrada(torch.float16))
    for modulo in modelo.modules():
        assert not modulo._forward_hooks
        assert not modulo._forward_pre_hooks


def test_falla_si_el_decoder_no_tiene_capas():
    class _Vacio(torch.nn.Module):
        pass

    with pytest.raises(RuntimeError, match="no expone `layers`"):
        with _ResidualDitFp32(_Vacio(), torch.float16):
            pass


def test_falla_si_falta_proj_out():
    modelo = _decoder(torch.float16)
    del modelo.proj_out
    with pytest.raises(RuntimeError, match="no expone `proj_out`"):
        with _ResidualDitFp32(modelo, torch.float16):
            pass


def test_falla_si_una_capa_renombra_sus_subcapas():
    modelo = _decoder(torch.float16)
    for nombre in ("self_attn", "cross_attn", "mlp"):
        delattr(modelo.layers[1], nombre)
    with pytest.raises(RuntimeError, match="no expone ninguna"):
        with _ResidualDitFp32(modelo, torch.float16):
            pass


def test_delata_un_desbordamiento_dentro_de_la_subcapa():
    """Si el aporte NO cabe en fp16, promover activaciones no basta y hay que decirlo."""
    torch.manual_seed(20260902)
    modelo = _DecoderFalso(HIDDEN, 2, 1.0e5).to(torch.float16).eval()
    with pytest.raises(RuntimeError, match="DENTRO de"):
        with _ResidualDitFp32(modelo, torch.float16), torch.no_grad():
            modelo(_entrada(torch.float16))


# --------------------------------------------------------------------------- #
# 5. El warm-up tiene que saber la variante del artefacto
# --------------------------------------------------------------------------- #
#
# Esto vive aqui porque es la otra mitad del mismo fallo: la promocion a fp32
# solo se activa con `variante="sft"`, y el WARM-UP corre dentro de `load()`,
# antes de que exista ninguna peticion que pueda decir la variante. MEDIDO el
# 2026-09-02: con `params={}` el warm-up calentaba en `turbo` sobre pesos `sft`,
# la promocion no se instalaba y la carga moria con 9.600 NaN en un latente de
# 6 s, sin llegar a generar nada.

def test_el_warmup_calienta_con_la_variante_del_artefacto():
    import ace_step_shim

    pipeline = object.__new__(ace_step_shim.PipelineAceStep)
    pipeline._variante_por_defecto = "sft"
    pipeline._comprobar_vivo = lambda: None
    vistos: dict = {}

    class _Render:
        duration_s = 6.0

    def _render(**kwargs):
        vistos.update(kwargs)
        return _Render()

    pipeline.render = _render
    pipeline.warmup()
    assert vistos["params"]["variante"] == "sft", (
        "El warm-up ha vuelto a calentar con la variante por defecto del modulo: "
        "con pesos sft eso es un latente de NaN en el arranque."
    )


def test_la_variante_por_defecto_se_normaliza():
    import ace_step_shim

    # Se comprueba el efecto, no la firma: la normalizacion es lo que impide que
    # un valor cualquiera del entorno se cuele como variante desconocida.
    assert ace_step_shim.normalizar_variante("sft") == "sft"
    assert ace_step_shim.normalizar_variante("turbo") == "turbo"
    with pytest.raises((ValueError, KeyError, RuntimeError)):
        ace_step_shim.normalizar_variante("no-existe")
