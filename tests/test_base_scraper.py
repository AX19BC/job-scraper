import pytest
from scrapers.base import BaseScraper
from models import Job


class ConcreteScraper(BaseScraper):
    def fetch_jobs(self) -> list[Job]:
        return []


def test_base_scraper_sets_attributes():
    cfg = {"name": "TestPortal", "url": "https://test.com", "is_public_sector": False}
    s = ConcreteScraper(cfg)
    assert s.name == "TestPortal"
    assert s.base_url == "https://test.com"
    assert s.is_public_sector is False

def test_base_scraper_cannot_be_instantiated_directly():
    cfg = {"name": "TestPortal", "url": "https://test.com", "is_public_sector": False}
    with pytest.raises(TypeError):
        BaseScraper(cfg)

def test_concrete_scraper_returns_list():
    cfg = {"name": "TestPortal", "url": "https://test.com", "is_public_sector": False}
    s = ConcreteScraper(cfg)
    assert isinstance(s.fetch_jobs(), list)
