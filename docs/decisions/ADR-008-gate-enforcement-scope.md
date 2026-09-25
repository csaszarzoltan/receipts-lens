# ADR-008: A VERITAS gate kényszerítő hatása — mit véd, és mit nem

> Az [ADR-007](/ZOO/issues/ZOO-23) **indoklását fordítja meg** a független review-k
> (Critic [ZOO-26](/ZOO/issues/ZOO-26), QA [ZOO-27](/ZOO/issues/ZOO-27)) alapján.
> Az ADR-007 döntése (a `.githooks/pre-commit` legyen az egyetlen lokális gate) **érvényben
> marad**; az indoklás egy része téves volt.

- **Dátum:** 2026-09-25
- **Státusz:** accepted
- **Szerző:** Architect
- **Kanban:** ZOO-23 (nyitó), javítások: ZOO-28, ZOO-30, ZOO-31, ZOO-32

## Kontextus

Az ADR-007 a `pre-commit` framework bevezetése ellen **a duplikáció-elvre** hivatkozott:
„a CI már telepíti a ruff-ot és futtatja a teljes láncot, újabb konfig = két divergens
minőségkapu". Mindkét független review ezt **cáfolta**, és reprodukcióval igazolta.

### A duplikáció-elv fordítva áll (BLOCKER-1)

A CI `verify_diff` **tiszta checkouton üres diffet néz** (`get_git_diff_files` a
`git status --porcelain` listájából olvas, `veritas_gate.py:168-196`; a
`VERITAS_DIFF_BASE` csak a szöveges diff-et befolyásolja, **nem** a fájllistát), és az
üres fájllista **early-return `True`**-t ad **a secret-scanner előtt** (`:336-338`).

Empirikus bizonyíték (tiszta klón, a commit már a HEAD-en, munkafa tiszta):

```
$ printf 'def test_no_metadata():\n    assert True\n' > tests/test_ci_violation.py
$ git add tests/test_ci_violation.py && git commit -m "ci probe"
$ git status --porcelain --untracked-files=no | wc -l     # -> 0
$ VERITAS_DIFF_BASE="origin/main" python3 scripts/veritas_gate.py \
      --verify-diff --verify-metadata --role auto
[INFO] No modified files detected in diff.
[INFO] No Python test files modified.
[OK] VERITAS Gate Check PASSED. Execution permitted.       # EXIT=0
```

**Egy commitolt metadata-sértés átmegy a CI-on.** A helyzet tehát nem „két kapu", hanem
**egy kapu és egy vak CI-ág** ugyanarra. A duplikáció-elv védte a VERITAS-t attól, hogy
mellé írjunk egy másodikat — ez a konklúzió jó volt, a **premissza** volt téves.

### A bekapcsolt gate a Test Author munkáját letiltja (BLOCKER-2)

A hook `--role "${VERITAS_ROLE:-auto}"`-val fut, `auto` → `implementer`
(`veritas_gate.py:687-690`), aminek deny-mátrixa tartalmazza a `tests/**`-t. Tiszta,
szabályos metadata-markerekkel ellátott teszt-commit:

| Role | Eredmény |
|---|---|
| `(unset → auto)` | `EXIT=1` — deny-matrix |
| `implementer` | `EXIT=1` — deny-matrix |
| `test_author` | **`EXIT=0`** |
| `spec_author` | `EXIT=1` — deny-matrix |
| `reviewer` | `EXIT=1` — deny-matrix |

A `spec_author` és `reviewer` **ugyanazt a sértést követik el implementerrel együtt** — a
`specs/**` és `.ai-execution/reviews/**` munkája is tiltva van. A `--no-verify` az egyetlen
út, tehát a gate-t *éppen azok* kerülik meg, akiknek a munkáját védelmezi.

### A deny-mátrix nem határ, hanem önbevallás

A role **önként deklarált env-var**, nem a commitelő identitásból származik
(egyetlen committer identity: `Zoltan Csaszar <csaszar.zoltan@gmail.com>`, 8/8 commit).
Ez mérhető megkerülés:

```
$ # implementer a saját tests/** tiltását írja fel
$ VERITAS_ROLE=test_author .githooks/pre-commit     # -> [PASS] EXIT=0
$ # sőt: a policy-fájlt MÁSA role-lal is átírhatja
$ printf '\n# tampered\n' >> .ai/permissions.yaml; git add .ai/permissions.yaml
$ VERITAS_ROLE=reviewer .githooks/pre-commit       # -> [PASS] EXIT=0
```

A `.ai/permissions.yaml` **nem** R3-érzékeny és **nem** konstitúciós (az R3-lista a
`.ai/constitutional-policy.yaml`-t védi, `veritas_gate.py:411`), így a **deny-mátrixot
magát** bármelyik agent átírhatja egy másik role önbevallásával.

## Döntés

1. **A role-felismerés a staged diffből történjen** (ZOO-28), **nem** env-var-ból. Ha a
   staged fájlok kizárólag `tests/**` alá esnek → `test_author`; kizárólag `specs/**` →
   `spec_author`; kizárólag `.ai-execution/reviews/**` → `reviewer`; egyébként az eddigi
   `implementer`. Ez a deny-mátrixot **kikényszeríti** ahelyett, hogy megkerülhető lenne:
   az `implementer` `tests/**` commitja így is bukik, csak most **szándék szerint**.
   Az env-var **override-ként megmarad** (explicit escape-hatch), de a hook fejlécében
   dokumentáltan.
2. **A deny-mátrix nem biztonsági határ** — ezt dokumentálni kell (hook fejléc + ADR), és
   a valódi kényszer a CI. A `.ai/permissions.yaml`-t ezért a `constitutional-policy.yaml`
   mintájára védelem alá kell vonni (ZOO-30).
3. **A metadata-gate a staged blobot olvassa**, nem a munkafát (QA F1), és a **CI
   `verify_diff` valódi diffet kapjon**, ne `git status`-t (QA F2) — ZOO-29. Enélkül a
   gate *nem azt vizsgálja, ami commitolódik*, és a `--no-verify` a CI-ellenőrzés egyetlen
   hatékony rétegét is kerüli meg (QA 3. kérdés).
4. **A `pre-commit` framework** nem vezet be — a duplikáció-elv **érvényben marad**, a
   javított premisszával. A staged hygiene hookok (trailing whitespace / staged secret-scan)
   valódi rést töltenének be, de **nem ebben a körben** (a 158 whitespace-es fájl rendbetétele
   előtt nem indokolt).

## Amit ez a döntés NEM állít

- Nem a `veritas_gate.py` CI-ág *policy-szabályainak* módosítása a kérdés; a fájllista-
  gyűjtés javítása. A szabályok változatlanok, ma épp csak nem érvényesülnek.
- Nem a `history-scan` fixture-ügye (QA F3) — az a `--check-all`/ZOO-17 hatóköre, külön ticket.
- A 87/92 metadata-marker-hiány **nem** hiba, amit most javítani kell: a **4** megjelölt
  teszt-fájl a gate-ek saját regressziós tesztje (`test_veritas_gate.py`,
  `test_precommit_gate_enforcement.py`, `test_security_gate_secret_scan.py`,
  `test_chat_query_049.py`) — azok a konkrét feltételeket viselik, amiket a gate maga
  kényszerít. Vagyis a marker-kötelezettség **már most is csak az újonnan írt teszteken
  érvényesül**, a meglévő 87 fájlon nem — a gate egy teszt szerkesztésekor a fájl
  egészét vizsgálja, nem csak az új sorokat (`verify_test_metadata` minden `def test_*`
  decorátorát újraolvassa). Ez rétegzett bevezetést igényel (külön ADR), nem egy
  commit-címkét.

## Következmény

- A `c5e5d6a` commit **önmagában nem volt regresszió okozója**: a deny-matrix blokkolása
  nem új, hanem a policy már meglévő viselkedése, amit a bekapcsolás felszínre hozott.
  A valódi regresszió a **kikapcsolt** CI-ág és a munkafát olvasó metadata-gate, amit a
  hook elfedett.
- A `core.hooksPath` lokális beállítás — a megbízhatósági lyuk megmarad (ZOO-31).
- A `--no-verify` a bekapcsolt gate mellett is megmarad megkerülésnek; ez dokumentált,
  elfogadott kockázat, **nem** biztonsági határ.

## Kapcsolódó

- Kód: `.githooks/pre-commit`, `scripts/veritas_gate.py`, `.github/workflows/veritas.yml`
- Korábbi: [ADR-007](/ZOO/issues/ZOO-23) (a döntés érvényes, az indoklás javítva)
- Gate-tulajdonos: Architect
