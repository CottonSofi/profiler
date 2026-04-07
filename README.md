# X Profiler Sentinel

Aplicacion de escritorio para monitorear actividad de cuentas de X, mostrar alertas y descargar media segun el modo configurado.

## Funciones actuales

- Multi-perfil por UID.
- Deteccion de posts, replies y retweets.
- Intervalo de deteccion aleatorio por perfil (min/max) para comportamiento mas natural.
- Popup con contexto de hilo/citas y soporte de media.
- Modo de descarga:
  - solo notificaciones
  - actividad seleccionada en monitoreo
  - cuenta completa (advertencia)
  - solo media subida por la cuenta monitoreada
- Carpeta global de cookies configurable (no por perfil).

## Archivos JSON usados

En la carpeta `profiler/` se usan estos JSON:

1. `profiles.json`
- Lista de perfiles.
- Claves usadas por perfil:
  - `uid`
  - `username`
  - `detect_post`
  - `detect_reply`
  - `detect_retweet`
  - `notify_popup`
  - `download_mode`
  - `output_dir`
  - `poll_min_seconds`
  - `poll_max_seconds`
  - `popup_auto_close`
  - `popup_close_seconds`
  - `popup_autoplay_media`
  - `auto_start`

2. `profiler_config.json`
- Configuracion global de la app.
- Claves usadas:
  - `run_at_startup`
  - `cookies_dir`

Nota: el archivo `cookies/cookie_usernames.json` se genera automaticamente para etiquetar cookies detectadas, pero no vive en la raiz `profiler/`.

## Estructura de guardado

- Estado por perfil: `profiler/state/<UID>.json`
- Eventos por perfil: `profiler/output/<UID>/events/YYYY/MM/DD/<kind>_<status_id>/`
  - `event.json`
  - `event.txt`
  - subcarpetas de media segun tipo de descarga

## Ejecutar

Desde la raiz del workspace:

```powershell
python profiler/app.py
```

Con venv:

```powershell
.\.venv\Scripts\Activate.ps1
python profiler/app.py
```
