import json
from unittest.mock import patch, MagicMock
from scrapers.bettercareer import BettercareerScraper

PORTAL_CFG = {"name": "BetterCareer", "url": "https://www.bettercareer.si", "is_public_sector": False}

NEXT_DATA = {
    "props": {
        "pageProps": {
            "jobs": [
                {
                    "jobSlug": "software-engineering-manager-12345",
                    "companySlug": "acme",
                    "companyName": "Acme d.o.o.",
                    "position": "Software Engineering Manager",
                    "salary": "4000 - 5000€ bruto",
                    "locations": "Ljubljana",
                    "published": "23. 06. 2026",
                    "shortDescription": "Iščemo izkušenega managerja.",
                    "categories": ["itManagement"],
                }
            ]
        }
    }
}

SAMPLE_HTML = f"""<html><body>
<script id="__NEXT_DATA__" type="application/json">{json.dumps(NEXT_DATA)}</script>
</body></html>"""


@patch("scrapers.bettercareer.requests.get")
def test_returns_list(mock_get):
    mock_get.return_value.text = SAMPLE_HTML
    mock_get.return_value.raise_for_status = MagicMock()
    jobs = BettercareerScraper(PORTAL_CFG, []).fetch_jobs()
    assert isinstance(jobs, list)


@patch("scrapers.bettercareer.requests.get")
def test_parses_title(mock_get):
    mock_get.return_value.text = SAMPLE_HTML
    mock_get.return_value.raise_for_status = MagicMock()
    jobs = BettercareerScraper(PORTAL_CFG, []).fetch_jobs()
    assert jobs[0].title == "Software Engineering Manager"


@patch("scrapers.bettercareer.requests.get")
def test_builds_correct_url(mock_get):
    mock_get.return_value.text = SAMPLE_HTML
    mock_get.return_value.raise_for_status = MagicMock()
    jobs = BettercareerScraper(PORTAL_CFG, []).fetch_jobs()
    assert jobs[0].url == "https://www.bettercareer.si/job/acme/software-engineering-manager-12345"


@patch("scrapers.bettercareer.requests.get")
def test_parses_salary(mock_get):
    mock_get.return_value.text = SAMPLE_HTML
    mock_get.return_value.raise_for_status = MagicMock()
    jobs = BettercareerScraper(PORTAL_CFG, []).fetch_jobs()
    assert jobs[0].salary == "4000 - 5000€ bruto"


@patch("scrapers.bettercareer.requests.get")
def test_deduplicates_across_categories(mock_get):
    mock_get.return_value.text = SAMPLE_HTML
    mock_get.return_value.raise_for_status = MagicMock()
    # Same HTML returned for all 5 categories — should yield only 1 unique job
    jobs = BettercareerScraper(PORTAL_CFG, []).fetch_jobs()
    assert len(jobs) == 1


@patch("scrapers.bettercareer.requests.get")
def test_missing_next_data_skipped(mock_get):
    mock_get.return_value.text = "<html><body>no data</body></html>"
    mock_get.return_value.raise_for_status = MagicMock()
    jobs = BettercareerScraper(PORTAL_CFG, []).fetch_jobs()
    assert jobs == []
