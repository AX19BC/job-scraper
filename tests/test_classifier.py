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
    "it_other": ["IT specialist", "IT engineer", "IT podpora", "IT strokovnjak",
                 "DevOps", "cloud", "Azure", "AWS", "informatika", "informatik",
                 "informacijska tehnologija", "programer", "developer",
                 "frontend", "backend", "full-stack", "fullstack",
                 "podatkovna baza", "testiranje programske",
                 "mobilna aplikacija", "spletni razvoj", "spletna aplikacija"],
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

def test_it_support_classified_as_it_other():
    assert classify(make_job("IT podpora in vzdrževanje"), KEYWORDS, False) == "it_other"

def test_computer_literacy_in_non_it_job_returns_unrelated():
    assert classify(make_job("Natakar", "Zahtevamo računalniško pismenost."), KEYWORDS, False) == "unrelated"

def test_healthcare_job_returns_unrelated():
    assert classify(make_job("Samostojni strokovni sodelavec v zdravstveni negi - socialni delavec"), KEYWORDS, False) == "unrelated"

def test_unrelated_job_returns_unrelated():
    assert classify(make_job("Prodajalec v trgovini"), KEYWORDS, False) == "unrelated"

def test_construction_safety_returns_unrelated():
    assert classify(make_job("Delavec za varnost pri delu"), KEYWORDS, False) == "unrelated"
