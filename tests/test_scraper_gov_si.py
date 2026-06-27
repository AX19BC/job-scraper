from unittest.mock import patch, MagicMock
from scrapers.gov_si import GovSiScraper

PORTAL_CFG = {"name": "GOV.SI", "url": "https://www.gov.si", "is_public_sector": True}

SAMPLE_HTML = """<html><body>
<table>
<tr><th>Naziv</th><th>Datum objave</th><th>Rok za prijavo</th><th>Institucija</th></tr>
<tr>
  <td class="td-title"><div class="cell"><a href="/zbirke/delovna-mesta/strokovnjak-kibernetska-varnost/">Strokovni sodelavec za kibernetsko varnost</a></div></td>
  <td class="td-publish-date"><div class="cell">23. 6. 2026</div></td>
  <td class="td-due-date"><div class="cell">30. 6. 2026</div></td>
  <td class="td-organisation"><div class="cell">Ministrstvo za digitalno preobrazbo</div></td>
</tr>
</table>
</body></html>"""


@patch("scrapers.gov_si.requests.get")
def test_returns_list(mock_get):
    mock_get.return_value.text = SAMPLE_HTML
    mock_get.return_value.raise_for_status = MagicMock()
    assert isinstance(GovSiScraper(PORTAL_CFG, []).fetch_jobs(), list)

@patch("scrapers.gov_si.requests.get")
def test_parses_title(mock_get):
    mock_get.return_value.text = SAMPLE_HTML
    mock_get.return_value.raise_for_status = MagicMock()
    jobs = GovSiScraper(PORTAL_CFG, []).fetch_jobs()
    assert "kibernetsko varnost" in jobs[0].title.lower()

@patch("scrapers.gov_si.requests.get")
def test_salary_always_none(mock_get):
    mock_get.return_value.text = SAMPLE_HTML
    mock_get.return_value.raise_for_status = MagicMock()
    jobs = GovSiScraper(PORTAL_CFG, []).fetch_jobs()
    assert jobs[0].salary is None
