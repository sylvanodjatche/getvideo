import yt_dlp
import re
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
        }

    def extract(self, url: str) -> Dict[str, Any]:
        clean_url = sanitize_media_url(url)
        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            info = ydl.extract_info(clean_url, download=False)
            if not info:
                raise ValueError("Impossible d'extraire les informations pour ce média.")

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

            # 1. Calcul dynamique des tailles réelles pour chaque qualité
            if platform == "youtube":
                max_h = max([f.get("height") or 0 for f in raw_formats if f.get("vcodec") != "none"] or [720])
                
                # Bitrates standards moyens en kbps pour estimation précise selon la durée réelle
                bitrate_map = {
                    1080: 3200,  # ~3.2 Mbps vidéo + 160 kbps audio
                    720: 1600,   # ~1.6 Mbps vidéo + 128 kbps audio
                    480: 850,    # ~850 kbps vidéo + 128 kbps audio
                    360: 450     # ~450 kbps vidéo + 96 kbps audio
                }

                resolutions = [
                    {"label": "1080p Full HD", "h": 1080},
                    {"label": "720p HD", "h": 720},
                    {"label": "480p SD", "h": 480},
                    {"label": "360p", "h": 360}
                ]
                
                for r in resolutions:
                    h = r["h"]
                    if h <= max_h or h == 360:
                        # Chercher si yt-dlp fournit la taille exacte du flux
                        matched_format = next((f for f in raw_formats if f.get("height") == h and f.get("vcodec") != "none"), None)
                        exact_size = None
                        if matched_format:
                            exact_size = matched_format.get("filesize") or matched_format.get("filesize_approx")
                            if exact_size and matched_format.get("acodec") == "none":
                                # Ajouter l'audio (~16 Ko/s * durée)
                                exact_size += int(16000 * duration)
                        
                        # Si pas de taille exacte dans les métadonnées, calculer précisément via (bitrate * durée)
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

                # Formats Audio calculés selon la durée réelle
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
                # Autres plateformes (TikTok, Instagram, Twitter/X, etc.)
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

                if not video_formats and info.get("url"):
                    video_formats.append({
                        "format_id": "best",
                        "type": "video",
                        "ext": info.get("ext", "mp4"),
                        "quality": "Haute Définition",
                        "filesize_formatted": format_filesize(info.get("filesize")),
                        "url": info.get("url"),
                        "media_url": clean_url,
                        "is_direct_cdn": True
                    })

            # 2. Extraction des sous-titres
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
            
            if not subtitles_list and auto_subs:
                for lang in ["fr", "en", "es", "ar"]:
                    if lang in auto_subs:
                        s_list = auto_subs[lang]
                        srt_entry = next((s for s in s_list if s.get("ext") in ("vtt", "srt")), s_list[0] if s_list else None)
                        if srt_entry:
                            subtitles_list.append({
                                "lang": lang,
                                "name": f"Auto-généré ({lang.upper()})",
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

extractor_service = MediaExtractor()
