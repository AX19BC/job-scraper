from models import Job

def test_job_has_required_fields():
    job = Job(
        title="Cyber Security Engineer",
        company="Telekom SI",
        url="https://example.com/job/1",
        portal="MojeDelo",
        description="We are looking for...",
        requirements=["CISSP", "Python"],
        salary="2500-3200 EUR",
        location="Ljubljana",
        posted_date="2026-06-23",
        category="cyber_security",
        scraped_at="2026-06-23T07:00:00",
    )
    assert job.title == "Cyber Security Engineer"
    assert job.salary == "2500-3200 EUR"
    assert job.requirements == ["CISSP", "Python"]

def test_job_salary_can_be_none():
    job = Job(
        title="IT Specialist",
        company="Acme",
        url="https://example.com/job/2",
        portal="Zaposlitev.net",
        description="...",
        requirements=[],
        salary=None,
        location="Maribor",
        posted_date="2026-06-23",
        category="it_other",
        scraped_at="2026-06-23T07:00:00",
    )
    assert job.salary is None
