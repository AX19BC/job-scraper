from unittest.mock import patch, MagicMock
from core.mailer import send_email

CFG = {"email": {"smtp_host": "smtp.gmail.com", "smtp_port": 587,
                 "sender": "s@gmail.com", "sender_password": "pw",
                 "recipient": "nejcviddmar@gmail.com"}}

RESULT = {
    "scraped_at": "2026-06-23T07:00:00", "total": 1, "errors": [],
    "jobs": [{"title": "Cyber Security Engineer", "company": "Telekom SI",
              "url": "https://example.com/1", "portal": "MojeDelo",
              "description": "Security role", "requirements": ["CISSP"],
              "salary": "2500 EUR", "location": "Ljubljana",
              "posted_date": "2026-06-23", "category": "cyber_security",
              "scraped_at": "2026-06-23T07:00:00"}],
}
EMPTY = {"scraped_at": "2026-06-23T07:00:00", "total": 0, "errors": [], "jobs": []}


@patch("core.mailer.smtplib.SMTP")
def test_sends_when_jobs_exist(mock_smtp):
    smtp = MagicMock()
    mock_smtp.return_value.__enter__.return_value = smtp
    send_email(RESULT, CFG)
    smtp.sendmail.assert_called_once()

@patch("core.mailer.smtplib.SMTP")
def test_skips_when_no_jobs(mock_smtp):
    send_email(EMPTY, CFG)
    mock_smtp.assert_not_called()

@patch("core.mailer.smtplib.SMTP")
def test_recipient_is_correct(mock_smtp):
    smtp = MagicMock()
    mock_smtp.return_value.__enter__.return_value = smtp
    send_email(RESULT, CFG)
    assert "nejcviddmar@gmail.com" in smtp.sendmail.call_args[0][1]

@patch("core.mailer.smtplib.SMTP")
def test_html_contains_job_title(mock_smtp):
    smtp = MagicMock()
    mock_smtp.return_value.__enter__.return_value = smtp
    send_email(RESULT, CFG)
    assert "Cyber Security Engineer" in smtp.sendmail.call_args[0][2]
