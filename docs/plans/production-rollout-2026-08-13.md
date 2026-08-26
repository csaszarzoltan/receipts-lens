# ReceiptLens élesítés — receipts.allthezoo.com

**Dátum**: 2026-08-13 · **Státusz**: Terv v3 (AI-scan = jövőbeli fizetős) · **Becsült munka**: fél nap

> **Frissítés (2026-08-26) — Fázis 1 KÉSZ**: `.env` éles (chmod 600, gitignored,
> nincs vision-key), backend systemd-ként fut (`receipts-lens-api.service`,
> 127.0.0.1:8130, health/ready 200), napi SQLite-backup cron 03:17 UTC
> (7 nap retention, script: `scripts/backup-sqlite.sh`), frontend prod-build
> zöld (`NEXT_PUBLIC_API_BASE_URL=https://receipts.allthezoo.com/api`,
> BUILD_ID `hzKabDfs8mzHqnPuTWusp`). AI-scan gate élőben ellenőrizve:
> upgrade-prompt jelen, AiScanToggle nincs renderelve, localhost-ref sincs a
> client chunkokban. ⚠️ Tanulság: `npm run dev` smoke-test törli a `.next`
> prod-buildet — dev-smoke után mindig újra `next build`. Következik: Fázis 2–3
> (frontend systemd + Caddy block + Cloudflare DNS/SPF/DKIM).

## Kiinduló állapot (mérve)

- Kód: HEAD `0f90207`, pytest **1452 passed**, `next build` **zöld**, ruff tiszta
- Auth: magic link + családi meghívók kész; SMTP-kliens beépített (`RECEIPTLENS_SMTP_*`)
  — de `RECEIPTLENS_AUTH_BASE_URL` defaultja `http://localhost:3000` → állítani kell
- OCR: Tesseract 5.3.4 telepítve; AI-vision útvonal API-key-hez kötött
- Minták a szerveren: `mealmind-api.service` + `mealmind-frontend.service` (systemd,
  hardeninggel), Caddy-block a `mealmind.allthezoo.com`-hoz (security headerek,
  `/api/*` → backend, többi → frontend) — ezekről másolunk
- DNS: allthezoo.com Cloudflare mögött van
- Szabad portok: **BE 8130**, **FE 3300**

## Fázis 0 — Döntések

| # | Döntés | Állapot |
|---|---|---|
| D1 | Subdomain | ✅ **`receipts.allthezoo.com`** (user, 2026-08-13) |
| D2 | Portok | BE 8130, FE 3300 |
| D3 | SMTP provider | ✅ **Resend** (SMTP: smtp.resend.com:587, feladó noreply@allthezoo.com) — API key beszerzés alatt |
| D4 | Cloudflare proxy | ✅ **DNS-only** (szürke felhő) — Caddy intézi a TLS-t |

### D3 indoklás — miért Resend?

- Beépített SMTP-kliensünk szabvány SMTP-t beszél → a Resend-nek van SMTP interfésze
  (`smtp.resend.com:587`, user=`resend`, jelszó=API key) — nulla kódváltozás
- Feladó: `noreply@allthezoo.com` — profibb, mint egy @gmail.com feladó;
  SPF+DKIM rekordok egyszeri beállítása a Cloudflare-ben
- Ingyenes tier: ~100 e-mail/nap — bétaszintre bőven elég
- Alternatíva (ha nem akarunk új fiókot): Gmail app-password (5 perc) — de gmail-es
  feladóval és a Google spam-politikájának kitettséggel

### D4 indoklás — miért DNS-only?

- Caddy automatikus Let's Encrypt tanúsítványt kap (HTTP-01 challenge átjut)
- Narancs-felhővel a challenge nem jut át → origin-cert kellene + dupla TLS réteg
- Proxy később is bekapcsolható (DDoS/WAF igény esetén), addig egyszerűség

## Fázis 1 — Production build + konfiguráció

1. `/home/zoltan/receipts-lens/.env` (gitignored, chmod 600):
   - `RECEIPTLENS_ENV=production` ⚠️ hatása: `/docs`+`/redoc` kikapcs,
     **demo header-auth kikapcsol** (csak valódi session-token fogadott!) — ezért
     kötelező az éles smoke-test a magic-link flow-ra
   - `RECEIPTLENS_AUTH_BASE_URL=https://receipts.allthezoo.com`
   - `RECEIPTLENS_ALLOWED_ORIGINS=https://receipts.allthezoo.com`
   - `RECEIPTLENS_SMTP_ENABLED=1` + `RECEIPTLENS_SMTP_HOST=smtp.resend.com`,
     `PORT=587`, `USER=resend`, `PASSWORD=<resend-api-key>`,
     `FROM=noreply@allthezoo.com`
   - 📝 **AI-scan (vision LLM) — JÖVŐBELI FIZETŐS FUNKCIÓ**: kulcs NEM kerül bele
     az éles `.env`-be. Az OCR alapból Tesseracttal fut. Az AI-scan kapcsoló a
     frontendben/kódban marad, de max `coming_soon` / upgrade-promptként jelenik
     meg (l. bővebben a végjegyzetet).
2. Frontend production build:
   `NEXT_PUBLIC_API_BASE_URL=https://receipts.allthezoo.com/api npm run build`
   (dev mód helyett `next start` — egyben a memória-problémát is megoldja: 545 MB → ~60 MB)
3. Backend: `.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8130` (1 worker elég induláshoz)
4. SQLite: fájl helye rögzítve + **backup cron** (naponta, `sqlite3 .backup`, 7 nap retention)

## Fázis 2 — systemd szolgáltatások

5. `/etc/systemd/system/receipts-lens-api.service` + `receipts-lens-frontend.service`
   — a mealmind egységek másolata (User=zoltan, NoNewPrivileges, PrivateTmp,
   Restart=always, EnvironmentFile), portokkal 8130/3300
6. `systemctl daemon-reload && enable --now` + `journalctl` ellenőrzés

## Fázis 3 — DNS + Caddy

7. Cloudflare: A record `receipts` → VPS IP (**DNS-only**)
8. E-mail kézbesítéshez (Resend): SPF + DKIM TXT/CNAME rekordok az allthezoo.com zone-ban
9. Caddy block a mealmind-mintáról:
   - ugyanaz a CSP/security-header szett (BUG-S2/S4 tapasztalat beépítve)
   - `/api/*` → `127.0.0.1:8130`, `/health` → 8130, minden más → `127.0.0.1:3300`
10. `caddy reload` ⚠️ éles szolgáltatás (mealmind is rajta) — validálás előbb: `caddy validate`

## Fázis 4 — Éles smoke-test (go/no-go)

11. `https://receipts.allthezoo.com/health` → 200; frontend betölt
12. **Magic-link E2E valós e-maillel**: kérés → e-mail megérkezik (SPF/DKIM pass) →
    link → belépés (production auth-ág: header-fallback NEM működik — csak session)
13. Nyugta-feltöltés OCR-rel + review-flow mentés
14. Rate-limit él (61. kérés 429), security headerek a válaszban
15. Sötét mód + hu/en nyelvváltás production builden
16. Monitoring: egyszerű uptime-cron (health 200?) + hibanapló-watch

## Kockázatok / nyitott kérdések

- ⚠️ **OCR terhelés**: BUG-009 maradék (2× Tesseract 300s+ terhelten) — shared VPS-en
  a mealmind mellett figyelni kell; induláskor max 1-2 párhuzamos OCR
- **Session-store memóriában van** → restart kijelentkeztet; elfogadható béta-szinten,
  később DB-be

## Végjegyzet — AI-scan (jövőbeli fizetős funkció)

Az **AI-scan** (vision LLM-es nyugtaleolvasás, jobb pontosság összetett számlákon)
élesben **nem aktivált**; az OCR kizárólag Tesseracttal fut. Döntésed szerint:

> *Legyen megjegyzés, hogy a jövőben a fizetős verzió része.*

Ezért:
- Az éles `.env`-be **nem kerül vision-LLM API-key**.
- A frontend `ai_scan` paraméter/kapcsoló bennmarad a kódban, de éles környezetben
  **upgrade-promptot** mutat („Hamarosan: AI-scan a Pro csomagban") vagy rejtve
  marad — fejleszti, hogy a feature-flag a `RECEIPTLENS_FEATURE_AI_SCAN` env-en múlik
  (default: off élesben).
- A kanban chain-ben „AI-scan fizetős mögé zárása" külön task lesz (Pro plan
  bevezetésekor), itt most csak a note+dokumentálás történik.

## Szállítás

Kanban chain (micro-saas-lab): infra-lépések (Fázis 1–3) developer-task,
smoke-test (Fázis 4) pre-tester/tester task, dokumenter frissíti a README-t.
Az SMTP-kulcs megérkezéséig a chain az infra-részig halad, utána blokkol.
