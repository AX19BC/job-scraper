from unittest.mock import MagicMock
from apscheduler.schedulers.background import BackgroundScheduler
from core.scheduler import create_scheduler


def test_returns_background_scheduler():
    s = create_scheduler(MagicMock(), "07:00")
    assert isinstance(s, BackgroundScheduler)
    s.shutdown(wait=False)

def test_adds_exactly_one_job():
    s = create_scheduler(MagicMock(), "07:00")
    assert len(s.get_jobs()) == 1
    s.shutdown(wait=False)

def test_sets_correct_hour_and_minute():
    s = create_scheduler(MagicMock(), "14:30")
    fields = {f.name: str(f) for f in s.get_jobs()[0].trigger.fields}
    assert fields["hour"] == "14"
    assert fields["minute"] == "30"
    s.shutdown(wait=False)
