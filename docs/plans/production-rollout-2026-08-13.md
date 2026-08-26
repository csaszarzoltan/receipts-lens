# ReceiptLens élesítés — receipts.allthezoo.com

**Dátum**: 2026-08-13 · **Státusz**: Terv v2 (döntésekkel) · **Becsült munka**: fél nap

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
| D3 | SMTP provider | **Javaslat: Resend** (SMTP-interfészen, l. lent) — user jóváhagyás + API key kell |
| D4 | Cloudflare proxy | **Javaslat: DNS-only** (szürke felhő) — Caddy maga intézi a TLS-t |

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
   - vision LLM key (ha bekapcsoljuk az AI-scan-t; külön döntés — költség)
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
- **AI-scan költség**: vision LLM key budget-döntés előbb, mint feature
- **Session-store memóriában van** → restart kijelentkeztet; elfogadható béta-szinten,
  később DB-be
- **User-input függőség**: Resend fiók + API key (D3), Cloudflare A record (Fázis 3)
  — ezek nélkül csak az infra-lépések futtathatók

## Szállítás

Kanban chain (micro-saas-lab): infra-lépések (Fázis 1–3) developer-task,
smoke-test (Fázis 4) pre-tester/tester task, dokumenter frissíti a README-t.
Az SMTP-kulcs megérkezéséig a chain az infra-részig halad, utána blokkol.
