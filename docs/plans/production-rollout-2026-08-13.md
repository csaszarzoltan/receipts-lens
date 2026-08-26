# ReceiptLens élesítés — receipts-lens.allthezoo.com

**Dátum**: 2026-08-13 · **Státusz**: Terv (nem indult el) · **Becsült munka**: fél nap

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

## Fázis 0 — Döntések (nincs kód)

| # | Döntés | Javaslat |
|---|---|---|
| D1 | Subdomain neve | `receipts-lens.allthezoo.com` (repo-névvel konzisztens) |
| D2 | Portok | BE 8130, FE 3300 |
| D3 | SMTP provider | Resend API vagy Gmail app-password (a beépített SMTP-klienshez) |
| D4 | Cloudflare proxy | DNS-only (szürke felhő) → Caddy maga intézi a TLS-t (HTTP-01), mint mealmind |

## Fázis 1 — Production build + konfiguráció

1. `.env.production` a repóban NEM tároljuk; `/home/zoltan/receipts-lens/.env`
   (gitignored, chmod 600):
   - `RECEIPTLENS_ENV=production` ⚠️ hatása: `/docs`+`/redoc` kikapcs,
     **demo header-auth kikapcsol** (csak valódi session-token fogadott!) — ezért
     kötelező az éles smoke-test a magic-link flow-ra
   - `RECEIPTLENS_AUTH_BASE_URL=https://receipts-lens.allthezoo.com`
   - `RECEIPTLENS_ALLOWED_ORIGINS=https://receipts-lens.allthezoo.com`
   - `RECEIPTLENS_SMTP_ENABLED=1` + `SMTP_HOST/PORT/USER/PASSWORD/FROM`
   - vision LLM key (ha bekapcsoljuk az AI-scan-t; külön döntés — költség)
2. Frontend production build:
   `NEXT_PUBLIC_API_BASE_URL=https://receipts-lens.allthezoo.com/api npm run build`
   (dev mód helyett `next start` — egyben a memória-problémát is megoldja: 545 MB → ~60 MB)
3. Backend: `.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8130` (1 worker elég induláshoz)
4. SQLite: fájl helye rögzítve + **backup cron** (naponta, `sqlite3 .backup`, 7 nap retention)

## Fázis 2 — systemd szolgáltatások

5. `/etc/systemd/system/receipts-lens-api.service` + `receipts-lens-frontend.service`
   — a mealmind egységek másolata (User=zoltan, NoNewPrivileges, PrivateTmp,
   Restart=always, EnvironmentFile), portokkal 8130/3300
6. `systemctl daemon-reload && enable --now` + `journalctl` ellenőrzés

## Fázis 3 — DNS + Caddy

7. Cloudflare: A record `receipts-lens` → VPS IP (DNS-only)
8. Caddy block a mealmind-mintáról:
   - ugyanaz a CSP/security-header szett (BUG-S2/S4 tapasztalat beépítve)
   - `/api/*` → `127.0.0.1:8130`, `/health` → 8130, minden más → `127.0.0.1:3300`
9. `caddy reload` + tanúsítvány-ellenőrzés

## Fázis 4 — Éles smoke-test (go/no-go)

10. `https://receipts-lens.allthezoo.com/health` → 200; frontend betölt
11. **Magic-link E2E valós e-maillel**: kérés → e-mail megérkezik → link → belépés
    (production auth-ág tesztelve: header-fallback NEM működik — csak session)
12. Nyugta-feltöltés OCR-rel + review-flow mentés
13. Rate-limit él (61. kérés 429), security headerek a válaszban
14. Sötét mód + hu/en nyelvváltás production builden
15. Monitoring: egyszerű uptime-cron (health 200?) + hibanapló-watch

## Kockázatok / nyitott kérdések

- ⚠️ **OCR terhelés**: BUG-009 maradék (2× Tesseract 300s+ terhelten) — shared VPS-en
  a mealmind mellett figyelni kell; induláskor max 1-2 párhuzamos OCR
- **AI-scan költség**: vision LLM key budget-döntés előbb, mint feature
- **Cloudflare proxy ha mégis bekapcsolva**: akkor Caddy origin-cert kell (HTTP-01 nem jut át)
- Session-store memóriában van → restart kijelentkeztet; elfogadható béta-szinten, később DB-be

## Szállítás

A terv jóváhagyása után kanban chain: infra-lépések (1–9) egy developer-task,
smoke-test (10–15) pre-tester/tester task, dokumenter frissíti a README-t.
