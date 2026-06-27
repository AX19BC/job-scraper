# Job Scraper — Design Spec
**Datum:** 2026-06-23  
**Status:** Odobren

---

## Povzetek

Aplikacija enkrat na dan (privzeto ob 7:00, nastavljivo) išče IT/cyber security oglase za službe na slovenskih portalih. Rezultate prikaže na lokalnem web dashboardu in pošlje HTML e-mail povzetek na `nejcviddmar@gmail.com`. Cyber security oglasi so prikazani na vrhu kot prioritetna kategorija.

---

## Arhitektura

**Pristop:** Python monolith — Flask (web dashboard) + APScheduler (urnik) v enem procesu.

```
job_scraper/
├── main.py                  # vstopna točka, zažene Flask + APScheduler
├── config.yaml              # portali, urnik, e-mail nastavitve, ključne besede
├── scrapers/
│   ├── base.py              # abstraktni razred BaseScraper
│   ├── mojedelo.py
│   ├── zaposlitev.py
│   ├── jobfluent.py
│   ├── gov_si.py            # javni sektor (GOV.SI, AJPES, občine)
│   └── ...                  # novi portali = nova datoteka
├── core/
│   ├── scheduler.py         # APScheduler, sproži scraping ob nastavljeni uri
│   ├── aggregator.py        # združi rezultate, dedupliciranje po URL-ju
│   ├── classifier.py        # razvrsti oglas v kategorijo
│   └── mailer.py            # pošlje dnevni HTML e-mail
├── web/
│   ├── app.py               # Flask aplikacija
│   └── templates/
│       └── dashboard.html   # web dashboard
├── data/
│   ├── jobs.json            # dnevni cache rezultatov
│   └── scraper.log          # log napak po portalih
└── requirements.txt
```

**Tok delovanja:**
1. `main.py` zažene Flask strežnik + APScheduler v istem procesu
2. Ob nastavljeni uri scheduler vzporedno sproži scraping vseh omogočenih portalov
3. `aggregator.py` združi in deduplika rezultate (po URL-ju)
4. `classifier.py` razvrsti vsak oglas v kategorijo
5. Rezultati se zapišejo v `data/jobs.json`
6. `mailer.py` pošlje HTML e-mail povzetek
7. Dashboard na `http://localhost:5000` bere `jobs.json`

---

## Podatkovni model

```python
@dataclass
class Job:
    title: str               # naziv delovnega mesta
    company: str             # podjetje
    url: str                 # direktna povezava do oglasa (unikatni ključ za dedup)
    portal: str              # vir (npr. "MojeDelo")
    description: str         # kratek opis (~300 znakov)
    requirements: list[str]  # zahteve, če so razvidne
    salary: str | None       # plača, None če ni navedena
    location: str            # kraj
    posted_date: str         # datum objave
    category: str            # glej kategorije spodaj
    scraped_at: str          # ISO timestamp scraping-a
```

**Kategorije** (vrstni red prikaza na dashboardu):
1. `cyber_security` — cyber security oglasi (zasebni sektor)
2. `public_sector_cyber` — javni sektor + cyber security ključne besede
3. `network` — network engineer / omrežje
4. `sysadmin` — sistemski administrator
5. `it_other` — ostali IT oglasi

Oglas dobi `public_sector_cyber` če portal spada v javni sektor IN vsebuje cyber security ključne besede.

---

## Klasifikacija — ključne besede (config.yaml)

```yaml
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
  public_sector_portals:
    - "gov.si"
    - "občina"
    - "ministrstvo"
    - "javni zavod"
    - "AJPES"
```

---

## Portali (config.yaml)

```yaml
portals:
  - name: "MojeDelo"
    enabled: true
    module: "scrapers.mojedelo"
    url: "https://www.mojedelo.com"
  - name: "Zaposlitev.net"
    enabled: true
    module: "scrapers.zaposlitev"
    url: "https://www.zaposlitev.net"
  - name: "JobFluent"
    enabled: true
    module: "scrapers.jobfluent"
    url: "https://www.jobfluent.com"
  - name: "GOV.SI"
    enabled: true
    module: "scrapers.gov_si"
    url: "https://www.gov.si"
    is_public_sector: true
```

Nov portal = nova datoteka v `scrapers/` + vnos v `config.yaml`. `enabled: false` začasno onemogoči portal brez brisanja kode.

---

## Scraping strategija

- Privzeto: `requests` + `BeautifulSoup` (hitro, brez overhead-a)
- Za portale z dinamičnim JS: `playwright` (samo kjer je nujno)
- Vsak scraper je neodvisen — napaka enega ne ustavi ostalih
- Timeout na scraper: 30 sekund

---

## Web Dashboard

- URL: `http://localhost:5000`
- Prikazuje oglase iz `data/jobs.json` (zadnje scraping)
- Razdelki po kategorijah (zaporedje = prioriteta):
  1. Cyber Security
  2. Javni sektor – Cyber Security
  3. Network Engineer
  4. Sysadmin
  5. Ostali IT
- Vsak oglas: naziv, podjetje, portal, datum, opis, zahteve, plača (če navedena), gumb `[Odpri oglas →]`
- Gumb **"Poženi zdaj"** za takojšen scraping brez čakanja na urnik
- Prikaže timestamp zadnje posodobitve

---

## E-mail povzetek

- Pošilja se po vsakem uspešnem scraping-u
- Prejemnik: `nejcviddmar@gmail.com`
- Format: HTML e-mail, enaka struktura kot dashboard
- Vsebuje skupno število oglasov po kategorijah
- Če scraping ne vrne nobenega rezultata, e-mail se NE pošlje

```yaml
email:
  smtp_host: smtp.gmail.com
  smtp_port: 587
  sender: ""         # nastavi uporabnik
  recipient: nejcviddmar@gmail.com
  run_time: "07:00"  # nastavljivo
```

---

## Error handling

- Napake po portalih se logirajo v `data/scraper.log`
- Dashboard in e-mail prikažeta opozorilo za portale ki so odpovedali: `⚠ MojeDelo: ni bilo mogoče prebrati (zadnji uspešen: <datum>)`
- Dedupliciranje: po URL-ju; če isti oglas pride iz dveh portalov, se ohrani enkrat z navedbo obeh virov

---

## Odvisnosti (requirements.txt)

```
flask
apscheduler
requests
beautifulsoup4
playwright
pyyaml
```

---

## Zagon

```bash
pip install -r requirements.txt
playwright install chromium
python main.py
# Dashboard dostopen na http://localhost:5000
```

Za samodejni zagon ob zagonu sistema: Windows Task Scheduler ali systemd (Linux).
