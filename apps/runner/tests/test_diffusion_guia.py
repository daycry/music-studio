"""Tests del bucle de difusion con guia (`vendor/pipeline/diffusion.py`).

Que se prueba, y por que estas tres cosas y no otras:

1. **Que el turbo no se ha movido ni un bit.** El bucle se unifico para que las
   dos variantes compartan codigo; el riesgo de eso es cambiar sin querer el
   camino que YA funciona. Aqui esta escrito el bucle turbo ANTERIOR, tal cual
   estaba antes del cambio, y se exige `torch.equal` con el actual.
2. **Que la pasada gemela SECUENCIAL da lo mismo que la POR LOTE de upstream.**
   Es la decision de diseno que impone la VRAM de la GTX 1070, y la unica forma
   honesta de sostenerla es comparar contra la version de upstream, escrita aqui
   al lado.
3. **Que se paga lo que se cree que se paga**: 1 pasada del DiT por paso sin
   guia, 2 con guia, y ninguna gemela fuera de `cfg_interval`.

El DiT real no aparece: son 2,4 GB de pesos y una GPU. El modelo falso es
determinista y sensible a `(x, t, encoder_hidden_states)`, que es todo lo que el
bucle manipula. Lo que se verifica es ARITMETICA DEL MUESTREADOR, no calidad de
audio (eso es escucha humana, G1).
"""

from __future__ import annotations

import pytest

torch = pytest.importorskip("torch", reason="el bucle de difusion necesita torch")
cache_utils = pytest.importorskip(
    "transformers.cache_utils", reason="el bucle usa EncoderDecoderCache"
)

from vendor.pipeline.diffusion import generar_latentes_text2music  # noqa: E402
from vendor.pipeline.scheduler import (  # noqa: E402
    construir_programacion_continua,
    programacion_efectiva,
)
from vendor.sft.apg_guidance import MomentumBuffer, apg_forward  # noqa: E402

DynamicCache = cache_utils.DynamicCache
EncoderDecoderCache = cache_utils.EncoderDecoderCache

T_FRAMES = 32
CANALES = 64
L_ENC = 7
HIDDEN = 8
DTYPE = torch.float32

#: Tolerancia de la comparacion lote-vs-secuencial, en error cuadratico medio
#: RELATIVO. No es cero y no puede serlo: `test_el_control_...` demuestra que un
#: `matmul` de lote 2 ya no es bit a bit igual a dos de lote 1 con las mismas
#: entradas (distinto reparto del GEMM). El umbral esta tres ordenes de magnitud
#: por debajo del error medido (~3e-7) y muy por debajo de un ulp de fp16, que
#: es el dtype real del pipeline.
TOL_RMS_RELATIVO = 1e-5


class _DecoderFalso(torch.nn.Module):
    """DiT de mentira, determinista y sensible a las tres entradas que importan."""

    def __init__(self) -> None:
        super().__init__()
        g = torch.Generator().manual_seed(7)
        self.w = torch.randn(CANALES, CANALES, generator=g, dtype=DTYPE)
        self.p = torch.randn(HIDDEN, CANALES, generator=g, dtype=DTYPE)
        self.llamadas: list[tuple[float, int]] = []

    def forward(self, *, hidden_states, timestep, timestep_r, attention_mask,
                encoder_hidden_states, encoder_attention_mask, context_latents,
                use_cache, past_key_values):
        self.llamadas.append((float(timestep[0]), int(encoder_hidden_states.shape[0])))
        cond = encoder_hidden_states.mean(dim=1) @ self.p
        t = timestep.view(-1, 1, 1)
        v = torch.tanh(hidden_states @ self.w) * (1.0 + t) + cond.unsqueeze(1) * 0.5
        return v, past_key_values


class _ModeloFalso(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.decoder = _DecoderFalso()
        g = torch.Generator().manual_seed(11)
        self.null_condition_emb = torch.nn.Parameter(
            torch.randn(1, 1, HIDDEN, generator=g, dtype=DTYPE), requires_grad=False
        )

    def prepare_noise(self, context_latents, seed):
        gen = torch.Generator(device="cpu").manual_seed(int(seed))
        forma = (
            context_latents.shape[0],
            context_latents.shape[1],
            context_latents.shape[-1] // 2,
        )
        return torch.randn(forma, generator=gen, dtype=context_latents.dtype)

    def get_x0_from_noise(self, zt, vt, t):
        return zt - vt * t.unsqueeze(-1).unsqueeze(-1)


class _CondFalso:
    def __init__(self) -> None:
        g = torch.Generator().manual_seed(3)
        self.context_latents = torch.randn(1, T_FRAMES, CANALES * 2, generator=g, dtype=DTYPE)
        self.encoder_hidden_states = torch.randn(1, L_ENC, HIDDEN, generator=g, dtype=DTYPE)
        self.encoder_attention_mask = torch.ones(1, L_ENC, dtype=DTYPE)
        self.attention_mask = torch.ones(1, T_FRAMES, dtype=DTYPE)


def _bucle_turbo_anterior(model, cond, seed, shift=3.0):
    """El bucle del turbo COPIADO tal cual estaba antes de unificar las variantes.

    Es la referencia de la no-regresion. No se refactoriza: si algun dia hay que
    cambiarlo para que compile, es que el bucle de produccion ha cambiado y este
    test tiene que fallar.
    """
    _, t_schedule_list = programacion_efectiva(shift)
    context_latents = cond.context_latents
    bsz, device, dtype = 1, context_latents.device, context_latents.dtype
    noise = model.prepare_noise(context_latents, seed)
    t_schedule = torch.tensor(t_schedule_list, device=device, dtype=dtype)
    num_steps = len(t_schedule)
    past_key_values = EncoderDecoderCache(DynamicCache(), DynamicCache())
    xt = noise
    for step_idx in range(num_steps):
        current_timestep = t_schedule[step_idx].item()
        t_curr_tensor = current_timestep * torch.ones((bsz,), device=device, dtype=dtype)
        with torch.no_grad():
            salidas = model.decoder(
                hidden_states=xt, timestep=t_curr_tensor, timestep_r=t_curr_tensor,
                attention_mask=cond.attention_mask,
                encoder_hidden_states=cond.encoder_hidden_states,
                encoder_attention_mask=cond.encoder_attention_mask,
                context_latents=context_latents, use_cache=True,
                past_key_values=past_key_values,
            )
        vt, past_key_values = salidas[0], salidas[1]
        if step_idx == num_steps - 1:
            xt = model.get_x0_from_noise(xt, vt, t_curr_tensor)
            break
        next_timestep = t_schedule[step_idx + 1].item()
        dt = current_timestep - next_timestep
        dt_tensor = dt * torch.ones((bsz,), device=device, dtype=dtype).unsqueeze(-1).unsqueeze(-1)
        xt = xt - vt * dt_tensor
    return xt


def _bucle_sft_por_lote(model, cond, seed, pasos, shift, escala):
    """El bucle POR LOTE de upstream (`generate_audio` del modelo base).

    Recortado a `text2music`: sin cover, sin SDE, sin ADG. Todo lo demas —la
    concatenacion del condicionamiento con `null_condition_emb`, el `chunk(2)`,
    la llamada a `apg_forward` con `dims=[1]` y el Euler— es literal.
    """
    context_latents = cond.context_latents
    device, dtype = context_latents.device, context_latents.dtype
    bsz = context_latents.shape[0]
    t = torch.tensor(construir_programacion_continua(pasos, shift), device=device, dtype=dtype)
    noise = model.prepare_noise(context_latents, seed)
    past_key_values = EncoderDecoderCache(DynamicCache(), DynamicCache())
    momentum_buffer = MomentumBuffer()
    ehs = torch.cat(
        [cond.encoder_hidden_states,
         model.null_condition_emb.expand_as(cond.encoder_hidden_states)], dim=0)
    eam = torch.cat([cond.encoder_attention_mask, cond.encoder_attention_mask], dim=0)
    ctx = torch.cat([context_latents, context_latents], dim=0)
    am = torch.cat([cond.attention_mask, cond.attention_mask], dim=0)
    xt = noise
    with torch.no_grad():
        for t_curr, t_prev in zip(t[:-1], t[1:]):
            x = torch.cat([xt, xt], dim=0)
            t_curr_tensor = t_curr * torch.ones((x.shape[0],), device=device, dtype=dtype)
            salidas = model.decoder(
                hidden_states=x, timestep=t_curr_tensor, timestep_r=t_curr_tensor,
                attention_mask=am, encoder_hidden_states=ehs,
                encoder_attention_mask=eam, context_latents=ctx,
                use_cache=True, past_key_values=past_key_values,
            )
            vt, past_key_values = salidas[0], salidas[1]
            pred_cond, pred_null = vt.chunk(2)
            vt = apg_forward(pred_cond=pred_cond, pred_uncond=pred_null,
                             guidance_scale=escala, momentum_buffer=momentum_buffer,
                             dims=[1])
            dt = t_curr - t_prev
            dt_tensor = dt * torch.ones((bsz,), device=device, dtype=dtype).unsqueeze(-1).unsqueeze(-1)
            xt = xt - vt * dt_tensor
    return xt


def _rms_relativo(a, b):
    return float((a - b).pow(2).mean().sqrt() / a.pow(2).mean().sqrt())


# --------------------------------------------------------------------------- #
# 1. El turbo no se ha movido
# --------------------------------------------------------------------------- #

class TestTurboSinRegresion:
    def test_bit_a_bit_igual_al_bucle_anterior(self):
        modelo, cond = _ModeloFalso(), _CondFalso()
        esperado = _bucle_turbo_anterior(modelo, cond, seed=1234)
        vistos_antes = [t for t, _ in modelo.decoder.llamadas]
        modelo.decoder.llamadas.clear()

        obtenido = generar_latentes_text2music(
            model=modelo, cond=cond, seed=1234, variante="turbo"
        ).target_latents

        assert torch.equal(esperado, obtenido)
        assert [t for t, _ in modelo.decoder.llamadas] == vistos_antes

    def test_ocho_pasadas_de_lote_uno_y_ninguna_gemela(self):
        modelo, cond = _ModeloFalso(), _CondFalso()
        resultado = generar_latentes_text2music(
            model=modelo, cond=cond, seed=1, variante="turbo"
        )
        assert len(modelo.decoder.llamadas) == 8
        assert {lote for _, lote in modelo.decoder.llamadas} == {1}
        assert resultado.time_costs["dit_forward_passes"] == 8.0
        assert resultado.time_costs["num_steps"] == 8.0
        assert resultado.time_costs["shift"] == 3.0
        assert resultado.time_costs["variante"] == "turbo"
        assert resultado.time_costs["guidance_scale"] == 1.0

    def test_por_defecto_sigue_siendo_turbo(self):
        modelo, cond = _ModeloFalso(), _CondFalso()
        resultado = generar_latentes_text2music(model=modelo, cond=cond, seed=1)
        assert resultado.time_costs["variante"] == "turbo"
        assert len(modelo.decoder.llamadas) == 8

    def test_guiar_el_turbo_se_rechaza(self):
        """No es una limitacion tecnica: guiar un modelo destilado lo empeora."""
        with pytest.raises(ValueError, match="destilado"):
            generar_latentes_text2music(
                model=_ModeloFalso(), cond=_CondFalso(), seed=1,
                variante="turbo", guidance_scale=7.0,
            )


# --------------------------------------------------------------------------- #
# 2. Secuencial == por lote
# --------------------------------------------------------------------------- #

class TestGemelaSecuencial:
    @pytest.mark.parametrize(
        "pasos,shift,escala",
        [(50, 1.0, 7.0), (12, 2.5, 5.0), (3, 1.0, 7.0), (30, 1.0, 7.0)],
    )
    def test_da_lo_mismo_que_la_pasada_por_lote_de_upstream(self, pasos, shift, escala):
        referencia = _bucle_sft_por_lote(
            _ModeloFalso(), _CondFalso(), seed=99, pasos=pasos, shift=shift, escala=escala
        )
        obtenido = generar_latentes_text2music(
            model=_ModeloFalso(), cond=_CondFalso(), seed=99, variante="sft",
            pasos=pasos, shift=shift, guidance_scale=escala,
        ).target_latents
        assert _rms_relativo(referencia, obtenido) < TOL_RMS_RELATIVO

    def test_el_control_de_por_que_la_tolerancia_no_es_cero(self):
        """Un `matmul` de lote 2 NO es bit a bit dos de lote 1: el GEMM reparte
        distinto. Sin este control, la tolerancia del test de arriba pareceria
        una concesion a un bug del bucle, y no lo es."""
        decoder = _DecoderFalso()
        cond = _CondFalso()
        x = torch.randn(1, T_FRAMES, CANALES, dtype=DTYPE)
        comun = dict(attention_mask=None, encoder_attention_mask=None,
                     context_latents=None, use_cache=False, past_key_values=None)
        ts1, ts2 = torch.ones(1, dtype=DTYPE), torch.ones(2, dtype=DTYPE)
        v2, _ = decoder(
            hidden_states=torch.cat([x, x], dim=0), timestep=ts2, timestep_r=ts2,
            encoder_hidden_states=torch.cat(
                [cond.encoder_hidden_states, cond.encoder_hidden_states], dim=0), **comun)
        v1, _ = decoder(
            hidden_states=x, timestep=ts1, timestep_r=ts1,
            encoder_hidden_states=cond.encoder_hidden_states, **comun)
        assert not torch.equal(v2[:1], v1)
        assert float((v2[:1] - v1).abs().max()) < 1e-4

    def test_las_dos_ramas_ven_condicionamientos_distintos(self):
        """Si las dos pasadas compartieran cache o condicionamiento, la gemela
        seria una copia de la condicional y la guia valdria 0."""
        modelo, cond = _ModeloFalso(), _CondFalso()
        generar_latentes_text2music(
            model=modelo, cond=cond, seed=1, variante="sft", pasos=2
        )
        # Dos pasadas por paso, cada par con el MISMO t.
        tiempos = [t for t, _ in modelo.decoder.llamadas]
        assert len(tiempos) == 4
        assert tiempos[0] == tiempos[1] and tiempos[2] == tiempos[3]
        assert tiempos[0] != tiempos[2]


# --------------------------------------------------------------------------- #
# 3. Lo que se paga
# --------------------------------------------------------------------------- #

class TestCoste:
    def test_defectos_del_sft_cincuenta_pasos_y_cien_pasadas(self):
        modelo, cond = _ModeloFalso(), _CondFalso()
        resultado = generar_latentes_text2music(
            model=modelo, cond=cond, seed=1, variante="sft"
        )
        assert resultado.time_costs["num_steps"] == 50.0
        assert resultado.time_costs["dit_forward_passes"] == 100.0
        assert resultado.time_costs["guidance_scale"] == 7.0
        assert resultado.time_costs["shift"] == 1.0
        assert {lote for _, lote in modelo.decoder.llamadas} == {1}, "hay una pasada por lote"

    def test_sin_guia_el_sft_no_paga_la_gemela(self):
        modelo, cond = _ModeloFalso(), _CondFalso()
        resultado = generar_latentes_text2music(
            model=modelo, cond=cond, seed=5, variante="sft", pasos=6, guidance_scale=1.0
        )
        assert resultado.time_costs["dit_forward_passes"] == 6.0

    def test_fuera_del_intervalo_de_guia_no_hay_gemela(self):
        modelo, cond = _ModeloFalso(), _CondFalso()
        resultado = generar_latentes_text2music(
            model=modelo, cond=cond, seed=5, variante="sft", pasos=10,
            cfg_interval=(0.5, 1.0),
        )
        con_guia = sum(
            1 for t in construir_programacion_continua(10, 1.0)[:-1] if 0.5 <= t <= 1.0
        )
        assert resultado.time_costs["dit_forward_passes"] == float(10 + con_guia)

    def test_el_intervalo_al_reves_se_rechaza(self):
        with pytest.raises(ValueError, match="al reves"):
            generar_latentes_text2music(
                model=_ModeloFalso(), cond=_CondFalso(), seed=1, variante="sft",
                pasos=4, cfg_interval=(1.0, 0.0),
            )

    def test_on_step_cuenta_pasos_no_pasadas(self):
        vistos: list[tuple[int, int]] = []
        generar_latentes_text2music(
            model=_ModeloFalso(), cond=_CondFalso(), seed=1, variante="sft", pasos=7,
            on_step=lambda hecho, total: vistos.append((hecho, total)),
        )
        assert vistos == [(i, 7) for i in range(1, 8)]

    def test_una_excepcion_de_on_step_se_propaga(self):
        """Es como el adapter aplica el tope de segundos de GPU: no se captura."""
        def parar(hecho, total):
            if hecho == 3:
                raise TimeoutError("presupuesto agotado")

        with pytest.raises(TimeoutError):
            generar_latentes_text2music(
                model=_ModeloFalso(), cond=_CondFalso(), seed=1, variante="sft",
                pasos=20, on_step=parar,
            )
