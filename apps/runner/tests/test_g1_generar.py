"""Tests del kit de ejecucion de G1 (`spikes/g1_generar.py`).

Que se prueba aqui y por que importa
====================================
Este script produce el material sobre el que se decide un gate que bloquea
589 h. Sus fallos no son ruidosos: si lee mal la tabla de briefs, si deja pasar
una etiqueta de seccion que el modelo canta, o si el mapa ciego no cuadra con lo
generado, **el resultado sigue siendo un WAV que suena**. El error solo aparece
al interpretar el veredicto, cuando ya es tarde.

De ahi que los tests se concentren en las cuatro cosas que fallan en silencio:

1. **La lectura de §4 del protocolo real** — no de una copia de laboratorio. Si
   alguien reordena la tabla o sustituye un brief, estos tests lo notan.
2. **Los bloqueos de validacion de letra** — etiquetas canonicas y tildes. Cada
   uno costo una tanda de GPU el 2026-09-02.
3. **El ciego** — que la etiqueta no revele el indice de toma y que el sello del
   mapa sea el del contenido.
4. **La estimacion** — que salga de las mediciones y sea monotona.

Sin torch y sin GPU, como el resto de la suite.
"""

from __future__ import annotations

import csv
import hashlib
import inspect
import json
from pathlib import Path

import pytest

import g1_generar as g1

RAIZ_REPO = Path(__file__).resolve().parents[3]
PROTOCOLO = RAIZ_REPO / g1.PROTOCOLO_REL


# --------------------------------------------------------------------------- #
# §4: lectura de los briefs del protocolo REAL
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="module")
def briefs() -> list[g1.Brief]:
    if not PROTOCOLO.is_file():
        pytest.skip(f"no esta el protocolo en {PROTOCOLO}")
    return g1.leer_briefs(PROTOCOLO)


def test_lee_los_diez_briefs_del_protocolo_real(briefs):
    assert [b.id for b in briefs] == [f"B-{i:02d}" for i in range(1, 11)]


def test_los_seis_ejes_de_cada_brief_estan_poblados(briefs):
    """§4 dice que D1 se puntua contra seis ejes declarados. Si alguno llega
    vacio, D1 no es medible en ese brief y el gate mide menos de lo que cree."""
    for b in briefs:
        assert b.genero and b.instrumentacion and b.voz and b.uso_final, b.id
        assert b.bpm > 0, b.id
        assert b.duracion_s > 0, b.id
        assert b.idioma in ("es", "en"), b.id
        assert b.destino in ("streaming", "broadcast"), b.id


def test_reparto_de_la_muestra_comprobado_en_el_protocolo(briefs):
    """§4 declara literalmente «6 briefs en castellano / 4 en ingles · 4 destino
    broadcast / 6 streaming». Es una afirmacion verificable del documento: si la
    tabla cambia y esa frase no, este test lo detecta."""
    assert sum(1 for b in briefs if b.idioma == "es") == 6
    assert sum(1 for b in briefs if b.idioma == "en") == 4
    assert sum(1 for b in briefs if b.destino == "broadcast") == 4
    assert sum(1 for b in briefs if b.destino == "streaming") == 6


def test_duraciones_y_tempos_leidos_de_la_tabla(briefs):
    por_id = {b.id: b for b in briefs}
    # «**3:00**», «**45 s** con final resuelto (no *fade*)» y «**30 s exactos**»
    # son tres formatos distintos en la misma columna.
    assert por_id["B-02"].duracion_s == 180
    assert por_id["B-01"].duracion_s == 45
    assert por_id["B-06"].duracion_s == 30
    assert por_id["B-09"].duracion_s == 165
    assert por_id["B-07"].bpm == 140


@pytest.mark.parametrize(
    "celda, esperado",
    [
        ("**3:00**", 180),
        ("**2:30**", 150),
        ("**45 s** con final resuelto (no *fade*)", 45),
        ("**30 s exactos**", 30),
        ("**1:30**", 90),
    ],
)
def test_parsear_duracion(celda, esperado):
    assert g1._parsear_duracion(celda) == esperado


def test_parsear_duracion_prefiere_el_formato_mm_ss():
    """«1:30» son 90 s, no 1 s. El `\\d+ s` tambien casaria con el «30» si se
    comprobara primero, y devolveria 30."""
    assert g1._parsear_duracion("**1:30**") == 90


@pytest.mark.parametrize(
    "celda, esperado",
    [
        ("Masculina media, doblada en el estribillo · **castellano**", "es"),
        ("Femenina susurrada · **inglés**", "en"),
        ("Masculina potente · **español**", "es"),
    ],
)
def test_parsear_idioma(celda, esperado):
    assert g1._parsear_idioma(celda) == esperado


def test_una_tabla_incompleta_aborta_en_vez_de_generar_de_menos(tmp_path):
    """Un gate calculado sobre 8 briefs no es este gate: las medias de §2 se
    calculan sobre 10 y una muestra corta las cambia. Fallar es lo correcto."""
    falso = tmp_path / "g1-protocolo.md"
    filas = "\n".join(
        f"| **B-{i:02d}** | uso | genero | 100 BPM | instr | voz · **castellano** "
        f"| **30 s** | Streaming | exigencia |"
        for i in range(1, 9)
    )
    falso.write_text("| ID |\n|---|\n" + filas + "\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="10 briefs y se leyeron 8"):
        g1.leer_briefs(falso)


def test_protocolo_inexistente_lo_dice_claro(tmp_path):
    with pytest.raises(SystemExit, match="No se encontro el protocolo"):
        g1.leer_briefs(tmp_path / "no-existe.md")


# --------------------------------------------------------------------------- #
# §4.2: derivacion mecanica del prompt
# --------------------------------------------------------------------------- #

def test_el_prompt_no_repite_el_idioma_ni_arrastra_el_punto_medio(briefs):
    """La columna «Voz / idioma» trae «... · **castellano**». Si no se separa, el
    prompt acaba diciendo «voz masculina media · castellano, 112 BPM, cantado en
    castellano»: punto medio e idioma repetido, que el modelo tokeniza igual."""
    for b in briefs:
        prompt = g1.derivar_prompt_estilo(b)
        assert "·" not in prompt, b.id
        assert "**" not in prompt, b.id
        idioma = "castellano" if b.idioma == "es" else "ingles"
        assert prompt.count(idioma) == 1, (b.id, prompt)
        assert prompt.endswith(f"cantado en {idioma}"), b.id
        assert f"{b.bpm} BPM" in prompt, b.id


def test_el_prompt_es_estable(briefs):
    """§4.2: el mismo literal va a ACE-Step, a Suno, a la busqueda de libreria y
    a CLAP. Si no fuera determinista, esas cuatro cosas divergirian."""
    for b in briefs:
        assert g1.derivar_prompt_estilo(b) == g1.derivar_prompt_estilo(b)


def test_derivar_tonalidad_usa_el_caracter_declarado(briefs):
    por_id = {b.id: b for b in briefs}
    # «Cantautor / folk-pop melancolico»
    assert g1.derivar_tonalidad(por_id["B-02"])[0] == g1.TONICA_MENOR
    # «Folk oscuro / neomedieval, solemne»
    assert g1.derivar_tonalidad(por_id["B-03"])[0] == g1.TONICA_MENOR
    # «Indie-rock luminoso» — sin palabra de caracter menor
    assert g1.derivar_tonalidad(por_id["B-01"])[0] == g1.TONICA_MAYOR


def test_la_tonica_es_constante_y_el_motivo_lo_declara(briefs):
    """La tonica no la declara ningun brief: es convencion, y el informe tiene
    que decirlo para que nadie la lea como una decision musical."""
    tonicas = {g1.derivar_tonalidad(b)[0] for b in briefs}
    assert tonicas <= {g1.TONICA_MENOR, g1.TONICA_MAYOR}
    for b in briefs:
        assert "convencional" in g1.derivar_tonalidad(b)[1], b.id


# --------------------------------------------------------------------------- #
# §4.1: validacion de letras — los dos bloqueos que costaron GPU
# --------------------------------------------------------------------------- #

def _brief(idioma: str = "es", duracion: int = 30) -> g1.Brief:
    return g1.Brief(
        id="B-99", uso_final="prueba", genero="pop", bpm=100,
        instrumentacion="guitarra", voz="femenina", idioma=idioma,
        duracion_s=duracion, destino="streaming", exigencia="ninguna",
    )


def _escribir(tmp_path: Path, texto: str) -> Path:
    (tmp_path / "B-99.txt").write_text(texto, encoding="utf-8", newline="\n")
    return tmp_path


LETRA_CORTA_OK = "[verse]\nLa mañana se despierta con olor a pan caliente,\nrueda el día y el sol viene de frente.\n"
LETRA_LARGA_OK = (
    "[verse]\nCamina la mañana sobre el vidrio del andén,\nel día se despierta.\n\n"
    "[chorus]\nQuédate, que el sueño todavía no se fue.\n\n"
    "[verse]\nSe apaga la bombilla del pasillo al amanecer.\n"
)


def test_letra_valida_pasa(tmp_path):
    letra = g1.cargar_letra(_escribir(tmp_path, LETRA_CORTA_OK), _brief(), False)
    assert letra.valida, letra.errores


def test_etiqueta_de_estilo_suno_es_error_bloqueante(tmp_path):
    """«[VERSO 1 - HOMBRE, entra el beat]» viaja verbatim al modelo y se CANTA.
    Medido el 2026-09-02. No puede ser un aviso: una pista generada asi no se
    distingue por el nombre del fichero y contaminaria la sesion."""
    texto = "[VERSO 1 - HOMBRE, entra el beat]\nUna línea.\nOtra línea.\n"
    letra = g1.cargar_letra(_escribir(tmp_path, texto), _brief(), False)
    assert not letra.valida
    assert any("no canonicas" in e for e in letra.errores)


def test_etiqueta_canonica_en_mayusculas_tambien_es_error(tmp_path):
    """`[VERSE]` no es `[verse]` para un tokenizador."""
    texto = "[VERSE]\nUna línea.\nOtra línea.\n"
    letra = g1.cargar_letra(_escribir(tmp_path, texto), _brief(), False)
    assert not letra.valida
    assert any("mayusculas" in e for e in letra.errores)


def test_letra_sin_ninguna_etiqueta_es_error(tmp_path):
    letra = g1.cargar_letra(_escribir(tmp_path, "Una línea.\nOtra línea.\n"), _brief(), False)
    assert not letra.valida
    assert any("etiqueta de seccion" in e for e in letra.errores)


def test_castellano_sin_tildes_es_error(tmp_path):
    """«soñar» y «sonar» son palabras distintas y secuencias de tokens distintas.
    Hundiria el WER por un fallo nuestro, no del modelo."""
    texto = "[verse]\nLa cancion se apaga sin remedio,\ny el corazon no responde.\n"
    letra = g1.cargar_letra(_escribir(tmp_path, texto), _brief("es"), False)
    assert not letra.valida
    assert any("sin una sola tilde" in e for e in letra.errores)


def test_castellano_sin_tildes_pasa_a_aviso_con_la_bandera(tmp_path):
    texto = "[verse]\nLa cancion se apaga sin remedio,\ny el corazon no responde.\n"
    letra = g1.cargar_letra(_escribir(tmp_path, texto), _brief("es"), True)
    assert letra.valida
    assert any("--permitir-sin-tildes" in a for a in letra.avisos)


def test_ingles_sin_tildes_no_se_penaliza(tmp_path):
    texto = "[verse]\nThe morning finds the window,\nand it breaks across the floor.\n"
    letra = g1.cargar_letra(_escribir(tmp_path, texto), _brief("en"), False)
    assert letra.valida, letra.errores


def test_brief_largo_exige_dos_estrofas_y_un_estribillo(tmp_path):
    """§4.1 para duracion >= 1:30."""
    corta = g1.cargar_letra(_escribir(tmp_path, LETRA_CORTA_OK), _brief("es", 150), False)
    assert not corta.valida
    assert any("dos estrofas y un estribillo" in e for e in corta.errores)

    larga = g1.cargar_letra(_escribir(tmp_path, LETRA_LARGA_OK), _brief("es", 150), False)
    assert larga.valida, larga.errores


def test_brief_corto_exige_dos_frases(tmp_path):
    texto = "[verse]\nUna sola línea.\n"
    letra = g1.cargar_letra(_escribir(tmp_path, texto), _brief("es", 30), False)
    assert not letra.valida
    assert any("al menos dos frases" in e for e in letra.errores)


def test_letra_ausente_no_se_inventa(tmp_path):
    """§4.1 y §9.1 ponen las letras del lado del propietario."""
    letra = g1.cargar_letra(tmp_path, _brief(), False)
    assert not letra.valida
    assert any("falta la letra" in e for e in letra.errores)
    assert letra.texto == ""


def test_referencia_wer_quita_las_marcas_y_conserva_tildes():
    """§4.1: «la referencia de WER es la version sin marcas». Las tildes se
    conservan (§6.2 lo dice explicitamente en la normalizacion)."""
    referencia = g1._referencia_wer(LETRA_LARGA_OK)
    assert "[verse]" not in referencia and "[chorus]" not in referencia
    assert "mañana" in referencia and "andén" in referencia
    assert "\n\n" not in referencia  # sin lineas en blanco


# --------------------------------------------------------------------------- #
# Ciego: etiquetas opacas, semillas y sello del mapa
# --------------------------------------------------------------------------- #

def test_la_etiqueta_ciega_es_opaca_y_del_formato_esperado():
    etiquetas = [g1._testigo(20260902, "B-01", i) for i in (1, 2, 3)]
    assert len(set(etiquetas)) == 3
    for e in etiquetas:
        assert len(e) == 6 and all(c in "0123456789abcdef" for c in e)


def test_ordenar_las_etiquetas_no_reconstruye_el_indice_de_toma():
    """El ataque realista contra este ciego es ordenar los ficheros por nombre y
    suponer que ese orden es 1, 2, 3. Tiene que acertar como acertaria el azar
    (1 de 6), no siempre.

    Se mide sobre 300 semillas maestras en vez de sobre una: con un solo caso,
    un testigo que ordenara perfectamente pasaria el test 1 de cada 6 veces por
    pura suerte, que es justo el fallo que se quiere descartar.
    """
    aciertos = 0
    intentos = 300
    for semilla in range(intentos):
        etiquetas = [g1._testigo(semilla, "B-01", i) for i in (1, 2, 3)]
        if etiquetas == sorted(etiquetas):
            aciertos += 1
    tasa = aciertos / intentos
    # 1/6 = 0,167. El intervalo es holgado a proposito: lo que se descarta es un
    # testigo ordenado (tasa 1,0) o degenerado (tasa 0,0), no una desviacion de
    # muestreo.
    assert 0.08 < tasa < 0.28, f"tasa de reconstruccion por orden alfabetico: {tasa}"


def test_etiquetas_y_semillas_son_reproducibles_y_distintas_por_brief():
    """Una repeticion de §8.5 con la misma semilla maestra tiene que reproducir
    la serie entera; briefs distintos no pueden compartir semilla."""
    assert g1._testigo(1, "B-01", 1) == g1._testigo(1, "B-01", 1)
    assert g1._testigo(1, "B-01", 1) != g1._testigo(2, "B-01", 1)
    assert g1._testigo(1, "B-01", 1) != g1._testigo(1, "B-02", 1)
    semillas = {g1._semilla_toma(7, f"B-{i:02d}", t) for i in range(1, 11) for t in (1, 2, 3)}
    assert len(semillas) == 30
    assert all(0 <= s < 2 ** 31 for s in semillas)


def test_el_plan_baraja_dentro_del_brief_y_es_reproducible(briefs):
    plan_a = g1.construir_plan(briefs, 3, 20260902)
    plan_b = g1.construir_plan(briefs, 3, 20260902)
    assert [t.etiqueta_ciega for t in plan_a] == [t.etiqueta_ciega for t in plan_b]
    assert len(plan_a) == 30

    # Los briefs salen en orden (para que --desde sirva)...
    orden_briefs = [t.brief_id for t in plan_a]
    assert orden_briefs == sorted(orden_briefs)
    # ...pero el indice de toma dentro de cada brief, no siempre.
    indices = {}
    for t in plan_a:
        indices.setdefault(t.brief_id, []).append(t.indice)
    assert all(sorted(v) == [1, 2, 3] for v in indices.values())
    assert any(v != [1, 2, 3] for v in indices.values()), "el barajado no hizo nada"


def test_otra_semilla_maestra_da_otro_barajado(briefs):
    a = [t.etiqueta_ciega for t in g1.construir_plan(briefs, 3, 1)]
    b = [t.etiqueta_ciega for t in g1.construir_plan(briefs, 3, 2)]
    assert a != b


def test_el_sello_del_mapa_es_el_del_contenido(tmp_path, briefs):
    plan = g1.construir_plan(briefs, 3, 20260902)
    filas = [
        {"brief": t.brief_id, "etiqueta_ciega": t.etiqueta_ciega, "indice_toma": t.indice,
         "orden_generacion": i, "semilla": t.semilla, "fichero": f"{t.etiqueta_ciega}.wav",
         "duracion_pedida_s": t.duracion_s, "duracion_real_s": t.duracion_s, "generada": "si"}
        for i, t in enumerate(plan, 1)
    ]
    sello = g1.sellar_mapa(tmp_path, filas, 20260902)
    csv_ruta = tmp_path / "05-ciego" / "mapa-tomas.csv"
    assert sello["sha256"] == hashlib.sha256(csv_ruta.read_bytes()).hexdigest()
    assert sello["filas"] == 30
    # El fichero que consume `sha256sum -c` tiene su formato.
    linea = (tmp_path / "05-ciego" / "mapa-tomas.sha256").read_text(encoding="utf-8")
    assert linea == f"{sello['sha256']}  mapa-tomas.csv\n"
    assert (tmp_path / "05-ciego" / "LEEME-NO-ABRIR.txt").is_file()
    assert json.loads((tmp_path / "05-ciego" / "sello.json").read_text(encoding="utf-8"))


def test_el_mapa_se_ordena_por_etiqueta_y_no_por_orden_de_generacion(tmp_path, briefs):
    """Si el CSV se escribiera en orden de generacion, abrirlo de reojo ya daria
    ese orden. Se ordena por la etiqueta, que es opaca."""
    plan = g1.construir_plan(briefs, 3, 20260902)
    filas = [
        {"brief": t.brief_id, "etiqueta_ciega": t.etiqueta_ciega, "indice_toma": t.indice,
         "orden_generacion": i, "semilla": t.semilla, "fichero": "", "generada": "si"}
        for i, t in enumerate(plan, 1)
    ]
    g1.sellar_mapa(tmp_path, filas, 1)
    with (tmp_path / "05-ciego" / "mapa-tomas.csv").open(encoding="utf-8", newline="") as f:
        leidas = list(csv.DictReader(f))
    etiquetas = [f["etiqueta_ciega"] for f in leidas]
    assert etiquetas == sorted(etiquetas)


# --------------------------------------------------------------------------- #
# Estimacion
# --------------------------------------------------------------------------- #

def test_el_modelo_de_tiempo_sale_de_las_mediciones():
    modelo = g1.modelo_de_tiempo()
    assert set(modelo) == {"optimista", "central", "pesimista"}
    # La pendiente es el dato robusto: las tres rectas coinciden en ~2,7 s de
    # computo por segundo de audio. Si alguna se fuera de ese entorno, la tabla
    # de mediciones se ha tocado sin recalibrar el texto que la explica.
    for nombre, (_, b) in modelo.items():
        assert 2.5 < b < 3.0, (nombre, b)


def test_la_estimacion_es_monotona_y_ordenada(briefs):
    est = g1.estimar(briefs, 3)
    esc = est["escenarios"]
    assert esc["optimista"]["total_s"] < esc["central"]["total_s"] < esc["pesimista"]["total_s"]
    assert est["pistas"] == 30
    assert est["audio_total_s"] == sum(b.duracion_s for b in briefs) * 3
    # Mas tomas, mas tiempo; y la carga se paga una sola vez.
    una = g1.estimar(briefs, 1)
    assert una["escenarios"]["central"]["carga_s"] == esc["central"]["carga_s"]
    assert esc["central"]["computo_s"] == pytest.approx(
        una["escenarios"]["central"]["computo_s"] * 3, rel=1e-6
    )


def test_la_estimacion_publica_la_procedencia_de_cada_medicion(briefs):
    """Una cifra de tiempo sin decir de donde sale no se puede recalibrar en otra
    maquina: se adivina un factor. Aqui van los 9 informes de origen."""
    est = g1.estimar(briefs, 3)
    assert len(est["mediciones_usadas"]) == len(g1.MEDICIONES_TIER3) == 9
    assert all(m["informe"].endswith(".json") for m in est["mediciones_usadas"])


def test_texto_de_la_estimacion_menciona_los_tres_escenarios(briefs):
    texto = g1.texto_estimacion(g1.estimar(briefs, 3), 3)
    for nombre in ("optimista", "central", "pesimista"):
        assert nombre in texto
    assert "30 pistas" in texto


# --------------------------------------------------------------------------- #
# Nivel de GPU y artefactos de §10.2
# --------------------------------------------------------------------------- #

def test_detectar_gpu_sin_cuda_no_revienta():
    """El ensayo en seco tiene que poder correrse en el portatil."""
    datos = g1.detectar_gpu()
    assert isinstance(datos, dict)
    assert "detectado" in datos
    if not datos["detectado"]:
        assert datos["motivo"]


def test_escribir_briefs_deja_utf8_con_saltos_lf(tmp_path, briefs):
    """Los ficheros de `01-briefs/` son artefactos del protocolo: su hash tiene
    que ser el mismo se generen en Windows o en el contenedor."""
    dir_letras = tmp_path / "letras"
    dir_letras.mkdir()
    subconjunto = briefs[:1]
    b = subconjunto[0]
    (dir_letras / f"{b.id}.txt").write_text(LETRA_LARGA_OK, encoding="utf-8", newline="\n")
    letras = {b.id: g1.cargar_letra(dir_letras, b, False)}
    prompts = {b.id: g1.derivar_prompt_estilo(b)}
    metas = {b.id: {"bpm": b.bpm, "keyscale": "A minor", "keyscale_motivo": "x",
                    "timesignature": "4/4", "prompt_origen": "derivado"}}
    raiz = tmp_path / "g1-2026"
    g1.escribir_briefs(raiz, subconjunto, prompts, letras, metas)

    for sufijo in ("prompt.txt", "letra.txt", "letra-referencia-wer.txt", "brief.json"):
        ruta = raiz / "01-briefs" / f"{b.id}.{sufijo}"
        assert ruta.is_file(), ruta
        assert b"\r" not in ruta.read_bytes(), f"{ruta} lleva CRLF"
    ficha = json.loads((raiz / "01-briefs" / f"{b.id}.brief.json").read_text(encoding="utf-8"))
    assert ficha["prompt_estilo"] == prompts[b.id]
    assert ficha["letra_sha256"] == hashlib.sha256(
        LETRA_LARGA_OK.encode("utf-8")
    ).hexdigest()


def _letras_completas(destino: Path, briefs: list[g1.Brief]) -> Path:
    """Escribe 10 letras validas de relleno para poder ejercitar `main()`."""
    destino.mkdir(parents=True, exist_ok=True)
    for b in briefs:
        texto = LETRA_LARGA_OK if b.duracion_s >= 90 else LETRA_CORTA_OK
        (destino / f"{b.id}.txt").write_text(texto, encoding="utf-8", newline="\n")
    return destino


def test_extra_sobreescribe_bpm_en_el_prompt_y_en_los_metadatos(tmp_path, briefs):
    """Regresion. El `bpm` de --extra se aplicaba a `metas` pero NO al prompt ni
    a los `model_params` de la generacion, que leian `brief.bpm` crudo: el prompt
    pedia 110 BPM y el bloque de metas decia 118. Es exactamente la contradiccion
    que el 2026-09-02 se arreglo poblando las metas, reintroducida por la puerta
    de atras. El fallo no da error: da una pista a un tempo indeterminado."""
    letras = _letras_completas(tmp_path / "letras", briefs)
    extra = tmp_path / "extra.json"
    extra.write_text(
        json.dumps({"B-10": {"keyscale": "F# minor", "bpm": 118}}), encoding="utf-8"
    )
    plan = tmp_path / "plan.json"
    codigo = g1.main([
        "--dry-run", "--letras", str(letras), "--extra", str(extra),
        "--plan-json", str(plan), "--protocolo", str(PROTOCOLO),
    ])
    assert codigo == 0
    datos = json.loads(plan.read_text(encoding="utf-8"))

    meta = datos["metadatos_musicales"]["B-10"]
    assert meta["bpm"] == 118
    assert meta["bpm_origen"] == "--extra"
    assert meta["keyscale"] == "F# minor"
    # Lo que de verdad importa: el prompt tiene que decir lo mismo.
    assert "118 BPM" in datos["prompts_estilo"]["B-10"]
    assert "110 BPM" not in datos["prompts_estilo"]["B-10"]
    # Y el brief efectivo que se archiva, tambien.
    assert [b["bpm"] for b in datos["briefs"] if b["id"] == "B-10"] == [118]
    # Un brief sin sobreescritura no se toca.
    assert datos["metadatos_musicales"]["B-01"]["bpm_origen"].startswith("columna")


def test_main_en_dry_run_no_escribe_en_la_raiz_de_evaluacion(tmp_path, briefs):
    """El ensayo en seco no puede dejar rastro: si escribiera `01-briefs/`, una
    ejecucion de prueba pisaria material de una sesion en curso."""
    letras = _letras_completas(tmp_path / "letras", briefs)
    raiz = tmp_path / "g1-2026"
    codigo = g1.main([
        "--dry-run", "--letras", str(letras), "--raiz-evaluacion", str(raiz),
        "--protocolo", str(PROTOCOLO),
    ])
    assert codigo == 0
    assert not raiz.exists()


def test_main_bloquea_con_codigo_3_si_falta_una_letra(tmp_path, briefs):
    letras = _letras_completas(tmp_path / "letras", briefs)
    (letras / "B-04.txt").unlink()
    raiz = tmp_path / "g1-2026"
    codigo = g1.main([
        "--dry-run", "--letras", str(letras), "--raiz-evaluacion", str(raiz),
        "--protocolo", str(PROTOCOLO),
    ])
    assert codigo == 3
    assert not raiz.exists()


def test_main_marca_la_sesion_como_no_conforme_con_una_sola_toma(tmp_path, briefs):
    """§5.2 fija 3 tomas. Con 1 no hay eleccion que hacer, y eso tiene que
    quedar escrito en el informe, no solo en la consola."""
    letras = _letras_completas(tmp_path / "letras", briefs)
    plan = tmp_path / "plan.json"
    assert g1.main([
        "--dry-run", "--letras", str(letras), "--tomas", "1",
        "--plan-json", str(plan), "--protocolo", str(PROTOCOLO),
    ]) == 0
    datos = json.loads(plan.read_text(encoding="utf-8"))
    assert datos["conformidad"]["tomas_conforme_5_2"] is False
    assert any("no_conforme_5_2" in a for a in datos["avisos_conformidad"])
    assert len(datos["plan_orden_generacion"]) == 10


def test_main_marca_serie_parcial_con_solo(tmp_path, briefs):
    letras = _letras_completas(tmp_path / "letras", briefs)
    plan = tmp_path / "plan.json"
    assert g1.main([
        "--dry-run", "--letras", str(letras), "--solo", "B-03,B-07",
        "--plan-json", str(plan), "--protocolo", str(PROTOCOLO),
    ]) == 0
    datos = json.loads(plan.read_text(encoding="utf-8"))
    assert datos["conformidad"]["briefs_completos"] is False
    assert any("SERIE PARCIAL" in a for a in datos["avisos_conformidad"])
    assert len(datos["plan_orden_generacion"]) == 6


def test_el_informe_registra_el_sha256_del_protocolo_leido(tmp_path, briefs):
    """§4 declara los briefs «propuestos, pendientes de ratificacion»: el
    propietario puede sustituir alguno antes de generar. El acta tiene que poder
    demostrar CONTRA QUE VERSION del protocolo se genero."""
    letras = _letras_completas(tmp_path / "letras", briefs)
    plan = tmp_path / "plan.json"
    assert g1.main([
        "--dry-run", "--letras", str(letras),
        "--plan-json", str(plan), "--protocolo", str(PROTOCOLO),
    ]) == 0
    datos = json.loads(plan.read_text(encoding="utf-8"))
    esperado = hashlib.sha256(PROTOCOLO.read_bytes()).hexdigest()
    assert datos["protocolo"]["sha256"] == esperado


def test_el_planificador_no_se_puede_apagar_desde_la_linea_de_ordenes():
    """El efecto medido del planificador de 5 Hz es del 60,7 % frente al 1-7 %
    del ruido de semilla: apagarlo cambiaria lo que el gate juzga. `--sin-lm`
    existe en generate_smoke.py para el A/B; aqui NO debe existir."""
    banderas = {
        accion.option_strings[0]
        for accion in g1.construir_parser()._actions
        if accion.option_strings
    }
    assert "--sin-lm" not in banderas
    assert "--dry-run" in banderas


# --------------------------------------------------------------------------- #
# El bloque de modelo del manifiesto (§10.2)
# --------------------------------------------------------------------------- #

def _informe_adapter(fichero_pesos: str) -> dict:
    """Recorte de `AceStepAdapter.describe()` con lo unico que mira el manifiesto."""
    return {
        "tarea": "T-05",
        "source": "gpu",
        "model_id": "ace-step",
        "model_version": "1.5",
        "weights_file": fichero_pesos,
        "weights_path": f"/weights/{fichero_pesos}",
    }


def test_el_bloque_de_modelo_no_dice_turbo_con_el_artefacto_sft():
    """El manifiesto es la trazabilidad de G1: no puede afirmar lo que no paso.

    `--fichero-pesos` ya permite generar con cualquiera de los tres artefactos
    de disco. Con el `sft` y sin planificador, un manifiesto que siguiera
    diciendo «turbo, artefacto con planificador de 5 Hz» seria una mentira
    silenciosa: no falla, no avisa, y el acta del gate la da por buena.
    """
    bloque = g1._descripcion_modelo(
        _informe_adapter("ace_step_1_5_sft_lm.safetensors"),
        {"variante": "sft", "usar_lm": False, "bpm": 96, "lm_cfg": 2.0},
    )
    plano = json.dumps(bloque, ensure_ascii=False).lower()
    assert "turbo" not in plano
    assert "con planificador" not in plano
    assert bloque["modelo_variante"] == "sft"
    assert bloque["planificador_5hz"] == "no"
    assert "ace_step_1_5_sft_lm.safetensors" in bloque["modelo"]
    assert "ace-step" in bloque["modelo"] and "1.5" in bloque["modelo"]


def test_el_bloque_de_modelo_declara_el_turbo_con_planificador_cuando_lo_hubo():
    """La otra mitad: con el artefacto de produccion tiene que decirlo."""
    bloque = g1._descripcion_modelo(
        _informe_adapter("ace_step_1_5_lm.safetensors"),
        {"variante": "turbo", "usar_lm": True},
    )
    assert bloque["modelo_variante"] == "turbo"
    assert bloque["planificador_5hz"] == "si"
    assert "ace_step_1_5_lm.safetensors" in bloque["modelo"]


def test_el_bloque_de_modelo_escribe_desconocido_en_vez_de_inventar():
    """Sin dato no hay afirmacion. Un `desconocido` se audita; un valor
    inventado se cree."""
    bloque = g1._descripcion_modelo({}, {})
    assert bloque["modelo_variante"] == "desconocido"
    assert bloque["planificador_5hz"] == "desconocido"
    assert "turbo" not in bloque["modelo"]
    assert "con planificador" not in bloque["modelo"]
    assert bloque["modelo"].count("desconocido") >= 3


def test_el_manifiesto_deriva_el_modelo_en_vez_de_clavarlo():
    """Guardarrail de la regresion concreta: el modelo del manifiesto se
    construia con un literal `"ACE-Step 1.5 (turbo, ...)"` mientras los pesos
    venian de `--fichero-pesos`. Ningun nombre de variante puede volver a
    aparecer clavado en el bucle de generacion."""
    fuente = inspect.getsource(g1.generar)
    assert "_descripcion_modelo(" in fuente
    # Se prohibe el LITERAL que describia el modelo, no la palabra: declarar la
    # variante del gate (`"variante": VARIANTE_G1`) es justo lo que hay que
    # hacer, y una prohibicion por palabra lo bloquearia.
    assert "ACE-Step 1.5 (turbo" not in fuente
    assert "artefacto con planificador" not in fuente


# --------------------------------------------------------------------------- #
# La variante de difusion, declarada y coherente con los pesos
# --------------------------------------------------------------------------- #

class TestVarianteDeclarada:
    """G1 se genera con el artefacto turbo, y eso tiene que estar DICHO.

    El shim resuelve la variante con `params.get("variante") or "turbo"`, asi que
    hasta ahora el bucle de difusion corria programacion turbo (8 pasos, sin
    guia) aunque se cargaran los pesos sft, que esperan 50 pasos con guia APG.
    Los dos checkpoints tienen las mismas claves con las mismas formas: no da
    error, da audio peor. Como el gate no puede depender de que nadie se
    equivoque de fichero, la variante se declara explicita y una guardia rechaza
    un artefacto que la contradiga.
    """

    def test_la_variante_del_gate_es_turbo(self):
        assert g1.VARIANTE_G1 == "turbo"

    def test_el_bucle_de_generacion_declara_la_variante(self):
        # Sin esto, el manifiesto dice "desconocido" en toda tanda real y el
        # shim decide por su cuenta.
        assert '"variante": VARIANTE_G1' in inspect.getsource(g1.generar)

    @pytest.mark.parametrize(
        "fichero",
        ["ace_step_1_5_sft_lm.safetensors", "ACE_STEP_1_5_SFT_LM.safetensors", "x-sft-y.safetensors"],
    )
    def test_unos_pesos_sft_se_rechazan_antes_de_generar(self, fichero):
        with pytest.raises(SystemExit) as info:
            g1.comprobar_pesos_de_la_variante(fichero)
        assert "sft" in str(info.value).lower()
        assert "turbo" in str(info.value).lower()

    @pytest.mark.parametrize(
        "fichero",
        ["ace_step_1_5_lm.safetensors", "ace_step_1_5.safetensors", "mi_artefacto_turbo.safetensors"],
    )
    def test_los_pesos_sin_marca_de_otra_variante_pasan(self, fichero):
        assert g1.comprobar_pesos_de_la_variante(fichero) is None

    def test_el_manifiesto_de_una_tanda_real_dice_la_variante_y_no_desconocido(self):
        # Regresion del hueco que dejaba el arreglo anterior: el campo existia
        # pero salia "desconocido" SIEMPRE, porque nadie lo declaraba.
        params = {"usar_lm": True, "variante": g1.VARIANTE_G1}
        informe = {"model_id": "ace-step", "model_version": "1.5",
                   "weights_file": "ace_step_1_5_lm.safetensors"}
        bloque = g1._descripcion_modelo(informe, params)
        assert bloque["modelo_variante"] == "turbo"
        assert "desconocido" not in bloque["modelo"]
