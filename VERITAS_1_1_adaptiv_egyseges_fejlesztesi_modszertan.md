# VERITAS 1.1

## Adaptív, követelményvezérelt és bizonyíték-alapú autonóm szoftverfejlesztési módszertan

**Angol feloldás:** Verified Evidence-governed Requirements, Implementation, Testing and Autonomous Software Development  
**Verzió:** 1.1  
**Dátum:** 2026-09-09  
**Státusz:** Egységes, normatív módszertani alapverzió  
**Eredet:** Az AEGIS 2.1, az RVAD 1.1 és a VERITAS 1.0 adaptív továbbfejlesztése

---

## 0. Cél és központi elv

A VERITAS olyan teljes életciklusú fejlesztési rendszer, amelyben emberek, LLM-agentek és determinisztikus futtatók együtt dolgoznak. Az LLM kutathat, specifikálhat, tesztet és kódot készíthet, diagnosztizálhat és kritikát fogalmazhat meg, de saját munkájának sikeréről nem dönthet.

> A jóváhagyott követelmény meghatározza a kívánt viselkedést. A teszt futtatható módon bizonyítja a követelményt. Az implementáció a specifikáció és a helyes tesztek teljesítésére készül. A determinisztikus Runner ellenőrzi a folyamatot és az eredményt. Az ember ott dönt, ahol termékérték, jog, biztonság, jelentős kockázat vagy visszafordíthatatlanság mérlegelése szükséges.

### 0.1. Adaptív operációs alapelv

> A VERITAS mindig a legkisebb olyan kontrollkészletet alkalmazza, amely a változás kockázatához, bizonytalanságához, visszafordíthatóságához, kontextus-összetettségéhez és a végrehajtó bizonyított képességéhez mérten még hiteles bizonyítékot szolgáltat.

Ez a **kockázatarányos minimális elégséges bizonyítás** elve. Kizárja mind a szükséges kontrollok önkényes elhagyását, mind a maximális szigor mechanikus, gazdaságtalan alkalmazását.

### 0.2. Conformance és Validity

- **Conformance:** azt valósítottuk-e meg, amit a specifikáció előír?
- **Validity:** a helyesen megvalósított működés megoldja-e a valós felhasználói problémát?

A tesztek elsősorban a conformance-ot igazolják. A valós felhasználói eredmények, production jelek, support és incidensek a validity-t ellenőrzik.

---

## 1. Alkotmányos mag

A következő R4-szintű szabályokat agent vagy automatikus governor nem lazíthatja:

1. Az alkotmányos policy agent által nem írható.
2. A Governor saját hatáskörét nem bővítheti.
3. Hiányzó vagy hibás evidence nem siker.
4. Tiltott állapotátmenetet a Runner blokkol.
5. Érvénytelen vagy előírás szerint aláíratlan policyval a Control Plane nem indul.
6. Audit és evidence-integritás nem kapcsolható ki autonóm módon.
7. Kötelező emberi kapu nem csökkenthető autonóm módon.
8. Az Implementer nem módosíthatja a feladatát igazoló tesztet vagy specifikációt.
9. Production write csak explicit capabilityvel és szükséges jóváhagyással történhet.
10. A teljes regressziót nem helyettesítheti LLM-állítás.
11. Exploration prototípus nem emelhető közvetlenül production-kóddá.
12. Cache-elt evidence csak igazolt végrehajtási ekvivalencia mellett használható.

### 1.1. Policyrétegek

- **Constitutional Policy:** emberi, aláírt változtatás.
- **Governance Policy:** szervezeti kockázat és jóváhagyás.
- **Project Policy:** stack, parancsok, repository- és minőségi szabályok.
- **Operational Policy:** előre engedélyezett tartományban hangolható küszöbök.
- **Runtime Configuration:** automatikus beállítás a magasabb korlátokon belül.

### 1.2. Fail-closed módok

```yaml
runner_modes:
  NORMAL:
    writes_allowed: true
  READ_ONLY_DEGRADED:
    writes_allowed: false
    diagnostics_allowed: true
  QUARANTINED:
    writes_allowed: false
    human_intervention_required: true
  BOOTSTRAP_HALTED:
    process_started: false
```

---

## 2. Autoritatív források

Konfliktusnál az elsőbbségi sorrend:

1. alkalmazandó jog és alkotmányos policy;
2. jóváhagyott domain-invariáns;
3. jóváhagyott feature-specifikáció adott verziója;
4. acceptance scenario és tesztleképezés;
5. helyesnek validált futtatható teszt;
6. implementáció;
7. generált dokumentáció és LLM-összefoglaló.

A kód a jelenlegi viselkedés bizonyítéka, nem automatikusan a kívánt viselkedés igazsága.

---

## 3. Kanonikus artifactmodell

```yaml
artifact:
  id: ART-000123
  type: feature_specification
  schema_version: "1.1"
  subject: FEAT-023
  version: 3
  status: approved
  produced_by:
    role: spec_author
    actor_id: AGENT-SPEC-02
    execution_id: RUN-20260909-001
  based_on:
    - BRIEF-023@2
    - INV-CART-001@4
  policy_version: VERITAS-POLICY@1
  content_hash: sha256:...
  created_at: 2026-09-09T10:00:00Z
  approvals: []
```

A hash integritást, nem hitelességet bizonyít. Normatív artifacthoz séma, provenance, státusz, jogosult előállító és szükség esetén aláírás kell.

### 3.1. Stabil azonosítók

`PROB-*`, `BRIEF-*`, `INV-*`, `FEAT-*`, `REQ-*`, `NFR-*`, `UI-*`, `API-*`, `AC-*`, `TEST-*`, `ADR-*`, `TASK-*`, `RUN-*`, `FIND-*`, `REL-*`, `INC-*`, `POL-*`.

---

## 4. Követelmény- és termékartifactok

### 4.1. Problem Record

Rögzíti a problémát, az érintett felhasználót vagy rendszert, a jelenlegi és kívánt eredmény eltérését, az evidence-et, a bizonytalanságot és a következményt. Nem kényszeríthet rá idő előtt műszaki megoldást.

### 4.2. Research Artifact

Külső tény, változó technológia, felhasználói viselkedés vagy több reális alternatíva esetén szükséges. Tartalmazza a forrást, dátumot, reprodukálható bizonyítékot, opciókat, korlátokat és bizonytalanságokat. Kutatási következtetés csak specifikációs döntéssel válik követelménnyé.

### 4.3. Feature Brief

```markdown
# BRIEF-XXX: Cím
## Probléma
## Célcsoport és használati kontextus
## Kívánt, megfigyelhető eredmény
## Sikermérés
## Scope
## Non-scope
## Érintett rendszerek
## Kockázatok
## Bizonytalanságok
## Kapcsolódó evidence
```

### 4.4. Domain-invariáns

Több feature-re érvényes `[MUST]`, `[MUST NOT]`, `[ALWAYS]`, `[SECURITY]`, `[PRIVACY]`, `[CONCURRENCY]`, `[PERFORMANCE]` vagy `[ACCESSIBILITY]` szabály. Stabil ID, hatókör, tulajdonos és verifikációs stratégia kötelező.

### 4.5. Feature-specifikáció

Kötelező szerkezet:

1. cél és felhasználói eredmény;
2. kontextus és források;
3. scope és non-scope;
4. szereplők és előfeltételek;
5. funkcionális követelmények;
6. nem funkcionális követelmények;
7. UI-szerződés;
8. felhasználói és GUI-folyamat;
9. állapotmodell;
10. API-, esemény- és adatszerződés;
11. acceptance scenario-k;
12. tesztleképezés;
13. kockázatok és emberi döntések;
14. nyitott kérdések;
15. rollback és megfigyelhetőség;
16. Definition of Done.

A happy path, edge, error, mobil, accessibility, concurrency és security nem külön feature csak dokumentumszervezési okból.

---

## 5. SPEC READY Gate

Ellenőrzi:

- a stabil azonosítókat és verziókat;
- a megfigyelhető felhasználói eredményt;
- scope-ot és non-scope-ot;
- a követelmények tesztelhetőségét;
- happy, edge, error és recovery viselkedést;
- auth, privacy, concurrency és konzisztencia kérdéseket;
- UI-, API-, állapot- és adatszerződést;
- requirement-scenario-tesztszint kapcsolatot;
- a nyitott blokkoló kérdések hiányát;
- kockázatot, prototípust és emberi jóváhagyást.

Blokkoló hiány esetén `NEEDS_CLARIFICATION`, egyébként `SPEC_READY`. A futás az adott specifikációverzióhoz kötődik.

---

## 6. Kockázati osztályok

- **R0:** dokumentáció, formázás, bizonyítottan viselkedéssemleges változás.
- **R1:** kis, visszafordítható változás stabil oracle mellett.
- **R2:** új vagy módosuló termékviselkedés, API, UI vagy integráció.
- **R3:** security, privacy, pénzügy, breaking contract, migráció vagy magas következmény.
- **R4:** alkotmányos policy, autonómiahatár, evidence-integritás vagy emberi gate változása.

A Runner felfelé minősíthet automatikusan. Lefelé minősítéshez policy szerinti jóváhagyás kell.

---

## 7. Végrehajtási pályák

### 7.1. Exploration Path

Bizonytalanságcsökkentésre szolgál, nem kiadható kód előállítására.

Engedélyezett kimenet:

- eldobható prototípus;
- kutatási artifact;
- UX-jelölt;
- technikai spike;
- benchmark és megvalósíthatósági evidence;
- Brief-, követelmény-, API-, UI- vagy ADR-javaslat.

Tiltott:

- production release vagy merge;
- production write;
- irreverzibilis migráció;
- külön engedély nélküli valós személyes adat;
- prototípuskód közvetlen promotionje.

Kötelező kontroll: izoláció, szintetikus vagy engedélyezett adat, idő- és költségbudget, `DISPOSABLE_PROTOTYPE` jelölés, hipotézis, értékelési feltétel és explicit lezárás.

### 7.2. Clean-Room Promotion

Csak validált tudás emelhető át, kód nem.

```yaml
exploration_promotion_policy:
  direct_code_promotion: forbidden
  promotable_artifacts:
    - validated_research_finding
    - feature_brief
    - proposed_requirement
    - proposed_acceptance_scenario
    - proposed_api_contract
    - proposed_ui_contract
    - feasibility_evidence
    - benchmark_result
    - failure_catalog
    - boundary_condition
    - architecture_option
  non_promotable_artifacts:
    - prototype_source_code
    - prototype_dependencies
    - prototype_lockfile
    - prototype_migration
    - prototype_test_baseline
    - prototype_configuration
    - generated_patch
  production_implementation_requires:
    - approved_specification
    - standard_or_assurance_path
    - fresh_execution_workspace
    - independent_test_contract
    - verified_red_evidence
```

A Promotion Package nem tartalmazhat kódrészletet, patch-et vagy pszeudokódnak álcázott implementációt. A Runner külön workspace-t, forráseredet-ellenőrzést, hash-tiltólistát, R2–R3 infrastruktúrán AST-, tree-sitter- vagy token n-gram hasonlóságvizsgálatot alkalmazhat. A hasonlóság findingot indít, nem automatikus bűnösségi döntést.

### 7.3. Fast Path

R0 és megfelelő R1 változtatásokhoz. Feltétel a stabil oracle, rollback, korlátozott scope, változatlan auth/privacy/public contract és egészséges érintett komponens. Inline Change Contract, célzott teszt, policy szerinti regresszió és diff-evidence itt is kötelező.

### 7.4. Standard Path

Általános R1 és R2 változásokhoz. Teljes specifikáció, tesztkontraktus, execution packet, RED, célzott és teljes regresszió, traceability és független review.

### 7.5. Assurance Path

R3-hoz. További szakértői review, threat vagy hazard analysis, erősebb izoláció, migration rehearsal, rollback drill, dual control és fokozatos release írható elő.

### 7.6. Constitutional Change Path

R4 külön, ember által jóváhagyott és aláírt eljárás. Agent nem aktiválhatja önállóan.

### 7.7. Path Eligibility Oracle

Szigorúbb pályára emel például új dependency, publikus API, migráció, auth/privacy, váratlan visual diff, bizonyíthatatlan rollback, architecture-boundary változás vagy regresszióhiba esetén.

---

## 8. Állapotgép

```text
INTAKE
  OBSERVED -> PROPOSED

EXPLORATION
  EXPLORATION_PLANNED
  -> EXPLORING
  -> EXPLORATION_ASSESSED
  -> DISCARDED | CONTINUE_EXPLORATION | PROMOTION_PROPOSED
  -> PROMOTION_VALIDATED
  -> SPEC, közvetlen BUILD nélkül

SPEC
  RESEARCHING
  -> BRIEF_READY
  -> SPECIFYING
  -> SPEC_READY
  -> SPEC_EXECUTION_FROZEN

BUILD
  TEST_CONTRACTED
  -> ARCHITECTED
  -> PLANNED
  -> CONTEXT_FITNESS_VERIFIED
  -> RED_VERIFIED
  -> IMPLEMENTING

VERIFY
  TARGET_VERIFIED
  -> REGRESSION_VERIFIED
  -> TRACEABILITY_VERIFIED
  -> EQUIVALENCE_VERIFIED, ha cache használt
  -> REVIEWED
  -> RELEASE_READY
  -> RELEASED
  -> OBSERVING
  -> OBSERVED_OUTCOME
```

Minden átmenethez bemeneti artifact, gate, jogosult szerepkör, evidence és hibaviselkedés tartozik.

---

## 9. Szerepkörök és jogosultságok

- **Product Authority:** probléma, eredmény, prioritás és értékdöntés.
- **Researcher:** evidence és bizonytalanság, követelményjóváhagyás nélkül.
- **Spec Author:** tesztelhető specifikáció, kódmódosítás nélkül.
- **Architect:** ADR és boundary, a felhasználói eredmény felülírása nélkül.
- **Test Author:** teszt, metaadat és RED, termékkód módosítása nélkül.
- **Implementer:** minimális kód, teszt és spec módosítása nélkül.
- **Reviewer/Critic:** read-only ellenőrzés és finding.
- **Arbiter:** feloldatlan vita rendezése.
- **Runner:** determinisztikus végrehajtás és gate-döntés.
- **Human Authority:** termék-, jogi, security-, production- és alkotmányos döntés.

Default deny érvényes. A Runner ellenőrzi az allow/deny mintákat, normalizált útvonalat, symlinket, traversal kísérletet, végső Git diffet, provenance-t, dependencyt és secretet.

---

## 10. Execution Packet

```yaml
task_id: TASK-FEAT-023-02
feature: FEAT-023@3
risk_class: R2
execution_path: standard
objective:
  - REQ-003
  - REQ-004
authoritative_inputs:
  - .specs/features/FEAT-023/specification.md
  - .specs/domain/invariants.md
allowed_files:
  - src/cart/cart-service.ts
forbidden_files:
  - tests/**
  - .specs/**
tests_to_satisfy:
  - TEST-INT-023-01
commands:
  targeted:
    - npm test -- cart-clear
  regression:
    - npm test
    - npx playwright test
    - npm run lint
    - npm run typecheck
    - npm run build
stop_conditions:
  - spec_conflict
  - forbidden_file_required
  - security_decision_required
  - repair_budget_exhausted
```

A packet a legkisebb koherens, önállóan verifikálható változtatási egység, nem szükségképpen egyetlen requirement.

### 10.1. Context Fitness Gate

A packetet az adott modell empirikusan validált működési tartományához kell mérni.

```yaml
context_fitness:
  requirements_count: 3
  acceptance_scenarios_count: 7
  allowed_files_count: 8
  relevant_code_lines: 850
  dependency_hops: 4
  architectural_boundaries: 3
  public_contracts_affected: 2
  domain_invariants_count: 5
  estimated_input_tokens: 42000
  required_tool_roundtrips: 9
  ambiguity_findings: 1
  context_risk: high
```

```yaml
model_execution_profile:
  profile_id: MEP-IMPL-MEDIUM-04
  model_class: implementation-medium
  validated_limits:
    maximum_relevant_code_lines: 700
    maximum_allowed_files: 6
    maximum_dependency_hops: 3
    maximum_architectural_boundaries: 2
    maximum_requirements: 3
  observed_quality:
    first_pass_success_rate: 0.84
    mean_patch_iterations: 1.7
    scope_violation_rate: 0.02
  sample_size: 120
```

Kimenetek: `FIT`, `FIT_WITH_RETRIEVAL`, `SPLIT_REQUIRED`, `MODEL_UPGRADE_REQUIRED`, `ARCHITECTURE_CLARIFICATION_REQUIRED`, `HUMAN_PLANNING_REQUIRED`.

A profil dinamikus. Romló sikerarány, javítási iteráció vagy diagnosztikai idő esetén a Governor csökkenti a limiteket. Bővítéshez új kalibráció kell.

### 10.2. Workflow Compression és fragmentáció

Koherens requirementek, célzott tesztek és validációk kötegelhetők, ha nem vész el a traceability, kockázati határ vagy rollback. A teljes regresszió a packet célzott GREEN állapota után alapértelmezetten egyszer fut.

`SPLIT_REQUIRED` esetén a bontási terv kötelezően tartalmazza:

- a közös invariánsokat;
- az átadási szerződéseket;
- dependency- és sorrendi feltételeket;
- cross-packet integration scenario-t és tesztet;
- végső közös regressziót és traceabilityt.

---

## 11. Tesztstratégia

```text
requirement coverage = teszttel lefedett kötelező requirement / összes kötelező requirement
verification coverage = aktuális futásban vagy ekvivalenciával bizonyított requirement / összes kötelező requirement
```

Alapértelmezett release-cél mindkettőnél 100 százalék.

A legalacsonyabb megfelelő tesztszintet kell használni: unit, contract, integration, E2E, vizuális, performance, security, resilience vagy canary.

Kötelezően értékelendő, ahol releváns: happy path, edge, hiba, recovery, auth, privacy, validáció, idempotencia, concurrency, adatkonzisztencia, accessibility, mobil, vizuális szerződés, kompatibilitás, teljesítmény, rollback és migráció.

### 11.1. RED Evidence

A tesztnek érvényesnek, felfedezhetőnek és ténylegesen futottnak kell lennie, továbbá a hiányzó vagy hibás funkció miatt kell buknia. A tesztfájl puszta létrejötte nem bizonyíték.

### 11.2. Kötelező regresszió

Minden módosítás után célzott teszt fut. Célzott GREEN után a projektprofil szerinti teljes regresszió, lint, typecheck, build és security scan ténylegesen lefut. Ezt summary nem helyettesíti.

---

## 12. Triage és javítás

Kategóriák:

- `IMPLEMENTATION_ERROR`;
- `TEST_ERROR`;
- `SPEC_CONFLICT`;
- `ENVIRONMENT_ERROR`;
- `POLICY_VIOLATION`;
- `ORACLE_FAILURE`;
- `RISK_ESCALATION`.

Vizsgálati sorrend: specifikáció, teszt, kód, környezet, policy.

```yaml
repair_policy:
  max_patch_iterations: 5
  max_environment_retries: 1
  max_duration_minutes: 30
  on_limit_reached: preserve_and_escalate
  on_policy_violation: stop_and_quarantine
```

---

## 13. Automatikus Traceability Graph

```text
Problem
  -> Brief
  -> Feature Specification Version
  -> Requirement
  -> Acceptance Scenario
  -> Declared Test
  -> Discovered Test
  -> Executed Test Result
  -> Evidence
  -> Review Finding
  -> Gate Decision
  -> Release
  -> Runtime Signal
```

A gráf a specifikációból, strukturált tesztmetaadatból, gépi tesztriportból, execution packetből, commitból, manifestből, review-ból és release-eseményből generálódik. Fájlnév és commitüzenet csak migrációs fallback.

A gate blokkol hiányzó teszt, nem futott vagy skipped bizonyíték, ismeretlen ID, commit- vagy specverzió-eltérés, ellentmondó forrás, sémahiba vagy elégtelen coverage esetén.

---

## 14. Determinisztikus Gate-rendszer

1. Exploration Safety Gate.
2. Clean-Room Promotion Gate.
3. Change Readiness Gate.
4. Spec Readiness Gate.
5. Context Fitness Gate.
6. Pre-test Safety Gate.
7. RED Gate.
8. Targeted GREEN Gate.
9. Full Regression Gate.
10. Traceability Gate.
11. Execution Equivalence Gate, ha cache van.
12. Independent Review Gate.
13. Final Safety Gate.
14. Release Gate.
15. Process Proportionality Gate.

### 14.1. Process Proportionality Gate

```text
control overhead ratio = kontrollidő / produktív build- és tesztidő
artifact overhead ratio = artifactköltség / teljes változtatási költség
duplicate verification ratio = új evidence nélküli ismétlés / összes ellenőrzés
human escalation precision = valódi emberi döntés / összes eszkaláció
evidence reuse rate = biztonságos reuse / reuse-ra alkalmas evidence
```

```yaml
process_proportionality_policy:
  review_triggers:
    - condition: risk_class_in_R0_R1
      control_overhead_ratio_greater_than: 2.0
      minimum_sample_size: 20
    - condition: duplicate_verification_ratio_greater_than
      threshold: 0.25
    - condition: human_escalation_precision_below
      threshold: 0.40
      minimum_sample_size: 15
  automatic_response:
    - create_process_review_proposal
    - identify_duplicate_gates
    - recommend_packet_rebatching
    - evaluate_fast_path_candidates
    - evaluate_evidence_cache_candidates
  forbidden_automatic_response:
    - remove_constitutional_gate
    - lower_required_coverage
    - waive_security_review
    - weaken_provenance
```

A kapu trendet és minimum mintanagyságot értékel. Review-t vagy optimalizálási javaslatot indít, de biztonsági szabályt nem lazíthat automatikusan.

---

## 15. Evidence-integritás és cache

### 15.1. Execution Equivalence Proof

Korábbi PASS csak akkor használható újra, ha bizonyítottan ekvivalens a jelenlegi végrehajtással.

```yaml
cached_evidence:
  evidence_id: EVD-20260909-0042
  test_suite: unit-cart
  result: passed
  equivalence_inputs:
    source_tree_hash: sha256:...
    transitive_dependency_hash: sha256:...
    lockfile_hash: sha256:...
    build_configuration_hash: sha256:...
    runtime_identity: python-3.12.14
    container_image_digest: sha256:...
    test_definition_hash: sha256:...
    fixture_hash: sha256:...
    schema_hash: sha256:...
    relevant_policy_hash: sha256:...
    environment_contract_hash: sha256:...
  reusable_when:
    impact_analysis_status: unaffected
    equivalence_inputs_unchanged: true
    maximum_age_not_exceeded: true
    policy_allows_reuse: true
```

Reuse módok:

- `DIRECT_REUSE`;
- `IMPACT_QUALIFIED_REUSE`;
- `PARTIAL_REUSE`;
- `REUSE_FORBIDDEN`.

Runner R0–R1 szinten szűkebb fájl-, teszt- és lockfile-hash cache megengedhető, csökkentett bizonyítási erő jelölésével. R2–R3 szinten hermetikus image digest, tranzitív dependency, környezeti szerződés és policyhash kell.

Security, auth, privacy, migráció, concurrency és release-kritikus tesztnél a cache alapértelmezetten tiltott. A Final Safety Gate nem régi zöld státuszt, hanem jelenidejű ekvivalenciát keres.

### 15.2. Audit és manifest

A Runner append-only, lehetőség szerint hash-láncolt auditban rögzíti az állapotátmenetet, artifactot, capabilityt, parancsot, exit kódot, gate-et, approvalt, policyt, release-t és rollbacket.

A lezárt manifest összeköti a specifikáció- és policyverziót, commitokat, teszteket, coverage-et, findingokat, approvalt és artifacthasheket. A technikai `PASSED` nem azonos a merge vagy release döntéssel.

---

## 16. Autonomy Governor

A Governor a megbízhatóság alapján csökkentheti a capabilityt, packetméretet, Fast Path jogosultságot és javítási budgetet, vagy több review-t és evidence-et kérhet.

Nem bővíthet capabilityt, nem csökkenthet emberi gate-et, coverage-et vagy evidence-minimumot, és nem módosíthat alkotmányos policyt.

A modellprofil kalibrációja negatív visszacsatolás: tartós minőségromlásnál a validált packetkorlátok automatikusan szűkülnek.

---

## 17. Izoláció és Ephemeral Tool Protocol

Szintek:

- **E0:** read-only elemzés;
- **E1:** izolált workspace-transzformáció;
- **E2:** kontrollált környezeti változás;
- **E3:** production-hatású, ember által jóváhagyott művelet.

Sandbox minimum: read-only alap, ephemeral írható réteg, default disabled network, nem root, tiltott host namespace és device, erőforráslimit, input- és outputhash, automatikus megsemmisítés.

Agent által készített toolhoz forrás, hash, capability, korlátozott input/output, dry-run, fixture-teszt, timeout, provenance és automatikus visszavonás kell.

---

## 18. Reviewer és Arbiter

Finding osztályok: `deterministic`, `empirical`, `risk_judgment`, `subjective`, `scope_or_value_decision`.

Legfeljebb három kör után:

- determinisztikus kérdésnél executable oracle;
- empirikus kérdésnél mérés;
- szubjektív kérdésnél policy szerinti alapértelmezés;
- kockázati vagy értékdöntésnél ember.

---

## 19. Release és Ground Truth

Ellenőrzési rétegek: lokális targeted watch, PR smoke, nightly full, staging, production canary, aggregált felhasználói és üzleti outcome.

Ha a synthetic oracle zöld, de a valós sikeresség tartósan romlik:

1. az oracle `SUSPECT`;
2. az érintett Fast Path felfüggeszthető;
3. a Governor szigorít;
4. új Problem és vizsgálat indul;
5. megerősített eltérésnél az oracle `INVALID`;
6. új specifikációs javaslat készül.

A runtime jel nem írja át automatikusan a követelményt.

---

## 20. Fenntarthatóság

### 20.1. Architectural Consolidation Cycle

Trigger lehet release-szám, időintervallum, coupling, circular dependency, redundáns interfész, növekvő buildidő vagy sérült architecture fitness function. A refaktor kis, visszafordítható packetekben történik.

### 20.2. Evidence-életciklus

- **Hot State:** aktuális részletes evidence.
- **Warm Summary:** ellenőrizhető összegzés és Merkle-bizonyíték.
- **Cold Evidence:** visszatölthető immutable részletek.

A Merkle-összegzés nem helyettesíti az eredeti evidence-et.

### 20.3. Human Attention Budget

A determinisztikusan eldönthető kérdés ne terhelje az embert. Alacsony prioritású döntések digestbe csoportosíthatók, kritikus security, privacy, adatvesztési, rollback vagy SLO esemény nem.

---

## 21. Kétdimenziós érettségi modell

### 21.1. Módszertani érettség

- **L1 Verified Core:** strukturált spec, stabil ID, RED, célzott és teljes regresszió, traceability, review.
- **L2 Enforced Execution:** packet, role- és fájlscope, izoláció, safety gate, manifest, Context Fitness.
- **L3 Governed Autonomy:** pályák, Oracle, Governor, clean-room promotion, ekvivalenciacache, policy.
- **L4 Continuous Ground Truth:** canary, runtime-feature kapcsolat, Ground Truth, profilkalibráció, architecture és epoch lifecycle.

### 21.2. Runner-érettség

- **Runner R0, CI-backed verifier:** CI, Git hook, séma, ID, diff, parancsfuttatás, riport, alap traceability és korlátozott cache.
- **Runner R1, isolated workspace:** worktree vagy konténer, allow/deny, szerep-diff, secret scan, packet, budget és manifest.
- **Runner R2, governed control plane:** daemon, állapotgép, policy engine, Path Oracle, capability, content-addressed store, approval queue és ekvivalenciabizonyítás.
- **Runner R3, high assurance:** aláírt policy, tamper-evident audit, microVM, dual control, replay, epoch evidence és szigorú production-közvetítés.

```yaml
veritas_adoption:
  methodology_level: L2
  runner_level: R1
  achieved_controls:
    - structured_specifications
    - generated_traceability
    - role_separated_diffs
    - targeted_and_full_regression
    - isolated_worktrees
  declared_gaps:
    - signed_policy
    - content_addressed_store
    - deterministic_replay
    - microvm_isolation
```

Az állított garanciák nem haladhatják meg a gyengébbik tengely bizonyított képességét.

---

## 22. Definition of Ready

Egy feature kész a fejlesztésre, ha a probléma, eredmény, scope, követelmény, invariáns, szükséges UI/API/állapot/adatszerződés, scenario, tesztleképezés, kockázat, pálya, prototípus és approval rendelkezésre áll, nincs blokkoló kérdés, és a SPEC READY Gate zöld.

---

## 23. Definition of Done

Egy változtatás kész, ha:

- minden kötelező requirement implementált;
- requirement és verification coverage eléri az előírt szintet;
- a RED evidence rendelkezésre áll;
- a célzott és teljes regresszió ténylegesen zöld;
- lint, typecheck, build és security ellenőrzés zöld;
- a Context Fitness elfogadott;
- packetbontásnál a cross-packet integráció zöld;
- cache esetén az Execution Equivalence Proof érvényes;
- exploration eredetnél a Clean-Room Promotion Gate zöld;
- traceability, provenance és review elfogadott;
- Final Safety és Release Gate zöld;
- rollback és observability biztosított;
- manifest lezárt;
- release utáni ellenőrzés konfigurált.

---

## 24. Minimális működő VERITAS

1. Strukturált feature-specifikáció.
2. Stabil requirement ID.
3. Requirement-teszt kapcsolat.
4. Tényleges RED, ahol értelmezhető.
5. Test Author és Implementer elkülönítése.
6. Minden módosítás után célzott teszt.
7. Célzott GREEN után teljes regresszió.
8. Gépi futási eredmény.
9. Osztályozott triage és javítási limit.
10. Kritikus bizonytalanságnál emberi stop-gate.
11. Független review.
12. Generált traceability.
13. Alapvető release-visszacsatolás.
14. Exploration-kód közvetlen promotionjének tiltása.
15. Packetméret és folyamatköltség rendszeres felülvizsgálata.

---

## 25. Anti-minták

Tiltott vagy kerülendő:

- hosszú prompt stabil requirement helyett;
- LLM-állítás evidence helyett;
- teszt lazítása a GREEN érdekében;
- Implementer saját oracle-módosítása;
- minden teszt E2E-ben;
- mechanikus user story-szaporítás;
- korlátlan javítás;
- kézi traceability autoritatív forrásként;
- Fast Path önbevallás;
- prototípus productionbe szivárgása;
- régi PASS ekvivalenciabizonyítás nélkül;
- túl nagy packet vagy túlzott fragmentáció;
- kontrollok mechanikus maximalizálása;
- proportionality metrika alapján automatikus biztonságlazítás;
- dokumentumbővítés végrehajtott bizonyíték helyett.

---

## 26. Referenciafolyamat

```text
OBSERVATION / IDEA / INCIDENT
  -> PROBLEM
  -> EXPLORATION, ha nagy a bizonytalanság
  -> PROMOTION PACKAGE vagy DISCARD
  -> RESEARCH
  -> FEATURE BRIEF
  -> FEATURE SPECIFICATION
  -> SPEC READY
  -> RISK AND PATH
  -> TEST CONTRACT
  -> EXECUTION PACKET
  -> CONTEXT FITNESS
  -> RED EVIDENCE
  -> MINIMAL IMPLEMENTATION
  -> TARGETED GREEN
  -> FULL OR EQUIVALENCE-QUALIFIED REGRESSION
  -> TRACEABILITY
  -> INDEPENDENT REVIEW
  -> FINAL SAFETY
  -> RELEASE
  -> GROUND TRUTH
  -> NEW PROBLEM OR SPEC CHANGE
```

---

## 27. Runner referenciaarchitektúra

```text
Signed Policy Loader
  -> Artifact Schema Registry
  -> Content-Addressed Artifact Store
  -> Deterministic State Machine
  -> Capability and Isolation Manager
  -> Exploration Boundary Manager
  -> Context Fitness Evaluator
  -> Command Executor
  -> Test Result Collectors
  -> Execution Equivalence Verifier
  -> Traceability Graph Builder
  -> Gate Evaluator
  -> Path Eligibility Oracle
  -> Process Proportionality Monitor
  -> Human Approval Queue
  -> Manifest Builder
  -> Append-Only Audit Log
```

A Runner Core nem tartalmazhat LLM-alapú állapotátmenetet vagy release-verdictet.

---

## 28. Záró összefoglalás

A VERITAS 1.1 dinamikus, kibernetikus szabályozórendszer. Nemcsak az agentek tipikus hibáit akadályozza meg, hanem saját működési torzulásait is figyeli és biztonságos irányban korrigálja.

Öt kulcsmechanizmusa:

1. Exploration Path és Clean-Room Promotion.
2. Empirikus Context Fitness és fragmentációbiztos Workflow Compression.
3. Execution Equivalence Proof alapú evidence cache.
4. Process Proportionality Gate a módszertani DoS ellen.
5. Kétdimenziós L1–L4 módszertani és R0–R3 Runner-érettség.

A VERITAS 1.1 ígérete nem az, hogy az LLM nem hibázik, és nem is az, hogy minden változtatásra maximális kontrollt alkalmaz. Az ígérete az, hogy az LLM hibája ne válhasson észrevétlenül elfogadott specifikációvá, hamis tesztsikerré vagy ellenőrizetlen release-zé, miközben a kontroll költsége arányos marad a valós kockázattal.
