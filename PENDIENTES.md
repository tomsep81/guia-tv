# Pendientes del proyecto Guía TV

## Estado actual
- Pasos 1 al 9 completos y probados con los canales de Chile.
- Siguiente: paso 10, automatizar con GitHub Actions y publicar en GitHub Pages
  (https://tomsep81.github.io/guia-tv/) para todos los canales en español.

## Para ver la guía en el PC (mientras no esté el paso 10)
1. python paso4_canales.py
2. python paso9_verificar.py
3. cd C:\Proyectos\epg
   npm run grab --- --channels=../guia-tv/datos/prueba_cl.channels.xml --output=../guia-tv/datos/guia_prueba_cl.xml --days=7 --maxConnections=5
   (usar barras "/" en las rutas, no "\")
4. cd C:\Proyectos\guia-tv
   python paso7_procesar.py datos/guia_prueba_cl.xml
5. python -m http.server 8000  ->  abrir http://localhost:8000/sitio/
   (detener con Ctrl + C)

## Canales que se ven "ralentizados" en VLC
Causas: servidor del canal lento o saturado, calidad alta (1080p) para la
conexión o Wi-Fi, o reserva de video de VLC muy pequeña (1 segundo por defecto).

Qué probar:
- Aumentar la reserva de VLC: Herramientas > Preferencias > Mostrar ajustes: "Todo"
  > Entrada / Códecs > "Caché de red (ms)": cambiar 1000 por 3000 > Guardar.
- Diagnosticar: Herramientas > Información de códec > Estadísticas.
  Si "Cuadros perdidos" sube siempre en un mismo canal, es su servidor.
  Si todos los canales fallan a la vez, revisar la conexión.

## Mejoras pendientes
- Agregar la reserva de red (:network-caching=3000) directamente al botón
  "Ver en VLC" (archivo windows/abrir_vlc.ps1).
- Revisar títulos en "Otros" y agregarlos a correcciones.txt
  (por ejemplo, películas como "Las momias de Guanajuato" o "La tumba del Diablo").