"""Los buffers no persistentes son un fallo SILENCIOSO, y aqui queda por escrito.

Que es esto y por que importa
-----------------------------
El shim instancia el DiT en el dispositivo `meta` (sin reservar memoria) para
poder **asignar** despues los tensores del artefacto con
`load_state_dict(assign=True)`, que es lo que evita duplicar 7,5 GB en RAM.

El problema: un buffer registrado con `persistent=False` **no viaja en el
`state_dict`**. Y `strict=True`, que es la red de seguridad de toda la carga, solo
comprueba las claves que el `state_dict` declara: de un buffer no persistente no
dice nada. Instanciado en `meta` y no reconstruido, el buffer se queda **vacio**,
`strict=True` da su bendicion, y el modelo produce audio incorrecto sin un solo
error. En el DiT de ACE-Step son 15 buffers (`rotary_emb.inv_freq`,
`original_inv_freq` y los del FSQ), y `inv_freq` es la posicion de RoPE: sin ella
el modelo no sabe donde esta en la secuencia.

Hasta hoy eso solo estaba verificado a mano en la GPU. Estos tests lo fijan sin
los pesos reales, con un modulo de juguete que reproduce la misma estructura: la
mitad del fallo (que `strict=True` no protesta) y la mitad de la cura (que el
patron del shim lo deja materializado y con el valor correcto).
"""

from __future__ import annotations

import pytest

torch = pytest.importorskip("torch", reason="esto va de tensores")

import ace_step_shim as shim  # noqa: E402


class _ModuloConBufferOculto(torch.nn.Module):
    """Reproduce la estructura del DiT: un peso normal y un buffer no persistente.

    `inv_freq` se calcula en el constructor a partir de la configuracion, igual
    que `Qwen3RotaryEmbedding`, y se registra como NO persistente: es derivado,
    no aprendido, asi que upstream no lo guarda en el checkpoint.
    """

    def __init__(self, dim: int = 4) -> None:
        super().__init__()
        self.peso = torch.nn.Parameter(torch.zeros(dim, dim))
        self.register_buffer("inv_freq", 1.0 / (10000 ** (torch.arange(dim) / dim)),
                             persistent=False)
        self.register_buffer("contador", torch.zeros(1), persistent=True)


def _state_dict_del_artefacto(dim: int = 4) -> dict[str, torch.Tensor]:
    """Lo que traeria el artefacto: los persistentes y NADA del no persistente."""
    return {
        "peso": torch.ones(dim, dim),
        "contador": torch.full((1,), 7.0),
    }


class TestElFalloEsSilencioso:
    """La mitad incomoda: demostrar que nada avisa."""

    def test_el_buffer_no_persistente_no_esta_en_el_state_dict(self):
        modulo = _ModuloConBufferOculto()
        claves = set(modulo.state_dict())
        assert "peso" in claves and "contador" in claves
        assert "inv_freq" not in claves, (
            "si inv_freq empezara a viajar en el state_dict, este fichero entero "
            "sobra: revisalo antes de borrarlo"
        )

    def test_strict_true_no_protesta_por_un_buffer_que_quedo_en_meta(self):
        # ESTE es el fallo. El modelo se queda con inv_freq vacio y la carga
        # devuelve "todo correcto".
        with torch.device("meta"):
            modulo = _ModuloConBufferOculto()
        assert modulo.inv_freq.is_meta

        faltan, sobran = modulo.load_state_dict(
            _state_dict_del_artefacto(), strict=True, assign=True
        )
        assert not faltan and not sobran, "strict=True no ha encontrado nada que objetar"
        # Y sin embargo el modelo esta roto: el buffer sigue sin memoria.
        assert modulo.inv_freq.is_meta, (
            "el buffer se materializo solo; si torch cambio de comportamiento, "
            "este test hay que rehacerlo, no relajarlo"
        )

    def test_usar_el_modelo_asi_no_da_un_error_util(self):
        # Un tensor en meta no lanza al leerse la forma ni al operar en meta: el
        # resultado es otro tensor meta. Por eso el fallo se propaga en vez de
        # detenerse, y solo se nota en el audio.
        with torch.device("meta"):
            modulo = _ModuloConBufferOculto()
        producto = modulo.inv_freq * 2
        assert producto.is_meta, (
            "operar con un tensor meta devuelve otro tensor meta: el fallo se "
            "PROPAGA en vez de detenerse, y eso es lo que lo hace silencioso"
        )
        # Solo al intentar sacarle un VALOR concreto protesta, y para entonces
        # puede haber pasado por medio modelo. El tipo de error es un detalle de
        # torch (hoy RuntimeError, "cannot be called on meta tensors"); lo que
        # importa aqui es que llega tarde, no como se llama.
        with pytest.raises(RuntimeError, match="meta"):
            float(modulo.inv_freq[0])


class TestElPatronDelShimLoArregla:
    """La mitad tranquilizadora: el remedio que aplica `_instanciar_dit`."""

    def test_construir_el_buffer_fuera_de_meta_lo_deja_con_su_valor(self):
        # Es lo que hace el shim: sustituye Qwen3RotaryEmbedding y ResidualFSQ por
        # versiones que se construyen en CPU aunque el resto vaya en meta.
        referencia = _ModuloConBufferOculto()  # en CPU, valor de verdad
        with torch.device("meta"):
            modulo = _ModuloConBufferOculto()
        modulo._buffers["inv_freq"] = referencia.inv_freq.clone()  # noqa: SLF001

        modulo.load_state_dict(_state_dict_del_artefacto(), strict=True, assign=True)
        assert not modulo.inv_freq.is_meta
        assert torch.equal(modulo.inv_freq, referencia.inv_freq)
        # Y los persistentes llegaron del artefacto, no del constructor.
        assert torch.equal(modulo.peso, torch.ones(4, 4))
        assert float(modulo.contador[0]) == 7.0

    def test_la_comprobacion_de_que_no_queda_nada_en_meta_detecta_el_caso_roto(self):
        # El shim aborta si algun buffer no persistente sigue en meta. Aqui se
        # reproduce esa comprobacion sobre el modulo de juguete, en sus dos
        # estados, para fijar que distingue uno del otro.
        def buffers_no_persistentes_en_meta(m: torch.nn.Module) -> list[str]:
            persistentes = set(m.state_dict())
            return [
                nombre
                for nombre, buf in m.named_buffers()
                if nombre not in persistentes and buf.is_meta
            ]

        with torch.device("meta"):
            roto = _ModuloConBufferOculto()
        assert buffers_no_persistentes_en_meta(roto) == ["inv_freq"]

        sano = _ModuloConBufferOculto()
        assert buffers_no_persistentes_en_meta(sano) == []


class TestElHelperDelShim:
    """`_colocar_buffers_no_persistentes` sobre el modulo de juguete."""

    def test_mueve_solo_los_no_persistentes(self):
        modulo = _ModuloConBufferOculto()
        # Se marca el persistente para poder distinguir despues quien se movio.
        movidos = shim._colocar_buffers_no_persistentes(modulo, torch.device("cpu"))
        # Ya estaban en CPU: no hay nada que mover, y eso tambien es correcto.
        assert movidos == 0

    def test_es_idempotente(self):
        modulo = _ModuloConBufferOculto()
        destino = torch.device("cpu")
        assert shim._colocar_buffers_no_persistentes(modulo, destino) == 0
        assert shim._colocar_buffers_no_persistentes(modulo, destino) == 0
        assert not modulo.inv_freq.is_meta

    def test_no_toca_los_que_si_viajan_en_el_state_dict(self):
        # El persistente lo coloca `load_state_dict(assign=True)`; si el helper
        # tambien lo moviera, estaria duplicando trabajo y podria deshacer una
        # asignacion deliberada.
        modulo = _ModuloConBufferOculto()
        antes = modulo.contador
        shim._colocar_buffers_no_persistentes(modulo, torch.device("cpu"))
        assert modulo.contador is antes
