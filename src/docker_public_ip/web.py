from datetime import datetime

from flask import Flask, render_template
from loguru import logger

from .config import WEB_HOST, WEB_PORT
from .database import Database


def create_app():
    app = Flask(__name__)
    db = Database()

    @app.route("/")
    def index():
        recent_checks = db.get_recent_checks(limit=1000)
        ip_changes = db.get_ip_changes()
        service_stats = db.get_service_stats()
        hourly_stats = db.get_hourly_stats()

        # Get current IP
        current_ip = None
        last_check = "Never"
        for check in recent_checks:
            if check["success"] and check["ip_address"]:
                current_ip = check["ip_address"]
                last_check = check["timestamp"]
                break

        # Calculate statistics
        total_checks = len(recent_checks)
        successful_checks = sum(1 for c in recent_checks if c["success"])
        success_rate = (
            round(successful_checks / total_checks * 100, 1) if total_checks > 0 else 0
        )

        # Prepare chart data for response times
        response_time_data = [
            {
                "x": [stat["service"].replace("https://", "") for stat in service_stats],
                "y": [stat["avg_response_time"] or 0 for stat in service_stats],
                "type": "bar",
                "marker": {"color": "rgb(55, 83, 109)"},
            }
        ]

        # Prepare chart data for checks over time
        checks_over_time_data = [
            {
                "x": [stat["hour"] for stat in hourly_stats],
                "y": [stat["total_checks"] for stat in hourly_stats],
                "type": "scatter",
                "mode": "lines+markers",
                "name": "Total Checks",
                "line": {"color": "rgb(55, 83, 109)"},
            }
        ]

        return render_template(
            "index.html",
            current_ip=current_ip,
            last_check=last_check,
            total_checks=total_checks,
            success_rate=success_rate,
            ip_change_count=len(ip_changes),
            ip_changes=ip_changes[:20],  # Show last 20 changes
            service_stats=service_stats,
            response_time_data=response_time_data,
            checks_over_time_data=checks_over_time_data,
        )

    @app.route("/health")
    def health():
        return {"status": "healthy"}

    return app


def run_web_server(checker):
    app = create_app()
    logger.info(f"Starting web server on {WEB_HOST}:{WEB_PORT}")
    app.run(host=WEB_HOST, port=WEB_PORT, debug=False)