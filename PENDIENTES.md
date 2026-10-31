# Proyecto Guía TV

## Estado actual
- Proyecto completo (pasos 1 al 10).
- Guía publicada en: https://tomsep81.github.io/guia-tv/
- Se actualiza sola cada día cerca de las 7:00 (hora de Chile en horario de verano;
  6:00 en invierno), con GitHub Actions. El PC no necesita estar encendido.
- Primera ejecución completa (30-10-2026): 383 canales, unos 33.000 programas.

## Uso diario
- Consultar la guía: abrir https://tomsep81.github.io/guia-tv/ en el celular o el PC.
- Ver un canal (solo en el PC): botón "Ver en VLC".
  - Usa windows/abrir_vlc.ps1, con 3 segundos de reserva (:network-caching=3000).
  - Si un canal se ve ralentizado, probar 5000 en esa línea.
  - Si se cambia la carpeta del proyecto de lugar, volver a ejecutar:
    powershell -ExecutionPolicy Bypass -File windows\instalar_enlace_vlc.ps1

## Mantenimiento
- Corregir la categoría de un programa: agregar una línea en correcciones.txt
  ("Título = Categoría") y subir a GitHub. Se aplica en la siguiente actualización.
- Actualizar la guía a mano: GitHub > pestaña Actions > "Actualizar guía" > Run workflow.
- Si una actualización falla, GitHub envía un correo. La página sigue mostrando la
  última guía publicada. Revisar el paso con X en Actions.
- GitHub desactiva las tareas programadas tras 60 días sin cambios; el paso
  "Mantener activa la tarea diaria" lo evita. Si aun así se desactiva, llega un
  correo y se reactiva con un clic en Actions.

## Respaldar cambios
VS Code > Control de código fuente (Ctrl + Shift + G) > escribir mensaje >
Confirmación > Sincronizar cambios.

## Probar en el PC (opcional, solo canales de Chile)
1. python paso4_canales.py
2. python paso9_verificar.py
3. cd C:\Proyectos\epg
   npm run grab --- --channels=../guia-tv/datos/prueba_cl.channels.xml --output=../guia-tv/datos/guia_prueba_cl.xml --days=7 --maxConnections=5
   (usar barras "/" en las rutas, no "\")
4. cd C:\Proyectos\guia-tv
   python paso7_procesar.py datos/guia_prueba_cl.xml
5. python -m http.server 8000  ->  abrir http://localhost:8000/sitio/
   (detener con Ctrl + C)

## Ideas para más adelante
- Canales favoritos en la guía.
- Seguir mejorando la clasificación (revisar "Otros").
- Ajustes de diseño de la página.