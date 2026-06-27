import json
from unittest.mock import patch, MagicMock
from core.pipeline import run_pipeline
from models import Job


def make_job(url, portal="MojeDelo"):
    return Job(
        title="IT Engineer", company="Acme", url=url, portal=portal,
        description="IT desc", requirements=[], salary=None,
        location="Ljubljana", posted_date="2026-06-23",
        category="", scraped_at="2026-06-23T07:00:00",
    )


MOCK_CFG = {
    "portals": [{"name": "MojeDelo", "enabled": True,
                 "module": "scrapers.mojedelo", "url": "https://mojedelo.com",
                 "is_public_sector": False}],
    "keywords": {"cyber_security": ["cyber"], "network": ["network"],
                 "sysadmin": ["sysadmin"], "it_other": ["IT"]},
    "search_queries": ["IT"],
    "schedule": {"run_time": "07:00"},
    "email": {"recipient": "test@example.com"},
}


def mock_scraper(jobs):
    s = MagicMock()
    s.fetch_jobs.return_value = jobs
    s.is_public_sector = False
    s.name = "MojeDelo"
    return s


@patch("core.pipeline.load_config", return_value=MOCK_CFG)
@patch("core.pipeline._load_scraper")
def test_pipeline_returns_expected_keys(mock_load, mock_cfg, tmp_path):
    mock_load.return_value = mock_scraper([make_job("https://a.com/1")])
    with patch("core.pipeline._jobs_path", tmp_path / "jobs.json"):
        result = run_pipeline()
    for key in ("scraped_at", "total", "errors", "jobs"):
        assert key in result


@patch("core.pipeline.load_config", return_value=MOCK_CFG)
@patch("core.pipeline._load_scraper")
def test_pipeline_writes_jobs_json(mock_load, mock_cfg, tmp_path):
    mock_load.return_value = mock_scraper([make_job("https://a.com/1")])
    path = tmp_path / "jobs.json"
    with patch("core.pipeline._jobs_path", path):
        run_pipeline()
    assert path.exists()
    assert json.loads(path.read_text())["total"] == 1


@patch("core.pipeline.load_config", return_value=MOCK_CFG)
@patch("core.pipeline._load_scraper")
def test_pipeline_records_scraper_error(mock_load, mock_cfg, tmp_path):
    mock_load.return_value.fetch_jobs.side_effect = Exception("timeout")
    mock_load.return_value.name = "MojeDelo"
    mock_load.return_value.is_public_sector = False
    with patch("core.pipeline._jobs_path", tmp_path / "jobs.json"):
        result = run_pipeline()
    assert len(result["errors"]) == 1
    assert result["errors"][0]["portal"] == "MojeDelo"


@patch("core.pipeline.load_config", return_value=MOCK_CFG)
@patch("core.pipeline._load_scraper")
def test_pipeline_deduplicates(mock_load, mock_cfg, tmp_path):
    job = make_job("https://a.com/1")
    mock_load.return_value = mock_scraper([job, job])
    with patch("core.pipeline._jobs_path", tmp_path / "jobs.json"):
        result = run_pipeline()
    assert result["total"] == 1
