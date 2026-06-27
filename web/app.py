import json, os
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, render_template, redirect, url_for
from apscheduler.schedulers.background import BackgroundScheduler
from core.pipeline import run_pipeline
from core.mailer import send_email
from core.config import load_config


CATEGORY_ORDER = ["cyber_security", "public_sector_cyber", "network", "sysadmin", "it_other"]
CATEGORY_LABELS = {
    "cyber_security": "Cyber Security",
    "public_sector_cyber": "Javni sektor – Cyber Security",
    "network": "Network Engineer",
    "sysadmin": "Sistemski Administrator",
    "it_other": "Ostali IT",
}


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates")

    def _jobs_path() -> Path:
        return Path(os.environ.get("JOBS_PATH", "data/jobs.json"))

    @app.route("/")
    def dashboard():
        path = _jobs_path()
        data = (json.loads(path.read_text(encoding="utf-8"))
                if path.exists()
                else {"scraped_at": None, "total": 0, "errors": [], "jobs": []})
        jobs_by_cat = {cat: [] for cat in CATEGORY_ORDER}
        for job in data.get("jobs", []):
            cat = job.get("category", "it_other")
            if cat in jobs_by_cat:
                jobs_by_cat[cat].append(job)
        seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        return render_template(
            "dashboard.html",
            jobs_by_cat=jobs_by_cat,
            category_labels=CATEGORY_LABELS,
            category_order=CATEGORY_ORDER,
            scraped_at=data.get("scraped_at"),
            total=data.get("total", 0),
            errors=data.get("errors", []),
            seven_days_ago=seven_days_ago,
        )

    @app.route("/run-now", methods=["POST"])
    def run_now():
        def _run():
            result = run_pipeline()
            send_email(result, load_config())

        scheduler = BackgroundScheduler()
        scheduler.add_job(_run, "date")
        scheduler.start()
        return redirect(url_for("dashboard"))


    return app


app = create_app()
