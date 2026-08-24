import yt_dlp
import re
import httpx
from typing import Dict, Any, List
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

def format_filesize(bytes_val: int | float | None) -> str:
    if not bytes_val or bytes_val <= 0:
        return "Taille estimée"
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
                    'player_client': ['tv_embedded', 'android', 'ios', 'mweb', 'web_creator'],
                }
            },
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            }
        }

    def _extract_piped_fallback(self, video_id: str, clean_url: str) -> Dict[str, Any]:
        """Fallback via instances Piped / Invidious si l'IP de Render est bloquée par YouTube."""
        instances = [
            f"https://pipedapi.kavin.rocks/streams/{video_id}",
            f"https://api.piped.privacydev.net/streams/{video_id}",
            f"https://piped-api.lunar.icu/streams/{video_id}",
            f"https://invidious.asir.dev/api/v1/videos/{video_id}",
        ]
        
        for endpoint in instances:
            try:
                with httpx.Client(timeout=8.0, follow_redirects=True) as client:
                    resp = client.get(endpoint)
                    if resp.status_code == 200:
                        data = resp.json()
                        title = data.get("title", "YouTube Video")
                        safe_title = clean_filename(title)
                        duration = data.get("duration", 0) or 0
                        uploader = data.get("uploader") or data.get("author") or "YouTube Creator"
                        thumbnail = data.get("thumbnailUrl") or (data.get("videoThumbnails") and data["videoThumbnails"][0]["url"])

                        video_formats = []
                        audio_formats = []
                        
                        # Piped streams parsing
                        video_streams = data.get("videoStreams", [])
                        audio_streams = data.get("audioStreams", [])

                        # Invidious fallback format
                        if not video_streams and "adaptiveFormats" in data:
                            for f in data.get("adaptiveFormats", []):
                                if "video" in f.get("type", ""):
                                    video_streams.append({
                                        "url": f.get("url"),
                                        "quality": f.get("qualityLabel", "HD"),
                                        "height": f.get("height", 720),
                                        "format": "MP4",
                                        "bitrate": f.get("bitrate", 1500000),
                                        "contentLength": f.get("clen")
                                    })
                                elif "audio" in f.get("type", ""):
                                    audio_streams.append({
                                        "url": f.get("url"),
                                        "quality": "128 kbps",
                                        "format": "M4A",
                                        "contentLength": f.get("clen")
                                    })

                        seen_qualities = set()
                        for v in video_streams:
                            q = v.get("quality", "720p")
                            if q not in seen_qualities:
                                seen_qualities.add(q)
                                size = v.get("contentLength") or v.get("filesize")
                                if not size and duration > 0:
                                    bitrate = v.get("bitrate", 1500000)
                                    size = int((bitrate / 8) * duration)

                                video_formats.append({
                                    "format_id": f"piped_{q}",
                                    "type": "video",
                                    "ext": "mp4",
                                    "quality": f"{q} HD",
                                    "filesize": size,
                                    "filesize_formatted": format_filesize(size),
                                    "url": v.get("url"),
                                    "media_url": clean_url,
                                    "is_direct_cdn": True
                                })

                        for a in audio_streams[:2]:
                            size = a.get("contentLength") or a.get("filesize")
                            if not size and duration > 0:
                                size = int((160000 / 8) * duration)
                            audio_formats.append({
                                "format_id": "piped_audio",
                                "type": "audio",
                                "ext": "mp3",
                                "quality": f"Audio ({a.get('quality', 'HQ')})",
                                "filesize": size,
                                "filesize_formatted": format_filesize(size),
                                "url": a.get("url"),
                                "media_url": clean_url,
                                "is_direct_cdn": True
                            })

                        # Subtitles
                        subtitles_list = []
                        for sub in data.get("subtitles", [])[:4]:
                            subtitles_list.append({
                                "lang": sub.get("code", "fr"),
                                "name": sub.get("name", "Sous-titres"),
                                "ext": "vtt",
                                "url": sub.get("url")
                            })

                        if video_formats or audio_formats:
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
            except Exception as ex:
                continue

        raise ValueError("YouTube restreint temporairement l'accès sur ce datacenter. Réessayez dans un instant.")

    def extract(self, url: str) -> Dict[str, Any]:
        clean_url = sanitize_media_url(url)
        video_id = extract_youtube_video_id(clean_url)

        try:
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
                if "youtube" in extractor_name:
                    platform = "youtube"
                elif "tiktok" in extractor_name:
                    platform = "tiktok"
                elif "instagram" in extractor_name:
                    platform = "instagram"
                elif "twitter" in extractor_name or "x" in extractor_name:
                    platform = "twitter"
                elif "soundcloud" in extractor_name:
                    platform = "soundcloud"

                raw_formats = info.get("formats", [])
                video_formats = []
                audio_formats = []

                if platform == "youtube":
                    max_h = max([f.get("height") or 0 for f in raw_formats if f.get("vcodec") != "none"] or [720])
                    bitrate_map = {1080: 3200, 720: 1600, 480: 850, 360: 450}
                    resolutions = [{"label": "1080p Full HD", "h": 1080}, {"label": "720p HD", "h": 720}, {"label": "480p SD", "h": 480}, {"label": "360p", "h": 360}]
                    
                    for r in resolutions:
                        h = r["h"]
                        if h <= max_h or h == 360:
                            matched_format = next((f for f in raw_formats if f.get("height") == h and f.get("vcodec") != "none"), None)
                            exact_size = None
                            if matched_format:
                                exact_size = matched_format.get("filesize") or matched_format.get("filesize_approx")
                                if exact_size and matched_format.get("acodec") == "none":
                                    exact_size += int(16000 * duration)
                            
                            if not exact_size and duration > 0:
                                total_kbps = bitrate_map.get(h, 1000) + 128
                                exact_size = int((total_kbps * 1000 / 8) * duration)

                            video_formats.append({
                                "format_id": f"bestvideo[height<={h}]+bestaudio/best[height<={h}][vcodec!=none][acodec!=none]/best",
                                "type": "video",
                                "ext": "mp4",
                                "quality": r['label'],
                                "height": h,
                                "filesize": exact_size,
                                "filesize_formatted": format_filesize(exact_size),
                                "media_url": clean_url,
                                "is_direct_cdn": False
                            })

                    audio_320_size = int((320 * 1000 / 8) * duration) if duration > 0 else None
                    audio_128_size = int((128 * 1000 / 8) * duration) if duration > 0 else None

                    audio_formats.append({
                        "format_id": "bestaudio/best",
                        "type": "audio",
                        "ext": "mp3",
                        "quality": "Audio MP3 (320 kbps)",
                        "filesize": audio_320_size,
                        "filesize_formatted": format_filesize(audio_320_size),
                        "media_url": clean_url,
                        "is_direct_cdn": False
                    })
                    audio_formats.append({
                        "format_id": "bestaudio[ext=m4a]/bestaudio",
                        "type": "audio",
                        "ext": "m4a",
                        "quality": "Audio M4A (Original)",
                        "filesize": audio_128_size,
                        "filesize_formatted": format_filesize(audio_128_size),
                        "media_url": clean_url,
                        "is_direct_cdn": False
                    })
                else:
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

                # Subtitles
                subtitles_list = []
                subs = info.get("subtitles") or {}
                auto_subs = info.get("automatic_captions") or {}
                for lang, s_list in list(subs.items())[:6]:
                    srt_entry = next((s for s in s_list if s.get("ext") in ("vtt", "srt")), s_list[0] if s_list else None)
                    if srt_entry:
                        subtitles_list.append({
                            "lang": lang,
                            "name": f"Sous-titres ({lang.upper()})",
                            "ext": srt_entry.get("ext", "vtt"),
                            "url": srt_entry.get("url")
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
                    "subtitles": subtitles_list
                }

        except Exception as e:
            error_str = str(e)
            # Si YouTube bloque l'IP du datacenter Render avec "Sign in to confirm you're not a bot"
            if video_id and ("Sign in to confirm" in error_str or "bot" in error_str or "HTTP Error 429" in error_str):
                return self._extract_piped_fallback(video_id, clean_url)
            raise e

extractor_service = MediaExtractor()
