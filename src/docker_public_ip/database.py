import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from loguru import logger

from .config import DB_PATH


class Database:
    def __init__(self):
        self.db_path = DB_PATH
        self.init_db()

    def init_db(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ip_checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    service TEXT NOT NULL,
                    ip_address TEXT,
                    response_time_ms REAL,
                    success BOOLEAN DEFAULT 1,
                    error_message TEXT
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON ip_checks (timestamp DESC)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_ip_address 
                ON ip_checks (ip_address)
            """)
            
            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")

    def record_check(
        self,
        service: str,
        ip_address: str = None,
        response_time_ms: float = None,
        success: bool = True,
        error_message: str = None,
    ):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO ip_checks 
                (service, ip_address, response_time_ms, success, error_message)
                VALUES (?, ?, ?, ?, ?)
                """,
                (service, ip_address, response_time_ms, success, error_message),
            )
            conn.commit()

    def get_recent_checks(self, limit: int = 100) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT * FROM ip_checks 
                ORDER BY timestamp DESC 
                LIMIT ?
                """,
                (limit,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_ip_changes(self) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                WITH ip_changes AS (
                    SELECT 
                        timestamp,
                        ip_address,
                        LAG(ip_address) OVER (ORDER BY timestamp) as previous_ip
                    FROM ip_checks
                    WHERE success = 1 AND ip_address IS NOT NULL
                )
                SELECT 
                    timestamp,
                    ip_address,
                    previous_ip
                FROM ip_changes
                WHERE ip_address != previous_ip OR previous_ip IS NULL
                ORDER BY timestamp DESC
                """
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_service_stats(self) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT 
                    service,
                    COUNT(*) as total_checks,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_checks,
                    AVG(CASE WHEN success = 1 THEN response_time_ms ELSE NULL END) as avg_response_time,
                    MIN(CASE WHEN success = 1 THEN response_time_ms ELSE NULL END) as min_response_time,
                    MAX(CASE WHEN success = 1 THEN response_time_ms ELSE NULL END) as max_response_time
                FROM ip_checks
                GROUP BY service
                ORDER BY successful_checks DESC, avg_response_time ASC
                """
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_hourly_stats(self, days: int = 7) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT 
                    strftime('%Y-%m-%d %H:00:00', timestamp) as hour,
                    COUNT(DISTINCT ip_address) as unique_ips,
                    COUNT(*) as total_checks,
                    AVG(response_time_ms) as avg_response_time
                FROM ip_checks
                WHERE timestamp > datetime('now', '-' || ? || ' days')
                    AND success = 1
                GROUP BY hour
                ORDER BY hour DESC
                """,
                (days,),
            )
            return [dict(row) for row in cursor.fetchall()]