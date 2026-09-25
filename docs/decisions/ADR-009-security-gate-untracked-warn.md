# ADR-009: security-gate — warn-szint a nem trackelt secret-fájlokra (ZOO-29)

- **Dátum:** 2026-09-25
- **Státusz:** accepted
- **Szerző:** Architect
- **Kanban:** [ZOO-29](/ZOO/issues/ZOO-29) (döntés), kutatás: [ZOO-24](/ZOO/issues/ZOO-24),
  megvalósítás: `081d946` (már a `main`-en), tesztek: `tests/test_security_gate_secret_scan.py`
- **Kapcsolódó:** [ADR-008](/ZOO/issues/ZOO-23) (a gate kényszerítő hatása)

## Kontextus

A [ZOO-24](/ZOO/issues/ZOO-24) kutatási jelentése (teljes szöveg a ZOO-24 threadben)
rögzíti: mind a négy mainstream tool (gitleaks, detect-secrets, git-secrets,
trufflehog) git-objektumokon (index / diff / history) scanel; a nem trackelt
munkafa mindenhol explicit opt-in, a `.gitignore` egyben sem alap-scope
(gitleaks `--gitignore`: 2026-03-19-én is nyitott PR). Non-fatal warn-szintre
**nincs iparági precedens** — mindhárom alkalmazott mechanizmus non-zero exittel
jelez. A kutatás egyetlen támasztott állítása: **ne legyen silent pass**.

A nyitott döntés: **jelezze-e a nem trackelt, gyanús fájlokat a gate?**

## Döntés

**Igen — WARN stdout-ra, exit 0 (a gate PASS-ol).** A megvalósítás (`081d946`)
már a `main`-en van, ez az ADR a döntést rögzíti utólag.

- Trackelt (indexben lévő) secret-név/minta → **FAIL, exit 1**. Repo-tartalom,
  commit vagy stage pillanatában leak.
- Nem trackelt (ignored vagy sem) secret-név/minta → **WARN, exit 0**.
  Helyi állapot, amit a gate nem engedhet át — a figyelmeztetés a fejlesztőnek
  szól, nem gate-sértés.
- Nem git-környezet / használhatatlan `git ls-files` → **exit 2, fail-closed**,
  soha nem csendes PASS üres listából.

## Indoklás (döntés a kutatás alapján — a konklúzió az Architecté)

1. **A trackelt-only scope nem „kényelem", hanem szemantika.**
   A ticket eredeti sugallatával szemben a kutatás cáfolta, hogy a scope-szűkítés
   a lokális `.env` elnézése lenne: a trackelt fájlt a `.gitignore` nem rejti el,
   a *commit-then-ignore* esetet a scan elkapja. A gate szerződése a repo-tartalom —
   **Bounded Contexts**: a „secret a repóban" és a „secret a gépen" két külön fogalom,
   a gate csak az elsőre blokkolhat anélkül, hogy a fejlesztői checkouton
   használhatatlanná válna (ez volt a ZOO-24 bug).
2. **A warn a „ne legyen silent pass" minimuma, nem több.**
   Mivel nincs precedens a non-fatal warn-ra, a döntés a legkisebb reverzibilis
   lépés: a jelzés megvan (a fájl egy `git add -f`-re van a leaktől), a
   használhatóság megmarad. **Reversibility**: exit-0 warn-ról egy soros
   változtatás a blokkolás — fordítva (blokkolásról levenni) egy feloldott
   usability-bug árán menne.
3. **Amit elfogadunk (a tévedés ára):**
   - *commit-then-untrack* (`git rm --cached`): a secret a history-ben marad,
     a gate mégis PASS + WARN-t ad — **reprodukálva 2026-09-25**.
     Ez nem a warn-szint hibája: blokkoló warn-nal is csak a *jelenlegi* állapotot
     látnánk, a history-t nem. A lyuk a **history-scan hiánya**, ami a ZOO-17
     hatásköre ([ADR-008](/ZOO/issues/ZOO-23) F3-ként nevesíti, nem e döntésé).
   - `--directory`-összevonás: ignored könyvtárak belseje nem enumerált
     (a teszt `TEST-RL-V02-017` rögzíti) — a trackelt-ellenőrzést nem érinti.
   - Zaj: a helyi `.env`-vel rendelkező checkout minden futtatáskor WARN-t ír
     (a fejlesztői gépen verifikálva). Ez szándékos: a csend ára egy észrevétlen
     `git add -f` lenne.

## Amit ez a döntés NEM állít

- Nem írja elő a history-scant — az a ZOO-17 / [ADR-008](/ZOO/issues/ZOO-23) F3 hatóköre.
- Nem a VERITAS metadata-gate staged-blob olvasása (QA F1) és nem a CI
  `verify_diff` fájllistája (QA F2) — az a [ZOO-30](/ZOO/issues/ZOO-30) hatóköre.
- Nem változtat a `.githooks/pre-commit` hatókörén: a `security-gate.sh`-t ma semmi
  nem hívja (sem hook, sem CI) — kézi eszköz; a bekötése külön döntés, külön ticket.

## Következmény

- A viselkedést a `tests/test_security_gate_secret_scan.py` rögzíti
  (`TEST-RL-V02-012`: local `.env` → exit 0 + WARN;
  `TEST-RL-V02-013`: trackelt → exit 1). Aki szigorít, a tesztet is módosítja.
- Felülvizsgálat akkor indokolt, ha: (a) commit-then-untrack leak történik és a
  WARN nem előzte meg, vagy (b) a WARN-zaj miatt a fejlesztők leszoktatják magukat
  a gate futtatásáról — mindkettő a warn *értelmét*, nem a szintjét kérdőjelezi meg.
