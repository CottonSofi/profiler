import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
import tkinter as tk
import importlib
import webbrowser
from urllib.request import Request, urlopen
from dataclasses import dataclass
from datetime import datetime, timedelta
from tkinter import filedialog, messagebox, ttk
from typing import Any
import random

CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0

Image = None
ImageTk = None
try:
    pil_image = importlib.import_module("PIL.Image")
    pil_imagetk = importlib.import_module("PIL.ImageTk")
    Image = pil_image
    ImageTk = pil_imagetk
except Exception:
    pass

screeninfo = None
get_monitors = None
try:
    screeninfo = importlib.import_module("screeninfo")
    get_monitors = getattr(screeninfo, "get_monitors", None)
except Exception:
    pass

vlc_mod = None
try:
    vlc_mod = importlib.import_module("vlc")
except Exception:
    vlc_mod = None

APP_TITLE = "X Profiler Sentinel - Advanced"
MAX_SEEN_IDS = 1000
DEFAULT_POLL_SECONDS = 300
MIN_POLL_SECONDS = 120

DOWNLOAD_MODE_NOTIFY_ONLY = "notify_only"
DOWNLOAD_MODE_ALL_ACTIVITY = "all_activity"
DOWNLOAD_MODE_SELECTED_ACTIVITY = "selected_activity"
DOWNLOAD_MODE_OWN_MEDIA_ONLY = "own_media_only"

DOWNLOAD_MODE_LABELS = {
    DOWNLOAD_MODE_NOTIFY_ONLY: "Solo notificaciones",
    DOWNLOAD_MODE_ALL_ACTIVITY: "Descargar cuenta completa (advertencia)",
    DOWNLOAD_MODE_SELECTED_ACTIVITY: "Descargar actividad seleccionada (en monitoreo)",
    DOWNLOAD_MODE_OWN_MEDIA_ONLY: "Descargar solo media subida por la cuenta",
}

TRANSLATIONS = {
    "English": {
        "SISTEMA ACTIVO": "ACTIVE SYSTEM",
        "Cargando estado...": "Loading status...",
        "Tiempo restante: -- s": "Time remaining: -- s",
        "🔄 Forzar Rotación Ahora": "🔄 Force Rotation Now",
        "▶️ Iniciar Todos los Monitores": "▶️ Start All Monitors",
        "⏸️ Pausar Todos los Monitores": "⏸️ Pause All Monitors",
        "Configuración Global de Tiempos y UI": "Global Timing and UI Settings",
        "Carpeta Global de Cookies (.txt):": "Global Cookies Folder (.txt):",
        "Cambiar carpeta": "Change folder",
        "Monitor para Popups (Global):": "Popup Monitor (Global):",
        "Actualizar monitores": "Update monitors",
        "Idioma (Global):": "Language (Global):",
        "Tiempo base de rotación (Segundos):": "Base rotation time (Seconds):",
        "Tiempo aleatorio extra (Segundos):": "Extra random time (Seconds):",
        "Iniciar app con Windows (global)": "Start app with Windows (global)",
        "💾 Guardar Configuración Global": "💾 Save Global Config",
        "Otras Utilidades y Acciones de Sistema": "Other Utilities and System Actions",
        "🔄 Reiniciar Aplicación (Actualizar a nuevo código)": "🔄 Restart App (Update to new code)",
        "Abrir otra ventana (Nueva Instancia)": "Open another window (New Instance)",
        "Nueva instancia": "New instance",
        "Archivos en carpeta: 0": "Files in folder: 0",
        "➕ Importar archivo de Cookie (.txt)": "➕ Import Cookie file (.txt)",
        "📁 Abrir carpeta de cookies": "📁 Open cookies folder",
        " ⚙️ Opciones Globales ": " ⚙️ Global Options ",
        " Registros (Logs) ": " Logs (Registry) ",
        " Monitoreo y Perfiles ": " Monitoring and Profiles ",
        "Perfiles Guardados": "Saved Profiles",
        "Configuracion de deteccion del Perfil": "Profile Detection Configuration",
        "Historial de popups": "Popup History",
        "Nuevo UID": "New UID",
        "Guardar perfil": "Save profile",
        "Eliminar perfil": "Delete profile",
        "▶ Iniciar monitor": "▶ Start monitor",
        "⏸ Detener monitor": "⏸ Stop monitor",
        "Ver Historial de Popups": "View Popup History",
        "UID:": "UID:",
        "Usuario X (sin @):": "X User (without @):",
        "Cuenta X (@usuario o URL):": "X Account (@user or URL):",
        "Detectar posts": "Detect posts",
        "Detectar replies": "Detect replies",
        "Detectar retweets": "Detect retweets",
        "Mostrar popup de alerta": "Show alert popup",
        "Modo descarga:": "Download Mode:",
        "Advertencia descarga": "Download Warning",
        "Ruta salida:": "Output Path:",
        "Elegir carpeta": "Choose Directory",
        "Chequeo min (seg):": "Check min (sec):",
        "Chequeo max (seg):": "Check max (sec):",
        "Modo de ejecución:": "Execution Mode:",
        "Horas (08:00, 14:30):": "Exact times (08:00, 14:30):",
        "Retraso inicial (min):": "Initial delay (min):",
        "Detener tras (min, 0=inf):": "Stop after (min, 0=inf):",
        "Auto-cerrar popup": "Auto-close popup",
        "Segundos popup:": "Popup seconds:",
        "Auto-reproducir gif/video": "Autoplay gif/video",
        "Iniciar monitoreo automaticamente": "Start monitoring automatically",
        "Ignorar historial (Baseline nueva)": "Ignore history (New Baseline)",
        "Filtrar por perfil:": "Filter by profile:",
        "Refrescar lista": "Refresh list",
        "Limpiar Log": "Clear Log",
        "💾 Guardar Perfil": "💾 Save Profile",
        "✨ Nuevo Perfil (Limpiar)": "✨ New Profile (Clear)",
        "🗑️ Eliminar Perfil": "🗑️ Delete Profile",
        "▶ Iniciar Seleccionado": "▶ Start Selected",
        "⏸ Detener Seleccionado": "⏸ Stop Selected",
        "Configuración global guardada.": "Global configuration saved.",
        "Perfil guardado": "Profile saved",
        "Perfil eliminado": "Profile deleted",
        "Detén el monitor antes de eliminar el perfil": "Stop the monitor before deleting the profile",
        "Ese perfil ya está corriendo": "That profile is already running",
        "Automatico": "Automatic",
        "Automático": "Automatic",
        "Perfiles de Monitor": "Monitor Profiles",
        "Intervalos": "Intervals",
        "Horas Exactas": "Exact Hours",
        "Solo notificaciones": "Notifications only",
        "Descargar cuenta completa (advertencia)": "Download entire account (warning)",
        "Descargar actividad seleccionada (en monitoreo)": "Download selected activity (monitoring)",
        "Descargar solo media subida por la cuenta": "Download only media uploaded by the account"
    }
}

for lang, mapping in [
    ("Français", {
        "SISTEMA ACTIVO": "SYSTÈME ACTIF", "Cargando estado...": "Chargement...", 
        "▶️ Iniciar Todos los Monitores": "▶️ Démarrer Tout", "⏸️ Pausar Todos los Monitores": "⏸️ Pause Tout",
        "Idioma (Global):": "Langue (Globale):", "💾 Guardar Perfil": "💾 Sauvegarder", "Automatico": "Automatique", "Automático": "Automatique",
        "Guardar perfil": "Enregistrer le profil", "▶ Iniciar monitor": "▶ Démarrer le moniteur", "⏸ Detener monitor": "⏸ Arrêter le moniteur"
    }),
    ("Português", {
        "SISTEMA ACTIVO": "SISTEMA ATIVO", "Cargando estado...": "Carregando estado...",
        "▶️ Iniciar Todos los Monitores": "▶️ Iniciar Todos", "⏸️ Pausar Todos los Monitores": "⏸️ Pausar Todos",
        "Idioma (Global):": "Idioma (Global):", "💾 Guardar Perfil": "💾 Salvar Perfil", "Automatico": "Automático", "Automático": "Automático",
        "Guardar perfil": "Salvar perfil", "▶ Iniciar monitor": "▶ Iniciar monitor", "⏸ Detener monitor": "⏸ Parar monitor"
    }),
    ("Deutsch", {
        "SISTEMA ACTIVO": "AKTIVES SYSTEM", "Cargando estado...": "Lädt Zustand...",
        "▶️ Iniciar Todos los Monitores": "▶️ Alle Starten", "⏸️ Pausar Todos los Monitores": "⏸️ Alle Pausieren",
        "Idioma (Global):": "Sprache (Global):", "💾 Guardar Perfil": "💾 Profil Speichern", "Automatico": "Automatisch", "Automático": "Automatisch",
        "Guardar perfil": "Profil speichern", "▶ Iniciar monitor": "▶ Monitor starten", "⏸ Detener monitor": "⏸ Monitor stoppen"
    })
]:
    merged = TRANSLATIONS["English"].copy()
    merged.update(mapping)
    TRANSLATIONS[lang] = merged

REPOST_TEXT_RE = re.compile(r"(reposted|repost|reposte[oó]|reposteaste|repostaste|rt\s*@)", flags=re.IGNORECASE)

STATUS_URL_RE = re.compile(
    r"https?://(?:www\.)?(?:x|twitter)\.com/(?:([^/?#]+)/status|i(?:/web)?/status)/(\d+)",
    flags=re.IGNORECASE,
)
USER_FROM_URL_RE = re.compile(
    r"https?://(?:www\.)?(?:x|twitter)\.com/([^/?#]+)/?",
    flags=re.IGNORECASE,
)


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def ensure_dir(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path


def normalize_status_url(url: str) -> str | None:
    text = (url or "").strip()
    if not text:
        return None
    m = STATUS_URL_RE.search(text)
    if not m:
        return None
    user = (m.group(1) or "").strip()
    status_id = m.group(2)
    if not user or user.lower() == "i":
        return f"https://x.com/i/web/status/{status_id}"
    return f"https://x.com/{user}/status/{status_id}"


def status_id_from_url(url: str) -> int | None:
    m = STATUS_URL_RE.search((url or "").strip())
    if not m:
        return None
    try:
        return int(m.group(2))
    except Exception:
        return None


def extract_username(text: str) -> str | None:
    raw = (text or "").strip()
    if not raw:
        return None
    if raw.startswith("@"):
        raw = raw[1:]
    match = USER_FROM_URL_RE.search(raw)
    if match:
        raw = match.group(1)
    raw = raw.strip().strip("/")
    if not raw:
        return None
    if raw.lower() in {"home", "i", "explore", "search"}:
        return None
    if not re.match(r"^[A-Za-z0-9_]{1,15}$", raw):
        return None
    return raw


def author_from_status_url(url: str) -> str | None:
    raw = (url or "").strip()
    if not raw:
        return None
    m = STATUS_URL_RE.search(raw)
    if not m:
        return None
    user = str(m.group(1) or "").strip().lstrip("@").lower()
    if not user or user == "i":
        return None
    if re.match(r"^[A-Za-z0-9_]{1,15}$", user):
        return user
    return None


def to_int_or_none(value: Any) -> int | None:
    try:
        iv = int(str(value))
        if iv > 0:
            return iv
    except Exception:
        pass
    return None


def parse_gallery_rows(stdout: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    def extract_handle(raw_value: object) -> str | None:
        if isinstance(raw_value, str):
            maybe = raw_value.strip().lstrip("@")
            if re.match(r"^[A-Za-z0-9_]{1,15}$", maybe):
                return maybe
            return None
        if isinstance(raw_value, dict):
            for key in ("nick", "screen_name", "username", "name"):
                maybe = str(raw_value.get(key) or "").strip().lstrip("@")
                if re.match(r"^[A-Za-z0-9_]{1,15}$", maybe):
                    return maybe
        return None

    def has_video(item: dict[str, Any]) -> bool:
        item_type = str(item.get("type") or "").strip().lower()
        if item_type in {"video", "animated_gif"}:
            return True
        if item.get("is_video") is True:
            return True
        media = item.get("media")
        if isinstance(media, list):
            for media_item in media:
                if not isinstance(media_item, dict):
                    continue
                m_type = str(media_item.get("type") or "").strip().lower()
                if m_type in {"video", "animated_gif"}:
                    return True
        return False

    def has_image(item: dict[str, Any]) -> bool:
        item_type = str(item.get("type") or "").strip().lower()
        if item_type in {"image", "photo"}:
            return True
        media = item.get("media")
        if isinstance(media, list):
            for media_item in media:
                if not isinstance(media_item, dict):
                    continue
                m_type = str(media_item.get("type") or "").strip().lower()
                if m_type in {"image", "photo"}:
                    return True
        return False

    def collect(item: dict[str, Any]) -> None:
        candidates: list[str] = []
        for key in ("url", "post_url", "tweet_url", "original_url"):
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                candidates.append(value)

        tweet_id = item.get("tweet_id") or item.get("id")
        author_handle = extract_handle(item.get("author") or item.get("screen_name") or item.get("user"))
        user_handle = extract_handle(item.get("user"))

        rt_obj = item.get("retweeted_status") or item.get("retweet_status")
        if not isinstance(rt_obj, dict):
            rt_obj = {}

        text = ""
        for text_key in ("content", "text", "full_text", "title", "description"):
            value = item.get(text_key)
            if isinstance(value, str) and value.strip():
                text = value.strip()
                break

        if rt_obj:
            rt_text = ""
            for text_key in ("content", "text", "full_text", "title", "description"):
                value = rt_obj.get(text_key)
                if isinstance(value, str) and value.strip():
                    rt_text = value.strip()
                    break
            if rt_text and (len(rt_text) > len(text) or text.startswith("RT @")):
                text = rt_text

        reply_id = item.get("reply_id")
        reply_id_int = to_int_or_none(reply_id)
        tweet_id_int = to_int_or_none(tweet_id)

        conversation_id_int = to_int_or_none(item.get("conversation_id")) or to_int_or_none(rt_obj.get("conversation_id"))

        reply_to_status_id = (
            to_int_or_none(item.get("in_reply_to_status_id"))
            or to_int_or_none(item.get("reply_to_status_id"))
            or to_int_or_none(item.get("parent_tweet_id"))
            or reply_id_int
            or to_int_or_none(rt_obj.get("in_reply_to_status_id"))
            or to_int_or_none(rt_obj.get("reply_to_status_id"))
            or to_int_or_none(rt_obj.get("parent_tweet_id"))
        )

        if reply_to_status_id is None and isinstance(tweet_id_int, int) and isinstance(conversation_id_int, int) and conversation_id_int != tweet_id_int:
            reply_to_status_id = conversation_id_int

        reply_to_author = (
            extract_handle(item.get("in_reply_to_user"))
            or extract_handle(item.get("reply_to_user"))
            or extract_handle(item.get("parent_author"))
            or extract_handle(item.get("in_reply_to_screen_name"))
            or extract_handle(rt_obj.get("in_reply_to_user"))
            or extract_handle(rt_obj.get("reply_to_user"))
            or extract_handle(rt_obj.get("parent_author"))
            or extract_handle(rt_obj.get("in_reply_to_screen_name"))
        )

        reply_to_url = None
        reply_url_candidates: list[str] = []
        for key in ("in_reply_to_url", "reply_to_url", "parent_url", "reply_url"):
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                reply_url_candidates.append(value)
        if isinstance(reply_to_status_id, int):
            if reply_to_author:
                reply_url_candidates.append(f"https://x.com/{reply_to_author}/status/{reply_to_status_id}")
            reply_url_candidates.append(f"https://x.com/i/web/status/{reply_to_status_id}")
        for candidate in reply_url_candidates:
            normalized = normalize_status_url(candidate)
            if normalized:
                reply_to_url = normalized
                break

        if tweet_id:
            if author_handle:
                candidates.append(f"https://x.com/{author_handle}/status/{tweet_id}")
            candidates.append(f"https://x.com/i/web/status/{tweet_id}")

        row_has_video = has_video(item) or has_video(rt_obj)
        row_has_image = has_image(item) or has_image(rt_obj)

        is_retweet = bool(item.get("retweeted_status") or item.get("retweet_status"))
        subcategory = str(item.get("subcategory") or "").strip().lower()
        if "retweet" in subcategory or "repost" in subcategory:
            is_retweet = True
        try:
            if int(str(item.get("retweet_id") or "0")) > 0:
                is_retweet = True
        except Exception:
            pass
        if item.get("user_retweets"):
            is_retweet = True

        quote_url = None
        quote_status_id = None
        quote_text = ""
        quote_has_video = False
        quote_has_image = False
        quote_chain: list[dict[str, Any]] = []

        q_cursor: dict[str, Any] | None = rt_obj if rt_obj else item
        seen_quote_keys: set[tuple[int | None, str]] = set()
        for depth in range(1, 8):
            if not isinstance(q_cursor, dict):
                break
            quote_obj = None
            for qkey in ("quoted_status", "quoted_tweet", "quote_tweet", "quoted_post"):
                q = q_cursor.get(qkey)
                if isinstance(q, dict):
                    quote_obj = q
                    break
            if not isinstance(quote_obj, dict):
                break

            q_author = extract_handle(quote_obj.get("author") or quote_obj.get("screen_name") or quote_obj.get("user"))
            qid = quote_obj.get("tweet_id") or quote_obj.get("id") or q_cursor.get("quoted_status_id") or q_cursor.get("quote_id")
            q_candidates: list[str] = []
            for k in ("url", "post_url", "tweet_url", "original_url"):
                v = quote_obj.get(k)
                if isinstance(v, str) and v.strip():
                    q_candidates.append(v)
            if qid:
                if q_author:
                    q_candidates.append(f"https://x.com/{q_author}/status/{qid}")
                q_candidates.append(f"https://x.com/i/web/status/{qid}")

            q_url = None
            for qc in q_candidates:
                norm = normalize_status_url(qc)
                if norm:
                    q_url = norm
                    break

            q_status = status_id_from_url(q_url or "") if q_url else to_int_or_none(qid)
            q_key = (q_status if isinstance(q_status, int) else None, q_url or "")
            if q_key in seen_quote_keys:
                break
            seen_quote_keys.add(q_key)

            q_text = ""
            for tk_ in ("content", "text", "full_text", "title", "description"):
                tv = quote_obj.get(tk_)
                if isinstance(tv, str) and tv.strip():
                    q_text = tv.strip()
                    break

            q_has_video = has_video(quote_obj)
            q_has_image = has_image(quote_obj)
            quote_chain.append(
                {
                    "depth": depth,
                    "url": q_url,
                    "status_id": q_status if isinstance(q_status, int) else None,
                    "text": q_text,
                    "has_video": q_has_video,
                    "has_image": q_has_image,
                    "has_media": bool(q_has_video or q_has_image),
                }
            )
            q_cursor = quote_obj

        if quote_chain:
            first_quote = quote_chain[0]
            quote_url = str(first_quote.get("url") or "") or None
            quote_status_id = first_quote.get("status_id") if isinstance(first_quote.get("status_id"), int) else None
            quote_text = str(first_quote.get("text") or "")
            quote_has_video = bool(first_quote.get("has_video", False))
            quote_has_image = bool(first_quote.get("has_image", False))

        for candidate in candidates:
            canonical = normalize_status_url(candidate)
            if not canonical:
                continue
            rows.append(
                {
                    "url": canonical,
                    "status_id": status_id_from_url(canonical),
                    "author_handle": author_handle,
                    "actor_handle": user_handle,
                    "conversation_id": conversation_id_int,
                    "reply_id": reply_id_int,
                    "reply_to_url": reply_to_url,
                    "reply_to_status_id": reply_to_status_id,
                    "text": text,
                    "has_video": row_has_video,
                    "has_image": row_has_image,
                    "has_media": bool(row_has_video or row_has_image),
                    "is_retweet": is_retweet,
                    "quote_url": quote_url,
                    "quote_status_id": quote_status_id,
                    "quote_text": quote_text,
                    "quote_has_video": quote_has_video,
                    "quote_has_image": quote_has_image,
                    "quote_has_media": bool(quote_has_video or quote_has_image),
                    "quote_chain": quote_chain,
                }
            )

    text = (stdout or "").strip()
    if text:
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                collect(parsed)
            elif isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, dict):
                        collect(item)
        except Exception:
            pass

    for line in (stdout or "").splitlines():
        row = line.strip().rstrip(",")
        if not row:
            continue
        try:
            item = json.loads(row)
        except Exception:
            continue
        if isinstance(item, dict):
            collect(item)
        elif isinstance(item, list):
            for entry in item:
                if isinstance(entry, dict):
                    collect(entry)

    unique: list[dict[str, Any]] = []
    seen_ids: set[int] = set()
    seen_urls: set[str] = set()
    for item in rows:
        url = str(item.get("url") or "")
        sid = item.get("status_id")
        if isinstance(sid, int):
            if sid in seen_ids:
                continue
            seen_ids.add(sid)
        else:
            if url in seen_urls:
                continue
            seen_urls.add(url)
        unique.append(item)
    return unique


def split_main_and_quote_text(raw_text: str, quote_text: str = "") -> tuple[str, str]:
    text = str(raw_text or "").strip()
    if not text:
        return "", str(quote_text or "").strip()

    existing_quote = str(quote_text or "").strip()
    if existing_quote and existing_quote in text:
        main = text.replace(existing_quote, "").strip()
        return main, existing_quote

    quote_markers = [
        "\nQuote\n",
        "\nQuoted\n",
        "\nCita\n",
        "\nTweet citado\n",
    ]
    for marker in quote_markers:
        if marker in text:
            parts = text.split(marker, 1)
            main = parts[0].strip()
            quote = parts[1].strip()
            return main, quote

    lines = [ln.rstrip() for ln in text.splitlines()]
    counter_idx = None
    for i in range(len(lines) - 1, -1, -1):
        if re.match(r"^\s*\d+(?:\.\d+)?[KkMm]?\s*$", lines[i] or ""):
            counter_idx = i
        elif counter_idx is not None:
            break
    if counter_idx is not None and counter_idx > 0 and existing_quote:
        lines = lines[:counter_idx]
        text = "\n".join(lines).strip()

    return text, existing_quote


@dataclass
class Profile:
    uid: str
    username: str
    detect_post: bool
    detect_reply: bool
    detect_retweet: bool
    notify_popup: bool
    download_mode: str
    output_dir: str
    poll_min_seconds: int
    poll_max_seconds: int
    popup_auto_close: bool
    popup_close_seconds: int
    popup_autoplay_media: bool
    auto_start: bool
    fresh_baseline: bool
    schedule_mode: str
    exact_times: str
    start_delay_minutes: int
    stop_after_minutes: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "uid": self.uid,
            "username": self.username,
            "detect_post": self.detect_post,
            "detect_reply": self.detect_reply,
            "detect_retweet": self.detect_retweet,
            "notify_popup": self.notify_popup,
            "download_mode": self.download_mode,
            "output_dir": self.output_dir,
            "poll_min_seconds": self.poll_min_seconds,
            "poll_max_seconds": self.poll_max_seconds,
            "popup_auto_close": self.popup_auto_close,
            "popup_close_seconds": self.popup_close_seconds,
            "popup_autoplay_media": self.popup_autoplay_media,
            "auto_start": self.auto_start,
            "fresh_baseline": self.fresh_baseline,
            "schedule_mode": self.schedule_mode,
            "exact_times": self.exact_times,
            "start_delay_minutes": self.start_delay_minutes,
            "stop_after_minutes": self.stop_after_minutes,
        }

    @staticmethod
    def from_dict(data: dict[str, Any], default_output: str) -> "Profile":
        base_poll = max(MIN_POLL_SECONDS, int(data.get("poll_seconds") or DEFAULT_POLL_SECONDS))
        poll_min = max(MIN_POLL_SECONDS, int(data.get("poll_min_seconds") or base_poll))
        poll_max = max(MIN_POLL_SECONDS, int(data.get("poll_max_seconds") or base_poll))
        if poll_max < poll_min:
            poll_min, poll_max = poll_max, poll_min

        return Profile(
            uid=str(data.get("uid") or ""),
            username=str(data.get("username") or "").strip().lstrip("@"),
            detect_post=bool(data.get("detect_post", True)),
            detect_reply=bool(data.get("detect_reply", False)),
            detect_retweet=bool(data.get("detect_retweet", False)),
            notify_popup=bool(data.get("notify_popup", True)),
            download_mode=str(data.get("download_mode") or DOWNLOAD_MODE_NOTIFY_ONLY),
            output_dir=str(data.get("output_dir") or default_output),
            poll_min_seconds=poll_min,
            poll_max_seconds=poll_max,
            popup_auto_close=bool(data.get("popup_auto_close", False)),
            popup_close_seconds=max(1, int(data.get("popup_close_seconds") or 12)),
            popup_autoplay_media=bool(data.get("popup_autoplay_media", False)),
            auto_start=bool(data.get("auto_start", False)),
            fresh_baseline=bool(data.get("fresh_baseline", False)),
            schedule_mode=str(data.get("schedule_mode") or "Intervalos"),
            exact_times=str(data.get("exact_times") or ""),
            start_delay_minutes=max(0, int(data.get("start_delay_minutes") or 0)),
            stop_after_minutes=max(0, int(data.get("stop_after_minutes") or 0)),
        )

# --- OPCIONES GLOBALES (COOKIE ÚNICA ACTIVA ROTATORIA) ---
class GlobalCookieManager:
    def __init__(self, cookies_dir: str, get_base_timeout_fn, get_rand_timeout_fn, get_cookie_map_fn):
        self.cookies_dir = cookies_dir
        self.get_base_timeout = get_base_timeout_fn
        self.get_rand_timeout = get_rand_timeout_fn
        self.get_cookie_map = get_cookie_map_fn
        self.lock = threading.Lock()
        self.active_cookie: str | None = None
        self.active_until: float = 0.0
        self.cookie_usage_counts: dict[str, int] = {}

    def _get_all_cookies(self) -> list[str]:
        if not os.path.isdir(self.cookies_dir):
            return []
        return [os.path.abspath(os.path.join(self.cookies_dir, f)) 
                for f in os.listdir(self.cookies_dir) if f.lower().endswith(".txt")]

    def force_rotate(self):
        with self.lock:
            self.active_until = 0.0

    def get_active_cookie(self) -> str | None:
        with self.lock:
            now = time.time()
            all_cookies = self._get_all_cookies()

            if not all_cookies:
                self.active_cookie = None
                self.active_until = 0.0
                return None

            current_cookie_set = set(all_cookies)
            self.cookie_usage_counts = {k: v for k, v in self.cookie_usage_counts.items() if k in current_cookie_set}

            for c in all_cookies:
                if c not in self.cookie_usage_counts:
                    self.cookie_usage_counts[c] = 0

            if self.active_cookie in all_cookies and now < self.active_until:
                return self.active_cookie

            choices = [c for c in all_cookies if c != self.active_cookie]
            if not choices:
                choices = all_cookies 
            
            min_uses = min((self.cookie_usage_counts[c] for c in choices), default=0)
            
            normalized_uses = {c: (self.cookie_usage_counts[c] - min_uses) for c in choices}
            max_norm = max((normalized_uses[c] for c in choices), default=0)
            
            weights = []
            for c in choices:
                base_weight = (max_norm - normalized_uses[c]) + 1
                weights.append(base_weight ** 3.0) 
            
            chosen_cookie = random.choices(choices, weights=weights, k=1)[0]
            
            self.cookie_usage_counts[chosen_cookie] += 1

            self.active_cookie = chosen_cookie
            base = self.get_base_timeout()
            rand = self.get_rand_timeout()
            self.active_until = now + base + random.uniform(0.0, rand)

            return self.active_cookie

    def get_status(self) -> dict[str, Any]:
        with self.lock:
            now = time.time()
            all_cookies = self._get_all_cookies()
            cmap = self.get_cookie_map()

            active_name = os.path.basename(self.active_cookie) if self.active_cookie in all_cookies else None
            profile_name = cmap.get(active_name, "Desconocido") if active_name else "N/A"

            return {
                "active_cookie": active_name,
                "profile": profile_name,
                "remaining_seconds": max(0, int(self.active_until - now)) if active_name else 0,
                "total_cookies": len(all_cookies),
                "all_cookies": all_cookies
            }


class MonitorWorker(threading.Thread):
    def __init__(
        self,
        profile: Profile,
        state_dir: str,
        log_fn,
        notify_fn,
        history_fn,
        cookie_manager: GlobalCookieManager,
    ):
        super().__init__(daemon=True)
        self.profile = profile
        self.state_dir = state_dir
        self.cookie_manager = cookie_manager
        self.log_fn = log_fn
        self.notify_fn = notify_fn
        self.history_fn = history_fn
        self.stop_event = threading.Event()
        self.state_path = os.path.join(state_dir, f"{profile.uid}.json")
        self.seen_ids: dict[str, set[int]] = {
            "post": set(),
            "reply": set(),
            "retweet": set(),
        }
        self.bootstrapped: dict[str, bool] = {
            "post": False,
            "reply": False,
            "retweet": False,
        }
        self.full_account_sync_done = False
        self.last_used_cookie = "Desconocida"
        self._last_success_cookie_path: str | None = None
        self._last_network_request_at = 0.0
        self._request_gap_seconds = 2.8
        self._backoff_seconds = 0.0
        self._backoff_until = 0.0
        self._current_cycle_cookies: list[str] = [""]

    def _sleep_with_stop(self, seconds: float) -> None:
        wait_for = max(0.0, float(seconds))
        if wait_for <= 0:
            return
        self.stop_event.wait(wait_for)

    def _looks_rate_limited(self, text: str) -> bool:
        low = str(text or "").lower()
        signals = (
            "429",
            "rate limit",
            "too many requests",
            "temporarily locked",
            "try again later",
            "suspicious",
            "please wait",
            "denied",
            "forbidden",
        )
        return any(sig in low for sig in signals)

    def _wait_for_backoff(self) -> None:
        now = time.time()
        if self._backoff_until > now:
            self._sleep_with_stop(self._backoff_until - now)

    def _before_network_request(self) -> None:
        now = time.time()
        elapsed = now - self._last_network_request_at
        if elapsed < self._request_gap_seconds:
            self._sleep_with_stop(self._request_gap_seconds - elapsed)
        self._sleep_with_stop(random.uniform(0.15, 0.75))
        self._last_network_request_at = time.time()

    def _register_network_result(self, ok: bool, rate_limited: bool = False) -> None:
        if ok:
            self._backoff_seconds = 0.0
            self._backoff_until = 0.0
            return

        if self._backoff_seconds <= 0:
            self._backoff_seconds = 15.0
        else:
            self._backoff_seconds = min(600.0, self._backoff_seconds * 2.0)

        if rate_limited:
            self._backoff_seconds = min(600.0, max(self._backoff_seconds, 60.0))
            # FIX: Forzar rotación global de cookie si detectamos Rate Limit
            self.cookie_manager.force_rotate()

        jitter = random.uniform(0.0, min(10.0, self._backoff_seconds * 0.2))
        self._backoff_until = time.time() + self._backoff_seconds + jitter

    def _event_folder_name(self, kind: str, status_id: int | None) -> str:
        safe_kind = (kind or "event").strip().lower()
        if isinstance(status_id, int):
            return f"{safe_kind}_{status_id}"
        return f"{safe_kind}_unknown_{int(time.time())}"

    def _event_dir_for(self, event: dict[str, Any]) -> str:
        kind = str(event.get("kind") or "event")
        sid = event.get("status_id")
        uid_root = ensure_dir(os.path.join(self.profile.output_dir, self.profile.uid))
        events_root = ensure_dir(os.path.join(uid_root, "events"))

        ts_raw = str(event.get("time") or "").strip()
        dt = None
        if ts_raw:
            try:
                dt = datetime.fromisoformat(ts_raw.split(".")[0])
            except Exception:
                dt = None
        if dt is None:
            dt = datetime.now()

        date_base = ensure_dir(os.path.join(events_root, f"{dt.year:04d}", f"{dt.month:02d}", f"{dt.day:02d}"))
        return ensure_dir(os.path.join(date_base, self._event_folder_name(kind, sid if isinstance(sid, int) else None)))

    def _merge_move_dir(self, src: str, dst: str) -> None:
        if not os.path.isdir(src):
            return
        ensure_dir(dst)
        for root, dirs, files in os.walk(src):
            rel = os.path.relpath(root, src)
            target_root = dst if rel == "." else os.path.join(dst, rel)
            ensure_dir(target_root)
            for d in dirs:
                ensure_dir(os.path.join(target_root, d))
            for f in files:
                src_file = os.path.join(root, f)
                dst_file = os.path.join(target_root, f)
                if os.path.exists(dst_file):
                    base, ext = os.path.splitext(f)
                    dst_file = os.path.join(target_root, f"{base}_migrated{ext}")
                try:
                    shutil.move(src_file, dst_file)
                except Exception:
                    continue
        try:
            shutil.rmtree(src, ignore_errors=True)
        except Exception:
            pass

    def _migrate_legacy_output(self) -> None:
        uid_root = ensure_dir(os.path.join(self.profile.output_dir, self.profile.uid))
        legacy_jsonl = os.path.join(uid_root, "events.jsonl")
        legacy_txt = os.path.join(uid_root, "events.txt")
        legacy_media = os.path.join(uid_root, "media")
        events_base = ensure_dir(os.path.join(uid_root, "events"))

        migrated_any = False
        parsed_events: list[dict[str, Any]] = []
        if os.path.isfile(legacy_jsonl):
            try:
                with open(legacy_jsonl, "r", encoding="utf-8", errors="replace") as f:
                    for raw in f:
                        line = raw.strip()
                        if not line:
                            continue
                        try:
                            item = json.loads(line)
                        except Exception:
                            continue
                        if isinstance(item, dict):
                            parsed_events.append(item)
            except Exception:
                parsed_events = []

        for item in parsed_events:
            kind = str(item.get("kind") or "event")
            sid = item.get("status_id")
            sid_int = sid if isinstance(sid, int) else None
            event_dir = ensure_dir(os.path.join(events_base, self._event_folder_name(kind, sid_int)))

            event_json = os.path.join(event_dir, "event.json")
            if not os.path.isfile(event_json):
                try:
                    with open(event_json, "w", encoding="utf-8") as jf:
                        json.dump(item, jf, ensure_ascii=False, indent=2)
                    migrated_any = True
                except Exception:
                    pass

            event_txt = os.path.join(event_dir, "event.txt")
            if not os.path.isfile(event_txt):
                preview = str(item.get("text_preview") or "-")
                text_block = (
                    f"[{item.get('time') or '-'}] {str(item.get('kind') or '-').upper()}\n"
                    f"status_id={item.get('status_id')}\n"
                    f"url={item.get('url') or '-'}\n"
                    f"author={item.get('author_handle') or '-'}\n"
                    f"text={preview}\n"
                )
                try:
                    with open(event_txt, "w", encoding="utf-8", errors="replace") as tf:
                        tf.write(text_block)
                    migrated_any = True
                except Exception:
                    pass

            if isinstance(sid_int, int):
                old_sid_media = os.path.join(legacy_media, str(sid_int))
                new_media_dir = os.path.join(event_dir, "media")
                if os.path.isdir(old_sid_media):
                    self._merge_move_dir(old_sid_media, new_media_dir)
                    migrated_any = True

        if os.path.isdir(legacy_media):
            try:
                for name in os.listdir(legacy_media):
                    old_dir = os.path.join(legacy_media, name)
                    if not os.path.isdir(old_dir):
                        continue
                    try:
                        sid_int = int(name)
                    except Exception:
                        sid_int = None
                    fallback_event_dir = ensure_dir(os.path.join(events_base, self._event_folder_name("event", sid_int)))
                    self._merge_move_dir(old_dir, os.path.join(fallback_event_dir, "media"))
                    migrated_any = True
            except Exception:
                pass

        if migrated_any:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            if os.path.isfile(legacy_jsonl):
                try:
                    shutil.move(legacy_jsonl, os.path.join(uid_root, f"events.jsonl.legacy_{ts}.bak"))
                except Exception:
                    pass
            if os.path.isfile(legacy_txt):
                try:
                    shutil.move(legacy_txt, os.path.join(uid_root, f"events.txt.legacy_{ts}.bak"))
                except Exception:
                    pass
            self.log_fn(self.profile.uid, "Salida legacy migrada a estructura por evento")

    def _migrate_events_by_date(self) -> None:
        uid_root = ensure_dir(os.path.join(self.profile.output_dir, self.profile.uid))
        events_base = ensure_dir(os.path.join(uid_root, "events"))

        try:
            names = list(os.listdir(events_base))
        except Exception:
            return

        for name in names:
            src = os.path.join(events_base, name)
            if not os.path.isdir(src):
                continue
            if re.match(r"^\d{4}$", name):
                continue

            event_json = os.path.join(src, "event.json")
            dt = None
            if os.path.isfile(event_json):
                try:
                    with open(event_json, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    ts_raw = str(data.get("time") or "").strip()
                    if ts_raw:
                        try:
                            dt = datetime.fromisoformat(ts_raw.split(".")[0])
                        except Exception:
                            dt = None
                except Exception:
                    dt = None
            if dt is None:
                try:
                    mtime = os.path.getmtime(src)
                    dt = datetime.fromtimestamp(mtime)
                except Exception:
                    dt = datetime.now()

            dst_parent = ensure_dir(os.path.join(events_base, f"{dt.year:04d}", f"{dt.month:02d}", f"{dt.day:02d}"))
            dst = os.path.join(dst_parent, name)
            if os.path.abspath(src) == os.path.abspath(dst):
                continue
            try:
                if os.path.exists(dst):
                    base, ext = os.path.splitext(name)
                    dst = os.path.join(dst_parent, f"{base}_migrado{ext}")
                shutil.move(src, dst)
            except Exception:
                continue

    def stop(self) -> None:
        self.stop_event.set()

    def _cookie_candidates(self) -> list[str]:
        return self._current_cycle_cookies

    def _run_gallery_dump(self, url: str, limit: int = 50) -> list[dict[str, Any]]:
        commands: list[list[str]] = []
        if shutil.which("gallery-dl"):
            commands.append(["gallery-dl"])
        commands.append([sys.executable, "-m", "gallery_dl"])

        cookie_candidates = self._cookie_candidates() or [""]
        for cookie in cookie_candidates:
            args = [
                "--range",
                f"1-{max(1, int(limit))}",
                "--dump-json",
                url,
            ]
            if cookie:
                args = ["--cookies", cookie, *args]
            for base_cmd in commands:
                try:
                    self._wait_for_backoff()
                    self._before_network_request()
                    proc = subprocess.run(
                        [*base_cmd, *args],
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        timeout=45,
                        check=False,
                        creationflags=CREATE_NO_WINDOW
                    )
                    if proc.returncode == 0:
                        self._last_success_cookie_path = cookie if cookie else None
                        self._register_network_result(True)
                        return parse_gallery_rows(proc.stdout or "")
                    merged_err = f"{proc.stdout or ''}\n{proc.stderr or ''}"
                    self._register_network_result(False, self._looks_rate_limited(merged_err))
                except subprocess.TimeoutExpired:
                    self._register_network_result(False)
                    continue
        return []

    def _fetch_profile_activity_html(self, include_replies: bool = True) -> list[dict[str, Any]]:
        try:
            from playwright.sync_api import sync_playwright
        except Exception as exc:
            self.log_fn(self.profile.uid, f"Posts HTML no disponible (playwright): {exc}")
            return []

        username = self.profile.username
        if not username:
            return []

        rows: list[dict[str, Any]] = []

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(viewport={"width": 1360, "height": 900})

                cookie_candidates = self._cookie_candidates()
                applied = False
                for cookie_file in cookie_candidates:
                    cookies = self._load_netscape_cookies(cookie_file)
                    if cookies:
                        try:
                            context.add_cookies(cookies)
                            applied = True
                            break
                        except Exception:
                            continue
                if not applied:
                    self.log_fn(self.profile.uid, "Posts HTML: ejecutando sin cookies validas aplicadas")

                page = context.new_page()
                target_url = f"https://x.com/{username}/with_replies" if include_replies else f"https://x.com/{username}"
                self._wait_for_backoff()
                self._before_network_request()
                page.goto(target_url, wait_until="domcontentloaded", timeout=45000)
                self._register_network_result(True)
                page.wait_for_timeout(1800)
                for _ in range(3):
                    page.mouse.wheel(0, 1500)
                    page.wait_for_timeout(600)

                raw = page.evaluate(
                    r"""
                    () => {
                        const normalizeStatus = (href) => {
                            if (!href) return null;
                            const m = String(href).match(/https?:\/\/(?:www\.)?(?:x|twitter)\.com\/(?:([^\/?#]+)\/status|i(?:\/web)?\/status)\/(\d+)/i);
                            if (!m) return null;
                            if ((m[1] || '').toLowerCase() === 'i') {
                                return `https://x.com/i/web/status/${m[2]}`;
                            }
                            return m[1] ? `https://x.com/${m[1]}/status/${m[2]}` : `https://x.com/i/web/status/${m[2]}`;
                        };

                        const repostRegex = /(reposted|repost|reposte[oó]|reposteaste|repostaste|rt\s*@)/i;
                        const out = [];
                        const seen = new Set();
                        const articles = Array.from(document.querySelectorAll('article'));
                        for (const article of articles) {
                            let chosen = null;
                            const timeNode = article.querySelector('time');
                            if (timeNode && timeNode.parentElement && timeNode.parentElement.tagName === 'A') {
                                chosen = timeNode.parentElement;
                            }
                            if (!chosen) {
                                chosen = article.querySelector('a[href*="/status/"]');
                            }
                            if (!chosen) continue;

                            const canonical = normalizeStatus(chosen.href || chosen.getAttribute('href') || '');
                            if (!canonical || seen.has(canonical)) continue;
                            seen.add(canonical);

                            const text = (article.innerText || '').trim();
                            const isReply = /replying to/i.test(text);
                            const isRetweet = repostRegex.test(text);
                            const links = Array.from(article.querySelectorAll('a[href*="/status/"]'))
                                .map(a => normalizeStatus(a.href || a.getAttribute('href') || ''))
                                .filter(Boolean);
                            const quoteUrl = links.find(l => l && l !== canonical) || null;
                            out.push({ url: canonical, text, isReply, isRetweet, quoteUrl });
                        }
                        return out;
                    }
                    """
                )

                if isinstance(raw, list):
                    for item in raw:
                        if not isinstance(item, dict):
                            continue
                        url = normalize_status_url(str(item.get("url") or ""))
                        sid = status_id_from_url(url or "") if url else None
                        if not url or not isinstance(sid, int):
                            continue
                        rows.append(
                            {
                                "url": url,
                                "status_id": sid,
                                "author_handle": username.lower(),
                                "actor_handle": username.lower(),
                                "reply_id": 1 if bool(item.get("isReply", False)) else None,
                                "text": str(item.get("text") or "").strip(),
                                "has_video": False,
                                "has_image": False,
                                "has_media": False,
                                "is_retweet": bool(item.get("isRetweet", False)),
                                "quote_url": normalize_status_url(str(item.get("quoteUrl") or "")) if item.get("quoteUrl") else None,
                                "quote_status_id": status_id_from_url(str(item.get("quoteUrl") or "")) if item.get("quoteUrl") else None,
                                "quote_text": "",
                                "quote_has_video": False,
                                "quote_has_image": False,
                                "quote_has_media": False,
                            }
                        )

                context.close()
                browser.close()
        except Exception as exc:
            self._register_network_result(False, self._looks_rate_limited(str(exc)))
            self.log_fn(self.profile.uid, f"Posts HTML fallo: {exc}")
            return []

        return rows

    def _fetch_retweets_html(self) -> list[dict[str, Any]]:
        try:
            from playwright.sync_api import sync_playwright
        except Exception as exc:
            self.log_fn(self.profile.uid, f"Retweets HTML no disponible (playwright): {exc}")
            return []

        username = self.profile.username
        if not username:
            return []

        rows_out: list[dict[str, Any]] = []
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(viewport={"width": 1360, "height": 900})

                applied = False
                cookie_file = None
                for cookie_file in self._cookie_candidates():
                    cookies = self._load_netscape_cookies(cookie_file)
                    if cookies:
                        try:
                            context.add_cookies(cookies)
                            applied = True
                            break
                        except Exception:
                            continue

                page = context.new_page()
                self._wait_for_backoff()
                self._before_network_request()
                page.goto(f"https://x.com/{username}", wait_until="domcontentloaded", timeout=45000)
                self._register_network_result(True)
                page.wait_for_timeout(1800)
                for _ in range(2):
                    page.mouse.wheel(0, 1400)
                    page.wait_for_timeout(600)

                raw_rows = page.evaluate(
                    r"""
                    () => {
                        const normalizeStatus = (href) => {
                            if (!href) return null;
                            const m = String(href).match(/https?:\/\/(?:www\.)?(?:x|twitter)\.com\/(?:([^\/?#]+)\/status|i(?:\/web)?\/status)\/(\d+)/i);
                            if (!m) return null;
                            if ((m[1] || '').toLowerCase() === 'i') {
                                return `https://x.com/i/web/status/${m[2]}`;
                            }
                            return m[1] ? `https://x.com/${m[1]}/status/${m[2]}` : `https://x.com/i/web/status/${m[2]}`;
                        };

                        const repostRegex = /(reposted|repost|reposte[oó]|reposteaste|repostaste)/i;
                        const out = [];
                        const seen = new Set();
                        const articles = Array.from(document.querySelectorAll('article'));
                        for (const article of articles) {
                            const text = (article.innerText || '').trim();
                            if (!repostRegex.test(text)) {
                                continue;
                            }

                            let chosen = null;
                            const timeNode = article.querySelector('time');
                            if (timeNode && timeNode.parentElement && timeNode.parentElement.tagName === 'A') {
                                chosen = timeNode.parentElement;
                            }
                            if (!chosen) {
                                chosen = article.querySelector('a[href*="/status/"]');
                            }
                            if (!chosen) {
                                continue;
                            }

                            const abs = chosen.href || chosen.getAttribute('href') || '';
                            const canonical = normalizeStatus(abs);
                            if (!canonical || seen.has(canonical)) {
                                continue;
                            }
                            seen.add(canonical);
                            const hasVideo = !!article.querySelector('video');
                            const hasImage = !!article.querySelector('img[src*="twimg"], img[alt*="Image" i]');
                            const links = Array.from(article.querySelectorAll('a[href*="/status/"]'))
                                .map(a => normalizeStatus(a.href || a.getAttribute('href') || ''))
                                .filter(Boolean);
                            const quoteUrl = links.find(l => l && l !== canonical) || null;
                            out.push({ url: canonical, text, hasVideo, hasImage, quoteUrl });
                        }
                        return out;
                    }
                    """
                )
                if isinstance(raw_rows, list):
                    for item in raw_rows:
                        if not isinstance(item, dict):
                            continue
                        rows_out.append(
                            {
                                "url": str(item.get("url") or "").strip(),
                                "text": str(item.get("text") or "").strip(),
                                "has_video": bool(item.get("hasVideo", False)),
                                "has_image": bool(item.get("hasImage", False)),
                                "quote_url": str(item.get("quoteUrl") or "").strip(),
                            }
                        )

                context.close()
                browser.close()
        except Exception as exc:
            self._register_network_result(False, self._looks_rate_limited(str(exc)))
            self.log_fn(self.profile.uid, f"Retweets HTML fallo: {exc}")
            return []

        out_rows: list[dict[str, Any]] = []
        for row in rows_out:
            canonical = normalize_status_url(str(row.get("url") or ""))
            if not canonical:
                continue
            sid = status_id_from_url(canonical)
            if not isinstance(sid, int):
                continue
            has_image = bool(row.get("has_image", False))
            has_video = bool(row.get("has_video", False))
            out_rows.append(
                {
                    "url": canonical,
                    "status_id": sid,
                    "author_handle": None,
                    "text": str(row.get("text") or "").strip(),
                    "has_video": has_video,
                    "has_image": has_image,
                    "has_media": bool(has_video or has_image),
                    "is_retweet": True,
                    "quote_url": normalize_status_url(str(row.get("quote_url") or "")) if row.get("quote_url") else None,
                    "quote_status_id": status_id_from_url(str(row.get("quote_url") or "")) if row.get("quote_url") else None,
                    "quote_text": "",
                    "quote_has_video": False,
                    "quote_has_image": False,
                    "quote_has_media": False,
                }
            )
        return out_rows

    def _load_netscape_cookies(self, file_path: str) -> list[dict[str, Any]]:
        if not file_path: return []
        cookies: list[dict[str, Any]] = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                for raw in f:
                    line = raw.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split("\t")
                    if len(parts) < 7:
                        continue
                    domain, _include_subdomains, path, secure_flag, expires, name, value = parts[:7]
                    if not domain or not name:
                        continue
                    cookie = {
                        "name": name,
                        "value": value,
                        "domain": domain,
                        "path": path or "/",
                        "secure": str(secure_flag).upper() == "TRUE",
                    }
                    try:
                        exp = int(float(expires))
                        if exp > 0:
                            cookie["expires"] = exp
                    except Exception:
                        pass
                    cookies.append(cookie)
        except Exception:
            return []
        return cookies

    def _load_state(self) -> None:
        if not os.path.isfile(self.state_path):
            return
        try:
            with open(self.state_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return
        for key in ("post", "reply", "retweet"):
            values = data.get(key) or []
            out = set()
            for value in values:
                try:
                    out.add(int(value))
                except Exception:
                    pass
            self.seen_ids[key] = out
            self.bootstrapped[key] = bool(data.get(f"{key}_bootstrapped", False))

    def _save_state(self) -> None:
        data = {}
        for key, values in self.seen_ids.items():
            trimmed = sorted(values)[-MAX_SEEN_IDS:]
            data[key] = trimmed
            data[f"{key}_bootstrapped"] = bool(self.bootstrapped.get(key, False))
        ensure_dir(os.path.dirname(self.state_path))
        with open(self.state_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _append_event_files(self, event: dict[str, Any]) -> None:
        event_dir = self._event_dir_for(event)
        event["event_dir"] = event_dir

        event_json = os.path.join(event_dir, "event.json")
        with open(event_json, "w", encoding="utf-8") as jf:
            json.dump(event, jf, ensure_ascii=False, indent=2)

        text = (
            f"[{event['time']}] {event['kind'].upper()}\n"
            f"status_id={event.get('status_id')}\n"
            f"url={event.get('url') or '-'}\n"
            f"url_reply={event.get('reply_to_url') or '-'}\n"
            f"url_citada={event.get('quote_url') or '-'}\n"
            f"author={event.get('author_handle') or '-'}\n"
            f"text={event.get('text_preview') or '-'}\n"
            f"text_reply={event.get('reply_to_text_preview') or '-'}\n"
            f"text_cita={event.get('quote_text_preview') or '-'}\n"
        )
        event_txt = os.path.join(event_dir, "event.txt")
        with open(event_txt, "w", encoding="utf-8", errors="replace") as tf:
            tf.write(text)

    def _collect_media_files(self, base_dir: str) -> set[str]:
        out: set[str] = set()
        if not os.path.isdir(base_dir):
            return out
        media_ext = {
            ".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp",
            ".mp4", ".mov", ".webm", ".mkv", ".m4v", ".avi",
        }
        for root, _dirs, files in os.walk(base_dir):
            for name in files:
                ext = os.path.splitext(name)[1].lower()
                if ext in media_ext:
                    out.add(os.path.abspath(os.path.join(root, name)))
        return out

    def _download_event(self, event: dict[str, Any]) -> list[str]:
        mode = self.profile.download_mode
        if mode == DOWNLOAD_MODE_NOTIFY_ONLY:
            return []

        if mode == DOWNLOAD_MODE_OWN_MEDIA_ONLY:
            author = (event.get("author_handle") or "").lower()
            account = (self.profile.username or "").lower()
            if author != account:
                return []

        base_event_dir = self._event_dir_for(event)
        cookie_candidates = self._cookie_candidates() or [""]

        def download_url(target_url: str, target_dir: str) -> list[str]:
            target_url = (target_url or "").strip()
            if not target_url:
                return []

            before_files = self._collect_media_files(target_dir)
            gallery_ok = False
            gallery_commands: list[list[str]] = []
            if shutil.which("gallery-dl"):
                gallery_commands.append(["gallery-dl"])
            gallery_commands.append([sys.executable, "-m", "gallery_dl"])

            for cookie in cookie_candidates:
                args = ["-D", target_dir, target_url]
                if cookie:
                    args = ["--cookies", cookie, *args]
                for base_cmd in gallery_commands:
                    self._wait_for_backoff()
                    self._before_network_request()
                    proc = subprocess.run(
                        [*base_cmd, *args],
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        timeout=180,
                        check=False,
                        creationflags=CREATE_NO_WINDOW
                    )
                    if proc.returncode == 0:
                        self._last_success_cookie_path = cookie if cookie else None
                        self._register_network_result(True)
                        self.log_fn(self.profile.uid, f"Descarga OK (gallery-dl): {target_url}")
                        gallery_ok = True
                        break
                    merged_err = f"{proc.stdout or ''}\n{proc.stderr or ''}"
                    self._register_network_result(False, self._looks_rate_limited(merged_err))
                if gallery_ok:
                    break

            if gallery_ok:
                after_files = self._collect_media_files(target_dir)
                return sorted(after_files - before_files)

            yt_bases: list[list[str]] = []
            if shutil.which("yt-dlp"):
                yt_bases.append(["yt-dlp"])
            yt_bases.append([sys.executable, "-m", "yt_dlp"])
            out_tpl = os.path.join(target_dir, "%(title).120s [%(id)s].%(ext)s")

            for cookie in cookie_candidates:
                for base in yt_bases:
                    cmd = [*base, "-o", out_tpl]
                    if cookie:
                        cmd += ["--cookies", cookie]
                    cmd += [target_url]
                    self._wait_for_backoff()
                    self._before_network_request()
                    proc = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        timeout=240,
                        check=False,
                        creationflags=CREATE_NO_WINDOW
                    )
                    if proc.returncode == 0:
                        self._last_success_cookie_path = cookie if cookie else None
                        self._register_network_result(True)
                        self.log_fn(self.profile.uid, f"Descarga OK (yt-dlp): {target_url}")
                        after_files = self._collect_media_files(target_dir)
                        return sorted(after_files - before_files)
                    merged_err = f"{proc.stdout or ''}\n{proc.stderr or ''}"
                    self._register_network_result(False, self._looks_rate_limited(merged_err))

            self.log_fn(self.profile.uid, f"Descarga fallo total: {target_url}")
            return []

        def _extract_pic_links(text: str) -> list[str]:
            out: list[str] = []
            raw = str(text or "")
            if not raw:
                return out
            patterns = [
                r"https?://(?:www\.)?pic\.x\.com/[A-Za-z0-9]+",
                r"https?://(?:www\.)?x\.com/i/web/status/\d+",
            ]
            for pat in patterns:
                for match in re.findall(pat, raw, flags=re.IGNORECASE):
                    m = str(match).strip()
                    if m and m not in out:
                        out.append(m)
            return out

        main_url = str(event.get("url") or "").strip()
        reply_url = str(event.get("reply_to_url") or "").strip()
        quote_url = str(event.get("quote_url") or "").strip()
        quote_chain_urls = [
            normalize_status_url(str(u) or "") for u in (event.get("_quote_chain_urls") or [])
            if isinstance(u, str) and str(u).strip()
        ]
        reply_thread_urls = [
            normalize_status_url(str(u) or "") for u in (event.get("_reply_thread_urls") or [])
            if isinstance(u, str) and str(u).strip()
        ]

        main_files = download_url(main_url, ensure_dir(os.path.join(base_event_dir, "main")))
        reply_files: list[str] = []
        if reply_url and reply_url not in {main_url, quote_url}:
            reply_files = download_url(reply_url, ensure_dir(os.path.join(base_event_dir, "reply_parent")))

        reply_thread_group_files: dict[str, list[str]] = {}
        seen_reply_thread: set[str] = set()
        for idx, rurl in enumerate(reply_thread_urls, start=1):
            if not rurl or rurl in seen_reply_thread or rurl in {main_url, reply_url, quote_url}:
                continue
            seen_reply_thread.add(rurl)
            key = f"reply_thread_{idx}"
            reply_thread_group_files[key] = download_url(rurl, ensure_dir(os.path.join(base_event_dir, key)))

        quote_files: list[str] = []
        if quote_url:
            quote_files = download_url(quote_url, ensure_dir(os.path.join(base_event_dir, "quoted")))

        if not quote_files:
            quoted_text_candidates = [
                str(event.get("quote_text") or ""),
                str(event.get("quote_text_preview") or ""),
            ]
            quoted_link_fallback: list[str] = []
            for txt in quoted_text_candidates:
                for ln in _extract_pic_links(txt):
                    if ln not in quoted_link_fallback:
                        quoted_link_fallback.append(ln)
            if quoted_link_fallback:
                quoted_dir = ensure_dir(os.path.join(base_event_dir, "quoted"))
                aggregated: list[str] = []
                seen_fallback_files: set[str] = set()
                for qlnk in quoted_link_fallback:
                    files = download_url(qlnk, quoted_dir)
                    if files:
                        self.log_fn(self.profile.uid, f"Descarga OK (quoted-links-fallback): {qlnk}")
                    for fp in files:
                        if fp not in seen_fallback_files:
                            seen_fallback_files.add(fp)
                            aggregated.append(fp)
                if aggregated:
                    quote_files = aggregated

        quote_chain_group_files: dict[str, list[str]] = {}
        seen_quote_chain: set[str] = set()
        for idx, qurl in enumerate(quote_chain_urls, start=1):
            if not qurl or qurl in seen_quote_chain or qurl in {main_url, reply_url, quote_url}:
                continue
            seen_quote_chain.add(qurl)
            key = f"quote_chain_{idx}"
            quote_chain_group_files[key] = download_url(qurl, ensure_dir(os.path.join(base_event_dir, key)))

        media_groups = {
            "main": main_files,
            "reply_parent": reply_files,
            "quoted": quote_files,
        }
        media_groups.update(reply_thread_group_files)
        media_groups.update(quote_chain_group_files)
        event["_downloaded_media_groups"] = media_groups

        out = []
        seen = set()
        all_group_files: list[str] = []
        for values in media_groups.values():
            all_group_files.extend(values)
        for p in all_group_files:
            if p not in seen:
                seen.add(p)
                out.append(p)
        return out

    def _fetch_status_context(self, status_url: str, status_id: int | None = None) -> dict[str, Any]:
        target_url = normalize_status_url(status_url or "")
        if not target_url:
            return {}
        rows = self._run_gallery_dump(target_url, limit=5)
        if not rows:
            return {}

        picked = None
        if isinstance(status_id, int):
            for row in rows:
                if row.get("status_id") == status_id:
                    picked = row
                    break
        if picked is None:
            for row in rows:
                if normalize_status_url(str(row.get("url") or "")) == target_url:
                    picked = row
                    break
        if picked is None:
            picked = rows[0]

        picked_url = normalize_status_url(str(picked.get("url") or "")) or target_url
        picked_quote_chain = picked.get("quote_chain") if isinstance(picked.get("quote_chain"), list) else []

        return {
            "url": picked_url,
            "status_id": picked.get("status_id") if isinstance(picked.get("status_id"), int) else status_id,
            "text": str(picked.get("text") or "").strip(),
            "has_image": bool(picked.get("has_image", False)),
            "has_video": bool(picked.get("has_video", False)),
            "has_media": bool(picked.get("has_media", False)),
            "quote_url": normalize_status_url(str(picked.get("quote_url") or "")),
            "quote_status_id": picked.get("quote_status_id") if isinstance(picked.get("quote_status_id"), int) else None,
            "reply_to_url": normalize_status_url(str(picked.get("reply_to_url") or "")),
            "reply_to_status_id": picked.get("reply_to_status_id") if isinstance(picked.get("reply_to_status_id"), int) else None,
            "quote_chain": picked_quote_chain,
            "conversation_id": picked.get("conversation_id") if isinstance(picked.get("conversation_id"), int) else None,
        }

    def _fetch_status_text_playwright(self, status_url: str) -> str:
        try:
            from playwright.sync_api import sync_playwright
        except Exception:
            return ""

        target_url = normalize_status_url(status_url or "")
        if not target_url:
            return ""

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(viewport={"width": 1360, "height": 900})

                applied = False
                cookie_file = None
                for cookie_file in self._cookie_candidates():
                    cookies = self._load_netscape_cookies(cookie_file)
                    if cookies:
                        try:
                            context.add_cookies(cookies)
                            applied = True
                            break
                        except Exception:
                            continue

                page = context.new_page()
                self._wait_for_backoff()
                self._before_network_request()
                page.goto(target_url, wait_until="domcontentloaded", timeout=45000)
                self._register_network_result(True)
                page.wait_for_timeout(2200)

                try:
                    reveal = page.locator("button:has-text('Show'), button:has-text('Mostrar')").first
                    if reveal and reveal.count() > 0:
                        reveal.click(timeout=1000)
                        page.wait_for_timeout(900)
                except Exception:
                    pass

                text = page.evaluate(
                    r'''
                    () => {
                        const article = document.querySelector('article');
                        if (!article) return '';
                        const chunks = [];
                        const nodes = article.querySelectorAll('[data-testid="tweetText"]');
                        for (const n of nodes) {
                            const t = (n.innerText || '').trim();
                            if (t) chunks.push(t);
                        }
                        if (chunks.length) return chunks.join('\n');
                        return (article.innerText || '').trim();
                    }
                    '''
                )

                context.close()
                browser.close()
                return str(text or "").strip()
        except Exception as exc:
            self._register_network_result(False, self._looks_rate_limited(str(exc)))
            return ""

    def _download_full_account_once(self) -> None:
        if self.full_account_sync_done:
            return
        if self.profile.download_mode != DOWNLOAD_MODE_ALL_ACTIVITY:
            return

        username = (self.profile.username or "").strip()
        if not username:
            return

        out_dir = ensure_dir(os.path.join(self.profile.output_dir, self.profile.uid, "media", "full_account"))
        cookie_candidates = self._cookie_candidates() or [""]

        urls: list[str] = []
        urls.append(f"https://x.com/{username}")
        if self.profile.detect_reply:
            urls.append(f"https://x.com/{username}/with_replies")

        self.log_fn(self.profile.uid, "Descarga cuenta completa iniciada (puede tardar)")

        gallery_commands: list[list[str]] = []
        if shutil.which("gallery-dl"):
            gallery_commands.append(["gallery-dl"])
        gallery_commands.append([sys.executable, "-m", "gallery_dl"])

        for target_url in urls:
            done = False
            for cookie in cookie_candidates:
                args = ["-D", out_dir, target_url]
                if cookie:
                    args = ["--cookies", cookie, *args]
                for base_cmd in gallery_commands:
                    self._wait_for_backoff()
                    self._before_network_request()
                    proc = subprocess.run(
                        [*base_cmd, *args],
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        timeout=1200,
                        check=False,
                        creationflags=CREATE_NO_WINDOW
                    )
                    if proc.returncode == 0:
                        self._last_success_cookie_path = cookie if cookie else None
                        self._register_network_result(True)
                        done = True
                        break
                    merged_err = f"{proc.stdout or ''}\n{proc.stderr or ''}"
                    self._register_network_result(False, self._looks_rate_limited(merged_err))
                if done:
                    break

            if not done:
                self.log_fn(self.profile.uid, f"Descarga cuenta completa parcial fallo: {target_url}")

        self.full_account_sync_done = True
        self.log_fn(self.profile.uid, "Descarga cuenta completa finalizada")

    def _build_events_from_posts(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        account = (self.profile.username or "").lower()

        for row in rows:
            sid = row.get("status_id")
            if not isinstance(sid, int):
                continue
            author = str(row.get("author_handle") or "").strip().lower()
            if author and author != account:
                continue

            row_text = str(row.get("text") or "")
            if bool(row.get("is_retweet", False)):
                continue
            if REPOST_TEXT_RE.search(row_text):
                continue

            is_reply = (row.get("reply_id") is not None) or (row.get("reply_to_status_id") is not None)
            kind = "reply" if is_reply else "post"

            out.append(
                {
                    "kind": kind,
                    "status_id": sid,
                    "url": row.get("url"),
                    "conversation_id": row.get("conversation_id"),
                    "reply_to_url": row.get("reply_to_url"),
                    "reply_to_status_id": row.get("reply_to_status_id"),
                    "text": row_text,
                    "author_handle": author,
                    "has_media": bool(row.get("has_media", False)),
                    "has_image": bool(row.get("has_image", False)),
                    "has_video": bool(row.get("has_video", False)),
                    "quote_url": row.get("quote_url"),
                    "quote_status_id": row.get("quote_status_id"),
                    "quote_text": str(row.get("quote_text") or ""),
                    "quote_has_media": bool(row.get("quote_has_media", False)),
                    "quote_has_image": bool(row.get("quote_has_image", False)),
                    "quote_has_video": bool(row.get("quote_has_video", False)),
                    "quote_chain": list(row.get("quote_chain") or []),
                }
            )
        return out

    def _build_events_from_retweets(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        account = (self.profile.username or "").strip().lstrip("@").lower()
        for row in rows:
            sid = row.get("status_id")
            if not isinstance(sid, int):
                continue
            url = str(row.get("url") or "").strip()
            original_author = str(author_from_status_url(url) or "").strip().lstrip("@").lower()
            if not original_author:
                original_author = str(row.get("author_handle") or "").strip().lstrip("@").lower()
            actor = str(row.get("actor_handle") or account or "").strip().lstrip("@").lower()

            out.append(
                {
                    "kind": "retweet",
                    "status_id": sid,
                    "url": url or row.get("url"),
                    "conversation_id": row.get("conversation_id"),
                    "reply_to_url": row.get("reply_to_url"),
                    "reply_to_status_id": row.get("reply_to_status_id"),
                    "text": str(row.get("text") or ""),
                    "author_handle": original_author,
                    "actor_handle": actor,
                    "has_media": bool(row.get("has_media", False)),
                    "has_image": bool(row.get("has_image", False)),
                    "has_video": bool(row.get("has_video", False)),
                    "quote_url": row.get("quote_url"),
                    "quote_status_id": row.get("quote_status_id"),
                    "quote_text": str(row.get("quote_text") or ""),
                    "quote_has_media": bool(row.get("quote_has_media", False)),
                    "quote_has_image": bool(row.get("quote_has_image", False)),
                    "quote_has_video": bool(row.get("quote_has_video", False)),
                    "quote_chain": list(row.get("quote_chain") or []),
                }
            )
        return out

    def _notify_and_store(self, event: dict[str, Any]) -> None:
        event_work = dict(event)
        
        self.log_fn(self.profile.uid, f"¡Nueva actividad! ({event_work['kind'].upper()} ID: {event_work.get('status_id')}) - Detectado con: {getattr(self, 'last_used_cookie', 'Desconocida')}")

        event_url = normalize_status_url(str(event_work.get("url") or ""))
        event_sid = event_work.get("status_id") if isinstance(event_work.get("status_id"), int) else None

        context_rows: list[dict[str, Any]] = []
        if event_url:
            context_rows = self._run_gallery_dump(event_url, limit=30) 

        current_ctx: dict[str, Any] = {}
        for row in context_rows:
            if row.get("status_id") == event_sid or normalize_status_url(str(row.get("url") or "")) == event_url:
                current_ctx = row
                break
        if not current_ctx and context_rows:
            current_ctx = context_rows[0]

        if current_ctx:
            ctx_text = str(current_ctx.get("text") or "").strip()
            if ctx_text:
                event_work["text"] = ctx_text
            for key in ("quote_url", "quote_status_id", "quote_text", "reply_to_url", "reply_to_status_id", "conversation_id"):
                ctx_val = current_ctx.get(key)
                if ctx_val:
                    event_work[key] = ctx_val
            event_work["has_image"] = bool(event_work.get("has_image") or current_ctx.get("has_image"))
            event_work["has_video"] = bool(event_work.get("has_video") or current_ctx.get("has_video"))
            event_work["has_media"] = bool(event_work.get("has_media") or current_ctx.get("has_media"))

        text_full = (event_work.get("text") or "").strip()
        
        reply_to_url = str(event_work.get("reply_to_url") or "").strip()
        reply_to_status_id = event_work.get("reply_to_status_id")
        quote_url = str(event_work.get("quote_url") or "").strip()
        quote_status_id = event_work.get("quote_status_id")

        reply_thread: list[dict[str, Any]] = []
        event_url_norm = normalize_status_url(event_url) if event_url else ""
        for row in context_rows:
            u = normalize_status_url(str(row.get("url") or ""))
            if u and u != event_url_norm:
                reply_thread.append(row)
        
        reply_thread.sort(key=lambda x: x.get("status_id") or 0)

        quote_chain: list[dict[str, Any]] = list(event_work.get("quote_chain") or [])
        if quote_url and (not quote_chain or not str(event_work.get("quote_text") or "").strip()):
            try:
                q_rows = self._run_gallery_dump(quote_url, limit=2)
                if q_rows:
                    if not quote_chain:
                        quote_chain.append(q_rows[0])
                    if str(q_rows[0].get("text") or "").strip():
                        event_work["quote_text"] = str(q_rows[0].get("text") or "").strip()
            except Exception:
                pass

        if quote_url and not str(event_work.get("quote_text") or "").strip():
            try:
                q_ctx = self._fetch_status_context(quote_url, quote_status_id if isinstance(quote_status_id, int) else None)
                if q_ctx:
                    q_ctx_text = str(q_ctx.get("text") or "").strip()
                    if q_ctx_text:
                        event_work["quote_text"] = q_ctx_text
                    if not quote_chain:
                        quote_chain.append(q_ctx)
            except Exception:
                pass

        if quote_url and not str(event_work.get("quote_text") or "").strip():
            pw_quote_text = self._fetch_status_text_playwright(quote_url)
            if pw_quote_text:
                event_work["quote_text"] = pw_quote_text
                if not quote_chain:
                    quote_chain.append({
                        "url": quote_url,
                        "status_id": quote_status_id if isinstance(quote_status_id, int) else status_id_from_url(quote_url),
                        "text": pw_quote_text,
                        "has_video": False,
                        "has_image": False,
                        "has_media": False,
                    })

        main_clean, quote_from_main = split_main_and_quote_text(text_full, str(event_work.get("quote_text") or ""))
        if main_clean:
            text_full = main_clean
            event_work["text"] = main_clean
        if not str(event_work.get("quote_text") or "").strip() and quote_from_main:
            event_work["quote_text"] = quote_from_main

        reply_thread_media_urls = [
            str(x.get("url") or "") for x in reply_thread 
            if str(x.get("url") or "").strip() and x.get("has_media")
        ]
        quote_chain_media_urls = [
            str(x.get("url") or "") for x in quote_chain 
            if str(x.get("url") or "").strip() and x.get("has_media")
        ]

        event_work["_quote_chain_urls"] = quote_chain_media_urls
        event_work["_reply_thread_urls"] = reply_thread_media_urls

        parent_has_media = True
        if reply_to_url:
            parent_has_media = False
            for r in reply_thread:
                if normalize_status_url(str(r.get("url") or "")) == normalize_status_url(reply_to_url):
                    parent_has_media = bool(r.get("has_media"))
                    break
        
        orig_rtu = event_work.get("reply_to_url")
        if not parent_has_media:
            event_work["reply_to_url"] = "" 

        downloaded_media: list[str] = []
        if self.profile.download_mode in {DOWNLOAD_MODE_SELECTED_ACTIVITY, DOWNLOAD_MODE_OWN_MEDIA_ONLY}:
            self.log_fn(self.profile.uid, "Descargando archivos multimedia (omitiendo posts de solo texto)...")
            downloaded_media = self._download_event(event_work)
            self.log_fn(self.profile.uid, "Descarga completada. Lanzando popup.")

        event_work["reply_to_url"] = orig_rtu 

        reply_to_text = ""
        if reply_thread:
            reply_to_text = str(reply_thread[0].get("text") or "").strip()
        if not reply_to_text:
            reply_to_text = str(event_work.get("reply_to_text") or "").strip()

        quote_text_preview = (event_work.get("quote_text") or "").strip()
        if not quote_text_preview and quote_chain:
            quote_text_preview = str(quote_chain[0].get("text") or "").strip()
        if not quote_text_preview and quote_url:
            quote_text_preview = "(Cita sin texto o post no disponible)"

        context_posts: list[dict[str, Any]] = []
        if reply_thread:
            for idx, item in enumerate(reply_thread, start=1):
                context_posts.append({
                    "role": "reply_thread",
                    "title": f"Parte del hilo ({idx}/{len(reply_thread)})",
                    "url": item.get("url"),
                    "status_id": item.get("status_id"),
                    "text": item.get("text") or "(sin texto)",
                })

        if quote_chain:
            for idx, item in enumerate(quote_chain, start=1):
                context_posts.append({
                    "role": "quote_chain",
                    "title": f"Quote {idx}",
                    "url": item.get("url"),
                    "status_id": item.get("status_id"),
                    "text": item.get("text") or "(sin texto)",
                })

        event_payload = {
            "uid": self.profile.uid,
            "username": self.profile.username,
            "output_dir": self.profile.output_dir,
            "used_cookie": getattr(self, "last_used_cookie", "Desconocida"),
            "kind": event["kind"],
            "status_id": event_work.get("status_id"),
            "url": event_work.get("url"),
            "reply_to_url": reply_to_url,
            "reply_to_status_id": reply_to_status_id,
            "quote_url": event_work.get("quote_url"),
            "quote_status_id": event_work.get("quote_status_id"),
            "author_handle": event_work.get("author_handle"),
            "actor_handle": event_work.get("actor_handle"),
            "actor_avatar": None,
            "time": now_iso(),
            "text_full": text_full,
            "text_preview": text_full[:280] if text_full else "",
            "reply_to_text_preview": reply_to_text[:280],
            "quote_text_preview": quote_text_preview[:280],
            "has_image": bool(event_work.get("has_image", False)),
            "has_video": bool(event_work.get("has_video", False)),
            "has_media": bool(event_work.get("has_media", False)),
            "quote_has_image": bool(event_work.get("quote_has_image", False)),
            "quote_has_video": bool(event_work.get("quote_has_video", False)),
            "quote_has_media": bool(event_work.get("quote_has_media", False)),
            "download_mode": self.profile.download_mode,
            "downloaded_media": downloaded_media,
            "downloaded_media_groups": dict(event_work.get("_downloaded_media_groups") or {}),
            "context_posts": context_posts,
            "popup_auto_close": bool(self.profile.popup_auto_close),
            "popup_close_seconds": int(self.profile.popup_close_seconds),
            "popup_autoplay_media": bool(self.profile.popup_autoplay_media),
        }

        self._append_event_files(event_payload)
        self.history_fn(event_payload)

        if self.profile.notify_popup:
            self.notify_fn(event_payload)

    def _ingest_events(self, events: list[dict[str, Any]]) -> int:
        new_count = 0
        for event in events:
            kind = str(event.get("kind") or "")
            sid = event.get("status_id")
            if kind not in self.seen_ids or not isinstance(sid, int):
                continue
            if sid in self.seen_ids[kind]:
                continue

            self.seen_ids[kind].add(sid)
            new_count += 1

            if not getattr(self, "_session_pillar_established", False):
                continue

            self._notify_and_store(event)

        for key in self.seen_ids:
            if len(self.seen_ids[key]) > MAX_SEEN_IDS:
                self.seen_ids[key] = set(sorted(self.seen_ids[key])[-MAX_SEEN_IDS:])

        self._save_state()
        return new_count

    def _bootstrap_if_needed(self, events: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
        if not self.bootstrapped.get(key, False):
            for event in events:
                sid = event.get("status_id")
                if isinstance(sid, int):
                    self.seen_ids[key].add(sid)
            self.bootstrapped[key] = True
            self._save_state()
            self.log_fn(self.profile.uid, f"Baseline {key}: {len(self.seen_ids[key])} item(s)")
            return []
        return events

    def _get_seconds_to_next_exact_time(self, exact_times_str: str) -> float:
        now = datetime.now()
        times = []
        for t in exact_times_str.replace(";", ",").split(","):
            t = t.strip()
            if not t: continue
            try:
                h, m = map(int, t.split(":"))
                times.append(datetime.strptime(f"{h:02d}:{m:02d}", "%H:%M").time())
            except Exception:
                pass
        if not times:
            return -1.0
        
        next_dt = None
        times.sort()
        for t in times:
            candidate = datetime.combine(now.date(), t)
            if candidate > now:
                next_dt = candidate
                break
        
        if not next_dt:
            next_dt = datetime.combine(now.date() + timedelta(days=1), times[0])
            
        return (next_dt - now).total_seconds()

    def run(self) -> None:
        if getattr(self.profile, "fresh_baseline", False):
            self.log_fn(self.profile.uid, "Iniciando con baseline limpio (Ignorando historial previo)")
            self._save_state()
        else:
            self._load_state()

        has_history = any(len(v) > 0 for v in self.seen_ids.values())
        if has_history:
            self._session_pillar_established = True
            
        try:
            self._migrate_legacy_output()
        except Exception as exc:
            self.log_fn(self.profile.uid, f"Migracion legacy fallo: {exc}")
        try:
            self._migrate_events_by_date()
        except Exception as exc:
            self.log_fn(self.profile.uid, f"Migracion eventos por fecha fallo: {exc}")
            
        # -- Manejo del Retraso Inicial --
        delay_mins = getattr(self.profile, "start_delay_minutes", 0)
        if delay_mins > 0:
            self.log_fn(self.profile.uid, f"Esperando {delay_mins} minutos antes de iniciar...")
            self.stop_event.wait(delay_mins * 60.0)
            
        if self.stop_event.is_set():
            self.log_fn(self.profile.uid, "Monitor detenido antes de iniciar.")
            return

        self.log_fn(self.profile.uid, f"Monitor iniciado para @{self.profile.username}")

        try:
            self._download_full_account_once()
        except Exception as exc:
            self.log_fn(self.profile.uid, f"Error descarga cuenta completa: {exc}")

        consecutive_empty = 0
        worker_start_time = time.time()

        while not self.stop_event.is_set():
            # -- Comprobar Tiempo Límite (TTL) --
            stop_after = getattr(self.profile, "stop_after_minutes", 0)
            if stop_after > 0:
                elapsed_mins = (time.time() - worker_start_time) / 60.0
                if elapsed_mins >= stop_after:
                    self.log_fn(self.profile.uid, f"Tiempo límite de {stop_after} minutos alcanzado. Deteniendo monitor automáticamente.")
                    break

            # --- OBTENER LA COOKIE ACTIVA ACTUAL ---
            assigned_cookie = self.cookie_manager.get_active_cookie()
            self._current_cycle_cookies = [assigned_cookie] if assigned_cookie else [""]

            if assigned_cookie:
                cookie_filename = os.path.basename(assigned_cookie)
                cookie_map = self.cookie_manager.get_cookie_map()
                self.last_used_cookie = cookie_map.get(cookie_filename, cookie_filename)
            else:
                self.last_used_cookie = "Sin cookie"

            try:
                username = self.profile.username
                if not username:
                    self.log_fn(self.profile.uid, "Sin username valido")
                    self.stop_event.wait(3)
                    continue

                timeline_rows: list[dict[str, Any]] = []
                saw_any_rows = False
                cycle_new_items = 0

                if self.profile.detect_post or self.profile.detect_reply:
                    posts_rows = self._run_gallery_dump(f"https://x.com/{username}/with_replies", limit=15)
                    if not posts_rows:
                        posts_rows = self._fetch_profile_activity_html(include_replies=True)
                    else:
                        html_rows = self._fetch_profile_activity_html(include_replies=True)
                        merged: dict[int, dict[str, Any]] = {}
                        for row in [*posts_rows, *html_rows]:
                            sid = row.get("status_id")
                            if isinstance(sid, int):
                                if sid not in merged:
                                    merged[sid] = row
                                else:
                                    existing = merged[sid]
                                    if not existing.get("text") and row.get("text"):
                                        existing["text"] = row.get("text")
                                    if existing.get("reply_id") is None and row.get("reply_id") is not None:
                                        existing["reply_id"] = row.get("reply_id")
                                    if not existing.get("author_handle") and row.get("author_handle"):
                                        existing["author_handle"] = row.get("author_handle")
                                    existing["has_image"] = bool(existing.get("has_image", False) or row.get("has_image", False))
                                    existing["has_video"] = bool(existing.get("has_video", False) or row.get("has_video", False))
                                    existing["has_media"] = bool(existing.get("has_media", False) or row.get("has_media", False) or existing["has_image"] or existing["has_video"])
                        posts_rows = list(merged.values())

                    timeline_rows = posts_rows
                    if posts_rows:
                        saw_any_rows = True

                    events = self._build_events_from_posts(posts_rows)

                    if self.profile.detect_post:
                        post_events = [e for e in events if e["kind"] == "post"]
                        post_events = self._bootstrap_if_needed(post_events, "post")
                        cycle_new_items += self._ingest_events(post_events)

                    if self.profile.detect_reply:
                        reply_events = [e for e in events if e["kind"] == "reply"]
                        reply_events = self._bootstrap_if_needed(reply_events, "reply")
                        cycle_new_items += self._ingest_events(reply_events)

                if self.profile.detect_retweet:
                    retweet_rows = [row for row in timeline_rows if bool(row.get("is_retweet", False))]
                    html_retweet_rows = self._fetch_retweets_html()
                    if html_retweet_rows:
                        merged_retweets: dict[int, dict[str, Any]] = {}
                        for row in [*retweet_rows, *html_retweet_rows]:
                            sid = row.get("status_id")
                            if not isinstance(sid, int):
                                continue
                            if sid not in merged_retweets:
                                merged_retweets[sid] = row
                                continue
                            existing = merged_retweets[sid]
                            if not existing.get("text") and row.get("text"):
                                existing["text"] = row.get("text")
                            for key in (
                                "author_handle",
                                "actor_handle",
                                "reply_to_url",
                                "reply_to_status_id",
                                "quote_url",
                                "quote_status_id",
                                "quote_text",
                            ):
                                if not existing.get(key) and row.get(key):
                                    existing[key] = row.get(key)
                            existing["has_image"] = bool(existing.get("has_image", False) or row.get("has_image", False))
                            existing["has_video"] = bool(existing.get("has_video", False) or row.get("has_video", False))
                            existing["has_media"] = bool(existing.get("has_media", False) or row.get("has_media", False) or existing["has_image"] or existing["has_video"])
                        retweet_rows = list(merged_retweets.values())

                    if not retweet_rows:
                        retweet_rows = html_retweet_rows
                    if retweet_rows:
                        saw_any_rows = True
                    retweet_events = self._build_events_from_retweets(retweet_rows)
                    retweet_events = self._bootstrap_if_needed(retweet_events, "retweet")
                    cycle_new_items += self._ingest_events(retweet_events)

            except Exception as exc:
                self.log_fn(self.profile.uid, f"Error monitor: {exc}")

            if saw_any_rows:
                consecutive_empty = 0
                if not getattr(self, "_session_pillar_established", False):
                    self._session_pillar_established = True
                    self.log_fn(self.profile.uid, "Pilar inicial establecido con éxito. Solo se alertará sobre actividad nueva de ahora en adelante.")
                else:
                    if cycle_new_items == 0:
                        cookie_used = getattr(self, '_last_success_cookie_path', None)
                        self.log_fn(self.profile.uid, f"Chequeo silencioso usando [{self.last_used_cookie}]: 0 items nuevos detectados.")
            else:
                consecutive_empty += 1
                if consecutive_empty in {30, 120}:
                    self.log_fn(self.profile.uid, "Advertencia: muchos ciclos sin datos nuevos o conexión fallida. Reintentando de fondo...")

            # -- Cálculo del Tiempo de Espera --
            schedule_mode = getattr(self.profile, "schedule_mode", "Intervalos")
            wait_seconds = 0
            
            if schedule_mode == "Horas Exactas":
                exact_times = getattr(self.profile, "exact_times", "")
                sec_to_next = self._get_seconds_to_next_exact_time(exact_times)
                if sec_to_next > 0:
                    wait_seconds = sec_to_next
                    next_t = datetime.now() + timedelta(seconds=wait_seconds)
                    self.log_fn(self.profile.uid, f"Modo Horas Exactas: Durmiendo hasta las {next_t.strftime('%H:%M:%S')}...")
                else:
                    self.log_fn(self.profile.uid, "Modo Horas Exactas sin horas validas. Usando intervalo...")
                    schedule_mode = "Intervalos"
                    
            if schedule_mode == "Intervalos":
                min_wait = max(MIN_POLL_SECONDS, int(self.profile.poll_min_seconds or DEFAULT_POLL_SECONDS))
                max_wait = max(min_wait, int(self.profile.poll_max_seconds or min_wait))
                if max_wait == min_wait:
                    wait_seconds = min_wait
                else:
                    wait_seconds = random.randint(min_wait, max_wait)
                
            self.stop_event.wait(wait_seconds)

        self.log_fn(self.profile.uid, "Monitor detenido")


class ProfilerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1080x860")
        self.root.minsize(980, 750)
        
        # --- Mejoras visuales (Mas bonito) ---
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")
            
        style.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=[12, 6])
        style.configure("TLabelframe.Label", font=("Segoe UI", 10, "bold"), foreground="#005fb8")
        style.configure("TButton", font=("Segoe UI", 9), padding=5)
        style.map("TButton", background=[("active", "#e1e1e1")])

        self.base_dir = os.path.dirname(__file__)
        self.state_dir = ensure_dir(os.path.join(self.base_dir, "state"))
        self.default_cookies_dir = ensure_dir(os.path.join(self.base_dir, "cookies"))
        self.cookies_dir = self.default_cookies_dir
        self.output_default_dir = ensure_dir(os.path.join(self.base_dir, "output"))
        self.profiles_path = os.path.join(self.base_dir, "profiles.json")

        self.ui_queue: queue.Queue[tuple[str, Any]] = queue.Queue()
        self.profiles: dict[str, Profile] = {}
        self.workers: dict[str, MonitorWorker] = {}
        self.log_by_uid: dict[str, list[str]] = {}
        self.log_filter_var = tk.StringVar(value="TODOS")
        self.popup_history_by_uid: dict[str, list[dict[str, Any]]] = {}
        self.history_window: tk.Toplevel | None = None
        self.history_uid_var = tk.StringVar(value="")
        self.history_listbox: tk.Listbox | None = None
        self.history_detail: tk.Text | None = None
        self.history_media_label: ttk.Label | None = None
        self.history_media_button_frame: ttk.Frame | None = None
        self.history_video_frame: ttk.Frame | None = None
        self._history_vlc_players: list[Any] = []
        self._history_media_refs: list[Any] = []
        self._history_view_rows: list[dict[str, Any]] = []
        self.popup_monitor_var = tk.StringVar(value="Automatico")

        self.uid_var = tk.StringVar(value=self._new_uid())
        self.username_var = tk.StringVar(value="")
        self.detect_post_var = tk.BooleanVar(value=True)
        self.detect_reply_var = tk.BooleanVar(value=False)
        self.detect_retweet_var = tk.BooleanVar(value=False)
        self.notify_popup_var = tk.BooleanVar(value=True)
        self.download_mode_var = tk.StringVar(value=DOWNLOAD_MODE_LABELS[DOWNLOAD_MODE_NOTIFY_ONLY])
        self.output_dir_var = tk.StringVar(value=self.output_default_dir)
        self.poll_min_seconds_var = tk.StringVar(value=str(DEFAULT_POLL_SECONDS))
        self.poll_max_seconds_var = tk.StringVar(value=str(DEFAULT_POLL_SECONDS))
        self.popup_auto_close_var = tk.BooleanVar(value=False)
        self.popup_close_seconds_var = tk.StringVar(value="12")
        self.popup_autoplay_media_var = tk.BooleanVar(value=False)
        self.auto_start_var = tk.BooleanVar(value=False)
        self.fresh_baseline_var = tk.BooleanVar(value=False)
        self.run_at_startup_var = tk.BooleanVar(value=False)
        self.language_var = tk.StringVar(value="Español")
        self.cookies_dir_var = tk.StringVar(value=self.cookies_dir)
        
        self.schedule_mode_var = tk.StringVar(value="Intervalos")
        self.exact_times_var = tk.StringVar(value="")
        self.start_delay_var = tk.StringVar(value="0")
        self.stop_after_var = tk.StringVar(value="0")
        
        # Variables Globales de Cookies
        self.cookie_cooldown_base_var = tk.StringVar(value="180")
        self.cookie_cooldown_rand_var = tk.StringVar(value="60")
        
        self._last_global_cookie = None
        self._vlc_instance = self._init_vlc_instance()

        self._load_global_config()
        
        # Inicializar Cookie Manager Global
        self.cookie_manager = GlobalCookieManager(
            self.cookies_dir, 
            get_base_timeout_fn=lambda: max(0.0, float(self.cookie_cooldown_base_var.get() or 180)),
            get_rand_timeout_fn=lambda: max(0.0, float(self.cookie_cooldown_rand_var.get() or 60)),
            get_cookie_map_fn=self._load_cookie_map
        )

        # Asegurar que SISTEMA existe en los logs desde el inicio
        self.log_by_uid.setdefault("SISTEMA", [])

        self._build_ui()
        self._apply_translations()
        self._bind_global_mousewheel()
        self._load_profiles()
        self._auto_start_monitors()
        self.root.after(120, self._drain_ui_queue)
        self.root.after(1000, self._update_cookie_ui)

    def _init_vlc_instance(self):
        if not vlc_mod:
            print("[DEBUG VLC] El módulo 'vlc' no está importado. ¿Falta pip install python-vlc?")
            return None
            
        if sys.platform.startswith("win"):
            for candidate in (
                r"C:\Program Files\VideoLAN\VLC",
                r"C:\Program Files (x86)\VideoLAN\VLC",
            ):
                try:
                    if os.path.isdir(candidate):
                        try:
                            os.add_dll_directory(candidate)
                        except Exception as e:
                            print(f"[DEBUG VLC] Error al añadir directorio DLL ({candidate}): {e}")
                            pass
                        plugin_path = os.path.join(candidate, "plugins")
                        if os.path.isdir(plugin_path):
                            os.environ.setdefault("VLC_PLUGIN_PATH", plugin_path)
                except Exception:
                    continue
        try:
            args = [
                "--quiet",
                "--no-video-title-show",
                "--avcodec-hw=none",  # <-- CAMBIO CLAVE: Desactivada la decodificación por hardware problemática
                "--drop-late-frames",
                "--skip-frames"
            ]
            return vlc_mod.Instance(args)
        except Exception as e:
            print(f"[DEBUG VLC] Error crítico al crear la instancia de VLC: {e}")
            try:
                # Intento de rescate sin argumentos
                return vlc_mod.Instance([])
            except Exception as e2:
                print(f"[DEBUG VLC] Falló también el intento de rescate: {e2}")
                return None

    def _build_embedded_video_player(self, host: tk.Widget, video_path: str):
        """
        Retorna (player, error_msg). Si falla, player es None y error_msg contiene la razón.
        """
        if not self._vlc_instance:
            return None, "Instancia principal de VLC no inicializada."
        if not os.path.isfile(video_path):
            return None, f"Archivo de video no encontrado:\n{os.path.basename(video_path)}"

        try:
            # 1. Asegurar que el widget host esté visible y renderizado
            host.update_idletasks()
            host.update()  # Forzar actualización en el MainLoop
            handle = host.winfo_id()

            if not handle:
                return None, "El widget contenedor no generó un handle (HWND) válido."

            player = self._vlc_instance.media_player_new()
            media = self._vlc_instance.media_new(video_path)
            player.set_media(media)
            player._media_path = video_path # Guardamos para el modo fullscreen

            # 2. Asociar el handle según el Sistema Operativo
            if sys.platform.startswith("win"):
                player.set_hwnd(handle)
            elif sys.platform.startswith("linux"):
                player.set_xwindow(handle)
            elif sys.platform == "darwin":
                player.set_nsobject(handle)

            player.video_set_scale(0)
            
            # 3. Forzar stop previo (limpieza) y play inicial
            player.stop()
            player.play()
            
            return player, ""
        except Exception as e:
            return None, f"Excepción interna de VLC:\n{str(e)}"

    def _release_vlc_players(self, players: list[Any]) -> None:
        for p in players:
            try:
                p.stop()
            except Exception:
                pass
            try:
                p.release()
            except Exception:
                pass

    def _fmt_ms(self, value_ms: int) -> str:
        total = max(0, int(value_ms // 1000))
        minutes = total // 60
        seconds = total % 60
        return f"{minutes:02d}:{seconds:02d}"

    def _bind_player_controls(self, scope_widget: tk.Widget, click_target: tk.Widget, player, controls_parent: tk.Widget, autoplay_var: tk.BooleanVar | None = None) -> None:
        if not player:
            return

        ctrl = tk.Frame(controls_parent, bg="#1e1e1e", padx=10, pady=5)
        ctrl.pack(fill="x", pady=(0, 6))

        pos_var = tk.DoubleVar(controls_parent, value=0.0)
        vol_var = tk.DoubleVar(controls_parent, value=100.0)
        dragging = {"active": False}
        length_cache = {"value": 0}

        btn_opts = {
            "bg": "#1e1e1e", "fg": "white", "bd": 0,
            "activebackground": "#3a3a3a", "activeforeground": "white",
            "font": ("Segoe UI", 11), "cursor": "hand2"
        }

        play_btn = tk.Button(ctrl, text="▶", width=3, **btn_opts)
        stop_btn = tk.Button(ctrl, text="⏹", width=3, **btn_opts)
        fs_btn = tk.Button(ctrl, text="⛶", width=3, **btn_opts)
        
        time_lbl = tk.Label(ctrl, text="00:00 / 00:00", bg="#1e1e1e", fg="#cccccc", font=("Segoe UI", 9))
        
        slider = ttk.Scale(ctrl, from_=0, to=100, orient="horizontal", variable=pos_var)
        
        vol_lbl = tk.Label(ctrl, text="🔊", bg="#1e1e1e", fg="white", font=("Segoe UI", 10))
        vol_slider = ttk.Scale(ctrl, from_=0, to=100, orient="horizontal", variable=vol_var)

        def _restart_and_play() -> None:
            try:
                player.stop()
                player.set_position(0.0)
                player.play()
                play_btn.config(text="⏸")
            except Exception:
                pass

        def toggle_play_pause(_event=None) -> None:
            try:
                st = player.get_state()
                ended_state = getattr(vlc_mod.State, "Ended", None)
                
                if st == ended_state:
                    _restart_and_play()
                    return

                if player.is_playing():
                    player.pause()
                    play_btn.config(text="▶")
                else:
                    player.play()
                    play_btn.config(text="⏸")
            except Exception:
                pass

        def do_stop(_event=None) -> None:
            try:
                player.stop()
                pos_var.set(0)
                time_lbl.config(text="00:00 / 00:00")
                play_btn.config(text="▶")
            except Exception:
                pass

        def _set_volume(_event=None):
            try:
                player.audio_set_volume(int(vol_var.get()))
            except Exception:
                pass

        def toggle_fullscreen(_event=None):
            path = getattr(player, "_media_path", None)
            if not path:
                return

            fs_win = tk.Toplevel(scope_widget.winfo_toplevel())
            fs_win.attributes("-fullscreen", True)
            fs_win.attributes("-topmost", True)
            fs_win.configure(bg="black")

            fs_host = tk.Frame(fs_win, bg="black")
            fs_host.pack(fill="both", expand=True)

            def close_fs(e=None):
                if not hasattr(fs_win, "_fs_player"):
                    return
                p = fs_win._fs_player
                current_time = p.get_time()
                p.stop()
                p.release()
                fs_win.destroy()
                if current_time > 0:
                    player.set_time(current_time)
                player.play()
                play_btn.config(text="⏸")

            fs_win.bind("<Escape>", close_fs)
            fs_win.bind("<Double-Button-1>", close_fs)
            fs_host.bind("<Double-Button-1>", close_fs)

            fs_player, err = self._build_embedded_video_player(fs_host, path)
            if fs_player:
                fs_win._fs_player = fs_player
                cur_time = player.get_time()
                player.pause()
                play_btn.config(text="▶")
                if cur_time > 0:
                    fs_player.set_time(cur_time)
                fs_player.play()
            else:
                fs_win.destroy()

        play_btn.config(command=toggle_play_pause)
        stop_btn.config(command=do_stop)
        fs_btn.config(command=toggle_fullscreen)

        click_target.bind("<Button-1>", toggle_play_pause)
        vol_slider.bind("<ButtonRelease-1>", _set_volume)
        slider.bind("<ButtonPress-1>", lambda _e: dragging.__setitem__("active", True))

        def _release_seek(_event=None) -> None:
            dragging["active"] = False
            try:
                length = int(player.get_length())
                if length <= 0:
                    length = int(length_cache["value"])
                if length > 0:
                    player.set_position(max(0.0, min(1.0, float(pos_var.get()) / 100.0)))
            except Exception:
                pass

        slider.bind("<ButtonRelease-1>", _release_seek)

        play_btn.pack(side="left", padx=2)
        stop_btn.pack(side="left", padx=2)
        time_lbl.pack(side="left", padx=(8, 8))
        slider.pack(side="left", fill="x", expand=True, padx=(5, 10))
        vol_lbl.pack(side="left", padx=(5, 2))
        vol_slider.pack(side="left", padx=(0, 5))
        vol_slider.config(length=60)
        fs_btn.pack(side="left", padx=(5, 0)) # El nuevo botón de fullscreen

        if autoplay_var is not None:
            loop_chk = tk.Checkbutton(ctrl, text="Bucle", variable=autoplay_var, bg="#1e1e1e", fg="#cccccc", selectcolor="#3a3a3a", activebackground="#1e1e1e", activeforeground="white", bd=0, cursor="hand2")
            loop_chk.pack(side="left", padx=(10, 5))

        def tick() -> None:
            if not scope_widget.winfo_exists():
                return
            try:
                st = player.get_state()
                ended_state = getattr(vlc_mod.State, "Ended", None)
                
                if st == ended_state:
                    if autoplay_var is not None and bool(autoplay_var.get()):
                        _restart_and_play()
                    else:
                        play_btn.config(text="▶")
                        pos_var.set(100.0)
                        
                cur = int(player.get_time())
                length = int(player.get_length())
                if length > 0:
                    length_cache["value"] = length
                    
                if not dragging["active"] and length_cache["value"] > 0 and st != ended_state:
                    pos_var.set(max(0.0, min(100.0, (cur / max(1, length_cache["value"])) * 100.0)))
                    
                time_lbl.configure(text=f"{self._fmt_ms(cur)} / {self._fmt_ms(length_cache['value'])}")
                
                if player.is_playing() and play_btn.cget("text") != "⏸":
                    play_btn.config(text="⏸")

            except Exception:
                pass

            scope_widget.after(300, tick)

        tick()

    def _new_uid(self) -> str:
        return f"uid_{int(time.time())}_{os.urandom(2).hex()}"

    def _get_profile_label(self, uid: str) -> str:
        if uid == "SISTEMA":
            return "🔧 EVENTOS DE SISTEMA"
        profile = self.profiles.get(uid)
        if profile and profile.username:
            return f"@{profile.username} ({uid})"
        return uid

    def _get_uid_from_label(self, label: str) -> str:
        label = label.strip()
        if label == "🔧 EVENTOS DE SISTEMA":
            return "SISTEMA"
        if label.endswith(")") and " (" in label:
            return label.rsplit(" (", 1)[-1].rstrip(")")
        return label

    def _global_config_path(self) -> str:
        return os.path.join(self.base_dir, "profiler_config.json")

    def _load_cookie_map(self) -> dict[str, str]:
        path = os.path.join(self.cookies_dir, "cookie_usernames.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _load_global_config(self) -> None:
        path = self._global_config_path()
        if not os.path.isfile(path):
            self.cookies_dir = ensure_dir(self.cookies_dir)
            self.cookies_dir_var.set(self.cookies_dir)
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            self.cookies_dir = ensure_dir(self.cookies_dir)
            self.cookies_dir_var.set(self.cookies_dir)
            return
        
        self.run_at_startup_var.set(bool(data.get("run_at_startup", False)))
        self.cookie_cooldown_base_var.set(str(data.get("cookie_cooldown_base", "180")))
        self.cookie_cooldown_rand_var.set(str(data.get("cookie_cooldown_rand", "60")))
        self.popup_monitor_var.set(data.get("popup_monitor", "Automatico"))
        self.language_var.set(data.get("language", "Español"))
        
        configured_cookies_dir = str(data.get("cookies_dir") or "").strip()
        if configured_cookies_dir:
            self.cookies_dir = os.path.abspath(configured_cookies_dir)
        self.cookies_dir = ensure_dir(self.cookies_dir)
        self.cookies_dir_var.set(self.cookies_dir)

    def _save_global_config(self, silent=False) -> None:
        path = self._global_config_path()
        selected_cookies_dir = str(self.cookies_dir_var.get() or "").strip()
        self.cookies_dir = ensure_dir(os.path.abspath(selected_cookies_dir or self.default_cookies_dir))
        self.cookies_dir_var.set(self.cookies_dir)
        self.cookie_manager.cookies_dir = self.cookies_dir
        
        data = {
            "run_at_startup": bool(self.run_at_startup_var.get()),
            "cookies_dir": self.cookies_dir,
            "cookie_cooldown_base": self.cookie_cooldown_base_var.get(),
            "cookie_cooldown_rand": self.cookie_cooldown_rand_var.get(),
            "popup_monitor": self.popup_monitor_var.get(),
            "language": self.language_var.get()
        }
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            if not silent:
                messagebox.showinfo(APP_TITLE, self._tr("Configuración global guardada."))
        except Exception:
            pass

    def _on_language_changed(self, event=None) -> None:
        self._save_global_config(silent=True)
        self._apply_translations()

    def _tr(self, text: str) -> str:
        lang = self.language_var.get()
        if lang == "Español" or lang not in TRANSLATIONS:
            return text
        return TRANSLATIONS[lang].get(text.strip(), text)

    def _tr_reverse(self, text: str) -> str:
        text_strip = text.strip()
        for lang, mapping in TRANSLATIONS.items():
            for k, v in mapping.items():
                if v.strip() == text_strip:
                    return k
        return text_strip

    def _apply_translations(self) -> None:
        def walk(widget):
            if isinstance(widget, (tk.Label, ttk.Label, tk.Button, ttk.Button, ttk.Checkbutton, ttk.Radiobutton, ttk.LabelFrame)):
                try:
                    if not hasattr(widget, "_orig_text"):
                        widget._orig_text = widget.cget("text")
                    widget.config(text=self._tr(widget._orig_text))
                except Exception:
                    pass
            
            # Notebook tabs
            if isinstance(widget, ttk.Notebook):
                try:
                    tabs = widget.tabs()
                    if not hasattr(widget, "_orig_tabs"):
                        widget._orig_tabs = {}
                        for t in tabs:
                            widget._orig_tabs[t] = widget.tab(t, "text")
                    
                    for t in tabs:
                        orig_text = widget._orig_tabs.get(t, "")
                        if orig_text:
                            widget.tab(t, text=self._tr(orig_text))
                except Exception:
                    pass
            for child in widget.winfo_children():
                walk(child)

        walk(self.root)

        if hasattr(self, 'download_mode_combo'):
            current_val = self._tr_reverse(self.download_mode_var.get())
            self.download_mode_combo["values"] = [
                self._tr(DOWNLOAD_MODE_LABELS[DOWNLOAD_MODE_NOTIFY_ONLY]),
                self._tr(DOWNLOAD_MODE_LABELS[DOWNLOAD_MODE_ALL_ACTIVITY]),
                self._tr(DOWNLOAD_MODE_LABELS[DOWNLOAD_MODE_SELECTED_ACTIVITY]),
                self._tr(DOWNLOAD_MODE_LABELS[DOWNLOAD_MODE_OWN_MEDIA_ONLY]),
            ]
            self.download_mode_var.set(self._tr(current_val))

        if hasattr(self, 'schedule_mode_combo'):
            current_val = self._tr_reverse(self.schedule_mode_var.get())
            self.schedule_mode_combo["values"] = [self._tr("Intervalos"), self._tr("Horas Exactas")]
            self.schedule_mode_var.set(self._tr(current_val))

    def _apply_run_at_startup(self) -> None:
        if not sys.platform.startswith("win"):
            return
        try:
            import winreg
        except Exception:
            return

        app_name = "XProfilerSentinel"
        
        # CAMBIO: Usar pythonw.exe en lugar de python.exe para evitar la ventana CMD
        exe_path = sys.executable
        if exe_path.lower().endswith("python.exe"):
            alt_exe = os.path.join(os.path.dirname(exe_path), "pythonw.exe")
            if os.path.exists(alt_exe):
                exe_path = alt_exe
                
        cmd = f'"{exe_path}" "{os.path.abspath(__file__)}"'
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\\Microsoft\\Windows\\CurrentVersion\\Run", 0, winreg.KEY_ALL_ACCESS)
        except Exception:
            try:
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\\Microsoft\\Windows\\CurrentVersion\\Run")
            except Exception:
                return

        try:
            if bool(self.run_at_startup_var.get()):
                try:
                    winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, cmd)
                except Exception:
                    pass
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                except FileNotFoundError:
                    pass
                except Exception:
                    pass
        finally:
            try:
                winreg.CloseKey(key)
            except Exception:
                pass

    def _on_toggle_run_at_startup(self) -> None:
        self._save_global_config()
        self._apply_run_at_startup()

    def _download_mode_key(self) -> str:
        val = self._tr_reverse(self.download_mode_var.get())
        reverse = {v: k for k, v in DOWNLOAD_MODE_LABELS.items()}
        return reverse.get(val, DOWNLOAD_MODE_NOTIFY_ONLY)

    def _auto_start_monitors(self) -> None:
        started_any = False
        for uid, profile in list(self.profiles.items()):
            if not getattr(profile, "auto_start", False):
                continue
            if uid in self.workers:
                continue
            worker = MonitorWorker(
                profile=profile,
                state_dir=self.state_dir,
                log_fn=self._log,
                notify_fn=self._notify_popup,
                history_fn=self._push_history,
                cookie_manager=self.cookie_manager
            )
            self.workers[uid] = worker
            worker.start()
            started_any = True
        if started_any:
            self._refresh_profile_list()

    def _build_ui(self) -> None:
        shell = ttk.Frame(self.root)
        shell.pack(fill="both", expand=True)

        top = ttk.Frame(shell, padding=10)
        top.pack(fill="x")
        ttk.Label(top, text=APP_TITLE, font=("Segoe UI", 16, "bold"), foreground="#005fb8").pack(side="left")
        ttk.Button(top, text="Nueva instancia", command=self._open_new_instance).pack(side="right")

        self.notebook = ttk.Notebook(shell)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # --- Pestaña 1: Monitoreo ---
        self.tab_monitor = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_monitor, text=" Monitoreo y Perfiles ")
        self._build_monitor_tab()

        # --- Pestaña 2: Opciones Globales ---
        self.tab_cookies = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_cookies, text=" ⚙️ Opciones Globales ")
        self._build_global_options_tab()

        # --- Pestaña 3: Logs ---
        self.tab_logs = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_logs, text=" Registros (Logs) ")
        self._build_log_tab()

    def _build_monitor_tab(self) -> None:
        body = self.tab_monitor
        left = ttk.Frame(body)
        left.pack(side="left", fill="y", padx=(0, 10))

        right = ttk.Frame(body)
        right.pack(side="left", fill="both", expand=True)

        prof_box = ttk.LabelFrame(left, text="Perfiles Guardados")
        prof_box.pack(fill="y", expand=True)

        self.profile_list = tk.Listbox(prof_box, height=25, width=34, font=("Consolas", 9, "bold"))
        self.profile_list.pack(fill="y", expand=True, padx=6, pady=6)
        self.profile_list.bind("<<ListboxSelect>>", self._on_select_profile)

        btns = ttk.Frame(prof_box)
        btns.pack(fill="x", padx=6, pady=(0, 6))
        ttk.Button(btns, text="Nuevo UID", command=self._reset_form).pack(fill="x", pady=2)
        ttk.Button(btns, text="Guardar perfil", command=self._save_profile).pack(fill="x", pady=2)
        ttk.Button(btns, text="Eliminar perfil", command=self._delete_profile).pack(fill="x", pady=2)
        ttk.Separator(btns, orient="horizontal").pack(fill="x", pady=4)
        ttk.Button(btns, text="▶ Iniciar monitor", command=self._start_selected).pack(fill="x", pady=2)
        ttk.Button(btns, text="⏹ Detener monitor", command=self._stop_selected).pack(fill="x", pady=2)
        ttk.Separator(btns, orient="horizontal").pack(fill="x", pady=4)
        ttk.Button(btns, text="Ver Historial de Popups", command=self._open_history_window).pack(fill="x", pady=2)

        # Configuracion
        cfg = ttk.LabelFrame(right, text="Configuracion de deteccion del Perfil")
        cfg.pack(fill="x")

        row = 0
        ttk.Label(cfg, text="UID:").grid(row=row, column=0, sticky="w", padx=8, pady=5)
        ttk.Entry(cfg, textvariable=self.uid_var, state="readonly", width=34).grid(row=row, column=1, sticky="w", padx=8, pady=5)

        row += 1
        ttk.Label(cfg, text="Cuenta X (@usuario o URL):").grid(row=row, column=0, sticky="w", padx=8, pady=5)
        ttk.Entry(cfg, textvariable=self.username_var, width=34).grid(row=row, column=1, sticky="w", padx=8, pady=5)

        row += 1
        detect_frame = ttk.Frame(cfg)
        detect_frame.grid(row=row, column=0, columnspan=2, sticky="w", padx=8, pady=5)
        ttk.Checkbutton(detect_frame, text="Detectar posts", variable=self.detect_post_var).pack(side="left", padx=(0, 10))
        ttk.Checkbutton(detect_frame, text="Detectar replies", variable=self.detect_reply_var).pack(side="left", padx=(0, 10))
        ttk.Checkbutton(detect_frame, text="Detectar retweets", variable=self.detect_retweet_var).pack(side="left")

        row += 1
        ttk.Checkbutton(cfg, text="Mostrar popup de alerta", variable=self.notify_popup_var).grid(row=row, column=0, sticky="w", padx=8, pady=5)
        ttk.Checkbutton(cfg, text="Auto-reproducir gif/video", variable=self.popup_autoplay_media_var).grid(row=row, column=1, sticky="w", padx=8, pady=5)

        row += 1
        ttk.Label(cfg, text="Modo descarga:").grid(row=row, column=0, sticky="w", padx=8, pady=5)
        self.download_mode_combo = ttk.Combobox(
            cfg,
            textvariable=self.download_mode_var,
            values=[
                DOWNLOAD_MODE_LABELS[DOWNLOAD_MODE_NOTIFY_ONLY],
                DOWNLOAD_MODE_LABELS[DOWNLOAD_MODE_ALL_ACTIVITY],
                DOWNLOAD_MODE_LABELS[DOWNLOAD_MODE_SELECTED_ACTIVITY],
                DOWNLOAD_MODE_LABELS[DOWNLOAD_MODE_OWN_MEDIA_ONLY],
            ],
            width=44,
            state="readonly",
        )
        self.download_mode_combo.grid(row=row, column=1, sticky="w", padx=8, pady=5)

        row += 1
        ttk.Button(cfg, text="Advertencia descarga", command=self._show_download_warning).grid(row=row, column=1, sticky="w", padx=8, pady=5)

        row += 1
        ttk.Label(cfg, text="Ruta salida:").grid(row=row, column=0, sticky="w", padx=8, pady=5)
        ttk.Entry(cfg, textvariable=self.output_dir_var, width=44).grid(row=row, column=1, sticky="w", padx=8, pady=5)
        ttk.Button(cfg, text="Elegir carpeta", command=self._pick_output_dir).grid(row=row, column=2, sticky="w", padx=8, pady=5)

        row += 1
        ttk.Label(cfg, text="Chequeo min (seg):").grid(row=row, column=0, sticky="w", padx=8, pady=5)
        ttk.Entry(cfg, textvariable=self.poll_min_seconds_var, width=10).grid(row=row, column=1, sticky="w", padx=8, pady=5)
        ttk.Label(cfg, text="Chequeo max (seg):").grid(row=row, column=2, sticky="e", padx=(8, 2), pady=5)
        ttk.Entry(cfg, textvariable=self.poll_max_seconds_var, width=10).grid(row=row, column=3, sticky="w", padx=(2, 8), pady=5)

        row += 1
        ttk.Label(cfg, text="Modo de ejecución:").grid(row=row, column=0, sticky="w", padx=8, pady=5)
        self.schedule_mode_combo = ttk.Combobox(cfg, textvariable=self.schedule_mode_var, values=["Intervalos", "Horas Exactas"], state="readonly", width=14)
        self.schedule_mode_combo.grid(row=row, column=1, sticky="w", padx=8, pady=5)
        ttk.Label(cfg, text="Horas (08:00, 14:30):").grid(row=row, column=2, sticky="e", padx=(8, 2), pady=5)
        ttk.Entry(cfg, textvariable=self.exact_times_var, width=15).grid(row=row, column=3, sticky="w", padx=(2, 8), pady=5)

        row += 1
        ttk.Label(cfg, text="Retraso inicial (min):").grid(row=row, column=0, sticky="w", padx=8, pady=5)
        ttk.Entry(cfg, textvariable=self.start_delay_var, width=10).grid(row=row, column=1, sticky="w", padx=8, pady=5)
        ttk.Label(cfg, text="Detener tras (min, 0=inf):").grid(row=row, column=2, sticky="e", padx=(8, 2), pady=5)
        ttk.Entry(cfg, textvariable=self.stop_after_var, width=10).grid(row=row, column=3, sticky="w", padx=(2, 8), pady=5)

        row += 1
        ttk.Checkbutton(cfg, text="Auto-cerrar popup", variable=self.popup_auto_close_var).grid(row=row, column=0, columnspan=2, sticky="w", padx=8, pady=5)
        ttk.Label(cfg, text="Segundos popup:").grid(row=row, column=2, sticky="e", padx=(8, 2), pady=5)
        ttk.Entry(cfg, textvariable=self.popup_close_seconds_var, width=6).grid(row=row, column=3, sticky="w", padx=(2, 8), pady=5)

        row += 1
        ttk.Checkbutton(cfg, text="Iniciar monitoreo automaticamente", variable=self.auto_start_var).grid(row=row, column=0, columnspan=2, sticky="w", padx=8, pady=5)
        ttk.Checkbutton(cfg, text="Ignorar historial (Baseline nueva)", variable=self.fresh_baseline_var).grid(row=row, column=2, columnspan=2, sticky="w", padx=8, pady=5)

        cfg.columnconfigure(1, weight=1)

    def _build_global_options_tab(self) -> None:
        parent = self.tab_cookies

        # Status Panel (Grande y Visible)
        status_frame = tk.Frame(parent, bg="#2b2b2b", padx=20, pady=20, relief="flat")
        status_frame.pack(fill="x", pady=(0, 15))

        self.lbl_active_title = tk.Label(status_frame, text="SISTEMA ACTIVO", font=("Segoe UI", 11, "bold"), fg="#ffffff", bg="#2b2b2b")
        self.lbl_active_title.pack(anchor="w")

        self.lbl_active_cookie = tk.Label(status_frame, text="Cargando estado...", font=("Segoe UI", 16, "bold"), fg="#4da6ff", bg="#2b2b2b")
        self.lbl_active_cookie.pack(anchor="w", pady=(5, 5))

        self.lbl_active_time = tk.Label(status_frame, text="Tiempo restante: -- s", font=("Segoe UI", 12), fg="#ffcc00", bg="#2b2b2b")
        self.lbl_active_time.pack(anchor="w")

        btn_force = ttk.Button(status_frame, text="🔄 Forzar Rotación Ahora", command=self._force_cookie_rotation)
        btn_force.pack(anchor="w", pady=(10, 0))

        controls_frame = tk.Frame(status_frame, bg="#2b2b2b")
        controls_frame.pack(anchor="w", pady=(10, 0))
        ttk.Button(controls_frame, text="▶️ Iniciar Todos los Monitores", command=self._start_all_monitors).pack(side="left", padx=(0, 10))
        ttk.Button(controls_frame, text="⏸️ Pausar Todos los Monitores", command=self._stop_all_monitors).pack(side="left")

        # Configuración Global
        cfg_frame = ttk.LabelFrame(parent, text="Configuración Global de Tiempos y UI")
        cfg_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(cfg_frame, text="Carpeta Global de Cookies (.txt):").grid(row=0, column=0, sticky="w", padx=10, pady=8)
        ttk.Entry(cfg_frame, textvariable=self.cookies_dir_var, width=50, state="readonly").grid(row=0, column=1, sticky="w", padx=10, pady=8)
        ttk.Button(cfg_frame, text="Cambiar carpeta", command=self._pick_cookies_dir).grid(row=0, column=2, sticky="w", padx=10, pady=8)

        ttk.Label(cfg_frame, text="Monitor para Popups (Global):").grid(row=1, column=0, sticky="w", padx=10, pady=8)
        self.popup_monitor_combo = ttk.Combobox(cfg_frame, textvariable=self.popup_monitor_var, width=47, state="readonly")
        self.popup_monitor_combo.grid(row=1, column=1, sticky="w", padx=10, pady=8)
        self.popup_monitor_combo.bind("<<ComboboxSelected>>", lambda e: self._save_global_config(silent=True))
        ttk.Button(cfg_frame, text="Actualizar monitores", command=self._refresh_popup_monitor_options).grid(row=1, column=2, sticky="w", padx=10, pady=8)

        ttk.Label(cfg_frame, text="Idioma (Global):").grid(row=2, column=0, sticky="w", padx=10, pady=8)
        self.language_combo = ttk.Combobox(cfg_frame, textvariable=self.language_var, values=["Español", "English", "Português", "Français", "Deutsch"], state="readonly", width=47)
        self.language_combo.grid(row=2, column=1, sticky="w", padx=10, pady=8)
        self.language_combo.bind("<<ComboboxSelected>>", self._on_language_changed)

        ttk.Label(cfg_frame, text="Tiempo base de rotación (Segundos):").grid(row=3, column=0, sticky="w", padx=10, pady=8)
        ttk.Entry(cfg_frame, textvariable=self.cookie_cooldown_base_var, width=15).grid(row=3, column=1, sticky="w", padx=10, pady=8)

        ttk.Label(cfg_frame, text="Tiempo aleatorio extra (Segundos):").grid(row=4, column=0, sticky="w", padx=10, pady=8)
        ttk.Entry(cfg_frame, textvariable=self.cookie_cooldown_rand_var, width=15).grid(row=4, column=1, sticky="w", padx=10, pady=8)
        
        ttk.Checkbutton(cfg_frame, text="Iniciar app con Windows (global)", variable=self.run_at_startup_var, command=self._on_toggle_run_at_startup).grid(row=5, column=0, sticky="w", padx=10, pady=8)

        ttk.Button(cfg_frame, text="💾 Guardar Configuración Global", command=self._save_global_config).grid(row=5, column=2, sticky="e", padx=10, pady=8)

        # Otras Utilidades / Sistema
        utils_frame = ttk.LabelFrame(parent, text="Otras Utilidades y Acciones de Sistema")
        utils_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(utils_frame, text="🔄 Reiniciar Aplicación (Actualizar a nuevo código)", command=self._restart_app).pack(side="left", padx=10, pady=8)
        ttk.Button(utils_frame, text="Abrir otra ventana (Nueva Instancia)", command=self._open_new_instance).pack(side="left", padx=10, pady=8)

        # Bottom Frame para info adicional
        info_frame = ttk.Frame(parent)
        info_frame.pack(fill="x", pady=(10, 0))

        self.lbl_total_cookies = ttk.Label(info_frame, text="Archivos en carpeta: 0", font=("Segoe UI", 10, "bold"))
        self.lbl_total_cookies.pack(side="left")

        ttk.Button(info_frame, text="➕ Importar archivo de Cookie (.txt)", command=self._import_cookie_file).pack(side="right", padx=5)
        ttk.Button(info_frame, text="📁 Abrir carpeta de cookies", command=lambda: self._open_media_external(self.cookies_dir)).pack(side="right", padx=5)
        
        self._refresh_popup_monitor_options()

    def _build_log_tab(self) -> None:
        log_box = ttk.Frame(self.tab_logs)
        log_box.pack(fill="both", expand=True)

        log_top = ttk.Frame(log_box)
        log_top.pack(fill="x", padx=4, pady=(4, 8))
        ttk.Label(log_top, text="Filtrar por perfil:").pack(side="left")
        self.log_filter_combo = ttk.Combobox(log_top, textvariable=self.log_filter_var, width=40, state="readonly")
        self.log_filter_combo.pack(side="left", padx=(6, 8))
        self.log_filter_combo.bind("<<ComboboxSelected>>", lambda _e: self._render_logs())
        ttk.Button(log_top, text="Refrescar lista", command=self._refresh_log_filter_options).pack(side="left")
        ttk.Button(log_top, text="Limpiar Log", command=lambda: self.log_text.delete("1.0", "end")).pack(side="right")

        self.log_text = tk.Text(log_box, wrap="word", bg="#1e1e1e", fg="#cccccc", font=("Consolas", 10))
        self.log_text.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(log_box, orient="vertical", command=self.log_text.yview)
        scroll.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=scroll.set)
        self._refresh_log_filter_options()

    def _force_cookie_rotation(self) -> None:
        self.cookie_manager.force_rotate()
        self._update_cookie_ui(force_immediate=True)
        messagebox.showinfo(APP_TITLE, "Rotación de cookie forzada. Se elegirá una nueva inmediatamente.")

    def _update_cookie_ui(self, force_immediate=False) -> None:
        try:
            active_path = self.cookie_manager.get_active_cookie()
            
            stats = self.cookie_manager.get_status()
            active_name = stats["active_cookie"]
            rem = stats["remaining_seconds"]
            total = stats["total_cookies"]
            prof = stats["profile"]

            if active_name != self._last_global_cookie:
                if self._last_global_cookie is not None and active_name is not None:
                    self._log("SISTEMA", f"Cookie global rotada a: {active_name} (@{prof})")
                self._last_global_cookie = active_name

            if active_name:
                self.lbl_active_cookie.config(text=f"Usando: {active_name} (@{prof})", fg="#88ff88")
                self.lbl_active_time.config(text=f"🔄 Rotación a la siguiente en: {rem} segundos", fg="#ffcc00")
            else:
                self.lbl_active_cookie.config(text="Ninguna (Faltan cookies en carpeta)", fg="#ff6666")
                self.lbl_active_time.config(text="🔄 Rotación detenida", fg="#aaaaaa")

            self.lbl_total_cookies.config(text=f"Archivos disponibles para rotación: {total}")
        except Exception:
            pass

        if not force_immediate:
            self.root.after(1000, self._update_cookie_ui)

    def _bind_global_mousewheel(self) -> None:
        self.root.bind_all("<MouseWheel>", self._on_global_mousewheel)
        self.root.bind_all("<Button-4>", self._on_global_mousewheel)
        self.root.bind_all("<Button-5>", self._on_global_mousewheel)

    def _on_global_mousewheel(self, event) -> None:
        widget = self.root.winfo_containing(self.root.winfo_pointerx(), self.root.winfo_pointery())
        while widget is not None:
            if hasattr(widget, "yview_scroll"):
                steps = 0
                if getattr(event, "num", None) == 4:
                    steps = -1
                elif getattr(event, "num", None) == 5:
                    steps = 1
                else:
                    delta = int(getattr(event, "delta", 0) or 0)
                    if delta != 0:
                        steps = -1 * int(delta / 120) if abs(delta) >= 120 else (-1 if delta > 0 else 1)
                if steps:
                    try:
                        widget.yview_scroll(steps, "units")
                    except Exception:
                        pass
                    return
            widget = widget.master

    def _log(self, uid: str, message: str) -> None:
        if uid == "SISTEMA":
            name_label = "🔧 EVENTOS DE SISTEMA"
        else:
            profile = self.profiles.get(uid)
            name_label = f"@{profile.username}" if profile and profile.username else uid
            
        line = f"[{now_iso()}] [{name_label}] {message}"
        self.ui_queue.put(("log", {"uid": uid, "line": line}))

    def _refresh_log_filter_options(self) -> None:
        options = ["TODOS", "🔧 EVENTOS DE SISTEMA"]
        for uid in sorted(self.log_by_uid.keys()):
            if uid != "SISTEMA":
                options.append(self._get_profile_label(uid))

        self.log_filter_combo["values"] = options
        if self.log_filter_var.get() not in options:
            self.log_filter_var.set("TODOS")
        self._render_logs()

    def _render_logs(self) -> None:
        selected_label = (self.log_filter_var.get() or "TODOS").strip()
        selected_uid = "TODOS" if selected_label == "TODOS" else self._get_uid_from_label(selected_label)

        lines: list[str] = []
        if selected_uid == "TODOS":
            merged = []
            for uid, arr in self.log_by_uid.items():
                for item in arr:
                    merged.append((item, uid))
            merged.sort(key=lambda x: x[0])
            lines = [m[0] for m in merged[-3000:]]
        else:
            lines = list(self.log_by_uid.get(selected_uid, []))[-3000:]

        self.log_text.delete("1.0", "end")
        if lines:
            self.log_text.insert("end", "\n".join(lines) + "\n")
        self.log_text.see("end")

    def _notify_popup(self, event_payload: dict[str, Any]) -> None:
        self.ui_queue.put(("popup", event_payload))

    def _push_history(self, event_payload: dict[str, Any]) -> None:
        self.ui_queue.put(("history", event_payload))

    def _drain_ui_queue(self) -> None:
        while not self.ui_queue.empty():
            kind, payload = self.ui_queue.get_nowait()
            if kind == "log":
                uid = str((payload or {}).get("uid") or "")
                line = str((payload or {}).get("line") or "")
                if uid and line:
                    bucket = self.log_by_uid.setdefault(uid, [])
                    bucket.append(line)
                    if len(bucket) > 8000:
                        self.log_by_uid[uid] = bucket[-8000:]
                    self._refresh_log_filter_options()
            elif kind == "popup":
                self._show_popup(payload)
            elif kind == "history":
                self._add_history_entry(payload)
        self.root.after(120, self._drain_ui_queue)

    def _media_label(self, event_payload: dict[str, Any]) -> str:
        has_img = bool(event_payload.get("has_image", False))
        has_vid = bool(event_payload.get("has_video", False))
        if has_img and has_vid:
            return "Imagen + Video"
        if has_vid:
            return "Video"
        if has_img:
            return "Imagen"
        return "Sin media"

    def _monitor_bounds(self) -> list[tuple[int, int, int, int]]:
        if not get_monitors:
            return []
        try:
            monitors = get_monitors() or []
        except Exception:
            return []
        out: list[tuple[int, int, int, int]] = []
        for m in monitors:
            try:
                out.append((int(m.x), int(m.y), int(m.width), int(m.height)))
            except Exception:
                continue
        return out

    def _refresh_popup_monitor_options(self) -> None:
        options = ["Automatico"]
        for idx, mon in enumerate(self._monitor_bounds(), start=1):
            mx, my, mw, mh = mon
            options.append(f"Monitor {idx}: {mw}x{mh} ({mx},{my})")
        self.popup_monitor_combo["values"] = options
        if self.popup_monitor_var.get() not in options:
            self.popup_monitor_var.set("Automatico")

    def _resolve_event_media_paths(self, event_payload: dict[str, Any]) -> list[str]:
        direct = [
            str(path).strip() for path in (event_payload.get("downloaded_media") or [])
            if isinstance(path, str) and path.strip() and os.path.isfile(path)
        ]
        if direct:
            return direct

        event_dir = str(event_payload.get("event_dir") or "").strip()
        if event_dir and os.path.isdir(event_dir):
            found_event: list[str] = []
            for root, _dirs, files in os.walk(event_dir):
                for name in files:
                    ext = os.path.splitext(name)[1].lower()
                    if ext in {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".mp4", ".mov", ".webm", ".mkv", ".m4v", ".avi"}:
                        found_event.append(os.path.abspath(os.path.join(root, name)))
            if found_event:
                return sorted(found_event)

        uid = str(event_payload.get("uid") or "").strip()
        sid = event_payload.get("status_id")
        if not uid or not isinstance(sid, int):
            return []

        base_out = str(event_payload.get("output_dir") or self.output_default_dir)
        base = os.path.join(base_out, uid, "media", str(sid))
        found: list[str] = []
        if os.path.isdir(base):
            for root, _dirs, files in os.walk(base):
                for name in files:
                    ext = os.path.splitext(name)[1].lower()
                    if ext in {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".mp4", ".mov", ".webm", ".mkv", ".m4v", ".avi"}:
                        found.append(os.path.abspath(os.path.join(root, name)))
        return sorted(found)

    def _resolve_event_media_groups(self, event_payload: dict[str, Any]) -> dict[str, list[str]]:
        raw = event_payload.get("downloaded_media_groups")
        out: dict[str, list[str]] = {"main": [], "reply_parent": [], "quoted": []}
        if isinstance(raw, dict):
            for key, values in raw.items():
                key_name = str(key or "").strip() or "group"
                current = out.setdefault(key_name, [])
                if isinstance(values, list):
                    current.extend(
                        [
                            str(p).strip() for p in values
                            if isinstance(p, str) and p.strip() and os.path.isfile(str(p).strip())
                        ]
                    )

        for key in list(out.keys()):
            dedup: list[str] = []
            seen: set[str] = set()
            for p in out.get(key, []):
                if p not in seen:
                    seen.add(p)
                    dedup.append(p)
            out[key] = dedup

        if any(out.values()):
            return out

        sid = event_payload.get("status_id")
        uid = str(event_payload.get("uid") or "").strip()
        if not uid or not isinstance(sid, int):
            return out
        base_out = str(event_payload.get("output_dir") or self.output_default_dir)
        base = os.path.join(base_out, uid, "media", str(sid))
        if not os.path.isdir(base):
            return out

        for key in os.listdir(base):
            folder = os.path.join(base, key)
            if not os.path.isdir(folder):
                continue
            all_paths = self._resolve_event_media_paths({**event_payload, "downloaded_media": [], "status_id": sid, "output_dir": base_out}).copy()
            out[key] = [
                p for p in all_paths
                if os.path.commonpath([os.path.abspath(folder), os.path.abspath(p)]) == os.path.abspath(folder)
            ]
        return out

    def _place_window_on_selected_monitor(self, win: tk.Toplevel, pref_w: int, pref_h: int) -> None:
        bounds = self._monitor_bounds()
        target = self.popup_monitor_var.get().strip()
        if not bounds or not target or target == "Automatico":
            win.geometry(f"{pref_w}x{pref_h}")
            return

        selected = None
        if target.startswith("Monitor "):
            try:
                idx = int(target.split(":")[0].split()[1]) - 1
                if 0 <= idx < len(bounds):
                    selected = bounds[idx]
            except Exception:
                selected = None

        if not selected:
            win.geometry(f"{pref_w}x{pref_h}")
            return

        mx, my, mw, mh = selected
        w = min(pref_w, max(320, mw - 40))
        h = min(pref_h, max(240, mh - 40))
        x = mx + max(0, (mw - w) // 2)
        y = my + max(0, (mh - h) // 2)
        win.geometry(f"{w}x{h}+{x}+{y}")

    def _add_history_entry(self, event_payload: dict[str, Any]) -> None:
        uid = str(event_payload.get("uid") or "").strip()
        if not uid:
            return
        bucket = self.popup_history_by_uid.setdefault(uid, [])
        bucket.append(dict(event_payload))
        if len(bucket) > 1000:
            self.popup_history_by_uid[uid] = bucket[-1000:]
            bucket = self.popup_history_by_uid[uid]

        if self.history_window and self.history_window.winfo_exists():
            if self.history_uid_var.get() == uid:
                self._refresh_history_list()

    def _download_original_avatar_for_event(self, event_payload: dict[str, Any]) -> str | None:
        kind = str(event_payload.get("kind") or "").strip().lower()
        if kind != "retweet":
            return None

        original_author = str(event_payload.get("author_handle") or "").strip().lstrip("@").lower()
        if not original_author:
            original_author = str(author_from_status_url(str(event_payload.get("url") or "")) or "")
        if not original_author:
            return None

        uid = str(event_payload.get("uid") or "").strip()
        if not uid:
            return None

        base_out = str(event_payload.get("output_dir") or self.output_default_dir)
        avatar_dir = ensure_dir(os.path.join(base_out, uid, "original_authors"))
        out_path = os.path.join(avatar_dir, f"{original_author}.jpg")
        if os.path.isfile(out_path):
            return out_path

        try:
            req = Request(f"https://unavatar.io/x/{original_author}", headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"})
            with urlopen(req, timeout=8) as resp:
                content_type = str(resp.headers.get("Content-Type") or "").lower()
                if "image" not in content_type:
                    return None
                data = resp.read()
            if not data:
                return None
            with open(out_path, "wb") as f:
                f.write(data)
            return out_path
        except Exception:
            return None

    def _open_media_external(self, path_or_url: str) -> bool:
        target = (path_or_url or "").strip()
        if not target:
            return False
        try:
            if re.match(r"^https?://", target, flags=re.IGNORECASE):
                return bool(webbrowser.open(target))
            if sys.platform.startswith("win"):
                os.startfile(target)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", target])
            else:
                subprocess.Popen(["xdg-open", target])
            return True
        except Exception:
            try:
                if sys.platform.startswith("win"):
                    subprocess.Popen(["cmd", "/c", "start", "", target], shell=False)
                    return True
            except Exception:
                pass
        return False

    def _show_popup(self, event_payload: dict[str, Any]) -> None:
        win = tk.Toplevel(self.root)
        win.title("Alerta X")
        self._place_window_on_selected_monitor(win, 980, 760)
        win.attributes("-topmost", True)

        popup_shell = ttk.Frame(win)
        popup_shell.pack(fill="both", expand=True)

        popup_canvas = tk.Canvas(popup_shell, highlightthickness=0)
        popup_scroll = ttk.Scrollbar(popup_shell, orient="vertical", command=popup_canvas.yview)
        popup_canvas.configure(yscrollcommand=popup_scroll.set)

        popup_scroll.pack(side="right", fill="y")
        popup_canvas.pack(side="left", fill="both", expand=True)

        frame = ttk.Frame(popup_canvas, padding=10)
        frame_window = popup_canvas.create_window((0, 0), window=frame, anchor="nw")

        def _on_popup_frame_configure(_event=None) -> None:
            popup_canvas.configure(scrollregion=popup_canvas.bbox("all"))

        def _on_popup_canvas_configure(event) -> None:
            popup_canvas.itemconfigure(frame_window, width=max(420, int(event.width)))

        def _on_popup_mousewheel(event) -> None:
            steps = 0
            if getattr(event, "num", None) == 4:
                steps = -1
            elif getattr(event, "num", None) == 5:
                steps = 1
            else:
                delta = int(getattr(event, "delta", 0) or 0)
                if delta:
                    steps = -1 * int(delta / 120) if abs(delta) >= 120 else (-1 if delta > 0 else 1)
            if steps:
                popup_canvas.yview_scroll(steps, "units")

        frame.bind("<Configure>", _on_popup_frame_configure)
        popup_canvas.bind("<Configure>", _on_popup_canvas_configure)
        win.bind("<MouseWheel>", _on_popup_mousewheel)
        win.bind("<Button-4>", _on_popup_mousewheel)
        win.bind("<Button-5>", _on_popup_mousewheel)
        win._vlc_players = []
        win._has_embedded_video = False

        kind = str(event_payload.get("kind") or "").upper()
        user = str(event_payload.get("username") or "")
        actor = str(event_payload.get("actor_handle") or "").strip().lstrip("@")
        original_author = str(event_payload.get("author_handle") or "").strip().lstrip("@")
        if not original_author:
            original_author = str(author_from_status_url(str(event_payload.get("url") or "")) or "")
        actor_avatar = str(event_payload.get("actor_avatar") or "").strip()
        if not actor_avatar or not os.path.isfile(actor_avatar):
            actor_avatar = str(self._download_original_avatar_for_event(event_payload) or "")
        sid = str(event_payload.get("status_id") or "")
        url = str(event_payload.get("url") or "")
        
        media_label = self._media_label(event_payload)
        download_mode = str(event_payload.get("download_mode") or DOWNLOAD_MODE_NOTIFY_ONLY)
        media_groups = self._resolve_event_media_groups(event_payload)
        
        downloaded_media: list[str] = []
        for values in media_groups.values():
            for p in values:
                if p not in downloaded_media:
                    downloaded_media.append(p)
        
        popup_autoplay_var = tk.BooleanVar(win, value=bool(event_payload.get("popup_autoplay_media", False)))
        context_posts = event_payload.get("context_posts") if isinstance(event_payload.get("context_posts"), list) else []

        ttk.Label(frame, text=f"{kind} detectado para @{user}", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 6))
        if kind == "RETWEET" and (actor or original_author):
            top_actor = ttk.Frame(frame)
            top_actor.pack(fill="x", pady=(0, 6))
            actor_text = f"retweet por: @{actor}" if actor else "retweet detectado"
            ttk.Label(top_actor, text=actor_text).pack(side="left", anchor="w")
            if original_author:
                ttk.Label(top_actor, text=f"  |  autor original: @{original_author}").pack(side="left", anchor="w", padx=(8, 0))
            if actor_avatar and os.path.isfile(actor_avatar) and Image and ImageTk:
                try:
                    av = Image.open(actor_avatar)
                    av = av.resize((42, 42), Image.Resampling.LANCZOS)
                    av_img = ImageTk.PhotoImage(av)
                    avatar_lbl = ttk.Label(top_actor, image=av_img)
                    avatar_lbl.image = av_img
                    avatar_lbl.pack(side="left", padx=(10, 0))
                except Exception:
                    pass
        ttk.Label(frame, text=f"status_id: {sid}").pack(anchor="w")
        ttk.Label(frame, text=f"media: {media_label}").pack(anchor="w")
        if download_mode != DOWNLOAD_MODE_NOTIFY_ONLY:
            ttk.Label(frame, text=f"archivos descargados: {len(downloaded_media)}").pack(anchor="w")
        ttk.Label(frame, text=f"url: {url}", wraplength=500).pack(anchor="w", pady=(0, 6))

        ttk.Label(frame, text="💬 TEXTO DEL TWEET PRINCIPAL:", font=("Segoe UI", 10, "bold"), foreground="#005fb8").pack(anchor="w", pady=(8, 2))
        
        main_text = str(event_payload.get("text_full") or "").strip()
        if not main_text:
            main_text = "(Sin texto adicional)"

        approx_lines = main_text.count("\n") + max(1, int(len(main_text) / 95)) + 2
        preview_box = tk.Text(frame, height=max(2, min(20, approx_lines)), wrap="word", bg="#f9f9f9")
        preview_box.pack(fill="x", expand=False)
        preview_box.insert("1.0", main_text)
        preview_box.configure(state="disabled")

        def _render_media_for_section(parent_container: tk.Widget, media_list: list[str], section_title: str):
            images = [p for p in media_list if os.path.splitext(p)[1].lower() in {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}]
            videos = [p for p in media_list if os.path.splitext(p)[1].lower() in {".mp4", ".mov", ".webm", ".mkv", ".m4v", ".avi"}]

            if not images and not videos:
                return

            media_panel = ttk.Frame(parent_container)
            media_panel.pack(fill="x", pady=(4, 6), padx=2)

            if images and Image and ImageTk:
                grid = ttk.Frame(media_panel)
                grid.pack(fill="both", expand=False)
                for path in images[:3]:
                    try:
                        im = Image.open(path)
                        img_w, img_h = im.size
                        max_w, max_h = 700, 380
                        if img_w > max_w or img_h > max_h:
                            ratio = min(max_w / max(1, img_w), max_h / max(1, img_h))
                            im = im.resize((max(1, int(img_w * ratio)), max(1, int(img_h * ratio))), Image.Resampling.LANCZOS)
                        tk_img = ImageTk.PhotoImage(im)
                        if not hasattr(win, "_thumb_refs"): win._thumb_refs = []
                        win._thumb_refs.append(tk_img)
                        lbl = ttk.Label(grid, image=tk_img)
                        lbl.image = tk_img  # <-- CLAVE: Asegura la referencia
                        lbl.pack(anchor="w", pady=4)
                    except Exception:
                        pass

            if download_mode != DOWNLOAD_MODE_NOTIFY_ONLY and videos:
                vids = ttk.Frame(media_panel)
                vids.pack(fill="x", pady=(4, 4))
                ttk.Label(vids, text=f"Videos ({section_title}):", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 4))

                for path in videos[:1]:  # Mostramos solo el primer video en el popup para no saturar memoria/pantalla
                    if not getattr(win, "_has_embedded_video", False):
                        win._has_embedded_video = True
                        embed_wrap = tk.Frame(vids, bg="black", height=340)
                        embed_wrap.pack(fill="x", pady=(4, 8))
                        embed_wrap.pack_propagate(False)
                        
                        player, error_msg = self._build_embedded_video_player(embed_wrap, path)
                        
                        if player is not None:
                            win._vlc_players.append(player)
                            self._bind_player_controls(win, embed_wrap, player, vids, autoplay_var=popup_autoplay_var)
                            if popup_autoplay_var.get():
                                win.after(120, lambda p=player: p.play() if win.winfo_exists() else None)
                            else:
                                win.after(180, lambda p=player: p.pause() if win.winfo_exists() else None)
                        else:
                            err_lbl = ttk.Label(embed_wrap, text=f"⚠️ Error de Reproducción:\n{error_msg}", foreground="#ff4444", background="black", justify="center")
                            err_lbl.pack(expand=True)

        main_media = media_groups.get("main", [])
        if main_media:
            _render_media_for_section(frame, main_media, "Principal")

        quote_url = str(event_payload.get("quote_url") or "").strip()
        quote_preview = str(event_payload.get("quote_text_preview") or "").strip()
        quote_chain_list = event_payload.get("quote_chain") if isinstance(event_payload.get("quote_chain"), list) else []
        
        quotes_to_render = []
        
        if quote_url or quote_preview:
            quotes_to_render.append({
                "url": quote_url,
                "text": quote_preview,
                "media": media_groups.get("quoted", []),
                "title": "🔄 TWEET CITADO (PRINCIPAL)"
            })
            
        quote_chain_urls_norm = [normalize_status_url(str(u)) for u in event_payload.get("_quote_chain_urls", []) if str(u).strip()]
        for idx, qitem in enumerate(quote_chain_list, start=1):
            q_u = normalize_status_url(str(qitem.get("url") or ""))
            if not q_u and not qitem.get("text"):
                continue
                
            if q_u == normalize_status_url(quote_url) and quote_url:
                continue
                
            q_media = []
            if q_u in quote_chain_urls_norm:
                try:
                    m_idx = quote_chain_urls_norm.index(q_u) + 1
                    q_media = media_groups.get(f"quote_chain_{m_idx}", [])
                except ValueError:
                    pass
                    
            quotes_to_render.append({
                "url": q_u,
                "text": str(qitem.get("text") or ""),
                "media": q_media,
                "title": f"🔄 CITA ANIDADA (Nivel {idx})"
            })

        for q_data in quotes_to_render:
            if not q_data["url"] and not q_data["text"] and not q_data["media"]:
                continue
                
            is_nested = "Nivel" in q_data["title"]
            pad_x_left = 25 if is_nested else 0
            
            quote_color = "#a37651" if is_nested else "#c25700"
            lbl = ttk.Label(frame, text=q_data["title"], font=("Segoe UI", 10, "bold"), foreground=quote_color)
            q_box = ttk.LabelFrame(frame, labelwidget=lbl)
            q_box.pack(fill="x", pady=(12, 4), padx=(pad_x_left, 0))

            if q_data["url"]:
                url_frame = ttk.Frame(q_box)
                url_frame.pack(fill="x", padx=6, pady=(4, 2))
                ttk.Label(url_frame, text=f"URL: {q_data['url']}").pack(side="left")
                ttk.Button(url_frame, text="Abrir Quote", command=lambda u=q_data["url"]: self._open_media_external(u)).pack(side="right")
                
            if q_data["text"]:
                q_lines = q_data["text"].count("\n") + max(1, int(len(q_data["text"]) / 95)) + 2
                bg_color = "#f4f7f9" if is_nested else "#ffffff"
                qtxt = tk.Text(q_box, height=max(2, min(10, q_lines)), wrap="word", bg=bg_color)
                qtxt.insert("1.0", q_data["text"])
                qtxt.configure(state="disabled")
                qtxt.pack(fill="x", padx=6, pady=(2, 6))
                
            if q_data["media"]:
                _render_media_for_section(q_box, q_data["media"], "Cita Anidada" if is_nested else "Cita")

        reply_to_url = str(event_payload.get("reply_to_url") or "").strip()
        reply_to_preview = str(event_payload.get("reply_to_text_preview") or "").strip()
        reply_media = media_groups.get("reply_parent", [])
        
        if not context_posts:
            if reply_to_url or reply_to_preview or reply_media:
                reply_box = ttk.LabelFrame(frame, text="↩️ POST ORIGINAL DEL COMENTARIO")
                reply_box.pack(fill="x", pady=(6, 6))
                if reply_to_url:
                    ttk.Label(reply_box, text=f"URL original: {reply_to_url}", wraplength=860).pack(anchor="w", padx=6, pady=(6, 2))
                if reply_to_preview:
                    rtxt = tk.Text(reply_box, height=4, wrap="word")
                    rtxt.insert("1.0", reply_to_preview)
                    rtxt.configure(state="disabled")
                    rtxt.pack(fill="x", padx=6, pady=(2, 6))
                if reply_media:
                    _render_media_for_section(reply_box, reply_media, "Original")

        if context_posts:
            for idx, post in enumerate(context_posts, start=1):
                if post.get("role") == "quote_chain": continue 

                title = str(post.get("title") or f"Contexto {idx}")
                post_url = str(post.get("url") or "").strip()
                post_text = str(post.get("text") or "").strip() or "(sin texto)"
                box = ttk.LabelFrame(frame, text=title)
                box.pack(fill="x", pady=(6, 6))
                if post_url:
                    ttk.Label(box, text=f"URL: {post_url}", wraplength=860).pack(anchor="w", padx=6, pady=(6, 2))
                lines = post_text.count("\n") + max(1, int(len(post_text) / 95)) + 2
                txt = tk.Text(box, height=max(3, min(14, lines)), wrap="word")
                txt.insert("1.0", post_text)
                txt.configure(state="disabled")
                txt.pack(fill="x", padx=6, pady=(2, 6))

        btns = ttk.Frame(frame)
        btns.pack(fill="x", pady=(12, 0))

        def copy_url() -> None:
            try:
                self.root.clipboard_clear()
                self.root.clipboard_append(url)
            except Exception:
                pass

        ttk.Button(btns, text="Copiar URL", command=copy_url).pack(side="left")
        ttk.Button(btns, text="Abrir post en navegador", command=lambda: self._open_media_external(url)).pack(side="left", padx=(6, 0))
        def close_popup() -> None:
            self._release_vlc_players(list(getattr(win, "_vlc_players", [])))
            if win.winfo_exists():
                win.destroy()

        ttk.Button(btns, text="Cerrar Alerta", command=close_popup).pack(side="right")

        popup_auto_close = bool(event_payload.get("popup_auto_close", False))
        try:
            popup_close_seconds = max(1, int(event_payload.get("popup_close_seconds") or 12))
        except Exception:
            popup_close_seconds = 12

        if popup_autoplay_var.get():
            autoplay_target = None
            for p in downloaded_media:
                ext = os.path.splitext(p)[1].lower()
                if ext in {".gif"}:
                    autoplay_target = p
                    break
            if autoplay_target:
                self._open_media_external(autoplay_target)

        if popup_auto_close:
            win.after(popup_close_seconds * 1000, close_popup)

        win.protocol("WM_DELETE_WINDOW", close_popup)

    def _close_history_window(self) -> None:
        win_to_close = self.history_window
        if win_to_close and win_to_close.winfo_exists():
            try:
                win_to_close.destroy()
            except Exception:
                pass
        self._release_vlc_players(self._history_vlc_players)
        self._history_vlc_players = []
        self.history_window = None
        self.history_listbox = None
        self.history_detail = None
        self.history_media_label = None
        self.history_media_button_frame = None
        self.history_video_frame = None
        self._history_media_refs = []
        self._history_view_rows = []

    def _open_history_window(self) -> None:
        if self.history_window and self.history_window.winfo_exists():
            self.history_window.lift()
            return

        uid_default = (self.uid_var.get() or "").strip()
        if not uid_default and self.profiles:
            uid_default = sorted(self.profiles.keys())[0]
        self.history_uid_var.set(self._get_profile_label(uid_default) if uid_default else "")

        self.history_window = tk.Toplevel(self.root)
        self.history_window.title("Historial de popups")
        self.history_window.geometry("900x520")

        shell = ttk.Frame(self.history_window, padding=10)
        shell.pack(fill="both", expand=True)

        top = ttk.Frame(shell)
        top.pack(fill="x", pady=(0, 8))
        ttk.Label(top, text="Perfil:").pack(side="left")

        uid_values = [self._get_profile_label(k) for k in sorted(self.profiles.keys())]
        uid_combo = ttk.Combobox(
            top,
            textvariable=self.history_uid_var,
            values=uid_values,
            state="readonly" if uid_values else "normal",
            width=36,
        )
        uid_combo.pack(side="left", padx=(6, 10))
        uid_combo.bind("<<ComboboxSelected>>", lambda _e: self._refresh_history_list())

        ttk.Button(top, text="Refrescar", command=self._refresh_history_list).pack(side="left")
        ttk.Button(top, text="Limpiar UID", command=self._clear_history_for_selected_uid).pack(side="left", padx=(6, 0))
        ttk.Button(top, text="Cerrar", command=self._close_history_window).pack(side="right")

        body = ttk.Frame(shell)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=2)
        body.columnconfigure(1, weight=3)
        body.rowconfigure(0, weight=1)

        left = ttk.Frame(body)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        left.rowconfigure(0, weight=1)
        left.columnconfigure(0, weight=1)

        self.history_listbox = ttk.Treeview(left, columns=("time", "kind", "media", "sid"), show="headings", selectmode="browse")
        self.history_listbox.heading("time", text="Fecha/Hora")
        self.history_listbox.heading("kind", text="Tipo")
        self.history_listbox.heading("media", text="Media")
        self.history_listbox.heading("sid", text="ID")
        self.history_listbox.column("time", width=140)
        self.history_listbox.column("kind", width=80)
        self.history_listbox.column("media", width=80)
        self.history_listbox.column("sid", width=120)
        self.history_listbox.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(left, orient="vertical", command=self.history_listbox.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.history_listbox.configure(yscrollcommand=scroll.set)
        self.history_listbox.bind("<<TreeviewSelect>>", self._on_history_select)

        right = ttk.Frame(body)
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)

        self.history_detail = tk.Text(right, wrap="word", bg="#fcfcfc")
        self.history_detail.grid(row=0, column=0, sticky="nsew")
        dscroll = ttk.Scrollbar(right, orient="vertical", command=self.history_detail.yview)
        dscroll.grid(row=0, column=1, sticky="ns")
        self.history_detail.configure(yscrollcommand=dscroll.set)
        
        self.history_detail.tag_configure("header", font=("Segoe UI", 11, "bold"), foreground="#005fb8")
        self.history_detail.tag_configure("label", font=("Segoe UI", 9, "bold"), foreground="#555555")
        self.history_detail.tag_configure("quote_header", font=("Segoe UI", 10, "bold"), foreground="#c25700")

        self.history_detail.configure(state="disabled")

        self.history_media_label = ttk.Label(right)
        self.history_media_label.grid(row=1, column=0, sticky="w", pady=(8, 4))

        self.history_media_button_frame = ttk.Frame(right)
        self.history_media_button_frame.grid(row=2, column=0, sticky="w")

        self.history_video_frame = ttk.Frame(right)
        self.history_video_frame.grid(row=3, column=0, sticky="ew", pady=(8, 0))

        self.history_window.protocol("WM_DELETE_WINDOW", self._close_history_window)
        self._refresh_history_list()

    def _refresh_history_list(self) -> None:
        if not self.history_listbox:
            return
        selected_label = (self.history_uid_var.get() or "").strip()
        uid = self._get_uid_from_label(selected_label)
        rows = list(self.popup_history_by_uid.get(uid, []))
        rows.sort(key=lambda x: str(x.get("time") or ""), reverse=True)
        self._history_view_rows = rows

        self.history_listbox.delete(*self.history_listbox.get_children())
        for row in rows:
            ts = str(row.get("time") or "-")
            kind = str(row.get("kind") or "-").upper()
            sid = str(row.get("status_id") or "-")
            media = self._media_label(row)
            self.history_listbox.insert("", "end", values=(ts, kind, media, sid))

        if rows:
            hchildren = self.history_listbox.get_children()
            if hchildren:
                self.history_listbox.selection_set(hchildren[0])
            self._render_history_detail(rows[0])
        else:
            self._render_history_detail(None)

    def _render_history_detail(self, row: dict[str, Any] | None) -> None:
        if not self.history_detail:
            return
        self.history_detail.configure(state="normal")
        self.history_detail.delete("1.0", "end")
        
        if row:
            self.history_detail.insert("end", f"{str(row.get('kind') or '-').upper()} detectado para @{row.get('username') or '-'}\n\n", "header")
            
            self.history_detail.insert("end", "Metadatos:\n", "label")
            self.history_detail.insert("end", f"UID: {row.get('uid') or '-'}\n")
            self.history_detail.insert("end", f"🍪 Cookie usada: {row.get('used_cookie') or '-'}\n")
            self.history_detail.insert("end", f"Media: {self._media_label(row)}\n")
            self.history_detail.insert("end", f"Status ID: {row.get('status_id') or '-'}\n")
            self.history_detail.insert("end", f"Hora: {row.get('time') or '-'}\n")
            self.history_detail.insert("end", f"URL: {row.get('url') or '-'}\n\n")

            self.history_detail.insert("end", "Texto Principal:\n", "label")
            self.history_detail.insert("end", f"{row.get('text_full') or row.get('text_preview') or '(sin texto principal)'}\n\n")

            if row.get('reply_to_url') or row.get('reply_to_text_preview'):
                self.history_detail.insert("end", "↩️ Respuesta a:\n", "quote_header")
                self.history_detail.insert("end", f"URL original: {row.get('reply_to_url') or '-'}\n")
                self.history_detail.insert("end", f"Texto original:\n{row.get('reply_to_text_preview') or '(sin texto)'}\n\n")

            if row.get('quote_url') or row.get('quote_text_preview'):
                self.history_detail.insert("end", "🔄 Cita:\n", "quote_header")
                self.history_detail.insert("end", f"URL citada: {row.get('quote_url') or '-'}\n")
                self.history_detail.insert("end", f"Texto citado:\n{row.get('quote_text_preview') or '(sin texto)'}\n\n")

            context_rows = row.get("context_posts") if isinstance(row.get("context_posts"), list) else []
            if context_rows:
                self.history_detail.insert("end", "Contexto (hilo/quotes):\n", "label")
                for idx, item in enumerate(context_rows, start=1):
                    title = str(item.get("title") or f"Contexto {idx}")
                    c_url = str(item.get("url") or "").strip() or "-"
                    c_text = str(item.get("text") or "").strip() or "(sin texto)"
                    self.history_detail.insert("end", f"{title}:\nURL: {c_url}\n{c_text}\n\n")

        self.history_detail.configure(state="disabled")

        if self.history_media_label:
            self.history_media_label.configure(image="", text="")
            self._history_media_refs = []

        if self.history_media_button_frame:
            for widget in self.history_media_button_frame.winfo_children():
                widget.destroy()

        if self.history_video_frame:
            for widget in self.history_video_frame.winfo_children():
                widget.destroy()

        self._release_vlc_players(self._history_vlc_players)
        self._history_vlc_players = []

        if not row:
            return

        media_groups = self._resolve_event_media_groups(row)
        media_paths: list[str] = []
        for values in media_groups.values():
            for p in values:
                if p not in media_paths:
                    media_paths.append(p)
        if not media_paths:
            return

        image_paths = [p for p in media_paths if os.path.splitext(p)[1].lower() in {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}]
        video_paths = [p for p in media_paths if os.path.splitext(p)[1].lower() in {".mp4", ".mov", ".webm", ".mkv", ".m4v", ".avi"}]

        if self.history_media_label and image_paths and Image and ImageTk:
            try:
                im = Image.open(image_paths[0])
                img_w, img_h = im.size
                max_w, max_h = 520, 320
                if img_w > max_w or img_h > max_h:
                    ratio = min(max_w / max(1, img_w), max_h / max(1, img_h))
                    im = im.resize((max(1, int(img_w * ratio)), max(1, int(img_h * ratio))), Image.Resampling.LANCZOS)
                tk_img = ImageTk.PhotoImage(im)
                self._history_media_refs = [tk_img]
                self.history_media_label.configure(image=tk_img, text="")
                self.history_media_label.image = tk_img # <-- CLAVE: Asegura la referencia
            except Exception:
                pass

        if self.history_media_button_frame:
            post_url = str(row.get("url") or "").strip()
            if post_url:
                ttk.Button(self.history_media_button_frame, text="Abrir post", command=lambda u=post_url: self._open_media_external(u)).pack(side="left", padx=(0, 6))

            all_paths = image_paths + video_paths
            for idx, path in enumerate(all_paths[:4], start=1):
                def _open_media(p=path) -> None:
                    try:
                        if sys.platform.startswith("win"):
                            os.startfile(p)
                        elif sys.platform == "darwin":
                            subprocess.Popen(["open", p])
                        else:
                            subprocess.Popen(["xdg-open", p])
                    except Exception:
                        pass

                ttk.Button(self.history_media_button_frame, text=f"Abrir media {idx}", command=_open_media).pack(side="left", padx=(0, 6))

        if self.history_video_frame and video_paths:
            host = tk.Frame(self.history_video_frame, bg="black", height=260)
            host.pack(fill="x")
            host.pack_propagate(False)
            
            player, error_msg = self._build_embedded_video_player(host, video_paths[0])
            
            if player is not None:
                self._history_vlc_players.append(player)
                scope = self.history_window if self.history_window else self.root
                self._bind_player_controls(scope, host, player, self.history_video_frame)
            else:
                err_lbl = ttk.Label(host, text=f"⚠️ Video no disponible:\n{error_msg}", foreground="#ff4444", background="black", justify="center")
                err_lbl.pack(expand=True)

    def _on_history_select(self, _event=None) -> None:
        if not self.history_listbox:
            return
        idxs = self.history_listbox.curselection()
        if not idxs:
            return
        idx = int(idxs[0])
        if 0 <= idx < len(self._history_view_rows):
            self._render_history_detail(self._history_view_rows[idx])

    def _clear_history_for_selected_uid(self) -> None:
        selected_label = (self.history_uid_var.get() or "").strip()
        uid = self._get_uid_from_label(selected_label)
        if not uid:
            return
        self.popup_history_by_uid[uid] = []
        self._refresh_history_list()
        self._log(uid, "Historial de popups limpiado")

    def _show_download_warning(self) -> None:
        messagebox.showwarning(
            APP_TITLE,
            self._tr("El modo 'Descargar cuenta completa (advertencia)' intenta bajar contenido histórico de la cuenta y puede consumir mucho tiempo, red y espacio.\n\n"
            "Si quieres descargar solo lo que se detecta mientras monitorea (posts/replies/retweets seleccionados), usa 'Descargar actividad seleccionada (en monitoreo)'.\n"
            "Si solo quieres alertas, usa 'Solo notificaciones'.")
        )

    def _pick_output_dir(self) -> None:
        selected = filedialog.askdirectory(initialdir=self.output_dir_var.get() or self.output_default_dir)
        if selected:
            self.output_dir_var.set(selected)

    def _pick_cookies_dir(self) -> None:
        selected = filedialog.askdirectory(
            title="Seleccionar carpeta global de cookies",
            initialdir=self.cookies_dir,
        )
        if selected:
            self.cookies_dir_var.set(os.path.abspath(selected))
            self._save_global_config()

    def _import_cookie_file(self) -> None:
        src = filedialog.askopenfilename(
            title="Importar cookies.txt",
            filetypes=[("Cookies", "*.txt"), ("Todos", "*.*")],
        )
        if not src:
            return
        try:
            self._save_global_config()
            dst = os.path.join(self.cookies_dir, os.path.basename(src) or "cookies.txt")
            shutil.copy2(src, dst)
            messagebox.showinfo(APP_TITLE, f"Cookie importada: {os.path.basename(dst)}")
        except Exception as exc:
            messagebox.showerror(APP_TITLE, f"No se pudo importar cookies: {exc}")

    def _open_new_instance(self) -> None:
        subprocess.Popen([sys.executable, os.path.abspath(__file__)])

    def _reset_form(self) -> None:
        self.uid_var.set(self._new_uid())
        self.username_var.set("")
        self.detect_post_var.set(True)
        self.detect_reply_var.set(False)
        self.detect_retweet_var.set(False)
        self.notify_popup_var.set(True)
        self.download_mode_var.set(self._tr(DOWNLOAD_MODE_LABELS[DOWNLOAD_MODE_NOTIFY_ONLY]))
        self.output_dir_var.set(self.output_default_dir)
        self.poll_min_seconds_var.set(str(DEFAULT_POLL_SECONDS))
        self.poll_max_seconds_var.set(str(DEFAULT_POLL_SECONDS))
        self.popup_auto_close_var.set(False)
        self.popup_close_seconds_var.set("12")
        self.popup_autoplay_media_var.set(False)
        self.auto_start_var.set(False)
        self.fresh_baseline_var.set(False)
        
        self.schedule_mode_var.set(self._tr("Intervalos"))
        self.exact_times_var.set("")
        self.start_delay_var.set("0")
        self.stop_after_var.set("0")

    def _validate_form(self) -> Profile | None:
        uid = (self.uid_var.get() or "").strip()
        if not uid:
            messagebox.showerror(APP_TITLE, "UID vacio")
            return None

        username = extract_username(self.username_var.get() or "")
        if not username:
            messagebox.showerror(APP_TITLE, "Usuario X invalido")
            return None

        detect_post = bool(self.detect_post_var.get())
        detect_reply = bool(self.detect_reply_var.get())
        detect_retweet = bool(self.detect_retweet_var.get())
        if not (detect_post or detect_reply or detect_retweet):
            messagebox.showerror(APP_TITLE, "Selecciona al menos un tipo de actividad")
            return None

        try:
            poll_min_seconds = max(MIN_POLL_SECONDS, int(float((self.poll_min_seconds_var.get() or str(DEFAULT_POLL_SECONDS)).strip())))
            poll_max_seconds = max(MIN_POLL_SECONDS, int(float((self.poll_max_seconds_var.get() or str(DEFAULT_POLL_SECONDS)).strip())))
        except Exception:
            messagebox.showerror(APP_TITLE, "Chequeo min/max (seg) invalido")
            return None

        if poll_max_seconds < poll_min_seconds:
            poll_min_seconds, poll_max_seconds = poll_max_seconds, poll_min_seconds

        try:
            popup_close_seconds = max(1, int(float((self.popup_close_seconds_var.get() or "12").strip())))
        except Exception:
            messagebox.showerror(APP_TITLE, "Segundos popup invalido")
            return None

        try:
            start_delay_minutes = max(0, int(float((self.start_delay_var.get() or "0").strip())))
            stop_after_minutes = max(0, int(float((self.stop_after_var.get() or "0").strip())))
        except Exception:
            messagebox.showerror(APP_TITLE, "Valores de tiempo (retraso/detener) inválidos")
            return None

        output_dir = (self.output_dir_var.get() or "").strip() or self.output_default_dir
        ensure_dir(output_dir)

        return Profile(
            uid=uid,
            username=username,
            detect_post=detect_post,
            detect_reply=detect_reply,
            detect_retweet=detect_retweet,
            notify_popup=bool(self.notify_popup_var.get()),
            download_mode=self._download_mode_key(),
            output_dir=output_dir,
            poll_min_seconds=poll_min_seconds,
            poll_max_seconds=poll_max_seconds,
            popup_auto_close=bool(self.popup_auto_close_var.get()),
            popup_close_seconds=popup_close_seconds,
            popup_autoplay_media=bool(self.popup_autoplay_media_var.get()),
            auto_start=bool(self.auto_start_var.get()),
            fresh_baseline=bool(self.fresh_baseline_var.get()),
            schedule_mode=self._tr_reverse(self.schedule_mode_var.get()),
            exact_times=self.exact_times_var.get(),
            start_delay_minutes=start_delay_minutes,
            stop_after_minutes=stop_after_minutes,
        )

    def _save_profiles(self) -> None:
        data = [p.to_dict() for p in self.profiles.values()]
        with open(self.profiles_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load_profiles(self) -> None:
        if not os.path.isfile(self.profiles_path):
            return
        try:
            with open(self.profiles_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return

        self.profiles.clear()
        if isinstance(data, list):
            for item in data:
                if not isinstance(item, dict):
                    continue
                profile = Profile.from_dict(item, self.output_default_dir)
                if profile.uid:
                    self.profiles[profile.uid] = profile

        self._refresh_profile_list()

    def _refresh_profile_list(self) -> None:
        self.profile_list.delete(0, "end")
        for uid, profile in sorted(self.profiles.items(), key=lambda x: x[0]):
            idx = self.profile_list.size()
            if uid in self.workers:
                self.profile_list.insert("end", f"▶ {uid} | @{profile.username}")
                self.profile_list.itemconfig(idx, bg="#d4edda", fg="#155724") 
            else:
                self.profile_list.insert("end", f"⏹ {uid} | @{profile.username}")
                self.profile_list.itemconfig(idx, bg="#f8d7da", fg="#721c24") 

    def _on_select_profile(self, _event=None) -> None:
        idxs = self.profile_list.curselection()
        if not idxs:
            return
        text = self.profile_list.get(idxs[0])
        uid = text.replace("▶", "").replace("⏹", "").split("|")[0].strip()
        profile = self.profiles.get(uid)
        if not profile:
            return

        self.uid_var.set(profile.uid)
        self.username_var.set(profile.username)
        self.detect_post_var.set(profile.detect_post)
        self.detect_reply_var.set(profile.detect_reply)
        self.detect_retweet_var.set(profile.detect_retweet)
        self.notify_popup_var.set(profile.notify_popup)
        self.download_mode_var.set(self._tr(DOWNLOAD_MODE_LABELS.get(profile.download_mode, DOWNLOAD_MODE_LABELS[DOWNLOAD_MODE_NOTIFY_ONLY])))
        self.output_dir_var.set(profile.output_dir)
        self.poll_min_seconds_var.set(str(profile.poll_min_seconds))
        self.poll_max_seconds_var.set(str(profile.poll_max_seconds))
        self.popup_auto_close_var.set(bool(profile.popup_auto_close))
        self.popup_close_seconds_var.set(str(profile.popup_close_seconds))
        self.popup_autoplay_media_var.set(bool(profile.popup_autoplay_media))
        self.auto_start_var.set(bool(getattr(profile, "auto_start", False)))
        self.fresh_baseline_var.set(bool(getattr(profile, "fresh_baseline", False)))
        
        self.schedule_mode_var.set(self._tr(getattr(profile, "schedule_mode", "Intervalos")))
        self.exact_times_var.set(getattr(profile, "exact_times", ""))
        self.start_delay_var.set(str(getattr(profile, "start_delay_minutes", 0)))
        self.stop_after_var.set(str(getattr(profile, "stop_after_minutes", 0)))
        
        self.log_filter_var.set(profile.uid)
        self._render_logs()

    def _save_profile(self) -> None:
        profile = self._validate_form()
        if not profile:
            return
        self.profiles[profile.uid] = profile
        self._save_profiles()
        
        if profile.uid in self.workers:
            self.workers[profile.uid].profile = profile
            
        self._refresh_profile_list()
        self._refresh_log_filter_options()
        self._log(profile.uid, "Perfil guardado")

    def _delete_profile(self) -> None:
        uid = (self.uid_var.get() or "").strip()
        if not uid:
            return
        if uid in self.workers:
            messagebox.showwarning(APP_TITLE, "Deten el monitor antes de eliminar el perfil")
            return
        if uid in self.profiles:
            del self.profiles[uid]
            self._save_profiles()
            self._refresh_profile_list()
            self._log(uid, "Perfil eliminado")
            self._reset_form()

    def _start_all_monitors(self) -> None:
        count = 0
        for uid, profile in self.profiles.items():
            if uid in self.workers:
                continue
            worker = MonitorWorker(
                profile=profile,
                state_dir=self.state_dir,
                log_fn=self._log,
                notify_fn=self._notify_popup,
                history_fn=self._push_history,
                cookie_manager=self.cookie_manager
            )
            self.workers[uid] = worker
            worker.start()
            count += 1
        if count > 0:
            self._refresh_profile_list()
            self._log("SISTEMA", f"Iniciados {count} monitores masivos.")

    def _stop_all_monitors(self) -> None:
        count = 0
        for uid, worker in list(self.workers.items()):
            worker.stop()
            worker.join(timeout=1)
            self.workers.pop(uid, None)
            count += 1
        if count > 0:
            self._refresh_profile_list()
            self._log("SISTEMA", f"Detenidos {count} monitores masivos.")

    def _restart_app(self) -> None:
        if messagebox.askyesno(APP_TITLE, "¿Estás seguro que deseas reiniciar la aplicación? Todos los monitores actuales se detendrán."):
            self._log("SISTEMA", "Reiniciando la aplicación...")
            self._stop_all_monitors()
            import sys
            import subprocess
            subprocess.Popen([sys.executable] + sys.argv)
            self.root.quit()

    def _start_selected(self) -> None:
        profile = self._validate_form()
        if not profile:
            return

        self.profiles[profile.uid] = profile
        self._save_profiles()

        if profile.uid in self.workers:
            messagebox.showinfo(APP_TITLE, "Ese perfil ya esta corriendo")
            return

        worker = MonitorWorker(
            profile=profile,
            state_dir=self.state_dir,
            log_fn=self._log,
            notify_fn=self._notify_popup,
            history_fn=self._push_history,
            cookie_manager=self.cookie_manager
        )
        self.workers[profile.uid] = worker
        worker.start()
        self._refresh_profile_list()

    def _stop_selected(self) -> None:
        uid = (self.uid_var.get() or "").strip()
        if not uid:
            return
        worker = self.workers.get(uid)
        if not worker:
            return
        worker.stop()
        worker.join(timeout=3)
        self.workers.pop(uid, None)
        self._refresh_profile_list()
        self._log(uid, "Solicitud de stop enviada")


def main() -> None:
    root = tk.Tk()
    app = ProfilerApp(root)

    def on_close() -> None:
        for uid, worker in list(app.workers.items()):
            worker.stop()
            worker.join(timeout=2)
            app.workers.pop(uid, None)
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


if __name__ == "__main__":
    main()