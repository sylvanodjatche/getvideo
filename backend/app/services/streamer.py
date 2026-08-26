import os
import uuid
import asyncio
import time
import httpx
import yt_dlp
import subprocess
import re
from typing import Dict, Any
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from ..config import settings

download_tasks: Dict[str, Dict[str, Any]] = {}

def cleanup_file(filepath: str, task_id: str | None = None):
    try:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        print(f"[MediaStreamer] Erreur suppression {filepath}: {e}")
    if task_id and task_id in download_tasks:
        download_tasks.pop(task_id, None)

def extract_youtube_video_id(url: str) -> str | None:
    try:
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(url)
        netloc = parsed.netloc.lower()
        if "youtube.com" in netloc or "m.youtube.com" in netloc:
            if "/shorts/" in parsed.path:
                return parsed.path.split("/shorts/")[1].split("/")[0].split("?")[0]
            query = parse_qs(parsed.query)
            if "v" in query:
                return query["v"][0]
        elif "youtu.be" in netloc:
            path_part = parsed.path.lstrip("/").split("/")[0].split("?")[0]
            if len(path_part) >= 10:
                return path_part
    except Exception:
        pass
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
    def _download_stream_chunks(cls, task_id: str, stream_url: str, out_file: str) -> bool:
        """Télécharge un flux binaire avec suivi de progression temps réel."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "*/*"
        }
        with httpx.Client(timeout=180.0, follow_redirects=True, headers=headers) as client:
            with client.stream("GET", stream_url) as resp:
                if resp.status_code != 200:
                    return False
                
                total_bytes = int(resp.headers.get("content-length", 0))
                total_mb = f"{total_bytes / (1024 * 1024):.1f} Mo" if total_bytes > 0 else "Calcul..."
                
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
                        percent = round((downloaded / total_bytes) * 100, 1) if total_bytes > 0 else min(95, int(downloaded / (20 * 1024 * 1024) * 100))

                        download_tasks[task_id].update({
                            "status": "downloading",
                            "percent": percent,
                            "speed": f"{speed_mb:.1f} Mo/s",
                            "downloaded_mb": f"{downloaded / (1024 * 1024):.1f} Mo",
                            "total_mb": total_mb,
                            "updated_at": time.time()
                        })
                return os.path.exists(out_file) and os.path.getsize(out_file) > 1024

    @classmethod
    def _download_via_invidious_pool(cls, task_id: str, video_id: str, final_file: str, is_audio: bool) -> bool:
        """Téléchargement direct YouTube via pool de miroirs Invidious décentralisés."""
        endpoints = [
            f"https://invidious.nerdvpn.de/api/v1/videos/{video_id}",
            f"https://inv.tux.pizza/api/v1/videos/{video_id}",
            f"https://invidious.jing.rocks/api/v1/videos/{video_id}",
            f"https://vid.priv.au/api/v1/videos/{video_id}",
            f"https://invidious.projectsegfau.lt/api/v1/videos/{video_id}"
        ]

        for ep in endpoints:
            try:
                with httpx.Client(timeout=4.0, follow_redirects=True) as client:
                    r = client.get(ep)
                    if r.status_code == 200:
                        data = r.json()
                        formats = data.get("formatStreams") or data.get("adaptiveFormats") or []
                        target_url = None

                        if is_audio:
                            for f in formats:
                                if "audio" in f.get("type", "").lower() or "audio" in f.get("mimeType", "").lower():
                                    target_url = f.get("url")
                                    if target_url: break
                        else:
                            for f in formats:
                                if "video" in f.get("type", "").lower() or "mp4" in f.get("type", "").lower():
                                    target_url = f.get("url")
                                    if target_url: break

                        if target_url:
                            temp_target = final_file + ".raw" if is_audio else final_file
                            success = cls._download_stream_chunks(task_id, target_url, temp_target)
                            if success:
                                if is_audio:
                                    cmd = ["ffmpeg", "-y", "-i", temp_target, "-vn", "-b:a", "320k", final_file]
                                    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
                                    if os.path.exists(temp_target): os.remove(temp_target)
                                return True
            except Exception:
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
        video_id = extract_youtube_video_id(media_url)

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

        # 1. Si c'est STRICTEMENT YouTube : Moteur Invidious Mirror Pool puis fallback yt-dlp
        if video_id:
            try:
                if cls._download_via_invidious_pool(task_id, video_id, final_file, is_audio):
                    if os.path.exists(final_file) and os.path.getsize(final_file) > 1024:
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

        # 2. Pour Facebook, TikTok, Instagram, Twitter/X, SoundCloud et fallback général
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
                    'player_client': ['tv_embedded', 'android', 'ios', 'mweb'],
                }
            },
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
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
                selector = f"bestvideo[height<={selector}]+bestaudio/best[height<={selector}]/best"
            elif "+bestaudio" not in selector and selector != "best":
                # Fusion automatique du flux audio pour Facebook / TikTok
                selector = f"{selector}+bestaudio/best"
            
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
            err_str = str(e)
            if "DOWNLOAD_CANCELLED_BY_USER" in err_str:
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
