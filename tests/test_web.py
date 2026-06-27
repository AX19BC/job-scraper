import json, pytest
from web.app import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("JOBS_PATH", str(tmp_path / "jobs.json"))
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c, tmp_path


def test_dashboard_returns_200(client):
    c, _ = client
    assert c.get("/").status_code == 200


def test_dashboard_shows_job_title(client):
    c, tmp_path = client
    (tmp_path / "jobs.json").write_text(json.dumps({
        "scraped_at": "2026-06-23T07:00:00", "total": 1, "errors": [],
        "jobs": [{"title": "Cyber Security Engineer", "company": "Telekom SI",
                  "url": "https://example.com/1", "portal": "MojeDelo",
                  "description": "Security role", "requirements": [],
                  "salary": "2500 EUR", "location": "Ljubljana",
                  "posted_date": "2026-06-23", "category": "cyber_security",
                  "scraped_at": "2026-06-23T07:00:00"}],
    }))
    assert b"Cyber Security Engineer" in c.get("/").data


def test_run_now_redirects(client, monkeypatch):
    c, _ = client

    class _FakeScheduler:
        def add_job(self, *args, **kwargs): pass
        def start(self): pass

    monkeypatch.setattr("web.app.BackgroundScheduler", _FakeScheduler)
    assert c.post("/run-now").status_code == 302
