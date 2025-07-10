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
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ip_checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    service TEXT NOT NULL,
                    ip_address TEXT,
                    response_time_ms REAL,
                    success BOOLEAN DEFAULT 1,
                    error_message TEXT
                )
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON ip_checks (timestamp DESC)
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_ip_address 
                ON ip_checks (ip_address)
            """
            )

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

    def get_ip_change_stats(self) -> Dict[str, Any]:
        """Get statistics about IP changes per day/week/month"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Get daily IP changes for last 30 days
            daily_cursor = conn.execute(
                """
                WITH ip_changes AS (
                    SELECT 
                        DATE(timestamp) as date,
                        ip_address,
                        ROW_NUMBER() OVER (PARTITION BY DATE(timestamp) ORDER BY timestamp) as rn,
                        LAG(ip_address) OVER (ORDER BY timestamp) as previous_ip
                    FROM ip_checks
                    WHERE success = 1 AND ip_address IS NOT NULL
                        AND timestamp > datetime('now', '-30 days')
                )
                SELECT 
                    date,
                    COUNT(CASE WHEN ip_address != previous_ip THEN 1 END) as changes
                FROM ip_changes
                WHERE rn = 1 OR ip_address != previous_ip
                GROUP BY date
                ORDER BY date DESC
                """
            )
            daily_changes = [dict(row) for row in daily_cursor.fetchall()]

            # Get weekly IP changes for last 12 weeks
            weekly_cursor = conn.execute(
                """
                WITH ip_changes AS (
                    SELECT 
                        strftime('%Y-W%W', timestamp) as week,
                        ip_address,
                        LAG(ip_address) OVER (ORDER BY timestamp) as previous_ip
                    FROM ip_checks
                    WHERE success = 1 AND ip_address IS NOT NULL
                        AND timestamp > datetime('now', '-84 days')
                )
                SELECT 
                    week,
                    COUNT(CASE WHEN ip_address != previous_ip THEN 1 END) as changes
                FROM ip_changes
                WHERE ip_address != previous_ip OR previous_ip IS NULL
                GROUP BY week
                ORDER BY week DESC
                """
            )
            weekly_changes = [dict(row) for row in weekly_cursor.fetchall()]

            # Get monthly IP changes for last 12 months
            monthly_cursor = conn.execute(
                """
                WITH ip_changes AS (
                    SELECT 
                        strftime('%Y-%m', timestamp) as month,
                        ip_address,
                        LAG(ip_address) OVER (ORDER BY timestamp) as previous_ip
                    FROM ip_checks
                    WHERE success = 1 AND ip_address IS NOT NULL
                        AND timestamp > datetime('now', '-12 months')
                )
                SELECT 
                    month,
                    COUNT(CASE WHEN ip_address != previous_ip THEN 1 END) as changes
                FROM ip_changes
                WHERE ip_address != previous_ip OR previous_ip IS NULL
                GROUP BY month
                ORDER BY month DESC
                """
            )
            monthly_changes = [dict(row) for row in monthly_cursor.fetchall()]

            return {
                "daily": daily_changes,
                "weekly": weekly_changes,
                "monthly": monthly_changes,
            }

    def get_ip_stability_stats(self) -> Dict[str, Any]:
        """Get statistics about IP stability"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Average time between IP changes
            cursor = conn.execute(
                """
                WITH ip_changes AS (
                    SELECT 
                        timestamp,
                        ip_address,
                        LAG(timestamp) OVER (ORDER BY timestamp) as previous_timestamp
                    FROM ip_checks
                    WHERE success = 1 AND ip_address IS NOT NULL
                        AND ip_address != (
                            SELECT ip_address 
                            FROM ip_checks AS ic2 
                            WHERE ic2.timestamp < ip_checks.timestamp 
                                AND ic2.success = 1 
                                AND ic2.ip_address IS NOT NULL
                            ORDER BY ic2.timestamp DESC 
                            LIMIT 1
                        )
                )
                SELECT 
                    AVG(CAST((julianday(timestamp) - julianday(previous_timestamp)) * 24 * 60 AS REAL)) as avg_minutes_between_changes,
                    COUNT(*) as total_changes,
                    MIN(CAST((julianday(timestamp) - julianday(previous_timestamp)) * 24 * 60 AS REAL)) as min_minutes_between_changes,
                    MAX(CAST((julianday(timestamp) - julianday(previous_timestamp)) * 24 * 60 AS REAL)) as max_minutes_between_changes
                FROM ip_changes
                WHERE previous_timestamp IS NOT NULL
                """
            )
            stability = dict(cursor.fetchone() or {})

            # Most frequent IPs
            cursor = conn.execute(
                """
                SELECT 
                    ip_address,
                    COUNT(*) as frequency,
                    MIN(timestamp) as first_seen,
                    MAX(timestamp) as last_seen
                FROM ip_checks
                WHERE success = 1 AND ip_address IS NOT NULL
                GROUP BY ip_address
                ORDER BY frequency DESC
                LIMIT 10
                """
            )
            frequent_ips = [dict(row) for row in cursor.fetchall()]

            return {"stability": stability, "frequent_ips": frequent_ips}
