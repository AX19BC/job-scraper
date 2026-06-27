from datetime import datetime
import requests
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper
from models import Job

TIMEOUT = 30
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; JobScraper/1.0)"}


class ZaposlitevScraper(BaseScraper):
    def __init__(self, portal_config: dict, search_queries: list[str]):
        super().__init__(portal_config)
        self.search_queries = search_queries

    def fetch_jobs(self) -> list[Job]:
        jobs, seen = [], set()
        for query in self.search_queries:
            url = f"{self.base_url}/dela?q={requests.utils.quote(query)}"
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            r.raise_for_status()
            for item in BeautifulSoup(r.text, "html.parser").select(
                "div.job-item, article.job, li.job-listing"
            ):
                job = self._parse(item)
                if job and job.url not in seen:
                    seen.add(job.url)
                    jobs.append(job)
        return jobs

    def _parse(self, item) -> Job | None:
        try:
            a = item.select_one("h2 a, h3 a, .job-title a")
            if not a:
                return None
            href = a["href"]
            url = href if href.startswith("http") else f"{self.base_url}{href}"
            company = item.select_one(".employer, .company")
            location = item.select_one(".location, .kraj")
            date = item.select_one(".date, time, .posted-date")
            salary = item.select_one(".salary, .placa, .wage")
            desc = item.select_one(".description, p")
            return Job(
                title=a.get_text(strip=True),
                company=company.get_text(strip=True) if company else "",
                url=url, portal=self.name,
                description=desc.get_text(strip=True)[:300] if desc else "",
                requirements=[],
                salary=salary.get_text(strip=True) if salary else None,
                location=location.get_text(strip=True) if location else "",
                posted_date=date.get_text(strip=True) if date else "",
                category="",
                scraped_at=datetime.now().isoformat(timespec="seconds"),
            )
        except Exception:
            return None
