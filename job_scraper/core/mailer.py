import smtplib
from email.message import EmailMessage

CATEGORY_ORDER = ["cyber_security", "public_sector_cyber", "network", "sysadmin", "it_other"]
CATEGORY_LABELS = {
    "cyber_security": "Cyber Security",
    "public_sector_cyber": "Javni sektor – Cyber Security",
    "network": "Network Engineer",
    "sysadmin": "Sistemski Administrator",
    "it_other": "Ostali IT",
}


def _build_html(result: dict) -> str:
    by_cat: dict[str, list] = {c: [] for c in CATEGORY_ORDER}
    for job in result["jobs"]:
        cat = job.get("category", "it_other")
        if cat in by_cat:
            by_cat[cat].append(job)

    sections = []
    for cat in CATEGORY_ORDER:
        jobs = by_cat[cat]
        if not jobs:
            continue
        cards = ""
        for j in jobs:
            salary = f"<p><strong>Plača:</strong> {j['salary']}</p>" if j.get("salary") else ""
            reqs = ", ".join(j["requirements"]) if j.get("requirements") else ""
            reqs_html = f"<p><strong>Zahteve:</strong> {reqs}</p>" if reqs else ""
            cards += (
                f'<div style="border:1px solid #ddd;border-radius:6px;padding:12px;margin-bottom:10px">'
                f'<h3 style="margin:0 0 4px"><a href="{j["url"]}">{j["title"]}</a></h3>'
                f'<p style="color:#555;margin:0">{j["company"]} &bull; {j["location"]} '
                f'&bull; {j["portal"]} &bull; {j["posted_date"]}</p>'
                f'<p>{j["description"]}</p>{reqs_html}{salary}</div>'
            )
        sections.append(f"<h2>{CATEGORY_LABELS[cat]} ({len(jobs)})</h2>{cards}")

    errors_html = ""
    if result.get("errors"):
        items = "".join(f"<li>⚠ {e['portal']}: {e['error']}</li>" for e in result["errors"])
        errors_html = f"<h3>Napake pri scrapingu</h3><ul>{items}</ul>"

    return (
        f'<html><body style="font-family:sans-serif;max-width:800px;margin:auto">'
        f'<h1>SLO Job Scraper — {result["scraped_at"][:10]}</h1>'
        f'<p>Skupaj {result["total"]} oglasov.</p>'
        f'{"".join(sections)}{errors_html}</body></html>'
    )


def send_email(result: dict, config: dict) -> None:
    if result["total"] == 0:
        return
    cfg = config["email"]
    if not cfg.get("sender") or not cfg.get("sender_password"):
        import logging
        logging.getLogger("job_scraper.mailer").warning(
            "Email skipped: sender or sender_password not configured in config.yaml"
        )
        return
    html = _build_html(result)
    msg = EmailMessage()
    msg["Subject"] = f"IT Službe SLO — {result['scraped_at'][:10]} ({result['total']} oglasov)"
    msg["From"] = cfg["sender"]
    msg["To"] = cfg["recipient"]
    msg.set_content(html, subtype="html")
    with smtplib.SMTP(cfg["smtp_host"], cfg["smtp_port"]) as smtp:
        smtp.starttls()
        smtp.login(cfg["sender"], cfg["sender_password"])
        smtp.sendmail(cfg["sender"], cfg["recipient"], msg.as_string())
