from datetime import datetime
import json
import requests
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper
from models import Job

TIMEOUT = 30
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; JobScraper/1.0)"}
BASE_URL = "https://www.bettercareer.si"
CATEGORIES = ["backend", "fullstack", "infrastructure", "data-science", "it-management"]


class BettercareerScraper(BaseScraper):
    def __init__(self, portal_config: dict, search_queries: list[str]):
        super().__init__(portal_config)

    def fetch_jobs(self) -> list[Job]:
        jobs, seen = [], set()
        for category in CATEGORIES:
            r = requests.get(f"{BASE_URL}/jobs/{category}",
                             headers=HEADERS, timeout=TIMEOUT)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            script = soup.find("script", id="__NEXT_DATA__")
            if not script:
                continue
            data = json.loads(script.string)
            items = data.get("props", {}).get("pageProps", {}).get("jobs", [])
            for item in items:
                job = self._parse(item)
                if job and job.url not in seen:
                    seen.add(job.url)
                    jobs.append(job)
        return jobs

    def _parse(self, item: dict) -> Job | None:
        try:
            job_slug = item.get("jobSlug", "")
            company_slug = item.get("companySlug", "")
            if not job_slug or not company_slug:
                return None
            locations = item.get("locations") or ""
            if isinstance(locations, list):
                locations = ", ".join(locations)
            return Job(
                title=item.get("position", ""),
                company=item.get("companyName", ""),
                url=f"{BASE_URL}/job/{company_slug}/{job_slug}",
                portal=self.name,
                description=item.get("shortDescription") or "",
                requirements=[],
                salary=item.get("salary"),
                location=locations,
                posted_date=item.get("published", ""),
                category="",
                scraped_at=datetime.now().isoformat(timespec="seconds"),
            )
        except Exception:
            return None
