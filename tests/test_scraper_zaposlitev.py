from unittest.mock import patch
from scrapers.zaposlitev import ZaposlitevScraper

PORTAL_CFG = {"name": "Zaposlitev.net", "url": "https://www.zaposlitev.net", "is_public_sector": False}

SAMPLE_HTML = """<html><body>
<div class="job-item">
  <h2 class="job-title"><a href="/delo/456">Network Engineer</a></h2>
  <span class="employer">Iskratel d.o.o.</span>
  <span class="location">Kranj</span>
  <span class="date">23.06.2026</span>
  <p class="description">Iščemo mrežnega inženirja.</p>
</div>
</body></html>"""


@patch("scrapers.zaposlitev.requests.get")
def test_returns_list(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.text = SAMPLE_HTML
    assert isinstance(ZaposlitevScraper(PORTAL_CFG, ["IT"]).fetch_jobs(), list)

@patch("scrapers.zaposlitev.requests.get")
def test_parses_title(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.text = SAMPLE_HTML
    jobs = ZaposlitevScraper(PORTAL_CFG, ["IT"]).fetch_jobs()
    assert jobs[0].title == "Network Engineer"

@patch("scrapers.zaposlitev.requests.get")
def test_salary_none_when_missing(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.text = SAMPLE_HTML
    jobs = ZaposlitevScraper(PORTAL_CFG, ["IT"]).fetch_jobs()
    assert jobs[0].salary is None
