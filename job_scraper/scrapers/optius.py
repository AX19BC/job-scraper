from datetime import datetime
import time
import requests
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper
from models import Job

TIMEOUT = 30
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; JobScraper/1.0)"}
SEARCH_URL = "https://www.optius.com/iskalci/prosta-delovna-mesta/"
BASE_URL = "https://www.optius.com"


class OptiusScraper(BaseScraper):
    def __init__(self, portal_config: dict, search_queries: list[str]):
        super().__init__(portal_config)
        self.search_queries = search_queries

    def fetch_jobs(self) -> list[Job]:
        jobs, seen = [], set()
        for i, query in enumerate(self.search_queries):
            if i > 0:
                time.sleep(1)
            r = requests.get(SEARCH_URL, headers=HEADERS,
                             params={"Keywords": query}, timeout=TIMEOUT)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            for li in soup.select("div.job-results-list ul li.item"):
                job = self._parse(li)
                if job and job.url not in seen:
                    seen.add(job.url)
                    jobs.append(job)
        return jobs

    def _parse(self, li) -> Job | None:
        try:
            a = li.select_one("a.hover-link")
            if not a:
                return None
            href = a["href"]
            url = href if href.startswith("http") else f"{BASE_URL}{href}"
            title_el = li.select_one("h3.h4")
            company_el = li.select_one(".company-name p a, .company-name p")
            infos = li.select(".job-infos ul li")
            date_el = infos[0].select_one(".date") if infos else None
            location_el = infos[1].select_one(".right") if len(infos) > 1 else None
            return Job(
                title=title_el.get_text(strip=True) if title_el else "",
                company=company_el.get_text(strip=True) if company_el else "",
                url=url,
                portal=self.name,
                description="",
                requirements=[],
                salary=None,
                location=location_el.get_text(strip=True) if location_el else "",
                posted_date=date_el.get_text(strip=True) if date_el else "",
                category="",
                scraped_at=datetime.now().isoformat(timespec="seconds"),
            )
        except Exception:
            return None
