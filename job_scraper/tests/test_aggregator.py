from core.aggregator import aggregate
from models import Job


def make_job(url, portal="MojeDelo"):
    return Job(
        title="IT Engineer", company="Acme", url=url, portal=portal,
        description="desc", requirements=[], salary=None,
        location="Ljubljana", posted_date="2026-06-23",
        category="it_other", scraped_at="2026-06-23T07:00:00",
    )


def test_no_duplicates_keeps_all():
    result = aggregate([[make_job("https://a.com/1"), make_job("https://a.com/2")],
                        [make_job("https://b.com/3", "Zaposlitev.net")]])
    assert len(result) == 3

def test_deduplicates_by_url():
    result = aggregate([[make_job("https://a.com/1", "MojeDelo")],
                        [make_job("https://a.com/1", "Zaposlitev.net")]])
    assert len(result) == 1

def test_merges_portal_names_on_duplicate():
    result = aggregate([[make_job("https://a.com/1", "MojeDelo")],
                        [make_job("https://a.com/1", "Zaposlitev.net")]])
    assert "MojeDelo" in result[0].portal
    assert "Zaposlitev.net" in result[0].portal

def test_empty_lists():
    assert aggregate([[], []]) == []

def test_single_list():
    result = aggregate([[make_job("https://a.com/1"), make_job("https://a.com/2")]])
    assert len(result) == 2
