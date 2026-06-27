from unittest.mock import patch, MagicMock
import pytest
from scrapers.mojedelo import MojedeloScraper

PORTAL_CFG = {"name": "MojeDelo", "url": "https://www.mojedelo.com", "is_public_sector": False}

SAMPLE_RESPONSE = {
    "data": {
        "items": [
            {
                "id": "abc-123",
                "title": "Cyber Security Engineer",
                "adSummary": "Iščemo varnostnega inženirja.",
                "startDate": "2026-06-23T00:00:00.000Z",
                "company": {"name": "Telekom SI"},
                "town": {"name": "Ljubljana"},
                "grossHourlyRate": None,
            }
        ]
    }
}

SAMPLE_RESPONSE_SALARY = {
    "data": {
        "items": [
            {
                "id": "def-456",
                "title": "Security Analyst",
                "adSummary": "Varnostni analitik.",
                "startDate": "2026-06-23T00:00:00.000Z",
                "company": {"name": "Acme d.o.o."},
                "town": {"name": "Maribor"},
                "grossHourlyRate": 25.5,
            }
        ]
    }
}


@patch("scrapers.mojedelo.requests.get")
def test_returns_list(mock_get):
    mock_get.return_value.json.return_value = SAMPLE_RESPONSE
    mock_get.return_value.raise_for_status = MagicMock()
    assert isinstance(MojedeloScraper(PORTAL_CFG, ["IT"]).fetch_jobs(), list)

@patch("scrapers.mojedelo.requests.get")
def test_parses_title(mock_get):
    mock_get.return_value.json.return_value = SAMPLE_RESPONSE
    mock_get.return_value.raise_for_status = MagicMock()
    jobs = MojedeloScraper(PORTAL_CFG, ["IT"]).fetch_jobs()
    assert jobs[0].title == "Cyber Security Engineer"

@patch("scrapers.mojedelo.requests.get")
def test_parses_salary(mock_get):
    mock_get.return_value.json.return_value = SAMPLE_RESPONSE_SALARY
    mock_get.return_value.raise_for_status = MagicMock()
    jobs = MojedeloScraper(PORTAL_CFG, ["IT"]).fetch_jobs()
    assert jobs[0].salary == "25.5 €/h"

@patch("scrapers.mojedelo.requests.get")
def test_timeout_raises(mock_get):
    import requests as req
    mock_get.side_effect = req.exceptions.Timeout()
    with pytest.raises(Exception):
        MojedeloScraper(PORTAL_CFG, ["IT"]).fetch_jobs()
