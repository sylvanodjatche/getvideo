import time
import ipaddress
from urllib.parse import urlparse
from collections import defaultdict
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

class SecurityManager:
    def __init__(self):
        # Rate Limiting: IP -> liste de timestamps
        self.request_history = defaultdict(list)
        self.MAX_REQUESTS_PER_MINUTE = 15
        self.RATE_LIMIT_WINDOW = 60  # secondes

        # Liste de bots malveillants connus / scrapers agressifs
        self.BLOCKED_USER_AGENTS = [
            "sqlmap", "nikto", "masscan", "nmap", "semrushbot",
            "mj12bot", "ahrefsbot", "dotbot", "censys", "zgrab"
        ]

        # IP privées interdites (Protection SSRF)
        self.BLOCKED_IP_NETWORKS = [
            ipaddress.ip_network("127.0.0.0/8"),
            ipaddress.ip_network("10.0.0.0/8"),
            ipaddress.ip_network("172.16.0.0/12"),
            ipaddress.ip_network("192.168.0.0/16"),
            ipaddress.ip_network("169.254.0.0/16"),
            ipaddress.ip_network("::1/128"),
            ipaddress.ip_network("fc00::/7"),
            ipaddress.ip_network("fe80::/10"),
        ]

    def get_client_ip(self, request: Request) -> str:
        # Prise en compte des headers Cloudflare / Reverse Proxy si présents
        cf_ip = request.headers.get("cf-connecting-ip")
        if cf_ip:
            return cf_ip.strip()
        x_forwarded = request.headers.get("x-forwarded-for")
        if x_forwarded:
            return x_forwarded.split(",")[0].strip()
        return request.client.host if request.client else "127.0.0.1"

    def check_rate_limit(self, client_ip: str):
        now = time.time()
        timestamps = self.request_history[client_ip]

        # Nettoyer les requêtes hors de la fenêtre
        self.request_history[client_ip] = [t for t in timestamps if now - t < self.RATE_LIMIT_WINDOW]

        if len(self.request_history[client_ip]) >= self.MAX_REQUESTS_PER_MINUTE:
            raise HTTPException(
                status_code=429,
                detail="Trop de requêtes. Veuillez patienter une minute avant de réessayer (Protection anti-abus)."
            )

        self.request_history[client_ip].append(now)

    def validate_url(self, url: str):
        """Protection stricte contre les attaques SSRF (Server-Side Request Forgery)."""
        if not url:
            raise HTTPException(status_code=400, detail="URL requise.")

        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise HTTPException(status_code=400, detail="Protocole non supporté. Utilisez http:// ou https://")

        hostname = parsed.hostname
        if not hostname:
            raise HTTPException(status_code=400, detail="Nom d'hôte invalide.")

        # Vérifier si l'URL pointe vers localhost ou une IP privée
        if hostname.lower() in ("localhost", "127.0.0.1", "0.0.0.0", "::1"):
            raise HTTPException(status_code=403, detail="Accès aux adresses locales strictement interdit.")

        try:
            ip = ipaddress.ip_address(hostname)
            for network in self.BLOCKED_IP_NETWORKS:
                if ip in network:
                    raise HTTPException(status_code=403, detail="Accès aux réseaux privés interdit.")
        except ValueError:
            # C'est un nom de domaine (ex: youtube.com), ce qui est valide
            pass

    def check_user_agent(self, request: Request):
        user_agent = request.headers.get("user-agent", "").lower()
        for blocked in self.BLOCKED_USER_AGENTS:
            if blocked in user_agent:
                raise HTTPException(status_code=403, detail="Accès refusé pour ce client.")

security_manager = SecurityManager()
