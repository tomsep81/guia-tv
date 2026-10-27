"""
Paso 6: crea el archivo de canales que usa la herramienta de iptv-org/epg
para descargar la programación. Elige UNA fuente de guía por canal.

Uso:
  python paso6_lista_guias.py        -> todos los canales con guía
  python paso6_lista_guias.py cl     -> solo un país (para pruebas)
"""
import json
import sys
from collections import Counter
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

CARPETA_DATOS = Path("datos")


def main():
    pais = sys.argv[1].lower() if len(sys.argv) > 1 else None

    canales = json.loads((CARPETA_DATOS / "canales.json").read_text(encoding="utf-8"))
    fuentes = json.loads((CARPETA_DATOS / "fuentes_guia.json").read_text(encoding="utf-8"))

    # Nombre de cada canal (tomado de la lista M3U)
    nombres = {}
    for c in canales:
        nombres.setdefault(c["id_guia"].split("@")[0], c["nombre"])

    # Los sitios que cubren más canales se prefieren (suelen ser más estables)
    popularidad = Counter(f["sitio"] for lista in fuentes.values() for f in lista)

    def puntaje(f):
        return (f["idioma"] == "es", popularidad[f["sitio"]])

    lineas = []
    for canal, lista in sorted(fuentes.items()):
        if pais and not canal.lower().endswith("." + pais):
            continue
        f = max(lista, key=puntaje)
        xmltv_id = canal + (f"@{f['variante']}" if f["variante"] else "")
        lineas.append(
            f'  <channel site={quoteattr(f["sitio"])} lang={quoteattr(f["idioma"] or "es")} '
            f'xmltv_id={quoteattr(xmltv_id)} site_id={quoteattr(str(f["id_en_sitio"]))}>'
            f'{escape(nombres.get(canal, canal))}</channel>'
        )

    nombre_archivo = f"prueba_{pais}.channels.xml" if pais else "guia.channels.xml"
    destino = CARPETA_DATOS / nombre_archivo
    destino.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<channels>\n'
        + "\n".join(lineas) + "\n</channels>\n",
        encoding="utf-8",
    )
    print(f"Canales incluidos: {len(lineas)}")
    print(f"Archivo creado:    {destino.resolve()}")


if __name__ == "__main__":
    main()