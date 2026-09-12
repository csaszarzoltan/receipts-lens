# AI-chat ("kérdezd a számláidat") — deep-dive kutatás + SPEC-javaslat

**Dátum:** 2026-09-11 · **Feladat:** RL RESEARCH-1 (t_e8a9057c) · **Módszer:** VERITAS 1.1 (normatív alap)
**Repo-local kontextus:** 48 BRIEF + FEAT-001..048 SPEC; `receipts(tenant_id, payload JSON, blob_ref)` modell; OCR-szöveg + kategóriák léteznek (FEAT-007/011); keresés/szűrés (FEAT-008), költéselemzés (FEAT-013), anomália-jelzés (FEAT-033), adatmegőrzés/törlés (FEAT-025) adott.
**Élő-web megjegyzés:** `web_search` működött, de `web_extract`/böngészős oldal-kinyerés nem (extract-backend hiány, böngésző-daemon hiba). A verbatim idézetek ezért **kereső-snippetekből** származnak, nem teljes oldalszövegből — az érintett sorokat `[snippet]` jelöli. Kód/teszt érintetlen.

---

## 1) Versenytárs "ask your receipts" funkciók

| Szempont | Dext (IRIS) AI Assist | Sage AutoEntry / Copilot | Veryfi | Ramp Reporting Agent | Expensify Concierge (+MCP) |
|---|---|---|---|---|---|
| NL-kérdés saját adaton | Nincs bizonyíték; tanuló könyvelő-agent | Copilot chat: `"Show me invoice 123"` jellegű parancsok [snippet] | Nincs consumer-chat; API/SDK platform | Van: "ask questions about your company's spend in plain English" [snippet][2] | Van: "ask questions about receipts, purchases, and mileage — all in plain language" [snippet][4]; MCP-n át külső LLM-ből is [snippet][5] |
| Író-művelet (kategória, jóváhagyás) | Döntés-automatizálás javaslatokkal | Folyamat-automatizálás (emlékeztető, számlafeldolgozás) | Szabálymotor + fraud API-n át | Policy Agent, auto-kódolás | Van: "create, edit, categorize, tag, approve, and reject expenses using plain language" [snippet] |
| Proaktív insight | Automatizálási javaslatok ("suggests ways you can automate") [snippet][1] | Anomália-figyelés ("monitoring the books for anomalies") [snippet] | InSights üzleti intelligencia | Charts + insights válaszban [snippet][2] | "analyze spend", quarterly flux analysis [snippet] |
| Erősség vs ReceiptLens | Könyvelőirodai workflow-mélység | Számviteli compliance-bizalom | 99%+ extraction-pontosság, fejlesztői platform | NL-reporting + vizualizáció egyben | Legteljesebb író-chat + nyílt MCP-réteg |
| Gyengeség / gap | Nincs publikus NL-lekérdező chat; SMB-háztartás helyett könyvelő-fókusz | AutoEntry önmagában csak capture+sync, chat nincs | Nincs végfelhasználói chat-felület | Vállalati kártya-költés fókusz, nem háztartási nyugta | Vállalati expense-fókusz; PII külső LLM-be megy |

**Verbatim (snippet-forrásból):**

- Dext: "AI Assist helps automate the repetitive decisions and actions that slow bookkeeping down. It learns from how you work and suggests ways to apply that knowledge across future documents." [snippet][1] — URL: https://dext.com/us/business/product/dext-ai-assist-bookkeeping-agent
- Ramp: "Reporting Agent lets you ask questions about your company's spend in plain English, and instantly receive charts, insights, and answers. No need to build reports manually or dig through filters." [snippet][2] — URL: https://support.ramp.com/reporting-agent
- Ramp: "ask Ramp data questions in natural language on spend by team, vendor, or cardholder" [snippet][3] — URL: https://ramp.com/expense-management
- Expensify: "You can create, edit, and ask questions about receipts, purchases, and mileage — all in plain language." [snippet][4] — URL: https://help.expensify.com/articles/new-expensify/concierge-ai/Expense-Assistant
- Expensify MCP: "Through Expensify MCP, you can connect Expensify to Claude, ChatGPT, Cursor, or any MCP-enabled AI platform and ask questions about your expense data in natural language." [snippet][5] — URL: https://use.expensify.com/ai-expense-management
- Expensify: "Members can ask questions like 'What did I spend on travel last month?' or 'Which expense reports need my approval?'" [snippet][11] — URL: https://ir.expensify.com/news-releases/news-release-details/expensify-launches-mcp-ai-powered-expense-management
- Sage Copilot: "an AI trained on accounting, so you can trust you'll get reliable, compliant responses to financial queries" [snippet][6] — URL: https://www.sage.com/en-us/sage-copilot/
- Veryfi (platform-pozíció): "transaction-based… you pay for each document you push to the API" [snippet][10]; a Veryfi nem consumer-chat, hanem fejlesztői extraction-API — ez a ReceiptLens self-hosted USP-jét erősíti (ld. 2026-08-27 revenue-kutatás: Veryfi API $500/hó belépő, ReceiptLens $0/doc).

**Tanulság ReceiptLensnek:** az olvasó-chat (NL→SQL + aggregáció) iparági standard (Ramp, Expensify); az író-chat csak jóváhagyási kapukkal létezik; a nyílt MCP-réteg (Expensify-minta) olcsó-nagyhatású differenciáló lehet később.

---

## 2) Scope-opciók (adat-scope · UX · kockázat)

### (a) Olvasó-chat — összegzés / keresés NL-ben
- **Adat-scope:** csak saját `tenant_id`; `receipts.payload` (kereskedő, dátum, összeg, kategória, OCR-szöveg) + FEAT-013 aggregátumok. Csak SELECT-jellegű lekérdezés, determinisztikus SQL/aggregáció fut, az LLM csak fordít + fogalmaz.
- **UX:** chat-panel a Nyugták-listán (FEAT-008) belül; minden válaszban **forrás-hivatkozás** (nyugta-sor + összeg), "olcsó kérdés → determinisztikus válasz" elv; üres/kevés adat esetén explicit "nincs elég adat" (FEAT-033 REQ-033-04 minta).
- **Kockázat: R2** (új termékviselkedés/UI, VERITAS 1.1 §6). R3-közeli pont: promptba kerülő PII → ld. 4. fejezet. Hallucináció-kockázat ellen: LLM nem számol, csak a DB-eredményt verbalizálja; szám-eltérés = hibaág (Text-to-SQL guardrail-minta: csak olvasó statement mehet végre [14]).

### (b) Író-chat — kategória-javítás, szabály-állítás
- **Adat-scope:** (a) + írási jog `receipts.payload` kategória-mezőjére és FEAT-021 szabályokra; pénzügyi igazságot érint.
- **UX:** javaslat → diff-előnézet → **explicit megerősítés** (FEAT-020/FEAT-032 audit-minta: minden javítás verziózott, visszavonható).
- **Kockázat: R3** (pénzügyi adat írása, VERITAS §6: "security, privacy, pénzügy"). Kötelező **Human Authority** kapu minden írás előtt; bulk/migrációs írás tiltott; Runner `fail-closed` (csak jóváhagyott csomag hajtódik végre).

### (c) Proaktív insight — "ez a hónap kilóg"
- **Adat-scope:** (a) olvasó-scope + FEAT-033 anomália-jelek + FEAT-012 keretek; háttérben futó, ütemezett kiértékelés.
- **UX:** nem chat, hanem értesítés-kártya (FEAT-026 csatornákon) + "nyisd meg a chatben" mélylink az (a) felületre; zaj-kontroll: küszöb + "téves jelzés" visszajelzés (REQ-033-05).
- **Kockázat: R2** (új viselkedés + értesítési felület). R3-közeli: hamis riasztás pénzügyi döntést terelhet → konfidencia-küszöb + magyarázhatóság (REQ-033-02) kötelező; spammelés = validity-kockázat.

---

## 3) LLM-költség becslés

**Feltételezés/kérdés:** NL→SQL olvasó-chat: rendszerprompt + séma + kategóriák (~1 500 tok) + kérdés (~50) + minta-sorok (~500) ≈ **2 000 input / 300 output tok**. Forrásárak (2026-09):

| Modell | Ár (input/output per 1M tok) | Költség/kérdés | 100 user × 20 kérdés (2 000 q/hó) | 1 000 user (20 000 q/hó) |
|---|---|---|---|---|
| GPT-4o mini | $0.15 / $0.60 [7] | ~$0.0005 | **~$1/hó** | **~$10/hó** |
| GPT-4o | $2.50 / $10.00 [7] | ~$0.008 | ~$16/hó | ~$160/hó |
| Claude Haiku 4.5 | $1 / $5 [8][12] | ~$0.0035 | ~$7/hó | ~$70/hó |
| Gemini Flash (bevezető, 2026-12-31-ig) | $0.75 / $3.75 [13] | ~$0.0026 | ~$5/hó | ~$52/hó |

Számítás (mini): 2 000×0.15/1M + 300×0.60/1M = $0.00030+$0.00018 ≈ $0.0005. **Javaslat:** indulás GPT-4o mini / Gemini Flash-Lite sávban ($0.10–0.15 input [9]); nehéz érvelésre eszkaláció (Haiku/Sonnet). Self-hosted LLM: $0 API-díj, de GPU/hosting + gyengébb NL→SQL-minőség → csak R3-adatrezidens igényre. Író-chat (b) +30–50% tokentöbblet (diff + megerősítő kör); proaktív (c) kötegelt, user-arányos költség nélkül futtatható.

---

## 4) Privacy / R3

- **PII a promptban?** Igen, elkerülhetetlen (kereskedő, összeg, dátum = pénzügyi PII). Szabály: csak a kérdéshez szükséges tenant-szelet mehet ki; teljes OCR-blob és képek **soha** (NFR-025-04/008-04 PRIVACY-minta: "csak a feladat elvégzéséhez szükséges adat"). Prompt-naplózás tiltott vagy PII-maszkolt.
- **Hol fusson az LLM?** Alapértelmezett: külső API (költség-funkció). Feltétel: EU-adatrezidencia + "trainingre nem használható" (zero-retention/opt-out) szerződés; enélkül R3-blokkoló. Self-hosted opció roadmap-re (USP-erősítő a revenue-kutatás szerint).
- **Adatmegőrzés:** chat-előzmény = FEAT-025 hatálya: látható megőrzési idő, tulajdonosi törlés, törlési előnézet + külön megerősítés (REQ-025-02/03/04). Szolgáltatói oldalon tárolt prompt-log: max 30 nap vagy kikapcsolt.
- **Jóváhagyási kapuk (Human Authority):** (a) olvasás → nincs kapu, de tenant-scoping kötelező (FEAT-008 REQ-008-06 MUST NOT-minta); (b) minden írás → explicit megerősítés + audit-nyom (FEAT-020/032); (c) insight-küldés → küszöb + leiratkozás; háztartási megosztott adatoknál tulajdonosi kontroll (FEAT-025 ACT-025-02).

---

## 5) RICE-rangsor + javasolt SPEC-vázlat

| Opció | Reach | Impact | Confidence | Effort (hét) | RICE (R×I×C/E) | Hely |
|---|---|---|---|---|---|---|
| (c) Proaktív insight | 9 (passzív, mindenkit elér) | 5 | 8 (FEAT-033 alap kész) | 2 | **180** | 1 |
| (a) Olvasó-chat | 8 | 6 | 7 (Ramp/Expensify bizonyít) | 3 | **112** | 2 |
| (b) Író-chat | 5 | 8 | 5 | 6 | **33** | 3 |

**Javaslat:** RICE-győztes a (c), de önmagában nem adja a "kérdezd a számláidat" élményt, és nagyban ráépül a már SPEC-elt FEAT-033/026-ra. Ezért az első új SPEC az **(a) olvasó-chat** legyen (a headline-funkció + a (b) előfeltétele), a (c)-t pedig FEAT-033 kiterjesztésként, olcsó követőként szállítsuk. A (b) csak (a) után, R3-kapukkal.

### SPEC-javaslat: FEAT-049 — AI olvasó-chat a saját nyugták felett (R2)

- **REQ-049-01 [MUST]:** Felhasználóként természetes nyelven kérdezhetek a saját nyugtáimról (pl. "mennyit költöttem ételre júliusban?"), és összeget + forrás-nyugtákat kapok.
- **REQ-049-02 [MUST]:** A válasz minden számadatához megnyitható forrás-sor tartozik (nyugta-részlet, FEAT-008 szerint).
- **REQ-049-03 [MUST]:** A chat csak a saját háztartás adatait látja; más tenant adata nem szivároghat (FEAT-008 REQ-008-06 minta).
- **REQ-049-04 [MUST]:** Számítást kizárólag determinisztikus lekérdezés/aggregáció végez; az LLM eredményt nem "emlékezetből" mond.
- **REQ-049-05 [MUST]:** Kevés/nincs adat esetén a rendszer ezt expliciten jelzi, nem találgat (REQ-033-04 minta).
- **REQ-049-06 [MUST NOT]:** A chat nem módosíthat adatot, szabályt vagy megőrzési beállítást (írás = FEAT-050, R3, külön SPEC).
- **REQ-049-07 [ALWAYS]:** Sikertelen LLM/DB-hívás nem jelenhet meg válaszként; újrapróbálás + naplózott hibaág.
- **REQ-049-08 [CONCURRENCY]:** Párhuzamos kérdés nem okoz duplikált mellékhatást (olvasó-volta miatt triviális, de tesztelt).
- **NFR:** UI-visszajelzés 500 ms-on belül (NFR-008-01 minta); PRIVACY: promptba csak szükséges szelet, teljes OCR/kép soha; költség-plafon: kérdésenkénti token-limit + havi kvóta.
- **Acceptance:** (1) 10 mintakérdés-bank (HU/EN) ≥9 determinisztikus egyezés DB-aggregációval; (2) kereszt-tenant szivárgási teszt negatív; (3) prompt-log PII-mentességi ellenőrzés; (4) "nincs adat" + hibaág UI-teszt; (5) havi költség ≤ becslési sáv 1 000 kérdésen. **Kockázat: R2**, Human Authority nem kell (olvasó), de privacy-review igen.

## Sources — Források (ledgerből generálva)

Sources:

[1] Dext AI Assist bookkeeping agent — https://dext.com/us/business/product/dext-ai-assist-bookkeeping-agent
[2] Ramp Reporting Agent — https://support.ramp.com/reporting-agent
[3] Ramp expense management NL query — https://ramp.com/expense-management
[4] Expensify Expense Assistant — https://help.expensify.com/articles/new-expensify/concierge-ai/Expense-Assistant
[5] Expensify AI expense MCP — https://use.expensify.com/ai-expense-management
[6] Sage Copilot — https://www.sage.com/en-us/sage-copilot/
[7] OpenAI GPT-4o pricing — https://developers.openai.com/api/docs/models/gpt-4o
[8] Claude pricing official — https://platform.claude.com/docs/en/about-claude/pricing
[9] Gemini API pricing BenchLM — https://benchlm.ai/google/api-pricing
[10] Veryfi pricing — https://www.veryfi.com/pricing/
[11] Expensify MCP launch PR — https://ir.expensify.com/news-releases/news-release-details/expensify-launches-mcp-ai-powered-expense-management
[12] Anthropic pricing guide Finout 2026 — https://www.finout.io/blog/anthropic-api-pricing
[13] Google Cloud Gemini pricing — https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing
[14] AgentNLQ guardrails — https://arxiv.org/html/2605.19010v1

## Ledger-fájl

`/home/zoltan/.hermes/kanban/boards/receipts-lens/workspaces/t_e8a9057c/ledger.json` (14 forrás, `sources.py` kompatibilis).
