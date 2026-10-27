"""
Paso 4: descarga la lista de canales en español de iptv-org
y muestra un resumen de lo que contiene.
"""
import json
import re
import urllib.request
from collections import Counter
from pathlib import Path

URL_LISTA = "https://iptv-org.github.io/iptv/languages/spa.m3u"
CARPETA_DATOS = Path("datos")
PATRON_ATRIBUTO = re.compile(r'([\w-]+)="([^"]*)"')


def descargar(url):
    print(f"Descargando {url} ...")
    peticion = urllib.request.Request(url, headers={"User-Agent": "guia-tv"})
    with urllib.request.urlopen(peticion, timeout=60) as respuesta:
        return respuesta.read().decode("utf-8", errors="replace")


def leer_m3u(texto):
    """Convierte el texto M3U en una lista de canales (diccionarios)."""
    canales = []
    actual = None
    for linea in texto.splitlines():
        linea = linea.strip()
        if linea.startswith("#EXTINF"):
            info, _, nombre = linea.partition(",")
            atributos = dict(PATRON_ATRIBUTO.findall(info))
            actual = {
                "nombre": nombre.strip(),
                "id_guia": atributos.get("tvg-id", ""),
                "logo": atributos.get("tvg-logo", ""),
                "categoria": atributos.get("group-title", ""),
                "opciones_vlc": [],
            }
        elif linea.startswith("#EXTVLCOPT") and actual is not None:
            actual["opciones_vlc"].append(linea.split(":", 1)[1])
        elif linea and not linea.startswith("#") and actual is not None:
            actual["url"] = linea
            canales.append(actual)
            actual = None
    return canales


def pais_de(id_guia):
    """'Canal13.cl@SD' -> 'cl'"""
    base = id_guia.split("@")[0]
    return base.rsplit(".", 1)[1].lower() if "." in base else "?"


def main():
    canales = leer_m3u(descargar(URL_LISTA))
    con_id = [c for c in canales if c["id_guia"]]

    print()
    print(f"Total de canales en la lista:           {len(canales)}")
    print(f"Con identificador para la guía (tvg-id): {len(con_id)}")
    print(f"Sin identificador (no podrán tener guía): {len(canales) - len(con_id)}")

    print("\nCanales por país (los 15 con más canales):")
    for pais, n in Counter(pais_de(c["id_guia"]) for c in con_id).most_common(15):
        print(f"  {pais:>4}  {n}")

    print("\nCanales por categoría (las 15 más comunes):")
    categorias = Counter()
    for c in canales:
        for cat in (c["categoria"] or "Sin categoría").split(";"):
            categorias[cat] += 1
    for cat, n in categorias.most_common(15):
        print(f"  {n:>5}  {cat}")

    print("\nEjemplos de canales:")
    for c in canales[:5]:
        print(f"  - {c['nombre']}  |  id: {c['id_guia'] or '(sin id)'}  |  {c['categoria']}")

    CARPETA_DATOS.mkdir(exist_ok=True)
    destino = CARPETA_DATOS / "canales.json"
    destino.write_text(json.dumps(canales, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nLista completa guardada en: {destino}")


if __name__ == "__main__":
    main()