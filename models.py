from dataclasses import dataclass
from typing import Optional


@dataclass
class Job:
    title: str
    company: str
    url: str
    portal: str
    description: str
    requirements: list[str]
    salary: Optional[str]
    location: str
    posted_date: str
    category: str
    scraped_at: str
