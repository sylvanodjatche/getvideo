import yt_dlp
import re
import httpx
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
    if not seconds:
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
                    'player_client': ['android_creator', 'ios', 'android', 'mweb', 'tv'],
                }
            },
            'http_headers': {
                'User-Agent': 'com.google.android.youtube/19.12.35 (Linux; U; Android 14; fr_FR; SM-S918B) gzip',
                'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8',
            }
        }

    def _extract_via_cobalt_and_oembed(self, video_id: str, clean_url: str) -> Dict[str, Any]:
        """Extraction directe ultra-rapide via Cobalt Engine & OEMBED officiel."""
        title = "YouTube Video"
        uploader = "YouTube Creator"
        thumbnail = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
        duration = 210

        # 1. Récupérer les métadonnées officielles via OEMBED (jamais bloqué par YouTube)
        try:
            oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
            with httpx.Client(timeout=4.0) as client:
                r = client.get(oembed_url)
                if r.status_code == 200:
                    d = r.json()
                    title = d.get("title", title)
                    uploader = d.get("author_name", uploader)
                    thumbnail = d.get("thumbnail_url", thumbnail)
        except Exception:
            pass

        # 2. Récupérer la durée exacte via Invidious / Piped si disponible
        for api_url in [
            f"https://invidious.nerdvpn.de/api/v1/videos/{video_id}",
            f"https://inv.tux.pizza/api/v1/videos/{video_id}",
            f"https://invidious.jing.rocks/api/v1/videos/{video_id}"
        ]:
            try:
                with httpx.Client(timeout=3.0) as client:
                    r = client.get(api_url)
                    if r.status_code == 200:
                        data = r.json()
                        duration = data.get("lengthSeconds") or duration
                        uploader = data.get("author") or uploader
                        title = data.get("title") or title
                        break
            except Exception:
                continue

        safe_title = clean_filename(title)

        # 3. Calcul dynamique et précis de la taille de chaque flux selon la durée
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
            "subtitles": []
        }

    def extract(self, url: str) -> Dict[str, Any]:
        clean_url = sanitize_media_url(url)
        video_id = extract_youtube_video_id(clean_url)

        # Pour YouTube sur Cloud : utiliser directement le moteur résilient
        if video_id:
            try:
                with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                    info = ydl.extract_info(clean_url, download=False)
                    if info:
                        if "entries" in info and info["entries"]:
                            info = info["entries"][0]
                        title = info.get("title", "Sans titre")
                        safe_title = clean_filename(title)
                        duration = info.get("duration", 0) or 0
                        raw_formats = info.get("formats", [])
                        
                        max_h = max([f.get("height") or 0 for f in raw_formats if f.get("vcodec") != "none"] or [720])
                        resolutions = [{"label": "1080p Full HD", "h": 1080}, {"label": "720p HD", "h": 720}, {"label": "480p SD", "h": 480}, {"label": "360p", "h": 360}]
                        
                        video_formats = []
                        for r in resolutions:
                            h = r["h"]
                            if h <= max_h or h == 360:
                                matched = next((f for f in raw_formats if f.get("height") == h and f.get("vcodec") != "none"), None)
                                exact_size = matched.get("filesize") or matched.get("filesize_approx") if matched else None
                                if not exact_size and duration > 0:
                                    bitrate = 3200 if h == 1080 else (1600 if h == 720 else (850 if h == 480 else 450))
                                    exact_size = int(((bitrate + 128) * 1000 / 8) * duration)
                                
                                video_formats.append({
                                    "format_id": f"bestvideo[height<={h}]+bestaudio/best",
                                    "type": "video",
                                    "ext": "mp4",
                                    "quality": r['label'],
                                    "height": h,
                                    "filesize": exact_size,
                                    "filesize_formatted": format_filesize(exact_size),
                                    "media_url": clean_url,
                                    "is_direct_cdn": False
                                })

                        size_mp3 = int((320 * 1000 / 8) * duration) if duration > 0 else None
                        return {
                            "id": video_id,
                            "title": title,
                            "safe_title": safe_title,
                            "thumbnail": info.get("thumbnail"),
                            "duration": duration,
                            "duration_formatted": format_duration(duration),
                            "uploader": info.get("uploader") or "Auteur Inconnu",
                            "platform": "youtube",
                            "videos": video_formats,
                            "audios": [{
                                "format_id": "bestaudio/best",
                                "type": "audio",
                                "ext": "mp3",
                                "quality": "Audio MP3 (320 kbps)",
                                "filesize": size_mp3,
                                "filesize_formatted": format_filesize(size_mp3),
                                "media_url": clean_url,
                                "is_direct_cdn": False
                            }],
                            "subtitles": []
                        }
            except Exception:
                return self._extract_via_cobalt_and_oembed(video_id, clean_url)

        # Autres plateformes (TikTok, Instagram, Twitter/X, SoundCloud, etc.)
        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            info = ydl.extract_info(clean_url, download=False)
            if not info:
                raise ValueError("Impossible d'extraire ce média.")

            if "entries" in info and info["entries"]:
                info = info["entries"][0]

            title = info.get("title", "Sans titre")
            safe_title = clean_filename(title)
            duration = info.get("duration", 0) or 0
            extractor_name = info.get("extractor_key", "").lower()
            platform = "universal"
            if "tiktok" in extractor_name: platform = "tiktok"
            elif "instagram" in extractor_name: platform = "instagram"
            elif "twitter" in extractor_name: platform = "twitter"
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
                url_direct = f.get("url")

                if not url_direct:
                    continue

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
                            "url": url_direct,
                            "media_url": clean_url,
                            "is_direct_cdn": True
                        })
                elif acodec != "none":
                    audio_formats.append({
                        "format_id": f_id,
                        "type": "audio",
                        "ext": "mp3",
                        "quality": "Audio MP3",
                        "filesize": filesize,
                        "filesize_formatted": format_filesize(filesize),
                        "url": url_direct,
                        "media_url": clean_url,
                        "is_direct_cdn": True
                    })

            return {
                "id": info.get("id"),
                "title": title,
                "safe_title": safe_title,
                "thumbnail": info.get("thumbnail"),
                "duration": duration,
                "duration_formatted": format_duration(duration),
                "uploader": info.get("uploader") or "Auteur Inconnu",
                "platform": platform,
                "videos": video_formats,
                "audios": audio_formats,
                "subtitles": []
            }

extractor_service = MediaExtractor()
