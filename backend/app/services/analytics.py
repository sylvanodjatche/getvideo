import sqlite3
import os
import time
from typing import Dict, Any

DB_PATH = os.path.join(os.path.dirname(__file__), "../../../data/analytics.db")

class AnalyticsManager:
    def __init__(self):
        # Assurer que le dossier data existe
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(DB_PATH, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Table des visites et événements
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    platform TEXT,
                    format_type TEXT,
                    filesize INTEGER DEFAULT 0,
                    client_ip_hash TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def track_event(self, event_type: str, platform: str = None, format_type: str = None, filesize: int = 0):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO events (event_type, platform, format_type, filesize)
                    VALUES (?, ?, ?, ?)
                """, (event_type, platform or "unknown", format_type or "unknown", filesize))
                conn.commit()
        except Exception as e:
            print(f"[Analytics] Erreur tracking: {e}")

    def get_dashboard_stats(self) -> Dict[str, Any]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Total Analyses et Téléchargements
            cursor.execute("SELECT COUNT(*) as total FROM events WHERE event_type = 'analyze'")
            total_analyses = cursor.fetchone()['total']

            cursor.execute("SELECT COUNT(*) as total FROM events WHERE event_type = 'download'")
            total_downloads = cursor.fetchone()['total']

            cursor.execute("SELECT SUM(filesize) as total_bytes FROM events WHERE event_type = 'download'")
            total_bytes = cursor.fetchone()['total_bytes'] or 0

            # 2. Répartition par Plateforme
            cursor.execute("""
                SELECT platform, COUNT(*) as count 
                FROM events 
                WHERE event_type = 'analyze' 
                GROUP BY platform 
                ORDER BY count DESC 
                LIMIT 5
            """)
            platforms = [dict(row) for row in cursor.fetchall()]

            # 3. Répartition Vidéo vs Audio
            cursor.execute("""
                SELECT format_type, COUNT(*) as count 
                FROM events 
                WHERE event_type = 'download' 
                GROUP BY format_type
            """)
            formats = [dict(row) for row in cursor.fetchall()]

            # 4. Activité des dernières 24h
            cursor.execute("""
                SELECT strftime('%H:00', created_at) as hour, COUNT(*) as count
                FROM events
                WHERE created_at >= datetime('now', '-24 hours') AND event_type = 'download'
                GROUP BY hour
                ORDER BY hour ASC
            """)
            recent_activity = [dict(row) for row in cursor.fetchall()]

            # Formatage de la bande passante totale
            gb_transferred = round(total_bytes / (1024 * 1024 * 1024), 2)

            return {
                "total_analyses": total_analyses,
                "total_downloads": total_downloads,
                "total_gb_transferred": gb_transferred,
                "platforms": platforms,
                "formats": formats,
                "recent_activity": recent_activity
            }

analytics_service = AnalyticsManager()
