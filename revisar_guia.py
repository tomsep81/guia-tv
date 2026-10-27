"""
Revisa un archivo de guía (XMLTV) y muestra qué información trae.

Uso:  python revisar_guia.py datos/guia_prueba_cl.xml
"""
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import datetime


def fecha(texto):
    """'20261026203000 +0000' -> datetime"""
    return datetime.strptime(texto.strip(), "%Y%m%d%H%M%S %z")


def main():
    raiz = ET.parse(sys.argv[1]).getroot()
    programas = raiz.findall("programme")

    con = Counter()
    categorias = Counter()
    por_canal = defaultdict(list)
    for p in programas:
        por_canal[p.get("channel")].append(fecha(p.get("start")))
        for campo in ("title", "desc", "category", "credits", "date", "icon", "episode-num"):
            if p.find(campo) is not None:
                con[campo] += 1
        for c in p.findall("category"):
            categorias[(c.text or "").strip()] += 1

    total = len(programas)
    print(f"Canales en el archivo:  {len(raiz.findall('channel'))}")
    print(f"Canales con programas:  {len(por_canal)}")
    print(f"Programas en total:     {total}")

    print("\nCuántos programas traen cada dato:")
    nombres = {"title": "título", "desc": "descripción", "category": "categoría",
               "credits": "reparto/actores", "date": "año", "icon": "imagen",
               "episode-num": "n° de episodio"}
    for campo, nombre in nombres.items():
        pct = 100 * con[campo] / total if total else 0
        print(f"  {nombre:<16} {con[campo]:>6}  ({pct:.0f}%)")

    print("\nCategorías más frecuentes (top 15):")
    for cat, n in categorias.most_common(15):
        print(f"  {n:>5}  {cat}")

    print("\nDías cubiertos por canal:")
    for canal, inicios in sorted(por_canal.items()):
        print(f"  {canal:<28} {min(inicios):%d-%m} a {max(inicios):%d-%m}  ({len(inicios)} programas)")

    print("\nEjemplos de programas:")
    for p in programas[:3]:
        print("  ---")
        print(f"  Canal:       {p.get('channel')}")
        print(f"  Inicio:      {p.get('start')}")
        print(f"  Título:      {p.findtext('title')}")
        print(f"  Categoría:   {', '.join(c.text or '' for c in p.findall('category')) or '(no trae)'}")
        print(f"  Descripción: {(p.findtext('desc') or '(no trae)')[:150]}")


if __name__ == "__main__":
    main()