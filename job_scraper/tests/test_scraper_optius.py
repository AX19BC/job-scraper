from unittest.mock import patch, MagicMock
from scrapers.optius import OptiusScraper

PORTAL_CFG = {"name": "Optius", "url": "https://www.optius.com", "is_public_sector": False}

SAMPLE_HTML = """<html><body>
<div class="job-results-list spacem-micro">
<ul>
<li class="item is-exposed" id="job952989">
  <a class="hover-link" href="/iskalci/prosta-delovna-mesta/it-specialist-mz-952989-952989/"></a>
  <div class="item-wrapper">
    <div class="title-wrapper has-bookmark">
      <div class="right">
        <h3 class="h4">IT Specialist (m/ž)</h3>
      </div>
    </div>
    <div class="job-infos">
      <ul>
        <li><div class="left">Prijave do</div>
            <div class="right"><span class="date">24. 7. 2026</span></div></li>
        <li><div class="left">Kraj dela</div>
            <div class="right">Ljubljana</div></li>
      </ul>
    </div>
    <div class="right other-links">
      <div class="company-data typography">
        <div class="company-name">
          <p><a href="/podjetja/techcorp/">TechCorp d.o.o.</a></p>
        </div>
      </div>
    </div>
  </div>
</li>
</ul>
</div>
</body></html>"""


@patch("scrapers.optius.requests.get")
def test_returns_list(mock_get):
    mock_get.return_value.text = SAMPLE_HTML
    mock_get.return_value.raise_for_status = MagicMock()
    jobs = OptiusScraper(PORTAL_CFG, ["IT"]).fetch_jobs()
    assert isinstance(jobs, list)


@patch("scrapers.optius.requests.get")
def test_parses_title(mock_get):
    mock_get.return_value.text = SAMPLE_HTML
    mock_get.return_value.raise_for_status = MagicMock()
    jobs = OptiusScraper(PORTAL_CFG, ["IT"]).fetch_jobs()
    assert "IT Specialist" in jobs[0].title


@patch("scrapers.optius.requests.get")
def test_builds_absolute_url(mock_get):
    mock_get.return_value.text = SAMPLE_HTML
    mock_get.return_value.raise_for_status = MagicMock()
    jobs = OptiusScraper(PORTAL_CFG, ["IT"]).fetch_jobs()
    assert jobs[0].url.startswith("https://www.optius.com")


@patch("scrapers.optius.requests.get")
def test_parses_company(mock_get):
    mock_get.return_value.text = SAMPLE_HTML
    mock_get.return_value.raise_for_status = MagicMock()
    jobs = OptiusScraper(PORTAL_CFG, ["IT"]).fetch_jobs()
    assert "TechCorp" in jobs[0].company


@patch("scrapers.optius.requests.get")
def test_parses_location(mock_get):
    mock_get.return_value.text = SAMPLE_HTML
    mock_get.return_value.raise_for_status = MagicMock()
    jobs = OptiusScraper(PORTAL_CFG, ["IT"]).fetch_jobs()
    assert jobs[0].location == "Ljubljana"


@patch("scrapers.optius.requests.get")
def test_parses_date(mock_get):
    mock_get.return_value.text = SAMPLE_HTML
    mock_get.return_value.raise_for_status = MagicMock()
    jobs = OptiusScraper(PORTAL_CFG, ["IT"]).fetch_jobs()
    assert "2026" in jobs[0].posted_date


@patch("scrapers.optius.requests.get")
def test_deduplicates_across_queries(mock_get):
    mock_get.return_value.text = SAMPLE_HTML
    mock_get.return_value.raise_for_status = MagicMock()
    jobs = OptiusScraper(PORTAL_CFG, ["IT", "cyber security"]).fetch_jobs()
    assert len(jobs) == 1
