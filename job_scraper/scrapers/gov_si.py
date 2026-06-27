from datetime import datetime
import requests
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper
from models import Job

TIMEOUT = 30
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; JobScraper/1.0)"}
# Single request for all active job listings — avoids rate-limit risk
LISTING_URL = "https://www.gov.si/zbirke/delovna-mesta/"


class GovSiScraper(BaseScraper):
    def __init__(self, portal_config: dict, search_queries: list[str]):
        super().__init__(portal_config)

    def fetch_jobs(self) -> list[Job]:
        r = requests.get(LISTING_URL, params={"nrOfItems": "100"},
                         headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        jobs, seen = [], set()
        for row in soup.select("table tr")[1:]:
            job = self._parse(row)
            if job and job.url not in seen:
                seen.add(job.url)
                jobs.append(job)
        return jobs

    def _parse(self, row) -> Job | None:
        try:
            a = row.select_one("td.td-title a")
            if not a:
                return None
            href = a["href"]
            url = href if href.startswith("http") else f"https://www.gov.si{href}"
            org = row.select_one(".td-organisation .cell")
            date = row.select_one(".td-publish-date .cell")
            return Job(
                title=a.get_text(strip=True),
                company=org.get_text(strip=True) if org else "Javni sektor",
                url=url,
                portal=self.name,
                description="",
                requirements=[],
                salary=None,
                location="Slovenija",
                posted_date=date.get_text(strip=True) if date else "",
                category="",
                scraped_at=datetime.now().isoformat(timespec="seconds"),
            )
        except Exception:
            return None
