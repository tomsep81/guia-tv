"""
Paso 5: revisa cuáles de nuestros canales en español tienen
una fuente de guía de programación disponible (según iptv-org).
"""
import json
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

URL_GUIAS = "https://iptv-org.github.io/api/guides.json"
CARPETA_DATOS = Path("datos")


def descargar_json(url):
    print(f"Descargando {url} ...")
    peticion = urllib.request.Request(url, headers={"User-Agent": "guia-tv"})
    with urllib.request.urlopen(peticion, timeout=120) as respuesta:
        return json.loads(respuesta.read().decode("utf-8"))


def id_canal(id_guia):
    """'Canal13.cl@SD' -> 'Canal13.cl' (quita la variante después de @)."""
    return id_guia.split("@")[0]


def main():
    canales = json.loads((CARPETA_DATOS / "canales.json").read_text(encoding="utf-8"))
    nuestros = {id_canal(c["id_guia"]) for c in canales if c["id_guia"]}

    guias = descargar_json(URL_GUIAS)

    # Para cada canal nuestro, las fuentes de guía que existen
    fuentes = defaultdict(list)
    for g in guias:
        if g.get("channel") in nuestros:
            fuentes[g["channel"]].append({
                "sitio": g.get("site"),
                "id_en_sitio": g.get("site_id"),
                "idioma": g.get("lang"),
                "variante": g.get("feed"),
            })

    print()
    print(f"Streams en la lista de canales:        {len(canales)}")
    print(f"Canales distintos (sin repetir):       {len(nuestros)}")
    print(f"Canales CON fuente de guía:            {len(fuentes)}")
    print(f"Canales SIN fuente de guía:            {len(nuestros) - len(fuentes)}")

    print("\nSitios de guía que cubren más canales nuestros (top 15):")
    por_sitio = Counter()
    for lista in fuentes.values():
        for sitio in {f["sitio"] for f in lista}:
            por_sitio[sitio] += 1
    for sitio, n in por_sitio.most_common(15):
        print(f"  {n:>5}  {sitio}")

    print("\nCanales con guía por país (top 10):")
    por_pais = Counter(c.rsplit(".", 1)[-1] for c in fuentes)
    for pais, n in por_pais.most_common(10):
        print(f"  {pais:>4}  {n}")

    destino = CARPETA_DATOS / "fuentes_guia.json"
    destino.write_text(json.dumps(fuentes, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDetalle guardado en: {destino}")


if __name__ == "__main__":
    main()