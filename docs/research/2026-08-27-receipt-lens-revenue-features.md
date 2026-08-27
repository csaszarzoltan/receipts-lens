# ReceiptLens Revenue / Pro Features — Deep Research (B: bevétel)

**Dátum:** 2026-08-27  
**Cél (B):** Pro plan fizetőssé tétele, ARPU növelés — ingyenes ma, mi hajt Konverziót?  
**Módszertan:** `innovation-engine` + `EVOLUTIONARY-SYSTEM.md` — 3 miner **kanban + párhuzamos agent** (`deleg_e0e35e15`, 9m48s, 3× hermes-default leaf, külön session):

| Miner | Feladat | Agent | Idő | Eredmény |
|-------|---------|-------|-----|----------|
| **VOC** | 8-12 verbatim, 3+ platform | sa-0-7bf7d1b5 | 574s | 18 idézet (Trustpilot 5, App landing 7, Reddit 3, LinkedIn/Blog 3), Top 3 pattern |
| **Competitor Pricing** | 6 versenytárs tier + API + self-hosted gap | sa-1-d2953a63 | 277s | 6 pricing mátrix, gap 14 pont |
| **JTBD + RICE** | Jobs + 5 feature RICE, vitamarket EAN/barcode angle | sa-2-8cdcd0a6 | 588s | JTBD + RICE draft (max_iterations truncate, kiegészítve szintézisben) |

**Kanban Gate:** 0 aktív task (swiss-p-map boardon 7 done, receipts-lens-en 0) — selector indulhatott.  
**Resilience:** Reddit JSON 403 → Exa snippet pivot, browser CDP 9555 unreachable → web_search/web_extract fallback — részleges is érték (innovation-engine elv).

---

## 1) VOC — mit fizetnek meg? (18 verbatim, 4 platform)

**Forrás:** `/tmp/receipt-lens-voc.md` (11,988 bytes, mind élő URL + dátum, `grounded-citations` ledger)

### Verbatim minta (3/18 — teljes tábla a /tmp fájlban)

| # | Idézet | Platform | Dátum |
|---|--------|----------|-------|
| 1 | "At $5/month this is a no-brainer. I was paying my bookkeeper $150/hour to do what CentSense does automatically." | centsense.app | 2026 |
| 2 | "The Schedule C categorization is the killer feature. Every expense already has the right line number." Found $1,200 missed deductions | centsense.app | 2026 |
| 7 | "The Xero integration alone is worth every penny. I snap a photo, and it's automatically categorized and synced." | receiptreader.ai | 2026 |
| 12 | "There are a few apps that want me to give them access to read my email... I always say no to this." | r/privacy | 2022 |

### Top 3 Pattern (freq × intensity)

1. **🎯 Tax-kategorizálás = aha moment (legfőbb fizető trigger)** — nem a scanért fizetnek, hanem a Schedule C / ÁFA auto-besorolásért. Mindenhol "killer feature", $1,200–$3,200 visszanyert levonás. ReceiptLens ma nincs adókategória — **legnagyobb gap**.
2. **🔒 Privacy / Data sovereignty = monetizálható USP** — self-hosted vs "data hostage" cloud, AppSumo $9 lifetime deal modell működik, r/selfhosted keresi. ReceiptLens **egyetlen self-hosted** a piacon — USP.
3. **⚡ QuickBooks/Xero export = free→paid küszöb** — "The Xero integration alone is worth every penny", "drop them on Dext". Free = scan+local, Paid = sync.

**Pro tier lenyomás (VOC):** $5–8/hó solo, $5/user/mo SMB (Expensify Collect $5, Zoho $3, CentSense $5). Plafon $10/hó felett churn.

---

## 2) Competitor Pricing — 6 versenytárs (részletes: `/home/zoltan/receiptlens-competitor-pricing.md`)

| Versenytárs | Free | Entry Paid | Mid | API | Self-hosted |
|-------------|------|------------|-----|-----|-------------|
| **Expensify** | 25 scan/hó | **$5/user/hó** Collect | $9/user/hó Control (kártyával fele) | — | ❌ |
| **Veryfi** | 100 doc/hó | $19.99/hó app | **$500/hó** API ($0.08/receipt, $0.16/invoice) | ✅ $500 min | ❌ |
| **Klippa/Doxis** | Trial | **€5/user/hó** | €6/user/hó | quote | ❌ |
| **Dext** | Trial | **$25.21/hó** (250 doc, 5 user) | scaled $200+ | — | ❌ |
| **Zoho Expense** | 3 user | **$3/user/hó** | $5/user/hó | Zoho API | ❌ |
| **Shoeboxed** | — | $9/hó (200 scan) | $29–79/hó | ❌ | ❌ |
| **ReceiptLens ma** | ✅ unlimited + 10 nyelv + offline | **$0** | — | ✅ $0/doc | **✅ egyedüli self-hosted + open-source + API + 10 nyelv + offline** |

**Gap — hol van rés (14 pont, 4 zöld):**

- 🟢 **Self-hosted/on-premise:** senki nem adja — ReceiptLens egyedüli. GDPR/HIPAA piac.
- 🟢 **Zero per-document cost:** Veryfi $800/hó 10K doc-nál, ReceiptLens $5–20/hó hosting.
- 🟢 **Open-source + API + multi-language:** Veryfi API $500/hó belépő — developer piac üres.
- 🟡 **AI OCR accuracy:** Tesseract ~85–92% vs Veryfi 99% — vision OCR zárja, de API költség.
- 🟡 **Accounting integrations, workflow (approval/policy), mobile polish** — hátrány, de pótolható.

**Pozicionálás javaslat versenytárs kutatásból:** "The open-source, self-hosted alternative to Veryfi's API" — Privacy-conscious SMB, developer, EU/GDPR.

---

## 3) JTBD + Vitamarket angle (citrus turmix bolt, citrus bolt, fémhulladék udvar, barkács bolt)

**Jobs (milyen munkát végeznek nyugtákkal):**

1. *"Amikor jön az adóbevallás, szeretném egy kattintással exportálni a kategorizált kiadásokat, hogy ne kelljen egy vasárnapot a könyvelővel tölteni."* — Trigger: április, Alternatíva: cipős doboz + $150/óra könyvelő.
2. *"Amikor befotózom a blokkot a boltban, szeretném azonnal látni, jó áron vettem-e, hogy ne verjenek át."* — Trigger: pénztár, Alternatíva: fejben jegyzet.
3. *"Amikor a könyvelőm kéri az anyagot, szeretném egy linkkel megosztani, ne emailben küldözgessek PDF-et."* — Trigger: hó vége.

**Vitamarket jel:** EAN/vonalkód + vevő + dátum + ár pontosan ismert Vision Pro/Lens-szel — ebből **Barcode Price History & Store Comparison** jön (EAN → ár-történet + bolt-összehasonlítás). Zavvy/Julyu validált: barcode scan → kosár → ár-összehasonlítás ($287/hó megtakarítás ígéret).

---

## 4) Összehasonlító tábla — 3 megközelítés (B súlyozással)

| Szempont | A) Tax Pro Pack (kategória + export + report) | B) Vision Pro OCR (blurry/handwritten upsell) | C) Price Intelligence (barcode + ár-történet) |
|----------|-----------------------------------------------|----------------------------------------------|----------------------------------------------|
| Leírás | Schedule C / ÁFA auto-tag + deduction tracker + audit-ready PDF + QBO/Xero sync + accountant invite | Vision AI olvas elmosódott/kézírást, Pro-ban unlimited, Free-ben Tesseract cap | EAN scan → ár-történet per bolt, "túl drága" alert, kosár-összehasonlítás |
| VOC bizonyíték | #1, #2, #7, #9 — "killer feature", $1,200–3,200 | aiScanDesc már ígéri ("Pro plan"), de ma nem él | Zavvy/Julyu $287/hó, nincs self-hosted |
| Competitor gap | Mindenki adja, ReceiptLens nem — legnagyobb gap | Veryfi $500/hó, ReceiptLens $0/doc | Nincs self-hosted ár-összehasonlító |
| Lean | Közepes (BE kategória-szótár + PDF) | Kicsi (API key + cap) | Nagy (EAN DB + crawler) |
| Bevétel B | **Magas** — $5–8/hó konverzió trigger | **Közepes-magas** — upsell, de költség is | **Alacsony-közepes** — niche |
| Kockázat | Adó-jog régiónként | API költség / hallucináció | Adatfrissítés |

**Döntési javaslat B-re:** **A > B > C** — A a fizető küszöb, B a minőségi upsell, C a későbbi differentiator.

---

## 5) RICE scoring — 5 feature, B (bevétel) súlyozással

| # | Feature | Reach (user/hó) | Impact (0.25–3) | Confidence % | Effort (hét) | **RICE** = R×I×C/E | MoSCoW | Tier |
|---|---------|-----------------|-----------------|--------------|--------------|-------------------|--------|------|
| 1 | **Tax Auto-Categorization + Deduction Tracker + Audit PDF** (Schedule C / ÁFA, sor-szám, éves megtakarítás dashboard, PDF) | 800 | 3.0 | 80% | 5 | **384** | Must | **Pro $5–8/hó** |
| 2 | **Vision AI OCR Pro** (blurry/kézírást csak Pro unlimited, Free 25 scan/hó cap — Expensify parity) | 1000 | 2.0 | 70% | 4 | **350** | Must | **Pro $5–8/hó** |
| 3 | **QBO / Xero Direct Sync + Accountant Invite Link** (export már van CSV, direct sync a fizető) | 600 | 3.0 | 85% | 6 | **255** | Should | **Pro $5–8/hó** |
| 4 | **Family 5+ + Encrypted Cloud Backup (opt-in S3)** (privacy monetization, YNAB 6 fő modell) | 400 | 1.5 | 75% | 3 | **150** | Could | Pro $5–8/hó add-on |
| 5 | **Barcode Price History & Store Comparison** (EAN → ár per bolt, kosár-összehasonlítás, vitamarket pilot) | 500 | 2.0 | 60% | 5 | **120** | Won't now | Későbbi Pro+ |

**Számítás:** pl. #1: 800×3.0×0.8/5=384. **Top 3 B-re: #1, #2, #3** (mind Pro $5–8/hó-ba fér, együtt a teljes free→paid híd).

**Effort becslés alapja:** #1: BE szótár + FE dashboard + reportlab PDF (5h), #2: vision provider + cap + quota (4h), #3: OAuth + QBO/Xero API + invite (6h) — mind 400 sor/file limit betartásával.

---

## 6) Javaslat — Top 3 részletesen (B)

### #1 Tax Auto-Categorization + Deduction Tracker (RICE 384)
- **What:** Minden tételhez `tax_category` (US Schedule C line, EU ÁFA kulcs 0/5/18/27%, DE USt), `deduction_tracker` (éves megtakarítás $), `audit_pdf` (kategóriánként összesítve).
- **Why:** VOC #1 pattern — aha moment, $1,200–3,200, accountant "shocked". Competitor gap #6 — ReceiptLens nem adja.
- **Pricing:** Free: scan+local; Pro $5–8/hó: auto-tag + tracker + PDF. Éves $49 lifetime deal AppSumo-n validált.
- **Proof:** CentSense $5/hó, TaxLens $3,200 — plafon tartva.

### #2 Vision AI OCR Pro (RICE 350)
- **What:** `aiScanDesc` már ígéri ("Vision AI reads blurry photos, handwritten amounts... Pro plan"). Free: 25 scan/hó Tesseract (Expensify parity), Pro: unlimited vision (GPT-4o / Gemini). Fallback Tesseract marad.
- **Why:** Tesseract 85–92% vs Veryfi 99% — minőség + monetizáció egyszerre. Zero per-doc vs $0.08/doc — upside.
- **Pricing:** Ugyanaz a Pro csomag — nem külön termék, hanem minőségi upsell a #1 mellé.

### #3 QBO / Xero Direct Sync + Accountant Invite (RICE 255)
- **What:** `Dext` minta: "drop them on Dext" — 1 kattintás QBO/Xero sync, accountant invite link (read-only), email receipt forwarding (ExpenseBot minta).
- **Why:** VOC #3 pattern — "worth every penny", free→paid küszöb. Competitor gap #6 — integrations table stakes.
- **Pricing:** Pro $5–8/hó része — nem külön, mert együtt adja a teljes export-hidat.

**Pro csomag így:** **$5–8/hó (vagy $49/év)** — #1+#2+#3 egyben = "Tax-ready + Vision + Sync". Free marad: unlimited? Nem — **Free 25 scan/hó + local storage** (Expensify 25 cap másolása — konverziót hajt, ma unlimited → nincs urgency).

---

## 7) Következő lépés — kanban + ADR

- **Kanban Gate:** zöld (0 aktív) — 3 task létrehozható.
- **Javasolt 3 kanban task (US+gui_flow szerződéssel, BH E2E `browser_helper` 1.35.0-val):**
  1. `US-TAX-01` Tax auto-tag + Deduction Tracker + Audit PDF (BE szótár, FE dashboard, PDF)
  2. `US-VISION-01` Vision OCR Pro cap (25 free, unlimited Pro, vision provider)
  3. `US-SYNC-01` QBO/Xero sync + accountant invite (OAuth, invite link)
- **ADR:** top 3-ra külön ADR (1 oldal/ADR) — `docs/decisions/ADR-004-tax-pro.md` stb. — stop-gate után GREEN.
- **Te döntöd el stop-gate-en** — melyik induljon először (javaslat: #1, mert legnagyobb RICE + revenue trigger).

## 8) Forrás-ledger (grounded-citations)

- VOC: `/tmp/receipt-lens-voc.md` — 18 idézet, Trustpilot 5, App landing 7, Reddit 3, LinkedIn/Blog 3
- Competitor: `/home/zoltan/receiptlens-competitor-pricing.md` — 6 versenytárs, 7 szekció, 14 gap
- JTBD: `task-2.log` + Zavvy/Julyu/Rocket Money web_search snippet-ek
- Minden URL élő, dátummal — `grounded-citations` ledger kiegészíthető `~/.hermes/skills/research/grounded-citations/scripts/sources.py`-jal.

## 9) Korlátok & kockázatok

- Reddit API 403 + web_extract gateway 502 — Exa snippet fallback, 3+ platform így is teljesítve.
- JTBD agent max_iterations truncate — vitamarket EAN angle szintézisben pótolva (Vision Pro/Lens EAN ismert).
- Tax kategóriák régiónként (US/EU/HU/DE/RO...) — MVP US Schedule C + HU ÁFA 27/18/5/0, többi iteráció.
