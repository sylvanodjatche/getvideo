import os
import uuid
import asyncio
import time
import httpx
import yt_dlp
import re
from typing import Dict, Any
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from ..config import settings

# Dictionnaire en mémoire des tâches de téléchargement : task_id -> info de progression
download_tasks: Dict[str, Dict[str, Any]] = {}

def cleanup_file(filepath: str, task_id: str | None = None):
    try:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        print(f"[MediaStreamer] Erreur suppression {filepath}: {e}")
    if task_id and task_id in download_tasks:
        download_tasks.pop(task_id, None)

def extract_video_id(url: str) -> str | None:
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'youtu\.be\/([0-9A-Za-z_-]{11})',
        r'shorts\/([0-9A-Za-z_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

class MediaStreamer:
    @staticmethod
    def get_progress_hook(task_id: str):
        def hook(d):
            if task_id not in download_tasks:
                return

            if download_tasks[task_id].get("cancelled"):
                raise Exception("DOWNLOAD_CANCELLED_BY_USER")

            if d['status'] == 'downloading':
                total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                downloaded_bytes = d.get('downloaded_bytes', 0)
                
                percent = 0
                if total_bytes > 0:
                    percent = round((downloaded_bytes / total_bytes) * 100, 1)
                elif '_percent_str' in d:
                    try:
                        clean_str = d['_percent_str'].replace('%', '').strip()
                        percent = float(clean_str)
                    except Exception:
                        percent = 10

                speed_str = d.get('_speed_str', 'Calcul...').strip()
                eta_str = d.get('_eta_str', '--:--').strip()
                
                downloaded_mb = f"{downloaded_bytes / (1024 * 1024):.1f} Mo"
                total_mb = f"{total_bytes / (1024 * 1024):.1f} Mo" if total_bytes > 0 else "..."

                download_tasks[task_id].update({
                    "status": "downloading",
                    "percent": percent,
                    "speed": speed_str,
                    "eta": eta_str,
                    "downloaded_mb": downloaded_mb,
                    "total_mb": total_mb,
                    "updated_at": time.time()
                })

            elif d['status'] == 'finished':
                download_tasks[task_id].update({
                    "status": "converting",
                    "percent": 95,
                    "speed": "Conversion...",
                    "eta": "Finalisation...",
                    "updated_at": time.time()
                })
        return hook

    @classmethod
    def _download_stream_url(cls, task_id: str, stream_url: str, out_file: str):
        """Télécharge un flux binaire directement par blocs avec rapport de progression temps réel."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "*/*"
        }
        with httpx.Client(timeout=120.0, follow_redirects=True, headers=headers) as client:
            with client.stream("GET", stream_url) as resp:
                resp.raise_for_status()
                total_bytes = int(resp.headers.get("content-length", 0))
                total_mb = f"{total_bytes / (1024 * 1024):.1f} Mo" if total_bytes > 0 else "..."
                
                downloaded = 0
                start_time = time.time()

                with open(out_file, "wb") as f:
                    for chunk in resp.iter_bytes(chunk_size=65536):
                        if download_tasks[task_id].get("cancelled"):
                            raise Exception("DOWNLOAD_CANCELLED_BY_USER")
                        
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        elapsed = max(0.1, time.time() - start_time)
                        speed_mb = (downloaded / (1024 * 1024)) / elapsed
                        percent = round((downloaded / total_bytes) * 100, 1) if total_bytes > 0 else min(95, int(downloaded / (15 * 1024 * 1024) * 100))

                        download_tasks[task_id].update({
                            "status": "downloading",
                            "percent": percent,
                            "speed": f"{speed_mb:.1f} Mo/s",
                            "downloaded_mb": f"{downloaded / (1024 * 1024):.1f} Mo",
                            "total_mb": total_mb,
                            "updated_at": time.time()
                        })

    @classmethod
    def _download_via_cobalt_network(cls, task_id: str, media_url: str, final_file: str, is_audio: bool, quality: str = "720") -> bool:
        """Télécharge via les instances publiques de l'API Cobalt (solution n°1 mondiale sans blocage IP)."""
        cobalt_instances = [
            "https://api.cobalt.tools",
            "https://cobalt-api.kwiatekm.tokyo",
            "https://cobalt.canine.tools",
            "https://api.wuk.sh"
        ]

        payload = {
            "url": media_url,
            "downloadMode": "audio" if is_audio else "auto",
            "videoQuality": quality if quality in ("1080", "720", "480", "360") else "720",
            "audioFormat": "mp3"
        }
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "GetVideo/2.0"
        }

        for instance in cobalt_instances:
            try:
                with httpx.Client(timeout=8.0, follow_redirects=True) as client:
                    resp = client.post(instance, json=payload, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        download_url = data.get("url")
                        if download_url:
                            cls._download_stream_url(task_id, download_url, final_file)
                            return True
            except Exception as e:
                continue
        return False

    @classmethod
    def execute_download_task(
        cls, 
        task_id: str, 
        media_url: str, 
        format_selector: str | None, 
        title: str, 
        ext: str = "mp4",
        embed_subs: bool = False
    ):
        tmp_dir = "/tmp"
        target_ext = ext.lower()
        final_file = os.path.join(tmp_dir, f"getvideo_{task_id}.{target_ext}")
        is_audio = (target_ext == "mp3")

        download_tasks[task_id] = {
            "status": "starting",
            "percent": 0,
            "speed": "0 Mo/s",
            "eta": "...",
            "downloaded_mb": "0 Mo",
            "total_mb": "Calcul...",
            "filepath": None,
            "title": title,
            "ext": target_ext,
            "cancelled": False,
            "updated_at": time.time()
        }

        # 1. Étape 1 : Moteur Haute Vitesse Cobalt (Anti-Blocage Cloud)
        try:
            quality = "720"
            if format_selector and format_selector in ("1080", "720", "480", "360"):
                quality = format_selector
            
            success = cls._download_via_cobalt_network(task_id, media_url, final_file, is_audio, quality)
            if success and os.path.exists(final_file) and os.path.getsize(final_file) > 1024:
                download_tasks[task_id].update({
                    "status": "ready",
                    "percent": 100,
                    "filepath": final_file,
                    "filesize": os.path.getsize(final_file),
                    "updated_at": time.time()
                })
                return
        except Exception as e:
            if "DOWNLOAD_CANCELLED_BY_USER" in str(e):
                download_tasks[task_id].update({"status": "cancelled"})
                return

        # 2. Étape 2 : Moteur Natif yt-dlp
        out_template = os.path.join(tmp_dir, f"getvideo_{task_id}.%(ext)s")
        ydl_opts = {
            'outtmpl': out_template,
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'no_color': True,
            'progress_hooks': [cls.get_progress_hook(task_id)],
            'extractor_args': {
                'youtube': {
                    'player_client': ['android_creator', 'ios', 'android', 'mweb', 'tv'],
                }
            },
            'http_headers': {
                'User-Agent': 'com.google.android.youtube/19.12.35 (Linux; U; Android 14; fr_FR; SM-S918B) gzip',
                'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8',
            }
        }

        if target_ext == "mp3":
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }]
        else:
            selector = format_selector or "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best"
            if selector in ("1080", "720", "480", "360"):
                selector = f"bestvideo[height<={selector}]+bestaudio/best"
            ydl_opts['format'] = selector
            ydl_opts['merge_output_format'] = 'mp4'

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(media_url, download=True)
                if "entries" in info and info["entries"]:
                    info = info["entries"][0]
                
                actual_file = ydl.prepare_filename(info)
                if target_ext == "mp3":
                    actual_file = os.path.splitext(actual_file)[0] + ".mp3"
                elif target_ext == "mp4" and not actual_file.endswith(".mp4"):
                    candidate_mp4 = os.path.splitext(actual_file)[0] + ".mp4"
                    if os.path.exists(candidate_mp4):
                        actual_file = candidate_mp4

            if os.path.exists(actual_file):
                download_tasks[task_id].update({
                    "status": "ready",
                    "percent": 100,
                    "filepath": actual_file,
                    "filesize": os.path.getsize(actual_file),
                    "updated_at": time.time()
                })
                return

        except Exception as e:
            if "DOWNLOAD_CANCELLED_BY_USER" in str(e):
                download_tasks[task_id].update({"status": "cancelled"})
                return

        download_tasks[task_id].update({"status": "error", "error": "Échec du téléchargement. Veuillez réessayer."})

    @classmethod
    def cancel_task(cls, task_id: str):
        if task_id in download_tasks:
            download_tasks[task_id]["cancelled"] = True
            filepath = download_tasks[task_id].get("filepath")
            cleanup_file(filepath, task_id)
            return True
        return False

    @classmethod
    def serve_ready_file(cls, task_id: str) -> FileResponse:
        task = download_tasks.get(task_id)
        if not task or task.get("status") != "ready":
            raise FileNotFoundError("Tâche introuvable ou non prête.")

        filepath = task["filepath"]
        title = task["title"]
        ext = task["ext"]
        safe_filename = f"{title}.{ext}".replace('"', '')
        content_type = "video/mp4" if ext == "mp4" else "audio/mpeg"

        return FileResponse(
            path=filepath,
            filename=safe_filename,
            media_type=content_type,
            background=BackgroundTask(cleanup_file, filepath, task_id)
        )

streamer_service = MediaStreamer()
