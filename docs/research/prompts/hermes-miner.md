# Hermes Natív VOC Miner — másolható runbook

> Hermes maga bányászik, nem csak a külsőket hívja. Több módszer, resilient — ha egy nem ad adatot, a többi megy tovább.

## Mikor futtasd
Minden deep research elején Hermes első hullámban fut, párhuzamosan a Geminivel (Gemini kvóta-hiba esetén Hermes marad egyedül — ez nem hiba, így tervezett).

## Eszköz-létra (sorrendben próbáld, ha egyik üres/megbukik → következő)

1. **web_search + web_extract** (alap): `site:reddit.com`, `site:news.ycombinator.com`, `site:trustpilot.com`, `site:g2.com` + témakör kulcsszavak (pl. "Swiss Baugesuch", "Steuerfuss", "housing search Zurich")
2. **agent-reach**: `agent-reach doctor --json` → aktív backend szerint `exa.web_search_exa`, `opencli reddit search`, `opencli xiaohongshu search` stb. Social watering holes: Reddit, X/Twitter, Product Hunt, YouTube
3. **Jina / Defuddle fallback**: `curl -s https://r.jina.ai/http://URL` vagy `defuddle` a cikk-tisztításhoz (paywall nélküli full text)
4. **Browser helper** (ha JS-heavy oldal): `browser_helper` navigál + `get_content` + `get_page_text` a dinamikus tartalomra
5. **Blocked-page recovery**: `blocked-page-recovery` létra (Wayback → archive.today → Google cache) 403/429/paywall esetén
6. **research-toolkit / arXiv** (ha tech téma): `curl https://export.arxiv.org/api/query?...` — csak kiegészítés, nem fő forrás

## Ledger-kényszer (grounded-citations)
```bash
S=~/.hermes/skills/research/grounded-citations/scripts/sources.py
python "$S" reset --ledger /tmp/ledger-deep-$(date +%F).json
python "$S" add <url1> <url2> --ledger /tmp/ledger-deep-$(date +%F).json  # minden web_extract URL-nél
python "$S" quote <id> --text "verbatim idézet" --from /tmp/page.txt --ledger /tmp/ledger-deep-$(date +%F).json
```

## Feladat: `{TEMA}` VOC bányászat

- Gyűjts **8-12 VERBATIM idézetet** (szó szerint, idézőjelben) — nincs parafrázis.
- Minden sor: `| # | Forrás (platform) | Verbatim ("...") | Kontextus | Dátum | URL | Érzelem | Téma (pain/trigger/desired_outcome/alternative/praise/complaint/JTBD) |`
- Minden sorhoz élő URL + dátum. Halott linket ne adj.
- Ha egy módszer üres: írd: `no source found — <módszer>: <query>` és menj tovább a létrán — **ne állj le**.
- Forrásmix: legalább 3 platform (pl. Reddit + HN + Trustpilot/G2) — ez validációs gate.
- Resilience: ha 2 módszer is üres, akkor is add le a meglevő 4-6 idézetet — részleges eredmény is érték.

## Kimenet
- Táblázat (fenti séma) + `Top 3 pattern` (leggyakoribb fájdalom/trigger, freq×intensity alapján)
- Minden idézet verbatim — későbbi evaluator és ADR ezt használja bizonyítékként.
