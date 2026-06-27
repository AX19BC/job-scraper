from datetime import datetime
import re
import requests
from scrapers.base import BaseScraper
from models import Job


def _to_slug(title: str) -> str:
    s = title.lower()
    for src, dst in [('č','c'),('š','s'),('ž','z'),('đ','d'),('ć','c')]:
        s = s.replace(src, dst)
    s = s.replace('/', '')
    s = re.sub(r'[^a-z0-9]+', '-', s)
    s = re.sub(r'-+', '-', s).strip('-')
    return s

API_URL = "https://api.mojedelo.com/job-ads-search"
API_HEADERS = {
    "tenantid": "5947a585-ad25-47dc-bff3-f08620d1ce17",
    "languageid": "db3c58e6-a083-4f72-b30b-39f2127bb18d",
    "channelid": "8805c1b8-a0a9-4f57-ad42-329af3c92a61",
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (compatible; JobScraper/1.0)",
}
TIMEOUT = 30
PAGE_SIZE = 50


class MojedeloScraper(BaseScraper):
    def __init__(self, portal_config: dict, search_queries: list[str]):
        super().__init__(portal_config)
        self.search_queries = search_queries

    def fetch_jobs(self) -> list[Job]:
        jobs, seen = [], set()
        for query in self.search_queries:
            params = {"keyword": query, "pageSize": PAGE_SIZE, "startFrom": 0}
            r = requests.get(API_URL, headers=API_HEADERS, params=params, timeout=TIMEOUT)
            r.raise_for_status()
            for item in r.json().get("data", {}).get("items", []):
                job = self._parse(item)
                if job and job.url not in seen:
                    seen.add(job.url)
                    jobs.append(job)
        return jobs

    def _parse(self, item: dict) -> Job | None:
        try:
            job_id = item.get("id", "")
            if not job_id:
                return None
            company = item.get("company") or {}
            town = item.get("town") or {}
            gross = item.get("grossHourlyRate")
            salary = f"{gross} €/h" if gross else None
            start = item.get("startDate", "")[:10] if item.get("startDate") else ""
            return Job(
                title=item.get("title", ""),
                company=company.get("name", "") if isinstance(company, dict) else "",
                url=f"https://www.mojedelo.com/oglas/{_to_slug(item.get('title',''))}/{job_id}",
                portal=self.name,
                description=item.get("adSummary", "")[:300],
                requirements=[],
                salary=salary,
                location=town.get("name", "") if isinstance(town, dict) else "",
                posted_date=start,
                category="",
                scraped_at=datetime.now().isoformat(timespec="seconds"),
            )
        except Exception:
            return None
