"""
Paso 7: procesa la guía descargada (XMLTV):
  - convierte los horarios a hora de Chile
  - cataloga cada programa en una categoría propia
  - deja los datos listos para la página web (datos/guia.json)

Uso:  python paso7_procesar.py datos/guia_prueba_cl.xml
"""
import json
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

CARPETA_DATOS = Path("datos")
ARCHIVO_CORRECCIONES = Path("correcciones.txt")
ZONA_CHILE = ZoneInfo("America/Santiago")
DIAS_GUIA = 7
LARGO_MAX_DESCRIPCION = 400

CATEGORIAS = [
    "Películas", "Series", "Deportes", "Noticias", "Documentales", "Infantil",
    "Música", "Entretenimiento", "Cultura y educación", "Política", "Religión", "Otros",
]

# Palabras clave (sin tildes, en minúsculas) -> categoría propia.
# Cada palabra debe aparecer al INICIO de una palabra del texto
# (así "arte" no coincide con "parte"). "\b" al final exige palabra exacta.
# Se revisan en este orden: la primera categoría que coincide gana.
REGLAS = [
    ("Infantil", [r"infantil", r"animacion", r"animad", r"dibujos", r"caricatura", r"ninos\b",
                  r"kids\b", r"preescolar"]),
    ("Películas", [r"pelicula", r"cine\b", r"cinema", r"film", r"largometraje", r"movie"]),
    ("Noticias", [r"noticia", r"noticiero", r"informativo", r"periodistic", r"news\b", r"actualidad",
                  r"reportaje", r"telediario", r"edicion central", r"24 horas", r"el tiempo\b",
                  r"pronostico", r"meteorolog", r"economi"]),
    ("Política", [r"politic", r"senado", r"camara de diputados", r"congreso", r"parlament",
                  r"legislativ", r"sesion de sala"]),
    ("Deportes", [r"deport", r"futbol", r"partido\b", r"liga\b", r"copa\b", r"tenis\b", r"basquet",
                  r"boxeo", r"automovilismo", r"formula 1", r"hipica", r"carreras\b", r"sports?\b",
                  r"olimpic", r"mundial\b", r"golf\b", r"rugby", r"ciclismo", r"voleibol", r"nba\b",
                  r"nfl\b", r"ufc\b", r"lucha libre"]),
    ("Documentales", [r"documental", r"documentary", r"naturaleza\b"]),
    ("Religión", [r"religio", r"misa\b", r"iglesia", r"evangel", r"biblia", r"oracion", r"culto\b",
                  r"predica", r"cristian", r"catolic", r"adventista", r"devocional"]),
    ("Música", [r"music", r"musica", r"concierto", r"videoclip", r"karaoke", r"hits\b"]),
    ("Series", [r"serie", r"telenovela", r"novela", r"teleserie", r"sitcom", r"drama", r"comedia"]),
    ("Cultura y educación", [r"cultura", r"educa", r"artes?\b", r"turismo", r"viaje", r"gastronom",
                             r"cocina", r"receta", r"ciencia", r"tecnolog", r"aprende"]),
    ("Entretenimiento", [r"entreten", r"variedad", r"magazine", r"matinal", r"espectaculo",
                         r"farandula", r"reality", r"concurso", r"estelar", r"humor", r"talk show",
                         r"interes general", r"estilo de vida", r"lifestyle", r"juego", r"show\b"]),
    ("Otros", [r"publicidad", r"televenta", r"infomercial", r"teletienda", r"fin de transmision"]),
]
REGLAS = [(cat, re.compile(r"\b(?:" + "|".join(palabras) + ")")) for cat, palabras in REGLAS]

# Categoría del CANAL en la lista M3U -> categoría propia (último recurso)
CATEGORIA_CANAL = {
    "Movies": "Películas", "Series": "Series", "Sports": "Deportes", "News": "Noticias",
    "Documentary": "Documentales", "Kids": "Infantil", "Animation": "Infantil",
    "Music": "Música", "Entertainment": "Entretenimiento", "Comedy": "Entretenimiento",
    "Lifestyle": "Entretenimiento", "Cooking": "Cultura y educación", "Travel": "Cultura y educación",
    "Culture": "Cultura y educación", "Education": "Cultura y educación", "Science": "Documentales",
    "Outdoor": "Documentales", "Legislative": "Política", "Religious": "Religión", "Shop": "Otros",
}

PATRON_EPISODIO = re.compile(r"temporada\s*\d+|episodio\s*\d+|capitulo\s*\d+|\bt\d+\s*e\d+", re.I)


def normalizar(texto):
    """Quita tildes y pasa a minúsculas: 'Película' -> 'pelicula'."""
    texto = unicodedata.normalize("NFD", texto or "")
    return "".join(c for c in texto if unicodedata.category(c) != "Mn").lower()


def buscar_regla(texto):
    texto = normalizar(texto)
    for categoria, patron in REGLAS:
        if patron.search(texto):
            return categoria
    return None


def leer_correcciones():
    """Lee correcciones.txt: líneas 'Título = Categoría'. Devuelve {titulo_normalizado: categoría}."""
    correcciones = {}
    if not ARCHIVO_CORRECCIONES.exists():
        return correcciones
    for n, linea in enumerate(ARCHIVO_CORRECCIONES.read_text(encoding="utf-8").splitlines(), 1):
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        titulo, _, categoria = linea.rpartition("=")
        titulo, categoria = titulo.strip(), categoria.strip()
        if categoria not in CATEGORIAS or not titulo:
            print(f"  Aviso: correcciones.txt línea {n} ignorada: {linea}")
            continue
        correcciones[normalizar(titulo)] = categoria
    return correcciones


CORRECCIONES = {}


def categorizar(cats_fuente, titulo, descripcion, cat_canal):
    """Devuelve (categoría, origen): 'manual', 'fuente', 'deducida', 'canal' o 'sin datos'."""
    # 0) Corrección manual (correcciones.txt): si el título empieza con el texto indicado
    titulo_norm = normalizar(titulo)
    for texto, categoria in CORRECCIONES.items():
        if titulo_norm.startswith(texto):
            return categoria, "manual"
    # 1) La categoría que trae la fuente (si no es en realidad info del episodio)
    for cat in cats_fuente:
        if not PATRON_EPISODIO.search(normalizar(cat)):
            encontrada = buscar_regla(cat)
            if encontrada:
                return encontrada, "fuente"
    # 2) Deducir del título y luego de la descripción
    for texto in (titulo, descripcion):
        encontrada = buscar_regla(texto)
        if encontrada:
            return encontrada, "deducida"
    # 3) Si traía info de temporada/episodio, es una serie
    if any(PATRON_EPISODIO.search(normalizar(c)) for c in cats_fuente + [titulo]):
        return "Series", "deducida"
    # 4) Usar la categoría del canal
    for cat in (cat_canal or "").split(";"):
        if cat in CATEGORIA_CANAL:
            return CATEGORIA_CANAL[cat], "canal"
    return "Otros", "sin datos"


def leer_fecha(texto):
    """'20261026060000 +0000' -> fecha y hora en Chile."""
    return datetime.strptime(texto.strip(), "%Y%m%d%H%M%S %z").astimezone(ZONA_CHILE)


def main():
    archivo_guia = sys.argv[1] if len(sys.argv) > 1 else "datos/guia.xml"
    CORRECCIONES.update(leer_correcciones())
    canales_m3u = json.loads((CARPETA_DATOS / "canales.json").read_text(encoding="utf-8"))

    # Datos de cada canal de la lista M3U (por id sin variante)
    info_canal = {}
    for c in canales_m3u:
        info_canal.setdefault(c["id_guia"].split("@")[0], c)

    ahora = datetime.now(ZONA_CHILE)
    limite = ahora.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=DIAS_GUIA + 1)

    raiz = ET.parse(archivo_guia).getroot()
    canales = []          # lista de canales que salen en la guía
    indice_canal = {}     # id -> posición en la lista
    programas = []
    origen = Counter()
    sin_categoria = Counter()

    for p in raiz.iter("programme"):
        id_canal = p.get("channel", "").split("@")[0]
        canal = info_canal.get(id_canal)
        if canal is None:
            continue
        inicio, fin = leer_fecha(p.get("start")), leer_fecha(p.get("stop"))
        if fin <= ahora or inicio >= limite:
            continue

        titulo = (p.findtext("title") or "").strip()
        descripcion = (p.findtext("desc") or "").strip()
        cats_fuente = [(c.text or "").strip() for c in p.findall("category") if c.text]
        episodio = next((c for c in cats_fuente if PATRON_EPISODIO.search(normalizar(c))), "")

        categoria, de_donde = categorizar(cats_fuente, titulo, descripcion, canal["categoria"])
        origen[de_donde] += 1
        if categoria == "Otros":
            sin_categoria[titulo] += 1

        if id_canal not in indice_canal:
            indice_canal[id_canal] = len(canales)
            canales.append({
                "id": id_canal,
                "nombre": re.sub(r"\s*\(\d+p\)|\s*\[.*?\]", "", canal["nombre"]).strip(),
                "logo": canal["logo"],
                "url": canal["url"],
                "opciones_vlc": canal["opciones_vlc"],
            })

        programas.append({
            "c": indice_canal[id_canal],
            "i": inicio.isoformat(timespec="minutes"),
            "f": fin.isoformat(timespec="minutes"),
            "t": titulo,
            "e": episodio,
            "d": descripcion[:LARGO_MAX_DESCRIPCION],
            "k": categoria,
        })

    programas.sort(key=lambda x: (x["i"], x["c"]))
    salida = {
        "generado": ahora.isoformat(timespec="minutes"),
        "categorias": CATEGORIAS,
        "canales": canales,
        "programas": programas,
    }
    destino = CARPETA_DATOS / "guia.json"
    destino.write_text(json.dumps(salida, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    print(f"Canales en la guía:   {len(canales)}")
    print(f"Programas (desde ahora hasta {DIAS_GUIA} días): {len(programas)}")
    print("\nProgramas por categoría:")
    por_cat = Counter(p["k"] for p in programas)
    for cat in CATEGORIAS:
        print(f"  {por_cat[cat]:>6}  {cat}")
    print("\nDe dónde salió la categoría:")
    for k in ("manual", "fuente", "deducida", "canal", "sin datos"):
        print(f"  {origen[k]:>6}  {k}")
    print("\nTítulos que quedaron en 'Otros' (los 15 más repetidos):")
    for titulo, n in sin_categoria.most_common(15):
        print(f"  {n:>4}  {titulo}")
    print("\nEjemplo por categoría (hora de Chile):")
    vistos = set()
    for p in programas:
        if p["k"] not in vistos:
            vistos.add(p["k"])
            hora = datetime.fromisoformat(p["i"]).strftime("%d-%m %H:%M")
            print(f"  [{p['k']}] {hora}  {canales[p['c']]['nombre']}: {p['t']}")
    print(f"\nDatos guardados en: {destino}")


if __name__ == "__main__":
    main()