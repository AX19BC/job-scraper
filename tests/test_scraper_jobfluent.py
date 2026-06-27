from unittest.mock import patch, MagicMock
from scrapers.jobfluent import JobfluentScraper

PORTAL_CFG = {"name": "JobFluent", "url": "https://www.jobfluent.com", "is_public_sector": False}

SAMPLE_HTML = """<html><body>
<div class="JobCard">
  <h2 class="JobCard__title"><a href="/jobs/789">DevOps Engineer</a></h2>
  <span class="JobCard__company">Studio Moderna</span>
  <span class="JobCard__location">Remote, Slovenia</span>
  <span class="JobCard__date">Jun 23, 2026</span>
  <p class="JobCard__description">Looking for a DevOps engineer.</p>
</div>
</body></html>"""


def _mock_pw(sample_html):
    pw = MagicMock()
    browser = MagicMock()
    page = MagicMock()
    page.content.return_value = sample_html
    browser.new_page.return_value = page
    pw.__enter__.return_value.chromium.launch.return_value = browser
    return pw


@patch("scrapers.jobfluent.sync_playwright")
def test_returns_list(mock_pw):
    mock_pw.return_value = _mock_pw(SAMPLE_HTML)
    assert isinstance(JobfluentScraper(PORTAL_CFG, ["IT"]).fetch_jobs(), list)

@patch("scrapers.jobfluent.sync_playwright")
def test_parses_title(mock_pw):
    mock_pw.return_value = _mock_pw(SAMPLE_HTML)
    jobs = JobfluentScraper(PORTAL_CFG, ["IT"]).fetch_jobs()
    assert len(jobs) >= 1
    assert jobs[0].title == "DevOps Engineer"
