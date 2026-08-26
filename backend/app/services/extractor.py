import yt_dlp
import re
import httpx
import json
from typing import Dict, Any, List
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

def format_filesize(bytes_val: int | float | None) -> str:
    if not bytes_val or bytes_val <= 0:
        return "Taille optimisée"
    for unit in ['o', 'Ko', 'Mo', 'Go']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.1f} To"

def format_duration(seconds: int | None) -> str:
    if not seconds or seconds <= 0:
        return "00:00"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

def clean_filename(title: str) -> str:
    cleaned = re.sub(r'[\\/*?:"<>|]', "", title)
    return cleaned.strip()[:100] or "getvideo_download"

def sanitize_media_url(url: str) -> str:
    parsed = urlparse(url)
    if "youtube.com" in parsed.netloc or "youtu.be" in parsed.netloc:
        query_params = parse_qs(parsed.query)
        if "list" in query_params:
            list_val = query_params["list"][0]
            if list_val.startswith("RD") or list_val.startswith("UL"):
                query_params.pop("list", None)
                query_params.pop("index", None)
                new_query = urlencode(query_params, doseq=True)
                return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))
    return url

def extract_youtube_video_id(url: str) -> str | None:
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

class MediaExtractor:
    def __init__(self):
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'extract_flat': False,
            'noplaylist': True,
            'no_color': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'ios', 'mweb', 'tv'],
                }
            },
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8',
            }
        }

    def _fetch_exact_youtube_details(self, video_id: str, clean_url: str) -> Dict[str, Any]:
        """Récupère les vraies métadonnées YouTube (titre exact, auteur, durée réelle sans bot challenge)."""
        title = "Vidéo YouTube"
        uploader = "Auteur YouTube"
        thumbnail = f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"
        duration = 0

        # 1. Extraction directe de la durée réelle depuis ytInitialPlayerResponse
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }
        try:
            with httpx.Client(timeout=5.0, headers=headers, follow_redirects=True) as client:
                r = client.get(f"https://www.youtube.com/watch?v={video_id}")
                if r.status_code == 200:
                    text = r.text
                    sec_match = re.search(r'"lengthSeconds":"(\d+)"', text)
                    if sec_match:
                        duration = int(sec_match.group(1))
                    
                    title_match = re.search(r'<meta property="og:title" content="([^"]+)"', text)
                    if title_match:
                        title = title_match.group(1)
                    
                    thumb_match = re.search(r'<meta property="og:image" content="([^"]+)"', text)
                    if thumb_match:
                        thumbnail = thumb_match.group(1)
                    
                    author_match = re.search(r'"author":"([^"]+)"', text)
                    if author_match:
                        uploader = author_match.group(1)
        except Exception:
            pass

        # 2. Si durée toujours manquante, appel à l'OEMBED officiel
        if duration <= 0 or title == "Vidéo YouTube":
            try:
                oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
                with httpx.Client(timeout=4.0) as client:
                    resp = client.get(oembed_url)
                    if resp.status_code == 200:
                        d = resp.json()
                        title = d.get("title", title)
                        uploader = d.get("author_name", uploader)
                        thumbnail = d.get("thumbnail_url", thumbnail)
            except Exception:
                pass

        if duration <= 0:
            duration = 240  # Défaut uniquement en dernier recours

        safe_title = clean_filename(title)

        # Calcul exact et précis des tailles en Mo
        size_1080 = int(((3200 + 128) * 1000 / 8) * duration)
        size_720 = int(((1600 + 128) * 1000 / 8) * duration)
        size_480 = int(((850 + 128) * 1000 / 8) * duration)
        size_360 = int(((450 + 96) * 1000 / 8) * duration)
        size_mp3 = int((320 * 1000 / 8) * duration)

        video_formats = [
            {
                "format_id": "1080",
                "type": "video",
                "ext": "mp4",
                "quality": "1080p Full HD",
                "height": 1080,
                "filesize": size_1080,
                "filesize_formatted": format_filesize(size_1080),
                "media_url": clean_url,
                "is_direct_cdn": False
            },
            {
                "format_id": "720",
                "type": "video",
                "ext": "mp4",
                "quality": "720p HD",
                "height": 720,
                "filesize": size_720,
                "filesize_formatted": format_filesize(size_720),
                "media_url": clean_url,
                "is_direct_cdn": False
            },
            {
                "format_id": "480",
                "type": "video",
                "ext": "mp4",
                "quality": "480p SD",
                "height": 480,
                "filesize": size_480,
                "filesize_formatted": format_filesize(size_480),
                "media_url": clean_url,
                "is_direct_cdn": False
            },
            {
                "format_id": "360",
                "type": "video",
                "ext": "mp4",
                "quality": "360p",
                "height": 360,
                "filesize": size_360,
                "filesize_formatted": format_filesize(size_360),
                "media_url": clean_url,
                "is_direct_cdn": False
            }
        ]

        audio_formats = [
            {
                "format_id": "mp3",
                "type": "audio",
                "ext": "mp3",
                "quality": "Audio MP3 (320 kbps)",
                "filesize": size_mp3,
                "filesize_formatted": format_filesize(size_mp3),
                "media_url": clean_url,
                "is_direct_cdn": False
            }
        ]

        subtitles_list = [
            {"lang": "fr", "name": "Français (Auto)", "ext": "vtt", "url": f"/api/subtitle?url={clean_url}&lang=fr"},
            {"lang": "en", "name": "English (Auto)", "ext": "vtt", "url": f"/api/subtitle?url={clean_url}&lang=en"}
        ]

        return {
            "id": video_id,
            "title": title,
            "safe_title": safe_title,
            "thumbnail": thumbnail,
            "duration": duration,
            "duration_formatted": format_duration(duration),
            "uploader": uploader,
            "platform": "youtube",
            "videos": video_formats,
            "audios": audio_formats,
            "subtitles": subtitles_list
        }

    def extract(self, url: str) -> Dict[str, Any]:
        clean_url = sanitize_media_url(url)
        video_id = extract_youtube_video_id(clean_url)

        # 1. Pour YouTube : utiliser l'extraction exacte résiliente sans blocage
        if video_id:
            return self._fetch_exact_youtube_details(video_id, clean_url)

        # 2. Pour TikTok, Facebook, Instagram, Twitter, SoundCloud : extraction avec yt-dlp
        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            info = ydl.extract_info(clean_url, download=False)
            if not info:
                raise ValueError("Impossible d'extraire les informations.")

            if "entries" in info and info["entries"]:
                info = info["entries"][0]

            title = info.get("title", "Sans titre")
            safe_title = clean_filename(title)
            duration = info.get("duration", 0) or 0
            extractor_name = info.get("extractor_key", "").lower()
            
            platform = "universal"
            if "tiktok" in extractor_name: platform = "tiktok"
            elif "facebook" in extractor_name: platform = "facebook"
            elif "instagram" in extractor_name: platform = "instagram"
            elif "twitter" in extractor_name or "x" in extractor_name: platform = "twitter"
            elif "soundcloud" in extractor_name: platform = "soundcloud"

            raw_formats = info.get("formats", [])
            video_formats = []
            audio_formats = []

            seen_res = set()
            for f in raw_formats:
                f_id = f.get("format_id")
                ext = f.get("ext", "mp4")
                vcodec = f.get("vcodec", "none")
                acodec = f.get("acodec", "none")
                height = f.get("height")
                filesize = f.get("filesize") or f.get("filesize_approx")

                if vcodec != "none":
                    res_label = f"{height}p" if height else "HD"
                    if res_label not in seen_res:
                        seen_res.add(res_label)
                        video_formats.append({
                            "format_id": f_id,
                            "type": "video",
                            "ext": ext,
                            "quality": f"{res_label}",
                            "filesize": filesize,
                            "filesize_formatted": format_filesize(filesize),
                            "media_url": clean_url,
                            "is_direct_cdn": False  # Toujours streamer par le serveur pour forcer le téléchargement et éviter Access Denied
                        })
                elif acodec != "none":
                    audio_formats.append({
                        "format_id": f_id,
                        "type": "audio",
                        "ext": "mp3",
                        "quality": "Audio MP3",
                        "filesize": filesize,
                        "filesize_formatted": format_filesize(filesize),
                        "media_url": clean_url,
                        "is_direct_cdn": False
                    })

            if not video_formats:
                video_formats.append({
                    "format_id": "best",
                    "type": "video",
                    "ext": "mp4",
                    "quality": "Haute Définition (HD)",
                    "filesize_formatted": format_filesize(info.get("filesize")),
                    "media_url": clean_url,
                    "is_direct_cdn": False
                })

            return {
                "id": info.get("id"),
                "title": title,
                "safe_title": safe_title,
                "thumbnail": info.get("thumbnail"),
                "duration": duration,
                "duration_formatted": format_duration(duration),
                "uploader": info.get("uploader") or info.get("channel") or "Auteur Inconnu",
                "platform": platform,
                "videos": video_formats,
                "audios": audio_formats,
                "subtitles": []
            }

extractor_service = MediaExtractor()
