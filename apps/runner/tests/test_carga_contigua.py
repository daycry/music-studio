"""Tests de la lectura contigua del artefacto (`carga_contigua.py`).

Que se prueba aqui, y por que importa: la lectura contigua es lo que baja
`vram_load` de 709 s a ~70 s, y lo hace **reinterpretando bytes crudos** en vez
de dejar que `safetensors` construya cada tensor. Un fallo suyo no daria un error
ruidoso: daria pesos silenciosamente equivocados. Por eso el test central es una
ida y vuelta comparada tensor a tensor contra `safetensors.torch.load_file`, con
todos los dtypes del artefacto real (incluido `bfloat16`) y con el caso
desalineado que trae de verdad (`aux.silence_latent`).

No hace falta GPU: la rama que escribe en un dispositivo distinto de CPU se
ejercita con `"cpu:0"`, que para `torch.device` es un dispositivo valido y para
este modulo es "no es la cadena 'cpu'", que es justo la bifurcacion.
"""

from __future__ import annotations

import ast
import json
import os
from pathlib import Path

import pytest

torch = pytest.importorskip("torch", reason="la carga de pesos necesita torch")
safetensors_torch = pytest.importorskip("safetensors.torch")

import ace_step_shim as shim  # noqa: E402
import adapter as modulo_adapter  # noqa: E402
import carga_contigua  # noqa: E402


# --------------------------------------------------------------------------- #
# Un artefacto de juguete con la misma forma que el de verdad
# --------------------------------------------------------------------------- #

def _artefacto_de_juguete(destino: Path) -> dict[str, torch.Tensor]:
    """Escribe un safetensors pequeno que reproduce los casos del real.

    Incluye: los cuatro dtypes que trae el artefacto (F16, BF16, F32, U8), varios
    componentes con prefijo, un tensor de rango 3, un escalar y —a proposito— un
    blob U8 de **longitud impar** delante de un F32, que es como aparece el unico
    tensor desalineado del artefacto real.
    """
    tensores = {
        "dit.decoder.a": torch.randn(64, 32, dtype=torch.float32).half(),
        "dit.decoder.b": torch.randn(8, 4, 2, dtype=torch.float32).half(),
        "dit.encoder.a": torch.randn(16, 16, dtype=torch.float32).half(),
        "text_encoder.embed": torch.randn(32, 8, dtype=torch.float32).half(),
        "lm.w": torch.randn(24, 6, dtype=torch.float32).to(torch.bfloat16),
        "vae.decoder.w": torch.randn(4, 4, dtype=torch.float32),
        "aux.config_json": torch.frombuffer(
            bytearray(json.dumps({"hola": "mundo", "n": 3}).encode()), dtype=torch.uint8
        ).clone(),
        # Longitud impar -> deja el siguiente F32 desalineado (el caso real).
        "aux.impar": torch.frombuffer(bytearray(b"x" * 777), dtype=torch.uint8).clone(),
        "aux.silence_latent": torch.randn(1, 8, 40, dtype=torch.float32),
        "aux.escalar": torch.tensor(3.5, dtype=torch.float32),
    }
    safetensors_torch.save_file(tensores, str(destino))
    return tensores


@pytest.fixture
def artefacto(tmp_path: Path) -> tuple[Path, dict[str, torch.Tensor]]:
    ruta = tmp_path / "juguete.safetensors"
    return ruta, _artefacto_de_juguete(ruta)


# --------------------------------------------------------------------------- #
# Cabecera
# --------------------------------------------------------------------------- #

class TestCabecera:
    def test_la_cabecera_coincide_con_la_de_safetensors(self, artefacto):
        ruta, tensores = artefacto
        cabecera, base = carga_contigua.leer_cabecera(str(ruta))
        claves = {k for k in cabecera if k != "__metadata__"}
        assert claves == set(tensores)
        assert base == 8 + int.from_bytes(ruta.read_bytes()[:8], "little")
        # El bloque de datos empieza donde acaba la cabecera y llega al final.
        fin = max(m["data_offsets"][1] for m in cabecera.values() if isinstance(m, dict))
        assert base + fin == ruta.stat().st_size

    def test_un_fichero_que_no_es_safetensors_se_rechaza(self, tmp_path):
        basura = tmp_path / "basura.safetensors"
        basura.write_bytes(b"\xff" * 4096)
        with pytest.raises(carga_contigua.ArtefactoIlegible):
            carga_contigua.leer_cabecera(str(basura))

    def test_un_fichero_vacio_se_rechaza(self, tmp_path):
        vacio = tmp_path / "vacio.safetensors"
        vacio.write_bytes(b"")
        with pytest.raises(carga_contigua.ArtefactoIlegible):
            carga_contigua.leer_cabecera(str(vacio))


# --------------------------------------------------------------------------- #
# Planificacion de tramos
# --------------------------------------------------------------------------- #

def _cabecera_sintetica(entradas: list[tuple[str, int, int]]) -> dict:
    return {
        clave: {"dtype": "U8", "shape": [fin - ini], "data_offsets": [ini, fin]}
        for clave, ini, fin in entradas
    }


class TestPlanificar:
    def test_lo_contiguo_con_el_mismo_destino_se_junta_en_un_solo_tramo(self):
        cab = _cabecera_sintetica([("a.1", 0, 10), ("a.2", 10, 20), ("a.3", 20, 30)])
        tramos = carga_contigua.planificar(cab, base=100)
        assert len(tramos) == 1
        assert (tramos[0].ini, tramos[0].fin) == (100, 130)
        assert tramos[0].claves == ["a.1", "a.2", "a.3"]

    def test_un_hueco_corta_el_tramo(self):
        # Este es el caso que la tarea pedia comprobar y no suponer: si el fusor
        # dejara relleno entre tensores, leer el rango entero de una vez y
        # repartirlo por offsets seguiria siendo correcto, pero un SOLAPE o un
        # hueco no declarado no lo seria. Se corta y se leen dos rangos.
        cab = _cabecera_sintetica([("a.1", 0, 10), ("a.2", 16, 26)])
        tramos = carga_contigua.planificar(cab, base=0)
        assert [(t.ini, t.fin) for t in tramos] == [(0, 10), (16, 26)]

    def test_cambiar_de_destino_corta_el_tramo(self):
        cab = _cabecera_sintetica([("a.1", 0, 10), ("b.1", 10, 20), ("a.2", 20, 30)])
        tramos = carga_contigua.planificar(cab, base=0, destinos={"b.": "cuda:0"})
        assert [(t.destino, t.ini, t.fin) for t in tramos] == [
            ("cpu", 0, 10),
            ("cuda:0", 10, 20),
            ("cpu", 20, 30),
        ]

    def test_el_tope_corta_el_tramo_pero_nunca_parte_un_tensor(self):
        cab = _cabecera_sintetica([(f"a.{i}", i * 10, i * 10 + 10) for i in range(5)])
        tramos = carga_contigua.planificar(cab, base=0, tope=25)
        assert all(t.bytes <= 30 for t in tramos)
        # Ningun tensor aparece en dos tramos, y estan todos.
        vistas = [c for t in tramos for c in t.claves]
        assert sorted(vistas) == sorted(cab)
        assert len(vistas) == len(set(vistas))

    def test_un_tensor_mayor_que_el_tope_forma_tramo_propio(self):
        cab = _cabecera_sintetica([("a.1", 0, 10), ("a.gordo", 10, 1000)])
        tramos = carga_contigua.planificar(cab, base=0, tope=50)
        assert [t.claves for t in tramos] == [["a.1"], ["a.gordo"]]

    def test_los_tramos_salen_en_orden_fisico_creciente(self, artefacto):
        # Recorrerlos en este orden es lo que convierte la carga en una unica
        # pasada hacia delante: en un disco mecanico, ir y volver la hunde.
        ruta, _ = artefacto
        cabecera, base = carga_contigua.leer_cabecera(str(ruta))
        tramos = carga_contigua.planificar(cabecera, base, tope=64)
        assert [t.ini for t in tramos] == sorted(t.ini for t in tramos)
        for anterior, siguiente in zip(tramos, tramos[1:]):
            assert anterior.fin <= siguiente.ini

    def test_el_prefijo_mas_largo_manda(self):
        cab = _cabecera_sintetica([("dit.decoder.x", 0, 10), ("dit.encoder.x", 10, 20)])
        tramos = carga_contigua.planificar(
            cab, base=0, destinos={"dit.": "cpu", "dit.decoder.": "cuda:0"}
        )
        assert {t.destino for t in tramos} == {"cpu", "cuda:0"}
        assert next(t for t in tramos if t.destino == "cuda:0").claves == ["dit.decoder.x"]


# --------------------------------------------------------------------------- #
# Ida y vuelta: los bytes tienen que ser LOS MISMOS
# --------------------------------------------------------------------------- #

class TestIdaYVuelta:
    @pytest.mark.parametrize("tope", [1 << 20, 128, 64, 33])
    def test_todos_los_tensores_son_identicos_a_los_de_load_file(self, artefacto, tope):
        # El tope se varia a proposito: con topes pequenos el mismo componente
        # cae en varios tramos y cada tensor se referencia contra un buffer
        # distinto. Si la aritmetica de offsets relativos estuviera mal, aqui
        # saldrian pesos corruptos en vez de una excepcion.
        ruta, esperados = artefacto
        obtenidos = carga_contigua.cargar_contiguo(str(ruta), tope_tramo=tope, bloque=17)
        assert set(obtenidos) == set(esperados)
        for clave, esperado in esperados.items():
            real = obtenidos[clave]
            assert real.dtype is esperado.dtype, clave
            assert real.shape == esperado.shape, clave
            assert torch.equal(real, esperado), clave

    def test_coincide_con_load_file_tensor_a_tensor(self, artefacto):
        ruta, _ = artefacto
        referencia = safetensors_torch.load_file(str(ruta), device="cpu")
        obtenidos = carga_contigua.cargar_contiguo(str(ruta))
        assert set(obtenidos) == set(referencia)
        for clave, esperado in referencia.items():
            assert torch.equal(obtenidos[clave], esperado), clave

    def test_el_tensor_desalineado_se_copia_y_queda_alineado(self, artefacto):
        # `aux.silence_latent` va detras de un blob U8 de 777 bytes, o sea que su
        # offset no es multiplo de 4. El cargador lo copia; si algun dia dejara de
        # hacerlo, este test avisa antes de que un kernel vectorizado lo note.
        ruta, esperados = artefacto
        obtenidos = carga_contigua.cargar_contiguo(str(ruta))
        latente = obtenidos["aux.silence_latent"]
        assert latente.data_ptr() % 4 == 0
        assert torch.equal(latente, esperados["aux.silence_latent"])

    def test_los_pesos_quedan_alineados_a_64_bytes(self, artefacto):
        # Importa de verdad: el planificador de 5 Hz corre en CPU y oneDNN recorre
        # sus 1.264 MiB en cada generacion. Un `bytearray` habria dado
        # `pagina + 16` de base y ni uno solo de estos punteros estaria alineado.
        # En el artefacto real el 99 % de los offsets relativos son multiplos de
        # 64, asi que con la base alineada salen alineados.
        ruta, _ = artefacto
        obtenidos = carga_contigua.cargar_contiguo(str(ruta))
        for clave in ("dit.decoder.a", "text_encoder.embed", "lm.w"):
            assert obtenidos[clave].untyped_storage().data_ptr() % 64 == 0, clave

    def test_el_escalar_conserva_el_rango_cero(self, artefacto):
        ruta, esperados = artefacto
        obtenidos = carga_contigua.cargar_contiguo(str(ruta))
        assert obtenidos["aux.escalar"].shape == esperados["aux.escalar"].shape == torch.Size([])

    def test_un_fichero_truncado_no_devuelve_pesos_a_medias(self, artefacto):
        ruta, _ = artefacto
        crudo = ruta.read_bytes()
        ruta.write_bytes(crudo[: len(crudo) - 64])
        with pytest.raises(carga_contigua.ArtefactoIlegible):
            carga_contigua.cargar_contiguo(str(ruta))


# --------------------------------------------------------------------------- #
# La propiedad que da nombre a todo esto: los tensores estan MATERIALIZADOS
# --------------------------------------------------------------------------- #

class TestMaterializacion:
    def test_el_diccionario_es_un_dict_y_lleva_la_marca(self, artefacto):
        ruta, _ = artefacto
        estado = carga_contigua.cargar_contiguo(str(ruta))
        # El shim comprueba `isinstance(state_dict, dict)`: si esto dejara de ser
        # un dict de verdad, `build_pipeline` levantaria TypeError.
        assert isinstance(estado, dict)
        assert estado.tensores_materializados is True
        assert getattr(estado, "tensores_materializados", False) is True

    def test_load_file_no_lleva_la_marca(self, artefacto):
        # El respaldo tiene que seguir comportandose como antes: con `load_file`
        # el shim debe seguir clonando.
        ruta, _ = artefacto
        estado = safetensors_torch.load_file(str(ruta), device="cpu")
        assert getattr(estado, "tensores_materializados", False) is False

    def test_el_fichero_queda_cerrado_y_los_tensores_siguen_valiendo(self, artefacto):
        # Prueba funcional de que NO hay mapeo vivo: en Windows no se puede borrar
        # un fichero mapeado. Si esto pasa, los pesos estan en RAM anonima, que es
        # justo lo que evita releer el disco pagina a pagina en cada subida a VRAM
        # (42,91 s frente a 0,43 s medidos).
        ruta, esperados = artefacto
        estado = carga_contigua.cargar_contiguo(str(ruta))
        os.remove(ruta)
        assert not ruta.exists()
        for clave, esperado in esperados.items():
            assert torch.equal(estado[clave], esperado), clave


# --------------------------------------------------------------------------- #
# La rama de "destino que no es la CPU" (escalera con buffer de escala)
# --------------------------------------------------------------------------- #

class TestDestinoDeDispositivo:
    def test_un_destino_de_dispositivo_no_altera_los_pesos(self, artefacto):
        # "cpu:0" es un dispositivo valido para torch: permite recorrer el camino
        # de `destinos` completo sin GPU.
        ruta, esperados = artefacto
        estado = carga_contigua.cargar_contiguo(
            str(ruta), destinos={"dit.decoder.": "cpu:0"}, bloque=7
        )
        for clave, esperado in esperados.items():
            assert torch.equal(estado[clave], esperado), clave

    @pytest.mark.parametrize("escala_bytes", [1, 7, 64, 4096])
    def test_la_escalera_por_buffer_de_escala_reproduce_el_rango_exacto(self, tmp_path, escala_bytes):
        # `_leer_a_dispositivo` es la ruta que en produccion mete 3.005 MiB en la
        # tarjeta sin pasar por un pico de 3 GiB en RAM. Se prueba con un destino
        # de CPU: lo que se verifica es la aritmetica de la escalera (offsets
        # acumulados, lecturas cortas, ultimo trozo), no el bus PCIe.
        datos = bytes(range(256)) * 40
        fichero = tmp_path / "crudo.bin"
        fichero.write_bytes(b"basura" + datos)
        destino = torch.empty(len(datos), dtype=torch.uint8)
        escala = torch.empty(escala_bytes, dtype=torch.uint8)
        with open(fichero, "rb", buffering=0) as f:
            f.seek(6)
            carga_contigua._leer_a_dispositivo(f, destino, len(datos), escala, str(fichero))
        assert bytes(destino.numpy().tobytes()) == datos

    def test_la_escalera_avisa_si_el_fichero_se_queda_corto(self, tmp_path):
        fichero = tmp_path / "corto.bin"
        fichero.write_bytes(b"solo diez")
        destino = torch.empty(100, dtype=torch.uint8)
        escala = torch.empty(8, dtype=torch.uint8)
        with open(fichero, "rb", buffering=0) as f:
            with pytest.raises(carga_contigua.ArtefactoIlegible):
                carga_contigua._leer_a_dispositivo(f, destino, 100, escala, str(fichero))

    def test_los_tensores_del_tramo_de_dispositivo_comparten_un_solo_buffer(self, artefacto):
        # Es la propiedad que hace que la copia H2D sea UNA por tramo y no una por
        # tensor: todos los tensores del tramo son vistas del mismo almacenamiento.
        ruta, _ = artefacto
        estado = carga_contigua.cargar_contiguo(str(ruta), destinos={"dit.decoder.": "cpu:0"})
        a = estado["dit.decoder.a"]
        b = estado["dit.decoder.b"]
        assert a.untyped_storage().data_ptr() == b.untyped_storage().data_ptr()

    def test_sin_vram_suficiente_se_aborta_antes_de_asignar(self, monkeypatch):
        # El guardarrail no puede desaparecer: capturar un OOM del driver deja el
        # asignador de PyTorch inservible para el resto del proceso.
        class _CudaFalso:
            @staticmethod
            def mem_get_info(_dev):
                return (100, 8192)

            @staticmethod
            def memory_reserved(_dev):
                return 0

            @staticmethod
            def memory_allocated(_dev):
                return 0

        falso = type("T", (), {"device": torch.device, "cuda": _CudaFalso})
        with pytest.raises(RuntimeError, match="VRAM insuficiente"):
            carga_contigua._exigir_vram(falso, "cuda:0", 4096)

    def test_con_vram_de_sobra_no_se_aborta(self):
        class _CudaFalso:
            @staticmethod
            def mem_get_info(_dev):
                return (1 << 30, 1 << 30)

            @staticmethod
            def memory_reserved(_dev):
                return 0

            @staticmethod
            def memory_allocated(_dev):
                return 0

        falso = type("T", (), {"device": torch.device, "cuda": _CudaFalso})
        carga_contigua._exigir_vram(falso, "cuda:0", 4096)


# --------------------------------------------------------------------------- #
# El acoplamiento con el shim: que no se separen
# --------------------------------------------------------------------------- #

def _prefijos_que_el_shim_manda_a_la_gpu() -> set[str]:
    """Lee el fuente del shim y saca los `_extraer(..., dispositivo, ...)`.

    Se hace sobre el AST y no importando: lo que interesa es el reparto
    DECLARADO en `build_pipeline`, sin necesidad de pesos ni de GPU.
    """
    fuente = Path(shim.__file__).read_text(encoding="utf-8")
    arbol = ast.parse(fuente)
    prefijos: set[str] = set()
    for nodo in ast.walk(arbol):
        if not isinstance(nodo, ast.Call):
            continue
        if not (isinstance(nodo.func, ast.Name) and nodo.func.id == "_extraer"):
            continue
        if len(nodo.args) < 3:
            continue
        destino = nodo.args[2]
        if not (isinstance(destino, ast.Name) and destino.id == "dispositivo"):
            continue
        prefijo = nodo.args[1]
        if isinstance(prefijo, ast.Constant) and isinstance(prefijo.value, str):
            prefijos.add(prefijo.value)
        elif isinstance(prefijo, ast.Name):
            prefijos.add(getattr(shim, prefijo.id))
    return prefijos


class TestAcoplamientoConElShim:
    #: Claves sueltas que van a la GPU y no justifican un tramo propio: son
    #: kilobytes, leerlas a RAM y subirlas no cuesta nada medible.
    SUELTAS = {shim.CLAVE_NULL_CONDITION}

    def test_todo_lo_que_se_declara_residente_lo_es_de_verdad(self):
        # Si alguien mueve `dit.decoder` a RAM y se olvida de la constante, el
        # cargador reservaria 3.005 MiB de VRAM para nada. Este test lo caza.
        declarados = set(shim.PREFIJOS_RESIDENTES_GPU)
        reales = _prefijos_que_el_shim_manda_a_la_gpu()
        assert declarados <= reales, f"declarados de mas: {declarados - reales}"

    def test_no_hay_componentes_grandes_yendo_a_la_gpu_sin_declararse(self):
        # Al reves: si el shim empieza a residenciar otro componente y nadie lo
        # declara, se pierde el ahorro de pico de RAM en silencio.
        reales = _prefijos_que_el_shim_manda_a_la_gpu()
        sin_declarar = reales - set(shim.PREFIJOS_RESIDENTES_GPU) - self.SUELTAS
        assert not sin_declarar, f"sin declarar en PREFIJOS_RESIDENTES_GPU: {sin_declarar}"

    def test_el_respaldo_documental_del_cargador_sigue_al_dia(self):
        assert carga_contigua.PREFIJOS_RESIDENTES_GPU_ESPERADOS == shim.PREFIJOS_RESIDENTES_GPU


# --------------------------------------------------------------------------- #
# Integracion con el adapter
# --------------------------------------------------------------------------- #

class TestAdapter:
    def test_el_adapter_le_pregunta_al_shim_por_los_prefijos(self):
        assert modulo_adapter._prefijos_residentes_gpu(shim.build_pipeline) == (
            shim.PREFIJOS_RESIDENTES_GPU
        )

    def test_una_factoria_sin_declaracion_no_pide_nada_a_la_gpu(self):
        def factoria_pelada(**_kwargs):
            return None

        assert modulo_adapter._prefijos_residentes_gpu(factoria_pelada) == ()

    def test_una_declaracion_mal_formada_se_ignora_con_aviso(self, monkeypatch):
        monkeypatch.setattr(shim, "PREFIJOS_RESIDENTES_GPU", "dit.decoder.", raising=False)
        assert modulo_adapter._prefijos_residentes_gpu(shim.build_pipeline) == ()

    def test_carga_el_artefacto_por_la_ruta_contigua(self, artefacto):
        ruta, esperados = artefacto
        estado = modulo_adapter._cargar_state_dict(str(ruta), shim.build_pipeline, "cpu")
        assert getattr(estado, "tensores_materializados", False) is True
        for clave, esperado in esperados.items():
            assert torch.equal(estado[clave], esperado), clave

    def test_en_cuda_se_le_pasa_el_destino_del_decoder_al_cargador(self, artefacto, monkeypatch):
        ruta, _ = artefacto
        vistos = {}

        def espia(ruta_, *, destinos):
            vistos["destinos"] = destinos
            return carga_contigua.EstadoDelArtefacto()

        monkeypatch.setattr(carga_contigua, "cargar_contiguo", espia)
        modulo_adapter._cargar_state_dict(str(ruta), shim.build_pipeline, "cuda:0")
        assert vistos["destinos"] == {"dit.decoder.": "cuda:0"}

    def test_si_la_lectura_contigua_falla_se_cae_a_load_file(self, artefacto, monkeypatch, caplog):
        ruta, esperados = artefacto

        def revienta(*_a, **_k):
            raise RuntimeError("disco poseido")

        monkeypatch.setattr(carga_contigua, "cargar_contiguo", revienta)
        with caplog.at_level("WARNING"):
            estado = modulo_adapter._cargar_state_dict(str(ruta), shim.build_pipeline, "cpu")
        # El respaldo funciona...
        assert set(estado) == set(esperados)
        # ...pero NO en silencio: un arranque de 12 minutos tiene que avisar.
        assert "disco poseido" in caplog.text
        assert getattr(estado, "tensores_materializados", False) is False

    def test_el_interruptor_de_entorno_vuelve_a_load_file(self, artefacto, monkeypatch):
        ruta, esperados = artefacto
        monkeypatch.setenv(modulo_adapter._CARGA_CONTIGUA_ENV, "0")
        estado = modulo_adapter._cargar_state_dict(str(ruta), shim.build_pipeline, "cpu")
        assert getattr(estado, "tensores_materializados", False) is False
        assert set(estado) == set(esperados)


# --------------------------------------------------------------------------- #
# El shim no clona cuando no hace falta
# --------------------------------------------------------------------------- #

class TestExtraerMaterializado:
    def test_sin_la_marca_se_clona_como_siempre(self):
        origen = torch.randn(4, 4)
        estado = {"p.w": origen}
        salida = shim._extraer(estado, "p.", torch.device("cpu"), 1)
        assert torch.equal(salida["w"], origen)
        assert salida["w"].data_ptr() != origen.data_ptr()
        assert estado == {}

    def test_con_la_marca_se_adopta_el_tensor_tal_cual(self):
        # Clonar aqui seria duplicar el componente entero; con `dit.decoder` son
        # 3.005 MiB de VRAM que no existen en una tarjeta de 8 GB.
        origen = torch.randn(4, 4)
        estado = {"p.w": origen}
        salida = shim._extraer(estado, "p.", torch.device("cpu"), 1, materializado=True)
        assert salida["w"].data_ptr() == origen.data_ptr()

    def test_con_la_marca_y_otro_dispositivo_se_sigue_copiando(self):
        # La bandera no autoriza a saltarse un cambio de dispositivo.
        origen = torch.randn(4, 4)
        estado = {"p.w": origen}
        salida = shim._extraer(estado, "p.", torch.device("cpu:0"), 1, materializado=True)
        assert torch.equal(salida["w"], origen)

    def test_el_recuento_esperado_se_sigue_comprobando(self):
        estado = {"p.w": torch.zeros(2)}
        with pytest.raises(RuntimeError, match="contrato verificado"):
            shim._extraer(estado, "p.", torch.device("cpu"), 7, materializado=True)


class _Alto(Exception):
    """Corta `build_pipeline` en cuanto se ha visto lo que se queria ver."""


def _estado_minimo_hasta_el_text_encoder(marcado: bool):
    """`state_dict` suficiente para que `build_pipeline` llegue al text encoder."""
    datos = {
        "dit.decoder.layers.0.mlp.up_proj.weight": torch.zeros(2, 2, dtype=torch.float16),
        "aux.config.vae_json": torch.zeros(4, dtype=torch.uint8),
    }
    for i in range(182):
        datos[f"vae.decoder.w{i}"] = torch.zeros(2, dtype=torch.float16)
    if not marcado:
        return dict(datos)
    estado = carga_contigua.EstadoDelArtefacto()
    estado.update(datos)
    return estado


@pytest.mark.parametrize("marcado", [True, False])
def test_build_pipeline_propaga_la_marca_al_text_encoder(monkeypatch, marcado):
    """La bandera tiene que LLEGAR a `construir_text_encoder`, no solo existir.

    Es el punto donde se decide si se clonan 1.136 MiB para nada, y es una
    propagacion por parametro: exactamente la clase de cosa que se rompe en una
    refactorizacion sin que nada proteste.
    """
    import text_conditioning  # noqa: PLC0415

    visto = {}
    monkeypatch.setattr(shim.text_conditioning, "construir_tokenizer", lambda _sd: object())
    monkeypatch.setattr(shim, "cargar_decoder", lambda *_a, **_k: torch.nn.Linear(2, 2))
    monkeypatch.setattr(shim, "_Residencia", lambda *_a, **_k: None)

    def espia(_state_dict, *, consumir, materializado):
        visto["consumir"] = consumir
        visto["materializado"] = materializado
        raise _Alto

    monkeypatch.setattr(text_conditioning, "construir_text_encoder", espia)

    with pytest.raises(_Alto):
        shim.build_pipeline(
            state_dict=_estado_minimo_hasta_el_text_encoder(marcado),
            device="cpu",
            dtype=None,
            offload=False,
        )
    assert visto == {"consumir": True, "materializado": marcado}
