from datetime import datetime
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper
from models import Job

TIMEOUT = 30000


class JobfluentScraper(BaseScraper):
    def __init__(self, portal_config: dict, search_queries: list[str]):
        super().__init__(portal_config)
        self.search_queries = search_queries

    def fetch_jobs(self) -> list[Job]:
        jobs, seen = [], set()
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            for query in self.search_queries:
                url = f"{self.base_url}/jobs-it-si?q={query}"
                page.goto(url, timeout=TIMEOUT)
                page.wait_for_load_state("networkidle", timeout=TIMEOUT)
                soup = BeautifulSoup(page.content(), "html.parser")
                for card in soup.select("div.JobCard, article.job-card, div[class*='JobCard']"):
                    job = self._parse(card)
                    if job and job.url not in seen:
                        seen.add(job.url)
                        jobs.append(job)
            browser.close()
        return jobs

    def _parse(self, card) -> Job | None:
        try:
            a = card.select_one("[class*='title'] a, h2 a, h3 a")
            if not a:
                return None
            href = a["href"]
            url = href if href.startswith("http") else f"{self.base_url}{href}"
            company = card.select_one("[class*='company'], [class*='employer']")
            location = card.select_one("[class*='location']")
            date = card.select_one("[class*='date'], time")
            salary = card.select_one("[class*='salary'], [class*='wage']")
            desc = card.select_one("[class*='description'], p")
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
