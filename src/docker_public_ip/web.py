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
        recent_checks = db.get_recent_checks(limit=100)
        ip_changes = db.get_ip_changes()
        service_stats = db.get_service_stats()
        change_stats = db.get_ip_change_stats()
        stability_stats = db.get_ip_stability_stats()

        # Get current IP
        current_ip = None
        last_check = "Never"
        for check in recent_checks:
            if check["success"] and check["ip_address"]:
                current_ip = check["ip_address"]
                last_check = check["timestamp"]
                break

        # Calculate basic statistics
        total_checks = len(recent_checks)
        successful_checks = sum(1 for c in recent_checks if c["success"])
        success_rate = (
            round(successful_checks / total_checks * 100, 1) if total_checks > 0 else 0
        )

        # Prepare chart data for daily IP changes
        daily_changes_data = [
            {
                "x": [stat["date"] for stat in change_stats["daily"]],
                "y": [stat["changes"] for stat in change_stats["daily"]],
                "type": "bar",
                "name": "Changes per Day",
                "marker": {"color": "rgb(55, 83, 109)"},
            }
        ]

        # Prepare chart data for weekly IP changes
        weekly_changes_data = [
            {
                "x": [stat["week"] for stat in change_stats["weekly"]],
                "y": [stat["changes"] for stat in change_stats["weekly"]],
                "type": "bar",
                "name": "Changes per Week",
                "marker": {"color": "rgb(26, 118, 255)"},
            }
        ]

        # Prepare chart data for monthly IP changes
        monthly_changes_data = [
            {
                "x": [stat["month"] for stat in change_stats["monthly"]],
                "y": [stat["changes"] for stat in change_stats["monthly"]],
                "type": "bar",
                "name": "Changes per Month",
                "marker": {"color": "rgb(255, 99, 132)"},
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
            daily_changes_data=daily_changes_data,
            weekly_changes_data=weekly_changes_data,
            monthly_changes_data=monthly_changes_data,
            stability_stats=stability_stats,
        )

    @app.route("/health")
    def health():
        return {"status": "healthy"}

    return app


def run_web_server(checker):
    app = create_app()
    logger.info(f"Starting web server on {WEB_HOST}:{WEB_PORT}")
    app.run(host=WEB_HOST, port=WEB_PORT, debug=False)
