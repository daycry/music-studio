# -*- coding: utf-8 -*-
"""Tests de `spikes/g1_anonimizar.py` — el ciego ENTRE SERIES de G1.

Que se esta protegiendo aqui
============================
`gates/g1-protocolo.md` §5.4 permite que el evaluador sepa a que brief responde
cada pista (sin eso D1 no es puntuable) y le prohibe saber **de que serie
viene** (propia / libreria / Suno). Si esa segunda parte falla, el gate no mide
calidad: mide expectativa.

`g1_generar.py` ya ciega las TOMAS dentro de la serie propia. Eso es otro ciego,
para otra decision (§5.2, elegir cual de las tres tomas manda). El de aqui es el
de §5.4 y es el que decide el gate.

Un ciego se rompe por el camino mas tonto, no por el mas listo, asi que los
tests van justo a esos caminos: el nombre del fichero, el orden alfabetico, la
fecha de modificacion, una etiqueta que se cuela en el WAV, una cabecera con
otra frecuencia de muestreo, una semilla que aparece fuera del sellado y un
`loudness.csv` que canta el nivel de origen.
"""

from __future__ import annotations

import csv
import hashlib
import math
import struct
import subprocess
import sys
from pathlib import Path

import pytest

np = pytest.importorskip("numpy")
pytest.importorskip("scipy")

import g1_anonimizar  # noqa: E402
import g1_sonoridad  # noqa: E402


BRIEFS_10 = tuple(f"B{i:02d}" for i in range(1, 11))
BRIEFS_3 = BRIEFS_10[:3]

#: Semilla fija para los tests. En produccion se sortea y solo vive en el sello.
SEMILLA = 20260903


def _seno(pico: float, hz: float, segundos: float, tasa: int, canales: int) -> "np.ndarray":
    n = np.arange(int(round(segundos * tasa)))
    onda = pico * np.sin(2.0 * math.pi * hz * n / tasa)
    return np.column_stack([onda] * canales)


def _material(raiz: Path, briefs=BRIEFS_3, con_suno: bool = True,
              tasa_libreria: int = 48000, canales_libreria: int = 2) -> dict[str, Path]:
    """Tres series verosimiles: la propia floja, la de libreria alta y masterizada.

    Cada serie usa una frecuencia distinta para que un test pueda identificarla
    por FFT sin mirar el mapa — que es exactamente lo que el evaluador NO puede
    hacer de oido, pero un test si necesita poder hacer.
    """
    plan = {
        "propia": (220.0, 0.05, 48000, 2),
        "libreria": (330.0, 0.90, tasa_libreria, canales_libreria),
    }
    if con_suno:
        plan["suno"] = (440.0, 0.30, 48000, 2)

    directorios: dict[str, Path] = {}
    for serie, (hz, pico, tasa, canales) in plan.items():
        destino = raiz / "fuente" / serie
        destino.mkdir(parents=True, exist_ok=True)
        for brief in briefs:
            senal = _seno(pico, hz, 1.5, tasa, canales)
            g1_sonoridad.escribir_wav(destino / f"{brief}-{serie[:2]}.wav", senal, tasa)
        directorios[serie] = destino
    return directorios


def _anonimizar_de_ensayo(*args, **kwargs):
    """`anonimizar()` con la rejilla relajada: estos tests montan 3 briefs, no 10.

    Montar los diez en cada test costaria segundos de audio sintetico por nada:
    lo que se prueba aqui es el circuito, no el recuento. La comprobacion de que
    la tanda de verdad exige los diez de §4 vive en
    `TestLaRejillaSeMideContraElProtocolo`, con rejillas sinteticas y sin audio.
    """
    kwargs.setdefault("briefs_esperados", None)
    return g1_anonimizar.anonimizar(*args, **kwargs)

def _leer_mapa(raiz: Path) -> list[dict[str, str]]:
    with (raiz / "05-ciego" / g1_anonimizar.NOMBRE_MAPA).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _serie_por_etiqueta(raiz: Path) -> dict[tuple[str, str], str]:
    return {(f["brief"], f["etiqueta_ciega"]): f["serie"] for f in _leer_mapa(raiz)}


def _trozos_riff(ruta: Path) -> list[str]:
    """Identificadores de los trozos RIFF del fichero, en orden."""
    datos = ruta.read_bytes()
    assert datos[:4] == b"RIFF" and datos[8:12] == b"WAVE"
    trozos: list[str] = []
    pos = 12
    while pos + 8 <= len(datos):
        ident = datos[pos:pos + 4].decode("ascii", "replace")
        (tamano,) = struct.unpack("<I", datos[pos + 4:pos + 8])
        trozos.append(ident)
        pos += 8 + tamano + (tamano % 2)
    return trozos


# --------------------------------------------------------------------------- #
# El instrumento existe y produce la rejilla completa
# --------------------------------------------------------------------------- #

def test_produce_una_pista_por_serie_y_brief_con_etiquetas_opacas(tmp_path):
    raiz = tmp_path / "g1-2026"
    informe = _anonimizar_de_ensayo(_material(tmp_path), raiz, semilla=SEMILLA)

    esperados = {f"{b}-x{i}.wav" for b in BRIEFS_3 for i in (1, 2, 3)}
    assert {p.name for p in (raiz / "04-sesion").glob("*.wav")} == esperados
    assert informe["pistas"] == 9
    assert informe["briefs"] == 3


def test_falta_una_pista_en_una_serie_y_se_aborta(tmp_path):
    """Un brief con dos pistas en vez de tres delata la serie ausente al instante."""
    series = _material(tmp_path)
    (series["libreria"] / "B02-li.wav").unlink()
    with pytest.raises(ValueError, match="B02"):
        _anonimizar_de_ensayo(series, tmp_path / "g1-2026", semilla=SEMILLA)


def test_dos_pistas_del_mismo_brief_en_una_serie_y_se_aborta(tmp_path):
    """La eleccion de toma (§5.2) ocurre ANTES; aqui llega una pista por celda."""
    series = _material(tmp_path)
    duplicada = series["propia"] / "B02-otra.wav"
    g1_sonoridad.escribir_wav(duplicada, _seno(0.05, 220.0, 1.5, 48000, 2), 48000)
    with pytest.raises(ValueError, match="B02"):
        _anonimizar_de_ensayo(series, tmp_path / "g1-2026", semilla=SEMILLA)


def test_la_variante_b_sin_suno_funciona_igual(tmp_path):
    """§5.6: prescindir de Suno cambia el material, no el criterio."""
    raiz = tmp_path / "g1-2026"
    informe = _anonimizar_de_ensayo(
        _material(tmp_path, con_suno=False), raiz, semilla=SEMILLA
    )
    assert informe["pistas"] == 6
    assert {p.name for p in (raiz / "04-sesion").glob("*.wav")} == {
        f"{b}-x{i}.wav" for b in BRIEFS_3 for i in (1, 2)
    }


# --------------------------------------------------------------------------- #
# Las tres vias por las que se rompe un ciego sin escuchar nada
# --------------------------------------------------------------------------- #

def test_el_nombre_del_fichero_no_dice_la_serie(tmp_path):
    raiz = tmp_path / "g1-2026"
    _anonimizar_de_ensayo(_material(tmp_path), raiz, semilla=SEMILLA)

    for pista in (raiz / "04-sesion").glob("*.wav"):
        assert g1_anonimizar.PATRON_ETIQUETA.fullmatch(pista.stem), pista.name
        minusculas = pista.name.lower()
        for serie in ("propia", "libreria", "suno", "pr", "li", "su"):
            assert serie not in minusculas.replace(".wav", "").split("-")[1:]


def test_el_orden_alfabetico_no_dice_la_serie(tmp_path):
    """La clave: la baraja es POR BRIEF, no global.

    Si fuera global, `x1` seria siempre la misma serie y descubrir una pista
    revelaria las treinta. Con diez briefs y tres series, una implementacion
    correcta reparte; una global da un unico valor en todas las posiciones.
    """
    raiz = tmp_path / "g1-2026"
    _anonimizar_de_ensayo(_material(tmp_path, briefs=BRIEFS_10), raiz, semilla=SEMILLA)
    mapa = _serie_por_etiqueta(raiz)

    for etiqueta in ("x1", "x2", "x3"):
        series_en_esa_posicion = {mapa[(b, etiqueta)] for b in BRIEFS_10}
        assert len(series_en_esa_posicion) > 1, (
            f"La etiqueta {etiqueta} cae siempre en {series_en_esa_posicion}: la baraja "
            "es global y no por brief."
        )

    permutaciones = {tuple(mapa[(b, e)] for e in ("x1", "x2", "x3")) for b in BRIEFS_10}
    assert len(permutaciones) > 1


def test_la_fecha_de_modificacion_no_dice_la_serie(tmp_path):
    """Se escriben en instantes distintos; salen todas con la misma marca."""
    raiz = tmp_path / "g1-2026"
    _anonimizar_de_ensayo(_material(tmp_path, briefs=BRIEFS_10), raiz, semilla=SEMILLA)

    marcas = {p.stat().st_mtime_ns for p in (raiz / "04-sesion").glob("*.wav")}
    assert len(marcas) == 1, "las fechas ordenan las pistas y el orden delata la serie"


# --------------------------------------------------------------------------- #
# Recodificacion uniforme y sin metadatos (§5.4.2)
# --------------------------------------------------------------------------- #

def test_el_wav_de_salida_no_lleva_ni_un_trozo_de_metadatos(tmp_path):
    """Un `LIST`/`INFO` o un `TSSE` delata el origen sin escuchar la pista."""
    raiz = tmp_path / "g1-2026"
    _anonimizar_de_ensayo(_material(tmp_path), raiz, semilla=SEMILLA)

    for pista in (raiz / "04-sesion").glob("*.wav"):
        assert _trozos_riff(pista) == ["fmt ", "data"], pista.name


def test_todas_salen_con_la_misma_cabecera_aunque_entren_distintas(tmp_path):
    """La libreria entra a 44,1 kHz y en mono; sale igual que las demas.

    Se comprueba tambien la DURACION, y no por completismo: reetiquetar la
    cabecera a 48 kHz sin remuestrear deja las cabeceras uniformes y la pista
    sonando un 8,8 % rapida y casi un semitono alta. Eso no solo delata la serie
    —es la unica que va desafinada—, es que ademas contamina D1 y D2 con un
    defecto nuestro.
    """
    raiz = tmp_path / "g1-2026"
    series = _material(tmp_path, tasa_libreria=44100, canales_libreria=1)
    _anonimizar_de_ensayo(series, raiz, semilla=SEMILLA)

    cabeceras = set()
    for pista in (raiz / "04-sesion").glob("*.wav"):
        matriz, tasa, ancho = g1_sonoridad.leer_wav(pista)
        cabeceras.add((tasa, matriz.shape[1], ancho))
        assert matriz.shape[0] / tasa == pytest.approx(1.5, abs=0.01), pista.name
    assert cabeceras == {(48000, 2, 2)}


# --------------------------------------------------------------------------- #
# Loudness de sesion (§5.5)
# --------------------------------------------------------------------------- #

def test_las_pistas_quedan_al_nivel_de_sesion(tmp_path):
    raiz = tmp_path / "g1-2026"
    _anonimizar_de_ensayo(_material(tmp_path), raiz, semilla=SEMILLA)

    for pista in (raiz / "04-sesion").glob("*.wav"):
        matriz, tasa, _ = g1_sonoridad.leer_wav(pista)
        assert g1_sonoridad.sonoridad_integrada(matriz, tasa) == pytest.approx(
            g1_sonoridad.OBJETIVO_LUFS_SESION, abs=0.2
        ), pista.name
        assert g1_sonoridad.pico_real_dbtp(matriz, tasa) <= (
            g1_sonoridad.TECHO_DBTP_SESION + 0.1
        ), pista.name


def test_una_pista_que_no_llega_al_objetivo_queda_registrada_y_no_recortada(tmp_path):
    """El caso de §5.5 que hay que poder leer en el acta, no adivinar."""
    series = _material(tmp_path)
    impulsos = np.zeros((48000 * 2, 2))
    impulsos[::1000, :] = 0.999
    g1_sonoridad.escribir_wav(series["libreria"] / "B01-li.wav", impulsos, 48000)

    raiz = tmp_path / "g1-2026"
    informe = _anonimizar_de_ensayo(series, raiz, semilla=SEMILLA)

    filas = {f["etiqueta_ciega"]: f for f in _leer_mapa(raiz) if f["brief"] == "B01"}
    capada = next(f for f in filas.values() if f["serie"] == "libreria")
    assert capada["objetivo_alcanzado"] == "no"
    assert capada["motivo"].strip()
    assert float(capada["lufs_final"]) < g1_sonoridad.OBJETIVO_LUFS_SESION
    assert informe["pistas_bajo_objetivo"] == 1

    matriz, tasa, _ = g1_sonoridad.leer_wav(raiz / "04-sesion" / f"B01-{capada['etiqueta_ciega']}.wav")
    assert float(np.max(np.abs(matriz))) < 1.0


def test_el_loudness_de_la_sesion_no_delata_el_nivel_de_origen(tmp_path):
    """El nivel de ORIGEN es un delator: un master a -9 LUFS solo puede ser la libreria.

    §5.5 pide anotar el valor medido en `04-sesion/loudness.csv`; ahi va el
    valor **final**, que es el que demuestra que la sesion esta igualada. El
    valor de origen, la ganancia aplicada y la serie viven dentro del sellado.
    """
    raiz = tmp_path / "g1-2026"
    _anonimizar_de_ensayo(_material(tmp_path), raiz, semilla=SEMILLA)

    texto = (raiz / "04-sesion" / "loudness.csv").read_text(encoding="utf-8")
    cabecera = texto.splitlines()[0].split(",")
    assert "serie" not in cabecera
    assert not [c for c in cabecera if "origen" in c or "ganancia" in c]
    for serie in ("propia", "libreria", "suno"):
        assert serie not in texto


# --------------------------------------------------------------------------- #
# Sellado del mapa (§5.4.4 y §5.6)
# --------------------------------------------------------------------------- #

def test_el_mapa_queda_sellado_con_sha256_y_su_leeme(tmp_path):
    raiz = tmp_path / "g1-2026"
    informe = _anonimizar_de_ensayo(_material(tmp_path), raiz, semilla=SEMILLA)

    ciego = raiz / "05-ciego"
    csv_ruta = ciego / g1_anonimizar.NOMBRE_MAPA
    digest = hashlib.sha256(csv_ruta.read_bytes()).hexdigest()

    # Misma convencion que `sellar_mapa` en g1_generar.py: `<nombre>.sha256`.
    assert (ciego / csv_ruta.with_suffix(".sha256").name).read_text(
        encoding="utf-8"
    ).startswith(digest)
    assert informe["sello_mapa"]["sha256"] == digest
    assert (ciego / g1_anonimizar.NOMBRE_LEEME).read_text(encoding="utf-8").strip()


def _claves(objeto) -> list[str]:
    if isinstance(objeto, dict):
        return [str(k) for k in objeto] + [c for v in objeto.values() for c in _claves(v)]
    if isinstance(objeto, (list, tuple)):
        return [c for v in objeto for c in _claves(v)]
    return []


def test_la_semilla_solo_vive_dentro_del_sellado(tmp_path):
    """Si la semilla se escapa, el ciego se reconstruye con dos lineas de python."""
    import json

    raiz = tmp_path / "g1-2026"
    informe = _anonimizar_de_ensayo(_material(tmp_path), raiz, semilla=SEMILLA)

    # El informe se imprime y se pega en el acta: ni la clave ni el valor.
    assert not [c for c in _claves(informe) if "semilla" in c.lower()]
    assert str(SEMILLA) not in json.dumps(informe, default=str)

    aguja = str(SEMILLA)
    fuera = [
        f for f in raiz.rglob("*")
        if f.is_file() and (raiz / "05-ciego") not in f.parents
        and aguja in f.read_bytes().decode("utf-8", "ignore")
    ]
    assert not fuera, f"la semilla aparece fuera de 05-ciego: {fuera}"

    sello = (raiz / "05-ciego" / g1_anonimizar.NOMBRE_SELLO).read_text(encoding="utf-8")
    assert aguja in sello, "la semilla tiene que quedar registrada, pero solo aqui"


def test_sin_semilla_explicita_se_sortea_una_distinta_cada_vez(tmp_path):
    import json

    semillas = set()
    for i in range(3):
        raiz = tmp_path / f"g1-{i}"
        _anonimizar_de_ensayo(_material(tmp_path / f"m{i}"), raiz)
        sello = json.loads((raiz / "05-ciego" / g1_anonimizar.NOMBRE_SELLO).read_text("utf-8"))
        semillas.add(sello["semilla"])
    assert len(semillas) == 3


def test_la_misma_semilla_reproduce_el_mismo_reparto(tmp_path):
    """Auditable: con la semilla del sello se puede rehacer y comprobar el mapa."""
    uno = tmp_path / "uno"
    dos = tmp_path / "dos"
    _anonimizar_de_ensayo(_material(tmp_path / "m"), uno, semilla=SEMILLA)
    _anonimizar_de_ensayo(_material(tmp_path / "m"), dos, semilla=SEMILLA)
    assert _serie_por_etiqueta(uno) == _serie_por_etiqueta(dos)


# --------------------------------------------------------------------------- #
# Superficie de linea de comandos
# --------------------------------------------------------------------------- #

def test_la_cli_no_deja_fijar_la_semilla(tmp_path):
    """La semilla se sortea. Un `--semilla` en el CLI seria una puerta trasera
    al ciego: quien la fija sabe el reparto sin abrir el sello."""
    with pytest.raises(SystemExit):
        g1_anonimizar.construir_parser().parse_args(
            ["--serie", "propia=x", "--salida", "y", "--semilla", "1"]
        )


def test_la_cli_anonimiza_de_punta_a_punta(tmp_path):
    series = _material(tmp_path)
    raiz = tmp_path / "g1-2026"
    # `--ensayo` porque el material son 3 briefs, no los 10 de §4. Sin la bandera
    # la CLI aborta, y hay un test justo debajo que lo comprueba.
    orden = [sys.executable, str(Path(g1_anonimizar.__file__)), "--salida", str(raiz), "--ensayo"]
    for nombre, ruta in series.items():
        orden += ["--serie", f"{nombre}={ruta}"]

    resultado = subprocess.run(orden, capture_output=True, text=True, timeout=600)
    assert resultado.returncode == 0, resultado.stderr
    assert len(list((raiz / "04-sesion").glob("*.wav"))) == 9
    assert "semilla" not in resultado.stdout.lower()


def test_la_cli_sin_ensayo_exige_los_diez_briefs(tmp_path):
    """La bandera no es cosmetica: sin ella, una tanda corta no se sella."""
    series = _material(tmp_path)
    raiz = tmp_path / "g1-corta"
    orden = [sys.executable, str(Path(g1_anonimizar.__file__)), "--salida", str(raiz)]
    for nombre, ruta in series.items():
        orden += ["--serie", f"{nombre}={ruta}"]
    resultado = subprocess.run(orden, capture_output=True, text=True, timeout=600)
    assert resultado.returncode == 1
    assert "B04" in resultado.stderr
    assert not (raiz / "05-ciego").exists(), "no se puede sellar una rejilla incompleta"


class TestElCsvDeSonoridadNoDelataLaSerie:
    """`04-sesion/loudness.csv` se puede abrir antes de puntuar. Que no delate.

    Con la normalizacion por ganancia pura, `lufs` queda clavado en el objetivo
    para todas las pistas — asi que no dice nada, bien. Pero `dbtp` sí: como
    `lufs` es constante, `dbtp` es exactamente el FACTOR DE CRESTA de la pista, y
    la cresta es justo lo que una ganancia constante NO altera. Un master de
    libreria comprimido y una pista propia sin comprimir tienen crestas muy
    distintas, y agrupan por serie a simple vista.

    Es el mismo tipo de fuga que la del informe con la semilla maestra: el dato
    no estaba pensado para delatar, pero delata.
    """

    def test_la_cabecera_no_publica_el_pico_por_pista(self):
        assert "dbtp" not in g1_anonimizar._CABECERA_LOUDNESS, (
            "con lufs constante, dbtp es el factor de cresta y agrupa por serie"
        )

    def test_sigue_publicando_lo_que_demuestra_que_la_sesion_esta_igualada(self):
        # Quitar la columna no puede convertir el fichero en algo inutil: §5.5
        # pide poder comprobar que todas las pistas estan al mismo nivel.
        assert "lufs" in g1_anonimizar._CABECERA_LOUDNESS
        assert "objetivo_lufs" in g1_anonimizar._CABECERA_LOUDNESS

    def test_el_techo_de_pico_se_sigue_declarando_como_politica_no_por_pista(self):
        # El techo es un parametro de la sesion, igual para todas: publicarlo no
        # distingue nada. Lo que delataba era el valor MEDIDO de cada pista.
        assert "techo_dbtp" in g1_anonimizar._CABECERA_LOUDNESS


class TestLaRejillaSeMideContraElProtocolo:
    """Un brief que falta en TODAS las series no deja hueco, y hoy pasa en silencio.

    `comprobar_rejilla` compara cada serie contra la UNION de los briefs
    presentes, asi que si B07 no esta en ninguna, la union tampoco lo tiene y la
    rejilla sale «completa». El script prepararia una sesion de 27 pistas sobre 9
    briefs y la sellaria tan contento.

    Y eso invalida el gate por §8.1: los umbrales de §2 se calculan sobre las
    **10** pistas propias («7 de las 10», «media sobre las 10»), no sobre las que
    hubiera. Una sesion de 9 mide otra cosa con el mismo nombre.
    """

    @staticmethod
    def _rejilla(briefs, series=("propia", "libreria")):
        from pathlib import Path

        return {s: {b: Path(f"{b}-{s}.wav") for b in briefs} for s in series}

    def test_las_diez_completas_pasan(self):
        diez = [f"B{i:02d}" for i in range(1, 11)]
        assert g1_anonimizar.comprobar_rejilla(self._rejilla(diez)) == diez

    def test_un_brief_ausente_en_todas_las_series_se_detecta(self):
        nueve = [f"B{i:02d}" for i in range(1, 11) if i != 7]
        with pytest.raises(ValueError, match="B07"):
            g1_anonimizar.comprobar_rejilla(self._rejilla(nueve))

    def test_el_mensaje_dice_que_el_gate_se_calcula_sobre_diez(self):
        ocho = [f"B{i:02d}" for i in range(1, 9)]
        with pytest.raises(ValueError) as info:
            g1_anonimizar.comprobar_rejilla(self._rejilla(ocho))
        assert "10" in str(info.value)

    def test_un_hueco_en_una_sola_serie_se_sigue_detectando(self):
        # Regresion de lo que ya funcionaba.
        diez = [f"B{i:02d}" for i in range(1, 11)]
        rejilla = self._rejilla(diez)
        del rejilla["libreria"]["B02"]
        with pytest.raises(ValueError, match="B02"):
            g1_anonimizar.comprobar_rejilla(rejilla)

    def test_se_puede_relajar_a_proposito_para_un_ensayo(self):
        # Probar el circuito con tres briefs es legitimo; hacerlo por descuido en
        # la tanda de verdad, no. Por eso se pide explicitamente.
        tres = ["B01", "B02", "B03"]
        assert g1_anonimizar.comprobar_rejilla(self._rejilla(tres), briefs_esperados=None) == tres
