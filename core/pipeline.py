import importlib
import json
import logging
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from core.aggregator import aggregate
from core.classifier import classify
from core.config import load_config
from models import Job

_jobs_path = Path(__file__).parent.parent / "data" / "jobs.json"

_logger = logging.getLogger("job_scraper.pipeline")
_logging_configured = False


def _configure_logging() -> None:
    global _logging_configured
    if _logging_configured:
        return
    log_path = Path(__file__).parent.parent / "data" / "scraper.log"
    log_path.parent.mkdir(exist_ok=True)
    handler = logging.FileHandler(str(log_path), encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
    _logger.addHandler(handler)
    _logger.setLevel(logging.ERROR)
    _logging_configured = True


def _load_scraper(portal_config: dict, search_queries: list[str]):
    module = importlib.import_module(portal_config["module"])
    raw = portal_config["module"].split(".")[-1]
    class_name = "".join(part.title() for part in raw.split("_")) + "Scraper"
    return getattr(module, class_name)(portal_config, search_queries)


def run_pipeline() -> dict:
    _configure_logging()
    cfg = load_config()
    errors: list[dict] = []
    job_lists: list[list[Job]] = []

    for portal_cfg in cfg["portals"]:
        if not portal_cfg.get("enabled", True):
            continue
        try:
            scraper = _load_scraper(portal_cfg, cfg["search_queries"])
            job_lists.append(scraper.fetch_jobs())
        except Exception as exc:
            _logger.error(f"{portal_cfg['name']}: {exc}")
            errors.append({"portal": portal_cfg["name"], "error": str(exc)})

    all_jobs = aggregate(job_lists)

    for job in all_jobs:
        is_public = any(
            p.get("is_public_sector", False) and p["name"] in job.portal
            for p in cfg["portals"]
        )
        job.category = classify(job, cfg["keywords"], is_public)

    all_jobs = [j for j in all_jobs if j.category != "unrelated"]

    result = {
        "scraped_at": datetime.now().isoformat(timespec="seconds"),
        "total": len(all_jobs),
        "errors": errors,
        "jobs": [asdict(j) for j in all_jobs],
    }

    _jobs_path.parent.mkdir(exist_ok=True)
    _jobs_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return result
