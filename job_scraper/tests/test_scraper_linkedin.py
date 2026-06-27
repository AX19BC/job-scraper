from unittest.mock import patch, MagicMock
from scrapers.linkedin import LinkedinScraper

PORTAL_CFG = {"name": "LinkedIn", "url": "https://si.linkedin.com", "is_public_sector": False}

SAMPLE_HTML = """<html><body>
<ul class="jobs-search__results-list">
  <li>
    <div class="base-search-card job-search-card">
      <a class="base-card__full-link" href="https://si.linkedin.com/jobs/view/security-engineer-12345?tracking=abc">
        Security Engineer
      </a>
      <h3 class="base-search-card__title">Security Engineer</h3>
      <h4 class="base-search-card__subtitle">
        <a>CyberCorp d.o.o.</a>
      </h4>
      <span class="job-search-card__location">Ljubljana, Ljubljana, Slovenia</span>
      <time datetime="2026-06-20">20. junij 2026</time>
    </div>
  </li>
</ul>
</body></html>"""


@patch("scrapers.linkedin.requests.get")
def test_returns_list(mock_get):
    mock_get.return_value.text = SAMPLE_HTML
    mock_get.return_value.raise_for_status = MagicMock()
    jobs = LinkedinScraper(PORTAL_CFG, ["cyber security"]).fetch_jobs()
    assert isinstance(jobs, list)


@patch("scrapers.linkedin.requests.get")
def test_parses_title(mock_get):
    mock_get.return_value.text = SAMPLE_HTML
    mock_get.return_value.raise_for_status = MagicMock()
    jobs = LinkedinScraper(PORTAL_CFG, ["cyber security"]).fetch_jobs()
    assert jobs[0].title == "Security Engineer"


@patch("scrapers.linkedin.requests.get")
def test_strips_tracking_from_url(mock_get):
    mock_get.return_value.text = SAMPLE_HTML
    mock_get.return_value.raise_for_status = MagicMock()
    jobs = LinkedinScraper(PORTAL_CFG, ["cyber security"]).fetch_jobs()
    assert "?" not in jobs[0].url
    assert jobs[0].url == "https://si.linkedin.com/jobs/view/security-engineer-12345"


@patch("scrapers.linkedin.requests.get")
def test_parses_location(mock_get):
    mock_get.return_value.text = SAMPLE_HTML
    mock_get.return_value.raise_for_status = MagicMock()
    jobs = LinkedinScraper(PORTAL_CFG, ["cyber security"]).fetch_jobs()
    assert "Ljubljana" in jobs[0].location


@patch("scrapers.linkedin.requests.get")
def test_parses_date(mock_get):
    mock_get.return_value.text = SAMPLE_HTML
    mock_get.return_value.raise_for_status = MagicMock()
    jobs = LinkedinScraper(PORTAL_CFG, ["cyber security"]).fetch_jobs()
    assert jobs[0].posted_date == "2026-06-20"


@patch("scrapers.linkedin.requests.get")
def test_deduplicates_across_queries(mock_get):
    mock_get.return_value.text = SAMPLE_HTML
    mock_get.return_value.raise_for_status = MagicMock()
    jobs = LinkedinScraper(PORTAL_CFG, ["IT", "cyber security"]).fetch_jobs()
    assert len(jobs) == 1


@patch("scrapers.linkedin.requests.get")
def test_empty_results(mock_get):
    mock_get.return_value.text = "<html><body><ul class='jobs-search__results-list'></ul></body></html>"
    mock_get.return_value.raise_for_status = MagicMock()
    jobs = LinkedinScraper(PORTAL_CFG, ["cyber security"]).fetch_jobs()
    assert jobs == []
