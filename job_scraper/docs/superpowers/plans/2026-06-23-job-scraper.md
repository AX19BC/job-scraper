# Job Scraper Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python app that scrapes Slovenian IT/cyber security job portals daily, displays results on a local web dashboard, and emails a summary to nejcviddmar@gmail.com.

**Architecture:** Single Python process runs Flask (port 5000) and APScheduler together. A pipeline module orchestrates scraper loading, aggregation, classification, and caching to `data/jobs.json`. The dashboard reads that file; email is sent after each successful pipeline run.

**Tech Stack:** Python 3.11+, Flask 3.x, APScheduler 3.x, requests, BeautifulSoup4, playwright, PyYAML, pytest

## Global Constraints

- Python 3.11+ required (`str | None` union syntax used throughout)
- All config in `config.yaml` — no hardcoded values in Python files
- Recipient email: `nejcviddmar@gmail.com` (set in config.yaml, not in code)
- Per-scraper timeout: 30 seconds (`requests`), 30000 ms (playwright)
- Deduplication key: `job.url` exact string match
- Category priority (first match wins): `cyber_security` → `public_sector_cyber` → `network` → `sysadmin` → `it_other`
- Portal failure: log to `data/scraper.log`, continue pipeline — never raise
- Zero results: skip email send
- All scrapers accept `(portal_config: dict, search_queries: list[str])` as constructor args

---

## File Map

| File | Purpose |
|---|---|
| `config.yaml` | All runtime config: portals, keywords, search queries, email, schedule |
| `models.py` | `Job` dataclass — single source of truth for the data shape |
| `core/config.py` | Loads and returns `config.yaml` as a dict |
| `core/classifier.py` | `classify(job, keywords, is_public_sector) -> str` |
| `core/aggregator.py` | `aggregate(job_lists) -> list[Job]` — merges and deduplicates by URL |
| `core/pipeline.py` | Orchestrates scrapers → aggregate → classify → save `data/jobs.json` |
| `core/mailer.py` | `send_email(result, config)` — builds and sends HTML email |
| `core/scheduler.py` | `create_scheduler(job_func, run_time) -> BackgroundScheduler` |
| `scrapers/base.py` | `BaseScraper` ABC with `fetch_jobs() -> list[Job]` |
| `scrapers/mojedelo.py` | `MojedeloScraper` |
| `scrapers/zaposlitev.py` | `ZaposlitveScraper` |
| `scrapers/jobfluent.py` | `JobfluentScraper` (playwright) |
| `scrapers/gov_si.py` | `GovSiScraper` (public sector) |
| `web/app.py` | Flask: `GET /` dashboard, `POST /run-now` trigger, `create_app() -> Flask` |
| `web/templates/dashboard.html` | Dashboard with category sections |
| `main.py` | Entrypoint: starts scheduler + Flask |
| `tests/` | pytest tests mirroring source layout |

---

### Task 1: Project scaffold

**Files:**
- Create: `requirements.txt`
- Create: `config.yaml`
- Create: `data/.gitkeep`
- Create: `scrapers/__init__.py`, `core/__init__.py`, `web/__init__.py`, `tests/__init__.py`
- Modify: `.gitignore`

**Interfaces:**
- Produces: `config.yaml` schema consumed by all subsequent tasks

- [ ] **Step 1: Create requirements.txt**

```
flask>=3.0
apscheduler>=3.10
requests>=2.31
beautifulsoup4>=4.12
playwright>=1.44
pyyaml>=6.0
pytest>=8.0
pytest-mock>=3.14
```

- [ ] **Step 2: Create config.yaml**

```yaml
schedule:
  run_time: "07:00"

email:
  smtp_host: smtp.gmail.com
  smtp_port: 587
  sender: ""
  sender_password: ""
  recipient: nejcviddmar@gmail.com

search_queries:
  - "IT"
  - "informatika"
  - "kibernetska varnost"
  - "network"
  - "sistemski administrator"
  - "cyber security"
  - "varnost"

portals:
  - name: "MojeDelo"
    enabled: true
    module: "scrapers.mojedelo"
    url: "https://www.mojedelo.com"
    is_public_sector: false
  - name: "Zaposlitev.net"
    enabled: true
    module: "scrapers.zaposlitev"
    url: "https://www.zaposlitev.net"
    is_public_sector: false
  - name: "JobFluent"
    enabled: true
    module: "scrapers.jobfluent"
    url: "https://www.jobfluent.com"
    is_public_sector: false
  - name: "GOV.SI"
    enabled: true
    module: "scrapers.gov_si"
    url: "https://www.gov.si"
    is_public_sector: true

keywords:
  cyber_security:
    - "cyber security"
    - "kibernetska varnost"
    - "cyber security engineer"
    - "inženir kibernetske varnosti"
    - "SOC"
    - "SIEM"
    - "penetration"
    - "pentest"
    - "CISSP"
    - "information security"
    - "varnost informacij"
  network:
    - "network engineer"
    - "omrežje"
    - "Cisco"
    - "firewall"
    - "VPN"
    - "routing"
  sysadmin:
    - "system administrator"
    - "sistemski administrator"
    - "Windows Server"
    - "Linux admin"
    - "Active Directory"
  it_other:
    - "IT specialist"
    - "IT engineer"
    - "DevOps"
    - "cloud"
    - "Azure"
    - "AWS"
    - "informatika"
    - "programer"
    - "developer"
```

- [ ] **Step 3: Create data/.gitkeep and update .gitignore**

Create empty file `data/.gitkeep`.

Add to `.gitignore`:
```
data/jobs.json
data/scraper.log
__pycache__/
*.pyc
.env
venv/
```

- [ ] **Step 4: Create empty __init__.py files**

Create empty files: `scrapers/__init__.py`, `core/__init__.py`, `web/__init__.py`, `tests/__init__.py`

- [ ] **Step 5: Install dependencies**

```bash
pip install -r requirements.txt
playwright install chromium
```

Expected: all packages install without errors.

- [ ] **Step 6: Commit**

```bash
git init
git add .
git commit -m "chore: project scaffold, config and dependencies"
```

---

### Task 2: Job model and config loader

**Files:**
- Create: `models.py`
- Create: `core/config.py`
- Create: `tests/test_models.py`
- Create: `tests/test_config.py`

**Interfaces:**
- Produces: `Job` dataclass imported by all scrapers and core modules
- Produces: `load_config() -> dict` used by pipeline, mailer, scheduler, web app

- [ ] **Step 1: Write failing test for Job**

`tests/test_models.py`:
```python
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
```

- [ ] **Step 2: Run test — expect FAIL**

```bash
pytest tests/test_models.py -v
```
Expected: `ModuleNotFoundError: No module named 'models'`

- [ ] **Step 3: Implement models.py**

```python
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
```

- [ ] **Step 4: Run test — expect PASS**

```bash
pytest tests/test_models.py -v
```
Expected: 2 passed.

- [ ] **Step 5: Write failing test for config loader**

`tests/test_config.py`:
```python
from core.config import load_config

def test_load_config_returns_dict():
    cfg = load_config()
    assert isinstance(cfg, dict)

def test_config_has_required_keys():
    cfg = load_config()
    assert "portals" in cfg
    assert "keywords" in cfg
    assert "email" in cfg
    assert "schedule" in cfg
    assert "search_queries" in cfg

def test_config_portals_have_required_fields():
    cfg = load_config()
    for portal in cfg["portals"]:
        assert "name" in portal
        assert "enabled" in portal
        assert "module" in portal
        assert "url" in portal
        assert "is_public_sector" in portal
```

- [ ] **Step 6: Run test — expect FAIL**

```bash
pytest tests/test_config.py -v
```
Expected: `ModuleNotFoundError: No module named 'core.config'`

- [ ] **Step 7: Implement core/config.py**

```python
from pathlib import Path
import yaml

_CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"


def load_config() -> dict:
    with open(_CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)
```

- [ ] **Step 8: Run tests — expect PASS**

```bash
pytest tests/test_config.py -v
```
Expected: 3 passed.

- [ ] **Step 9: Commit**

```bash
git add models.py core/config.py tests/test_models.py tests/test_config.py
git commit -m "feat: Job dataclass and config loader"
```

---

### Task 3: BaseScraper

**Files:**
- Create: `scrapers/base.py`
- Create: `tests/test_base_scraper.py`

**Interfaces:**
- Produces: `BaseScraper(portal_config: dict)` sets `self.name: str`, `self.base_url: str`, `self.is_public_sector: bool`
- Produces: abstract method `fetch_jobs(self) -> list[Job]`

- [ ] **Step 1: Write failing tests**

`tests/test_base_scraper.py`:
```python
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
```

- [ ] **Step 2: Run test — expect FAIL**

```bash
pytest tests/test_base_scraper.py -v
```
Expected: `ModuleNotFoundError: No module named 'scrapers.base'`

- [ ] **Step 3: Implement scrapers/base.py**

```python
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
```

- [ ] **Step 4: Run test — expect PASS**

```bash
pytest tests/test_base_scraper.py -v
```
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add scrapers/base.py tests/test_base_scraper.py
git commit -m "feat: BaseScraper abstract class"
```

---

### Task 4: Classifier

**Files:**
- Create: `core/classifier.py`
- Create: `tests/test_classifier.py`

**Interfaces:**
- Consumes: `Job` from `models.py`
- Produces: `classify(job: Job, keywords: dict, is_public_sector: bool) -> str`
  - Returns one of: `"cyber_security"`, `"public_sector_cyber"`, `"network"`, `"sysadmin"`, `"it_other"`

- [ ] **Step 1: Write failing tests**

`tests/test_classifier.py`:
```python
from core.classifier import classify
from models import Job

KEYWORDS = {
    "cyber_security": [
        "cyber security", "kibernetska varnost", "cyber security engineer",
        "inženir kibernetske varnosti", "SOC", "SIEM", "penetration",
        "pentest", "CISSP", "information security", "varnost informacij",
    ],
    "network": ["network engineer", "omrežje", "Cisco", "firewall", "VPN", "routing"],
    "sysadmin": ["system administrator", "sistemski administrator",
                 "Windows Server", "Linux admin", "Active Directory"],
    "it_other": ["IT specialist", "IT engineer", "DevOps", "cloud",
                 "Azure", "AWS", "informatika", "programer", "developer"],
}


def make_job(title="", description=""):
    return Job(
        title=title, company="Acme", url="https://example.com/1",
        portal="MojeDelo", description=description, requirements=[],
        salary=None, location="Ljubljana", posted_date="2026-06-23",
        category="", scraped_at="2026-06-23T07:00:00",
    )


def test_classifies_cyber_security_by_title():
    assert classify(make_job("Cyber Security Engineer"), KEYWORDS, False) == "cyber_security"

def test_classifies_slovenian_cyber():
    assert classify(make_job("Inženir kibernetske varnosti"), KEYWORDS, False) == "cyber_security"

def test_classifies_public_sector_cyber():
    assert classify(make_job("Specialist kibernetska varnost"), KEYWORDS, True) == "public_sector_cyber"

def test_public_sector_without_cyber_is_not_public_sector_cyber():
    assert classify(make_job("Network Engineer"), KEYWORDS, True) == "network"

def test_classifies_network():
    assert classify(make_job("Network Engineer Ljubljana"), KEYWORDS, False) == "network"

def test_classifies_sysadmin():
    assert classify(make_job("Sistemski Administrator"), KEYWORDS, False) == "sysadmin"

def test_classifies_it_other():
    assert classify(make_job("DevOps Engineer"), KEYWORDS, False) == "it_other"

def test_cyber_takes_priority_over_network():
    assert classify(make_job("Network Security SIEM Engineer"), KEYWORDS, False) == "cyber_security"

def test_case_insensitive():
    assert classify(make_job("CISSP CERTIFIED"), KEYWORDS, False) == "cyber_security"

def test_unknown_falls_back_to_it_other():
    assert classify(make_job("Računalniška podpora"), KEYWORDS, False) == "it_other"
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
pytest tests/test_classifier.py -v
```
Expected: `ModuleNotFoundError: No module named 'core.classifier'`

- [ ] **Step 3: Implement core/classifier.py**

```python
from models import Job


def classify(job: Job, keywords: dict, is_public_sector: bool) -> str:
    text = f"{job.title} {job.description}".lower()

    is_cyber = any(kw.lower() in text for kw in keywords["cyber_security"])

    if is_public_sector and is_cyber:
        return "public_sector_cyber"
    if is_cyber:
        return "cyber_security"
    if any(kw.lower() in text for kw in keywords["network"]):
        return "network"
    if any(kw.lower() in text for kw in keywords["sysadmin"]):
        return "sysadmin"
    return "it_other"
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
pytest tests/test_classifier.py -v
```
Expected: 10 passed.

- [ ] **Step 5: Commit**

```bash
git add core/classifier.py tests/test_classifier.py
git commit -m "feat: job classifier with keyword matching"
```

---

### Task 5: Aggregator

**Files:**
- Create: `core/aggregator.py`
- Create: `tests/test_aggregator.py`

**Interfaces:**
- Produces: `aggregate(job_lists: list[list[Job]]) -> list[Job]`
  - Deduplicates by `job.url`; on duplicate, appends second portal to `job.portal` (e.g. `"MojeDelo, Zaposlitev.net"`)

- [ ] **Step 1: Write failing tests**

`tests/test_aggregator.py`:
```python
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
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
pytest tests/test_aggregator.py -v
```
Expected: `ModuleNotFoundError: No module named 'core.aggregator'`

- [ ] **Step 3: Implement core/aggregator.py**

```python
from models import Job


def aggregate(job_lists: list[list[Job]]) -> list[Job]:
    seen: dict[str, Job] = {}
    for jobs in job_lists:
        for job in jobs:
            if job.url in seen:
                existing = seen[job.url]
                if job.portal not in existing.portal:
                    existing.portal = f"{existing.portal}, {job.portal}"
            else:
                seen[job.url] = job
    return list(seen.values())
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
pytest tests/test_aggregator.py -v
```
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add core/aggregator.py tests/test_aggregator.py
git commit -m "feat: job aggregator with URL-based deduplication"
```

---

### Task 6: Pipeline

**Files:**
- Create: `core/pipeline.py`
- Create: `tests/test_pipeline.py`

**Interfaces:**
- Produces: `run_pipeline() -> dict` with shape:
  ```python
  {
    "scraped_at": "2026-06-23T07:00:00",
    "total": 25,
    "errors": [{"portal": "MojeDelo", "error": "timeout"}],
    "jobs": [...]   # list[dict] via dataclasses.asdict
  }
  ```
- Side effect: writes result to `data/jobs.json`
- Internal: `_load_scraper(portal_config, search_queries) -> BaseScraper` — dynamically imports scraper class by module path

**Class name convention:** module `scrapers.gov_si` → class `GovSiScraper` (split on `_`, title-case each part, join, append `Scraper`)

- [ ] **Step 1: Write failing tests**

`tests/test_pipeline.py`:
```python
import json
from unittest.mock import patch, MagicMock
from core.pipeline import run_pipeline
from models import Job


def make_job(url, portal="MojeDelo"):
    return Job(
        title="IT Engineer", company="Acme", url=url, portal=portal,
        description="IT desc", requirements=[], salary=None,
        location="Ljubljana", posted_date="2026-06-23",
        category="", scraped_at="2026-06-23T07:00:00",
    )


MOCK_CFG = {
    "portals": [{"name": "MojeDelo", "enabled": True,
                 "module": "scrapers.mojedelo", "url": "https://mojedelo.com",
                 "is_public_sector": False}],
    "keywords": {"cyber_security": ["cyber"], "network": ["network"],
                 "sysadmin": ["sysadmin"], "it_other": ["IT"]},
    "search_queries": ["IT"],
    "schedule": {"run_time": "07:00"},
    "email": {"recipient": "test@example.com"},
}


def mock_scraper(jobs):
    s = MagicMock()
    s.fetch_jobs.return_value = jobs
    s.is_public_sector = False
    s.name = "MojeDelo"
    return s


@patch("core.pipeline.load_config", return_value=MOCK_CFG)
@patch("core.pipeline._load_scraper")
def test_pipeline_returns_expected_keys(mock_load, mock_cfg, tmp_path):
    mock_load.return_value = mock_scraper([make_job("https://a.com/1")])
    with patch("core.pipeline._jobs_path", tmp_path / "jobs.json"):
        result = run_pipeline()
    for key in ("scraped_at", "total", "errors", "jobs"):
        assert key in result


@patch("core.pipeline.load_config", return_value=MOCK_CFG)
@patch("core.pipeline._load_scraper")
def test_pipeline_writes_jobs_json(mock_load, mock_cfg, tmp_path):
    mock_load.return_value = mock_scraper([make_job("https://a.com/1")])
    path = tmp_path / "jobs.json"
    with patch("core.pipeline._jobs_path", path):
        run_pipeline()
    assert path.exists()
    assert json.loads(path.read_text())["total"] == 1


@patch("core.pipeline.load_config", return_value=MOCK_CFG)
@patch("core.pipeline._load_scraper")
def test_pipeline_records_scraper_error(mock_load, mock_cfg, tmp_path):
    mock_load.return_value.fetch_jobs.side_effect = Exception("timeout")
    mock_load.return_value.name = "MojeDelo"
    mock_load.return_value.is_public_sector = False
    with patch("core.pipeline._jobs_path", tmp_path / "jobs.json"):
        result = run_pipeline()
    assert len(result["errors"]) == 1
    assert result["errors"][0]["portal"] == "MojeDelo"


@patch("core.pipeline.load_config", return_value=MOCK_CFG)
@patch("core.pipeline._load_scraper")
def test_pipeline_deduplicates(mock_load, mock_cfg, tmp_path):
    job = make_job("https://a.com/1")
    mock_load.return_value = mock_scraper([job, job])
    with patch("core.pipeline._jobs_path", tmp_path / "jobs.json"):
        result = run_pipeline()
    assert result["total"] == 1
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
pytest tests/test_pipeline.py -v
```
Expected: `ModuleNotFoundError: No module named 'core.pipeline'`

- [ ] **Step 3: Implement core/pipeline.py**

```python
import importlib
import json
import logging
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from core.aggregator import aggregate
from core.classifier import classify
from core.config import load_config
from models import Job

_jobs_path = Path("data/jobs.json")
_log_path = Path("data/scraper.log")

logging.basicConfig(
    filename=str(_log_path),
    level=logging.ERROR,
    format="%(asctime)s %(message)s",
)


def _load_scraper(portal_config: dict, search_queries: list[str]):
    module = importlib.import_module(portal_config["module"])
    raw = portal_config["module"].split(".")[-1]
    class_name = "".join(part.title() for part in raw.split("_")) + "Scraper"
    return getattr(module, class_name)(portal_config, search_queries)


def run_pipeline() -> dict:
    cfg = load_config()
    errors: list[dict] = []
    job_lists: list[list[Job]] = []

    for portal_cfg in cfg["portals"]:
        if not portal_cfg.get("enabled", True):
            continue
        try:
            scraper = _load_scraper(portal_cfg, cfg["search_queries"])
            job_lists.append(scraper.fetch_jobs())
        except Exception as exc:
            logging.error(f"{portal_cfg['name']}: {exc}")
            errors.append({"portal": portal_cfg["name"], "error": str(exc)})

    all_jobs = aggregate(job_lists)

    for job in all_jobs:
        is_public = any(
            p.get("is_public_sector", False) and p["name"] in job.portal
            for p in cfg["portals"]
        )
        job.category = classify(job, cfg["keywords"], is_public)

    result = {
        "scraped_at": datetime.now().isoformat(timespec="seconds"),
        "total": len(all_jobs),
        "errors": errors,
        "jobs": [asdict(j) for j in all_jobs],
    }

    _jobs_path.parent.mkdir(exist_ok=True)
    _jobs_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return result
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
pytest tests/test_pipeline.py -v
```
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add core/pipeline.py tests/test_pipeline.py
git commit -m "feat: pipeline orchestrating scrapers, aggregation and classification"
```

---

### Task 7: MojeDelo scraper

**Files:**
- Create: `scrapers/mojedelo.py`
- Create: `tests/test_scraper_mojedelo.py`

**Interfaces:**
- Produces: `MojedeloScraper(portal_config: dict, search_queries: list[str])` → `fetch_jobs() -> list[Job]`

> CSS selectors target the live MojeDelo.com HTML. Run the verification step after tests pass to confirm selectors match the live site.

- [ ] **Step 1: Write failing tests**

`tests/test_scraper_mojedelo.py`:
```python
from unittest.mock import patch
import pytest
from scrapers.mojedelo import MojedeloScraper

PORTAL_CFG = {"name": "MojeDelo", "url": "https://www.mojedelo.com", "is_public_sector": False}

SAMPLE_HTML = """<html><body>
<article class="jobad">
  <h3 class="jobad__title"><a href="/delo/123">Cyber Security Engineer</a></h3>
  <span class="jobad__employer">Telekom SI</span>
  <span class="jobad__location">Ljubljana</span>
  <span class="jobad__date">23. 6. 2026</span>
  <span class="jobad__salary">2500-3200 EUR</span>
  <p class="jobad__description">Iščemo varnostnega inženirja.</p>
</article>
</body></html>"""


@patch("scrapers.mojedelo.requests.get")
def test_returns_list(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.text = SAMPLE_HTML
    assert isinstance(MojedeloScraper(PORTAL_CFG, ["IT"]).fetch_jobs(), list)

@patch("scrapers.mojedelo.requests.get")
def test_parses_title(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.text = SAMPLE_HTML
    jobs = MojedeloScraper(PORTAL_CFG, ["IT"]).fetch_jobs()
    assert jobs[0].title == "Cyber Security Engineer"

@patch("scrapers.mojedelo.requests.get")
def test_parses_salary(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.text = SAMPLE_HTML
    jobs = MojedeloScraper(PORTAL_CFG, ["IT"]).fetch_jobs()
    assert jobs[0].salary == "2500-3200 EUR"

@patch("scrapers.mojedelo.requests.get")
def test_timeout_raises(mock_get):
    import requests as req
    mock_get.side_effect = req.exceptions.Timeout()
    with pytest.raises(Exception):
        MojedeloScraper(PORTAL_CFG, ["IT"]).fetch_jobs()
```

- [ ] **Step 2: Run test — expect FAIL**

```bash
pytest tests/test_scraper_mojedelo.py -v
```
Expected: `ModuleNotFoundError: No module named 'scrapers.mojedelo'`

- [ ] **Step 3: Implement scrapers/mojedelo.py**

```python
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper
from models import Job

TIMEOUT = 30
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; JobScraper/1.0)"}


class MojedeloScraper(BaseScraper):
    def __init__(self, portal_config: dict, search_queries: list[str]):
        super().__init__(portal_config)
        self.search_queries = search_queries

    def fetch_jobs(self) -> list[Job]:
        jobs, seen = [], set()
        for query in self.search_queries:
            url = f"{self.base_url}/dela?q={requests.utils.quote(query)}&pSize=50"
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            r.raise_for_status()
            for article in BeautifulSoup(r.text, "html.parser").select("article.jobad"):
                job = self._parse(article)
                if job and job.url not in seen:
                    seen.add(job.url)
                    jobs.append(job)
        return jobs

    def _parse(self, article) -> Job | None:
        try:
            a = article.select_one("h3.jobad__title a") or article.select_one("h3 a")
            if not a:
                return None
            href = a["href"]
            url = href if href.startswith("http") else f"{self.base_url}{href}"
            company = (article.select_one(".jobad__employer") or article.select_one(".employer"))
            location = article.select_one(".jobad__location, .location")
            date = article.select_one(".jobad__date, time")
            salary = article.select_one(".jobad__salary, .salary")
            desc = article.select_one(".jobad__description, p")
            return Job(
                title=a.get_text(strip=True),
                company=company.get_text(strip=True) if company else "",
                url=url, portal=self.name,
                description=desc.get_text(strip=True)[:300] if desc else "",
                requirements=[],
                salary=salary.get_text(strip=True) if salary else None,
                location=location.get_text(strip=True) if location else "",
                posted_date=date.get_text(strip=True) if date else "",
                category="",
                scraped_at=datetime.now().isoformat(timespec="seconds"),
            )
        except Exception:
            return None
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
pytest tests/test_scraper_mojedelo.py -v
```
Expected: 4 passed.

- [ ] **Step 5: Verify selectors against live site**

```bash
python -c "
from core.config import load_config
from scrapers.mojedelo import MojedeloScraper
cfg = load_config()
p = next(x for x in cfg['portals'] if x['name'] == 'MojeDelo')
jobs = MojedeloScraper(p, ['IT']).fetch_jobs()
for j in jobs[:3]: print(j.title, '|', j.company, '|', j.salary)
"
```
Expected: 3 job entries printed. If empty: open `https://www.mojedelo.com/dela?q=IT` in browser, inspect a job card, find the real CSS class names, update selectors in `_parse`.

- [ ] **Step 6: Commit**

```bash
git add scrapers/mojedelo.py tests/test_scraper_mojedelo.py
git commit -m "feat: MojeDelo scraper"
```

---

### Task 8: Zaposlitev.net scraper

**Files:**
- Create: `scrapers/zaposlitev.py`
- Create: `tests/test_scraper_zaposlitev.py`

**Interfaces:**
- Produces: `ZaposlitveScraper(portal_config: dict, search_queries: list[str])` → `fetch_jobs() -> list[Job]`

- [ ] **Step 1: Write failing tests**

`tests/test_scraper_zaposlitev.py`:
```python
from unittest.mock import patch
from scrapers.zaposlitev import ZaposlitveScraper

PORTAL_CFG = {"name": "Zaposlitev.net", "url": "https://www.zaposlitev.net", "is_public_sector": False}

SAMPLE_HTML = """<html><body>
<div class="job-item">
  <h2 class="job-title"><a href="/delo/456">Network Engineer</a></h2>
  <span class="employer">Iskratel d.o.o.</span>
  <span class="location">Kranj</span>
  <span class="date">23.06.2026</span>
  <p class="description">Iščemo mrežnega inženirja.</p>
</div>
</body></html>"""


@patch("scrapers.zaposlitev.requests.get")
def test_returns_list(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.text = SAMPLE_HTML
    assert isinstance(ZaposlitveScraper(PORTAL_CFG, ["IT"]).fetch_jobs(), list)

@patch("scrapers.zaposlitev.requests.get")
def test_parses_title(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.text = SAMPLE_HTML
    jobs = ZaposlitveScraper(PORTAL_CFG, ["IT"]).fetch_jobs()
    assert jobs[0].title == "Network Engineer"

@patch("scrapers.zaposlitev.requests.get")
def test_salary_none_when_missing(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.text = SAMPLE_HTML
    jobs = ZaposlitveScraper(PORTAL_CFG, ["IT"]).fetch_jobs()
    assert jobs[0].salary is None
```

- [ ] **Step 2: Run test — expect FAIL**

```bash
pytest tests/test_scraper_zaposlitev.py -v
```
Expected: `ModuleNotFoundError: No module named 'scrapers.zaposlitev'`

- [ ] **Step 3: Implement scrapers/zaposlitev.py**

```python
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper
from models import Job

TIMEOUT = 30
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; JobScraper/1.0)"}


class ZaposlitveScraper(BaseScraper):
    def __init__(self, portal_config: dict, search_queries: list[str]):
        super().__init__(portal_config)
        self.search_queries = search_queries

    def fetch_jobs(self) -> list[Job]:
        jobs, seen = [], set()
        for query in self.search_queries:
            url = f"{self.base_url}/dela?q={requests.utils.quote(query)}"
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            r.raise_for_status()
            for item in BeautifulSoup(r.text, "html.parser").select(
                "div.job-item, article.job, li.job-listing"
            ):
                job = self._parse(item)
                if job and job.url not in seen:
                    seen.add(job.url)
                    jobs.append(job)
        return jobs

    def _parse(self, item) -> Job | None:
        try:
            a = item.select_one("h2 a, h3 a, .job-title a")
            if not a:
                return None
            href = a["href"]
            url = href if href.startswith("http") else f"{self.base_url}{href}"
            company = item.select_one(".employer, .company")
            location = item.select_one(".location, .kraj")
            date = item.select_one(".date, time, .posted-date")
            salary = item.select_one(".salary, .placa, .wage")
            desc = item.select_one(".description, p")
            return Job(
                title=a.get_text(strip=True),
                company=company.get_text(strip=True) if company else "",
                url=url, portal=self.name,
                description=desc.get_text(strip=True)[:300] if desc else "",
                requirements=[],
                salary=salary.get_text(strip=True) if salary else None,
                location=location.get_text(strip=True) if location else "",
                posted_date=date.get_text(strip=True) if date else "",
                category="",
                scraped_at=datetime.now().isoformat(timespec="seconds"),
            )
        except Exception:
            return None
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
pytest tests/test_scraper_zaposlitev.py -v
```
Expected: 3 passed.

- [ ] **Step 5: Verify selectors against live site**

```bash
python -c "
from core.config import load_config
from scrapers.zaposlitev import ZaposlitveScraper
cfg = load_config()
p = next(x for x in cfg['portals'] if x['name'] == 'Zaposlitev.net')
jobs = ZaposlitveScraper(p, ['IT']).fetch_jobs()
for j in jobs[:3]: print(j.title, '|', j.company)
"
```
Expected: 3 entries. If empty: inspect `https://www.zaposlitev.net/dela?q=IT`, update `select()` selector and `_parse` child selectors.

- [ ] **Step 6: Commit**

```bash
git add scrapers/zaposlitev.py tests/test_scraper_zaposlitev.py
git commit -m "feat: Zaposlitev.net scraper"
```

---

### Task 9: JobFluent scraper (playwright)

**Files:**
- Create: `scrapers/jobfluent.py`
- Create: `tests/test_scraper_jobfluent.py`

**Interfaces:**
- Produces: `JobfluentScraper(portal_config: dict, search_queries: list[str])` → `fetch_jobs() -> list[Job]`
- Uses `playwright` because JobFluent renders listings client-side

- [ ] **Step 1: Write failing tests**

`tests/test_scraper_jobfluent.py`:
```python
from unittest.mock import patch, MagicMock
from scrapers.jobfluent import JobfluentScraper

PORTAL_CFG = {"name": "JobFluent", "url": "https://www.jobfluent.com", "is_public_sector": False}

SAMPLE_HTML = """<html><body>
<div class="JobCard">
  <h2 class="JobCard__title"><a href="/jobs/789">DevOps Engineer</a></h2>
  <span class="JobCard__company">Studio Moderna</span>
  <span class="JobCard__location">Remote, Slovenia</span>
  <span class="JobCard__date">Jun 23, 2026</span>
  <p class="JobCard__description">Looking for a DevOps engineer.</p>
</div>
</body></html>"""


def _mock_pw(sample_html):
    pw = MagicMock()
    browser = MagicMock()
    page = MagicMock()
    page.content.return_value = sample_html
    browser.new_page.return_value = page
    pw.__enter__.return_value.chromium.launch.return_value = browser
    return pw


@patch("scrapers.jobfluent.sync_playwright")
def test_returns_list(mock_pw):
    mock_pw.return_value = _mock_pw(SAMPLE_HTML)
    assert isinstance(JobfluentScraper(PORTAL_CFG, ["IT"]).fetch_jobs(), list)

@patch("scrapers.jobfluent.sync_playwright")
def test_parses_title(mock_pw):
    mock_pw.return_value = _mock_pw(SAMPLE_HTML)
    jobs = JobfluentScraper(PORTAL_CFG, ["IT"]).fetch_jobs()
    assert len(jobs) >= 1
    assert jobs[0].title == "DevOps Engineer"
```

- [ ] **Step 2: Run test — expect FAIL**

```bash
pytest tests/test_scraper_jobfluent.py -v
```
Expected: `ModuleNotFoundError: No module named 'scrapers.jobfluent'`

- [ ] **Step 3: Implement scrapers/jobfluent.py**

```python
from datetime import datetime
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper
from models import Job

TIMEOUT = 30000


class JobfluentScraper(BaseScraper):
    def __init__(self, portal_config: dict, search_queries: list[str]):
        super().__init__(portal_config)
        self.search_queries = search_queries

    def fetch_jobs(self) -> list[Job]:
        jobs, seen = [], set()
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            for query in self.search_queries:
                url = f"{self.base_url}/jobs-it-si?q={query}"
                page.goto(url, timeout=TIMEOUT)
                page.wait_for_load_state("networkidle", timeout=TIMEOUT)
                soup = BeautifulSoup(page.content(), "html.parser")
                for card in soup.select("div.JobCard, article.job-card, div[class*='JobCard']"):
                    job = self._parse(card)
                    if job and job.url not in seen:
                        seen.add(job.url)
                        jobs.append(job)
            browser.close()
        return jobs

    def _parse(self, card) -> Job | None:
        try:
            a = card.select_one("[class*='title'] a, h2 a, h3 a")
            if not a:
                return None
            href = a["href"]
            url = href if href.startswith("http") else f"{self.base_url}{href}"
            company = card.select_one("[class*='company'], [class*='employer']")
            location = card.select_one("[class*='location']")
            date = card.select_one("[class*='date'], time")
            salary = card.select_one("[class*='salary'], [class*='wage']")
            desc = card.select_one("[class*='description'], p")
            return Job(
                title=a.get_text(strip=True),
                company=company.get_text(strip=True) if company else "",
                url=url, portal=self.name,
                description=desc.get_text(strip=True)[:300] if desc else "",
                requirements=[],
                salary=salary.get_text(strip=True) if salary else None,
                location=location.get_text(strip=True) if location else "",
                posted_date=date.get_text(strip=True) if date else "",
                category="",
                scraped_at=datetime.now().isoformat(timespec="seconds"),
            )
        except Exception:
            return None
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
pytest tests/test_scraper_jobfluent.py -v
```
Expected: 2 passed.

- [ ] **Step 5: Verify selectors against live site**

```bash
python -c "
from core.config import load_config
from scrapers.jobfluent import JobfluentScraper
cfg = load_config()
p = next(x for x in cfg['portals'] if x['name'] == 'JobFluent')
jobs = JobfluentScraper(p, ['IT']).fetch_jobs()
for j in jobs[:3]: print(j.title, '|', j.company)
"
```
Expected: 3 entries. If empty: open `https://www.jobfluent.com/jobs-it-si` in browser, inspect a job card, update `select()` and `_parse` selectors. Also verify the search URL pattern is correct.

- [ ] **Step 6: Commit**

```bash
git add scrapers/jobfluent.py tests/test_scraper_jobfluent.py
git commit -m "feat: JobFluent scraper using playwright"
```

---

### Task 10: GOV.SI scraper

**Files:**
- Create: `scrapers/gov_si.py`
- Create: `tests/test_scraper_gov_si.py`

**Interfaces:**
- Produces: `GovSiScraper(portal_config: dict, search_queries: list[str])` → `fetch_jobs() -> list[Job]`
- `portal_config["is_public_sector"]` is `True` — pipeline will classify matching jobs as `public_sector_cyber`

- [ ] **Step 1: Write failing tests**

`tests/test_scraper_gov_si.py`:
```python
from unittest.mock import patch
from scrapers.gov_si import GovSiScraper

PORTAL_CFG = {"name": "GOV.SI", "url": "https://www.gov.si", "is_public_sector": True}

SAMPLE_HTML = """<html><body>
<div class="views-row">
  <h3 class="views-field-title"><a href="/razpisi/123">Strokovni sodelavec za kibernetsko varnost</a></h3>
  <span class="views-field-field-organ">Ministrstvo za digitalno preobrazbo</span>
  <span class="views-field-field-kraj">Ljubljana</span>
  <span class="views-field-field-datum-objave">23. 6. 2026</span>
  <div class="views-field-body">Razpis za strokovnjaka s področja kibernetske varnosti.</div>
</div>
</body></html>"""


@patch("scrapers.gov_si.requests.get")
def test_returns_list(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.text = SAMPLE_HTML
    assert isinstance(GovSiScraper(PORTAL_CFG, ["kibernetska varnost"]).fetch_jobs(), list)

@patch("scrapers.gov_si.requests.get")
def test_parses_title(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.text = SAMPLE_HTML
    jobs = GovSiScraper(PORTAL_CFG, ["kibernetska varnost"]).fetch_jobs()
    assert "kibernetsko varnost" in jobs[0].title.lower()

@patch("scrapers.gov_si.requests.get")
def test_salary_always_none(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.text = SAMPLE_HTML
    jobs = GovSiScraper(PORTAL_CFG, ["kibernetska varnost"]).fetch_jobs()
    assert jobs[0].salary is None
```

- [ ] **Step 2: Run test — expect FAIL**

```bash
pytest tests/test_scraper_gov_si.py -v
```
Expected: `ModuleNotFoundError: No module named 'scrapers.gov_si'`

- [ ] **Step 3: Implement scrapers/gov_si.py**

```python
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper
from models import Job

TIMEOUT = 30
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; JobScraper/1.0)"}


class GovSiScraper(BaseScraper):
    def __init__(self, portal_config: dict, search_queries: list[str]):
        super().__init__(portal_config)
        self.search_queries = search_queries

    def fetch_jobs(self) -> list[Job]:
        jobs, seen = [], set()
        for query in self.search_queries:
            url = (f"{self.base_url}/javne-objave/"
                   f"?tip=razpis-za-prosto-delovno-mesto"
                   f"&q={requests.utils.quote(query)}")
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            r.raise_for_status()
            for row in BeautifulSoup(r.text, "html.parser").select(
                "div.views-row, article.objava, li.razpis"
            ):
                job = self._parse(row)
                if job and job.url not in seen:
                    seen.add(job.url)
                    jobs.append(job)
        return jobs

    def _parse(self, row) -> Job | None:
        try:
            a = row.select_one("h3 a, h2 a, .views-field-title a")
            if not a:
                return None
            href = a["href"]
            url = href if href.startswith("http") else f"{self.base_url}{href}"
            company = row.select_one(".views-field-field-organ, .organ")
            location = row.select_one(".views-field-field-kraj, .kraj")
            date = row.select_one(".views-field-field-datum-objave, time")
            desc = row.select_one(".views-field-body, p")
            return Job(
                title=a.get_text(strip=True),
                company=company.get_text(strip=True) if company else "Javni sektor",
                url=url, portal=self.name,
                description=desc.get_text(strip=True)[:300] if desc else "",
                requirements=[],
                salary=None,
                location=location.get_text(strip=True) if location else "Slovenija",
                posted_date=date.get_text(strip=True) if date else "",
                category="",
                scraped_at=datetime.now().isoformat(timespec="seconds"),
            )
        except Exception:
            return None
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
pytest tests/test_scraper_gov_si.py -v
```
Expected: 3 passed.

- [ ] **Step 5: Verify selectors against live site**

```bash
python -c "
from core.config import load_config
from scrapers.gov_si import GovSiScraper
cfg = load_config()
p = next(x for x in cfg['portals'] if x['name'] == 'GOV.SI')
jobs = GovSiScraper(p, ['kibernetska varnost']).fetch_jobs()
for j in jobs[:3]: print(j.title, '|', j.company)
"
```
Expected: entries from GOV.SI. If empty: open `https://www.gov.si/javne-objave/` in browser, inspect HTML, update `select()` and `_parse` selectors, and verify the URL query parameter names.

- [ ] **Step 6: Run full test suite**

```bash
pytest -v
```
Expected: all tests pass.

- [ ] **Step 7: Commit**

```bash
git add scrapers/gov_si.py tests/test_scraper_gov_si.py
git commit -m "feat: GOV.SI public sector scraper"
```

---

### Task 11: Mailer

**Files:**
- Create: `core/mailer.py`
- Create: `tests/test_mailer.py`

**Interfaces:**
- Consumes: `result: dict` (pipeline output), `config: dict`
- Produces: `send_email(result: dict, config: dict) -> None`
  - No-op if `result["total"] == 0`
  - Sends HTML email to `config["email"]["recipient"]` via SMTP STARTTLS

- [ ] **Step 1: Write failing tests**

`tests/test_mailer.py`:
```python
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
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
pytest tests/test_mailer.py -v
```
Expected: `ModuleNotFoundError: No module named 'core.mailer'`

- [ ] **Step 3: Implement core/mailer.py**

```python
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

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
    html = _build_html(result)
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"IT Službe SLO — {result['scraped_at'][:10]} ({result['total']} oglasov)"
    msg["From"] = cfg["sender"]
    msg["To"] = cfg["recipient"]
    msg.attach(MIMEText(html, "html", "utf-8"))
    with smtplib.SMTP(cfg["smtp_host"], cfg["smtp_port"]) as smtp:
        smtp.starttls()
        smtp.login(cfg["sender"], cfg["sender_password"])
        smtp.sendmail(cfg["sender"], cfg["recipient"], msg.as_string())
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
pytest tests/test_mailer.py -v
```
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add core/mailer.py tests/test_mailer.py
git commit -m "feat: HTML email sender"
```

---

### Task 12: Scheduler

**Files:**
- Create: `core/scheduler.py`
- Create: `tests/test_scheduler.py`

**Interfaces:**
- Produces: `create_scheduler(job_func: callable, run_time: str) -> BackgroundScheduler`
  - `run_time` format: `"HH:MM"` (e.g. `"07:00"`)
  - Returns a **started** `BackgroundScheduler` with one cron job

- [ ] **Step 1: Write failing tests**

`tests/test_scheduler.py`:
```python
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
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
pytest tests/test_scheduler.py -v
```
Expected: `ModuleNotFoundError: No module named 'core.scheduler'`

- [ ] **Step 3: Implement core/scheduler.py**

```python
from apscheduler.schedulers.background import BackgroundScheduler


def create_scheduler(job_func, run_time: str) -> BackgroundScheduler:
    hour, minute = map(int, run_time.split(":"))
    scheduler = BackgroundScheduler()
    scheduler.add_job(job_func, "cron", hour=hour, minute=minute)
    scheduler.start()
    return scheduler
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
pytest tests/test_scheduler.py -v
```
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add core/scheduler.py tests/test_scheduler.py
git commit -m "feat: APScheduler wrapper for daily pipeline trigger"
```

---

### Task 13: Flask web app and dashboard

**Files:**
- Create: `web/app.py`
- Create: `web/templates/dashboard.html`
- Create: `tests/test_web.py`

**Interfaces:**
- Produces: `create_app() -> Flask`
- Produces: `GET /` — renders dashboard reading `data/jobs.json` (or `JOBS_PATH` env var for tests)
- Produces: `POST /run-now` — calls `run_pipeline()` + `send_email()`, redirects to `GET /`

- [ ] **Step 1: Write failing tests**

`tests/test_web.py`:
```python
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
    monkeypatch.setattr("web.app.run_pipeline",
                        lambda: {"total": 0, "jobs": [], "errors": [], "scraped_at": ""})
    monkeypatch.setattr("web.app.send_email", lambda r, cfg: None)
    monkeypatch.setattr("web.app.load_config", lambda: {"email": {}})
    assert c.post("/run-now").status_code == 302
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
pytest tests/test_web.py -v
```
Expected: `ModuleNotFoundError: No module named 'web.app'`

- [ ] **Step 3: Implement web/app.py**

```python
import json, os
from pathlib import Path
from flask import Flask, render_template, redirect, url_for
from core.pipeline import run_pipeline
from core.mailer import send_email
from core.config import load_config

CATEGORY_ORDER = ["cyber_security", "public_sector_cyber", "network", "sysadmin", "it_other"]
CATEGORY_LABELS = {
    "cyber_security": "Cyber Security",
    "public_sector_cyber": "Javni sektor – Cyber Security",
    "network": "Network Engineer",
    "sysadmin": "Sistemski Administrator",
    "it_other": "Ostali IT",
}


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates")

    def _jobs_path() -> Path:
        return Path(os.environ.get("JOBS_PATH", "data/jobs.json"))

    @app.route("/")
    def dashboard():
        path = _jobs_path()
        data = (json.loads(path.read_text(encoding="utf-8"))
                if path.exists()
                else {"scraped_at": None, "total": 0, "errors": [], "jobs": []})
        jobs_by_cat = {cat: [] for cat in CATEGORY_ORDER}
        for job in data.get("jobs", []):
            cat = job.get("category", "it_other")
            if cat in jobs_by_cat:
                jobs_by_cat[cat].append(job)
        return render_template(
            "dashboard.html",
            jobs_by_cat=jobs_by_cat,
            category_labels=CATEGORY_LABELS,
            category_order=CATEGORY_ORDER,
            scraped_at=data.get("scraped_at"),
            total=data.get("total", 0),
            errors=data.get("errors", []),
        )

    @app.route("/run-now", methods=["POST"])
    def run_now():
        result = run_pipeline()
        send_email(result, load_config())
        return redirect(url_for("dashboard"))

    return app
```

- [ ] **Step 4: Implement web/templates/dashboard.html**

```html
<!DOCTYPE html>
<html lang="sl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SLO Job Scraper</title>
  <style>
    body{font-family:sans-serif;max-width:900px;margin:0 auto;padding:16px;background:#f5f5f5}
    header{display:flex;justify-content:space-between;align-items:center;margin-bottom:24px}
    h1{margin:0;font-size:1.4rem}
    .meta{color:#666;font-size:.9rem}
    button{background:#2563eb;color:#fff;border:none;padding:8px 16px;border-radius:6px;cursor:pointer;font-size:.9rem}
    button:hover{background:#1d4ed8}
    .section{background:#fff;border-radius:8px;padding:16px;margin-bottom:20px;box-shadow:0 1px 3px rgba(0,0,0,.1)}
    .section-header{font-size:1.1rem;font-weight:700;margin-bottom:12px;padding-bottom:8px;border-bottom:2px solid #e5e7eb}
    .cyber_security .section-header{border-color:#ef4444;color:#dc2626}
    .public_sector_cyber .section-header{border-color:#3b82f6;color:#2563eb}
    .network .section-header{border-color:#f97316;color:#ea580c}
    .sysadmin .section-header{border-color:#eab308;color:#ca8a04}
    .it_other .section-header{border-color:#9ca3af;color:#6b7280}
    .job-card{border:1px solid #e5e7eb;border-radius:6px;padding:12px;margin-bottom:10px}
    .job-title{font-weight:600;font-size:1rem;margin-bottom:4px}
    .job-title a{color:#1d4ed8;text-decoration:none}
    .job-title a:hover{text-decoration:underline}
    .job-meta{color:#6b7280;font-size:.85rem;margin-bottom:6px}
    .job-desc{font-size:.9rem;color:#374151;margin-bottom:4px}
    .job-salary{font-size:.9rem;font-weight:600;color:#059669}
    .job-reqs{font-size:.85rem;color:#6b7280}
    .error-box{background:#fef2f2;border:1px solid #fecaca;border-radius:6px;padding:10px;margin-bottom:12px;font-size:.85rem;color:#991b1b}
  </style>
</head>
<body>
<header>
  <div>
    <h1>SLO Job Scraper</h1>
    {% if scraped_at %}
      <div class="meta">Zadnja posodobitev: {{ scraped_at }} &bull; {{ total }} oglasov</div>
    {% else %}
      <div class="meta">Ni podatkov — klikni Poženi zdaj.</div>
    {% endif %}
  </div>
  <form method="post" action="/run-now">
    <button type="submit">Poženi zdaj</button>
  </form>
</header>

{% for err in errors %}
  <div class="error-box">⚠ {{ err.portal }}: {{ err.error }}</div>
{% endfor %}

{% for cat in category_order %}
  {% set jobs = jobs_by_cat[cat] %}
  {% if jobs %}
  <div class="section {{ cat }}">
    <div class="section-header">{{ category_labels[cat] }} ({{ jobs|length }})</div>
    {% for job in jobs %}
    <div class="job-card">
      <div class="job-title"><a href="{{ job.url }}" target="_blank" rel="noopener">{{ job.title }}</a></div>
      <div class="job-meta">{{ job.company }} &bull; {{ job.location }} &bull; {{ job.portal }} &bull; {{ job.posted_date }}</div>
      {% if job.description %}<div class="job-desc">{{ job.description }}</div>{% endif %}
      {% if job.requirements %}<div class="job-reqs">Zahteve: {{ job.requirements | join(', ') }}</div>{% endif %}
      {% if job.salary %}<div class="job-salary">Plača: {{ job.salary }}</div>{% endif %}
    </div>
    {% endfor %}
  </div>
  {% endif %}
{% endfor %}

{% if total == 0 and scraped_at %}
  <p style="color:#9ca3af">Ni najdenih oglasov za nastavljene ključne besede.</p>
{% endif %}
</body>
</html>
```

- [ ] **Step 5: Run tests — expect PASS**

```bash
pytest tests/test_web.py -v
```
Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
git add web/app.py web/templates/dashboard.html tests/test_web.py
git commit -m "feat: Flask dashboard with category sections and run-now trigger"
```

---

### Task 14: Entrypoint

**Files:**
- Create: `main.py`
- Create: `tests/test_main.py`

**Interfaces:**
- Produces: `main()` — creates scheduler with pipeline+email as the daily job, then starts Flask; blocks until Ctrl+C

- [ ] **Step 1: Write failing test**

`tests/test_main.py`:
```python
from unittest.mock import patch, MagicMock

MOCK_CFG = {"schedule": {"run_time": "07:00"}, "email": {},
            "portals": [], "keywords": {}, "search_queries": []}


def test_main_starts_scheduler_and_flask():
    with patch("main.load_config", return_value=MOCK_CFG):
        with patch("main.create_scheduler") as mock_sched:
            with patch("main.create_app") as mock_app:
                app = MagicMock()
                mock_app.return_value = app
                mock_sched.return_value = MagicMock()
                app.run.side_effect = KeyboardInterrupt()
                try:
                    from main import main
                    main()
                except (KeyboardInterrupt, SystemExit):
                    pass
                mock_sched.assert_called_once()
                app.run.assert_called_once_with(
                    host="0.0.0.0", port=5000, use_reloader=False
                )
```

- [ ] **Step 2: Run test — expect FAIL**

```bash
pytest tests/test_main.py -v
```
Expected: `ModuleNotFoundError: No module named 'main'`

- [ ] **Step 3: Implement main.py**

```python
from core.config import load_config
from core.pipeline import run_pipeline
from core.mailer import send_email
from core.scheduler import create_scheduler
from web.app import create_app


def main():
    cfg = load_config()

    def scheduled_job():
        result = run_pipeline()
        send_email(result, cfg)

    create_scheduler(scheduled_job, cfg["schedule"]["run_time"])
    create_app().run(host="0.0.0.0", port=5000, use_reloader=False)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test — expect PASS**

```bash
pytest tests/test_main.py -v
```
Expected: 1 passed.

- [ ] **Step 5: Run full test suite**

```bash
pytest -v
```
Expected: all tests pass.

- [ ] **Step 6: Smoke test**

Set `sender` and `sender_password` in `config.yaml` (Gmail App Password: Google Account → Security → 2-Step Verification → App Passwords).

```bash
python main.py
```
Expected: `Running on http://0.0.0.0:5000` in terminal. Open `http://localhost:5000` — dashboard loads. Click **Poženi zdaj** — wait 30–60 seconds, page refreshes with job listings grouped by category. Check `nejcviddmar@gmail.com` inbox for the email summary.

- [ ] **Step 7: Final commit**

```bash
git add main.py tests/test_main.py
git commit -m "feat: main entrypoint wiring scheduler and Flask"
```
