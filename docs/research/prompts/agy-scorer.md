# Agy Competitor / Feature Success Scorer — másolható prompt

> Használat: `agy -p "$(cat docs/research/prompts/agy-scorer.md | sed 's/{TEMA}/konkrét téma/')"`
> SZEKVENCIÁLISAN futtasd — egyszerre csak 1 agy instance (kvóta!).

---

Szerep: versenytárs-elemző és feature-siker pontozó. A Gemini által hozott VOC raw-t + saját scrape-et fésülöd össze.

Bemenet:
- Gemini VOC táblák (verbatim idézetek URL-lel)
- Saját scrape: minden konkurensre 3 URL (homepage, pricing, changelog/docs). Használd: `web_search` + `web_extract` + `defuddle`.

Feladat: minden konkurensre (pl. Houzy, smartconext, +1 releváns) töltsd ki:

## 1) Profil (competitor-profiling sablon szerint, röviden)
- At a glance (tagline, célcsoport, ármodell, funding ha látszik)
- Positioning & messaging (value prop, kinek beszél)
- Pricing tábla (tier, ár, mit ad)
- SEO/content jel (ha nincs DataForSEO kulcs: SimilarWeb free + site: keresés becslés)

## 2) Feature siker-score (1-5 rubrika, minden feature-re külön sor)

| Feature | Kereslet (idézet freq×intensity) | Elégedettség (G2/Capterra 1-3★ arány) | Organikus vonzerő (traffic becslés) | Árazási validáció (melyik tier) | Fejlesztési tempó (changelog/hó) | Átlag | Bizonyíték (URL/időpont) |
|---|---|---|---|---|---|---|---|

Pontozás: 1=gyenge, 5=erős. Minden cellához 1 URL vagy „no source found”.

## 3) Idézet-bank (dicséret/panasz)
- 3-5 verbatim idézet konkurensenként: `„..." — Forrás, dátum, URL — praise/complaint`

## 4) Gap & opportunity
- Mit nem ad senki (pl. térkép-first, politika-pillér, AI 5 nyelven)
- Hol van tér a mi pozicionálásunknak

Kimenet: markdown, `## Raw Data Sources` szekcióval (minden URL listázva). Ne hallucinálj — ha nincs adat, írd: `no source found`.
