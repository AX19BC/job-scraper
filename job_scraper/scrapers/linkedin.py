from datetime import datetime
import time
import requests
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper
from models import Job

TIMEOUT = 30
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}
SEARCH_URL = "https://si.linkedin.com/jobs/search/"


class LinkedinScraper(BaseScraper):
    def __init__(self, portal_config: dict, search_queries: list[str]):
        super().__init__(portal_config)
        self.search_queries = search_queries

    def fetch_jobs(self) -> list[Job]:
        jobs, seen = [], set()
        for i, query in enumerate(self.search_queries):
            if i > 0:
                time.sleep(2)
            params = {"keywords": query, "location": "Slovenia", "f_TPR": "r2592000"}
            r = requests.get(SEARCH_URL, headers=HEADERS, params=params, timeout=TIMEOUT)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            for li in soup.select("ul.jobs-search__results-list li"):
                job = self._parse(li)
                if job and job.url not in seen:
                    seen.add(job.url)
                    jobs.append(job)
        return jobs

    def _parse(self, li) -> Job | None:
        try:
            a = li.select_one("a.base-card__full-link")
            if not a:
                return None
            url = a["href"].split("?")[0]
            title_el = li.select_one(".base-search-card__title")
            company_el = li.select_one(".base-search-card__subtitle")
            location_el = li.select_one(".job-search-card__location")
            date_el = li.select_one("time")
            return Job(
                title=title_el.get_text(strip=True) if title_el else "",
                company=company_el.get_text(strip=True) if company_el else "",
                url=url,
                portal=self.name,
                description="",
                requirements=[],
                salary=None,
                location=location_el.get_text(strip=True) if location_el else "",
                posted_date=date_el.get("datetime", "") if date_el else "",
                category="",
                scraped_at=datetime.now().isoformat(timespec="seconds"),
            )
        except Exception:
            return None
