from abc import ABC, abstractmethod
from models import Job


class BaseScraper(ABC):
    def __init__(self, portal_config: dict):
        self.name: str = portal_config["name"]
        self.base_url: str = portal_config["url"]
        self.is_public_sector: bool = portal_config.get("is_public_sector", False)

    @abstractmethod
    def fetch_jobs(self) -> list[Job]:
        ...
