"""
Paso 9: verifica qué streams responden y deja en datos/canales.json
solo los que funcionan. La lista completa queda en datos/canales_todos.json.

Criterio:
  - Funciona: entrega video real. Si es una lista HLS (.m3u8), se sigue
    hasta el primer trozo de video y se comprueba que también responda.
  - Se conserva por si acaso: 401/403 (suele ser bloqueo por país o por servidor;
    puede funcionar desde Chile aunque falle desde otro lugar).
  - Se descarta: no existe (404/410), error del servidor (5xx),
    no responde a tiempo o no se puede conectar.
"""
import json
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

CARPETA_DATOS = Path("datos")
TIEMPO_ESPERA = 12        # segundos por stream
CONEXIONES = 40           # streams que se prueban a la vez
AGENTE = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"


def pedir(url, cabeceras, bytes_max):
    peticion = urllib.request.Request(url, headers=cabeceras)
    with urllib.request.urlopen(peticion, timeout=TIEMPO_ESPERA) as r:
        return r.geturl(), r.read(bytes_max)


def siguiente_enlace(url_base, texto):
    """En una lista .m3u8, devuelve el primer enlace (variante o trozo de video)."""
    for linea in texto.splitlines():
        linea = linea.strip()
        if linea and not linea.startswith("#"):
            return urllib.parse.urljoin(url_base, linea)
    return None


def probar(canal):
    """Devuelve 'ok', 'dudoso' o 'caido'."""
    cabeceras = {"User-Agent": AGENTE}
    for op in canal.get("opciones_vlc", []):
        clave, _, valor = op.partition("=")
        if clave == "http-referrer":
            cabeceras["Referer"] = valor
        elif clave == "http-user-agent":
            cabeceras["User-Agent"] = valor
    url = canal["url"]
    try:
        # Se baja la lista y se sigue (máximo 3 saltos) hasta llegar al video
        for _ in range(3):
            url_final, datos = pedir(url, cabeceras, 200_000)
            texto = datos.decode("utf-8", errors="replace")
            if not texto.lstrip().startswith("#EXTM3U"):
                return "ok" if datos else "caido"     # ya es video
            url = siguiente_enlace(url_final, texto)
            if url is None:
                return "caido"                        # lista vacía
        return "ok"
    except urllib.error.HTTPError as e:
        # 403 solo se conserva si iptv-org marca el canal como bloqueado por país
        if e.code in (401, 403) and "geo-blocked" in canal.get("nombre", "").lower():
            return "dudoso"
        return "caido"
    except Exception:
        return "caido"


def main():
    archivo_todos = CARPETA_DATOS / "canales_todos.json"
    archivo_canales = CARPETA_DATOS / "canales.json"

    canales = json.loads(archivo_canales.read_text(encoding="utf-8"))
    archivo_todos.write_text(json.dumps(canales, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Probando {len(canales)} streams ({CONEXIONES} a la vez, hasta {TIEMPO_ESPERA} s cada uno)...")
    with ThreadPoolExecutor(max_workers=CONEXIONES) as grupo:
        resultados = list(grupo.map(probar, canales))

    conteo = Counter(resultados)
    vivos = [c for c, r in zip(canales, resultados) if r != "caido"]
    archivo_canales.write_text(json.dumps(vivos, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n  Funcionan:              {conteo['ok']}")
    print(f"  Dudosos (se conservan): {conteo['dudoso']}")
    print(f"  Caídos (se descartan):  {conteo['caido']}")
    print(f"\nCanales que quedan: {len(vivos)}  ->  {archivo_canales}")
    print(f"Lista completa respaldada en: {archivo_todos}")


if __name__ == "__main__":
    main()