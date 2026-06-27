import re
from models import Job


def _matches(keyword: str, text: str) -> bool:
    # Word-boundary match so "SOC" doesn't hit "socialni", "VPN" doesn't hit "vpneka", etc.
    pattern = r'(?<![a-z0-9])' + re.escape(keyword.lower()) + r'(?![a-z0-9])'
    return bool(re.search(pattern, text))


def classify(job: Job, keywords: dict, is_public_sector: bool) -> str:
    text = f"{job.title} {job.description}".lower()

    is_cyber = any(_matches(kw, text) for kw in keywords["cyber_security"])

    if is_public_sector and is_cyber:
        return "public_sector_cyber"
    if is_cyber:
        return "cyber_security"
    if any(_matches(kw, text) for kw in keywords["network"]):
        return "network"
    if any(_matches(kw, text) for kw in keywords["sysadmin"]):
        return "sysadmin"
    if any(_matches(kw, text) for kw in keywords["it_other"]):
        return "it_other"
    return "unrelated"
