---
id: FEAT-044
title: Kiadási célok és megtakarítási lehetőségek
status: spec_ready
version: 1
risk: high
owner: system-architect
related_brief: BRIEF-044
---

# FEAT-044: Kiadási célok és megtakarítási lehetőségek

## 1. Cél és felhasználói eredmény

A BRIEF-044 képesség teljes, tenant-biztos, magyarázható és felhasználó által kontrollált megvalósítási szerződése. Kész akkor, ha mind a nyolc követelmény RED→GREEN bizonyítékkal, célzott teszttel és teljes regresszióval igazolt, és a felület hibánál nem állít valótlan sikert.

## 2. Kontextus és források

Kanonikus források: `briefs/BRIEF-044-kiadasi-celok-es-megtakaritasi-lehetosegek.md`, `METHODOLOGY.md`, `.agents/rules/methodology.md`. Kapcsolódó platform-invariánsok: explicit tenant, szerveroldali RBAC, audit, revízió, idempotencia, stabil hibaszerződés és érzékeny adatok minimalizálása.

### Target Files

- `app/savings_models.py (NEW)`
- `app/savings_service.py (NEW)`
- `app/savings_api.py (NEW)`
- `app/api_v2.py (MODIFY)`
- `frontend/app/savings-goals/page.tsx (NEW)`
- `frontend/components/savings/GoalRecommendationPanel.tsx (NEW)`
- `frontend/lib/savings.ts (NEW)`

A felsorolás implementációs határ. A Fázis 1 nem módosítja ezeket; a fejlesztő modell kizárólag sikeres RED bizonyíték után dolgozhat rajtuk.

## 3. Scope (Benne van / Nincs benne)

### Benne van
- A BRIEF teljes happy path, empty, loading, részleges, konfliktusos, jogosulatlan és retry állapota.
- REST, domain, perzisztencia, audit és konkrét böngészős út szerződése.
- Tenant-izoláció, idempotencia és konkurens módosítás.

### Nincs benne
- Production implementáció ebben a fázisban.
- Automatikus pénzügyi vagy jogi döntés felhasználói kontroll nélkül.
- A BRIEF-ben nem szereplő általános platform-újratervezés.

## 4. Szereplők és előfeltételek

- ACT-044-01: háztartási tag, aki saját jogosultságán belül használja a funkciót.
- ACT-044-02: tulajdonos vagy pénzügyi felelős, aki döntést és felülbírálást végez.
- ACT-044-03: könyvelő vagy ellenőrző, korlátozott, auditált hozzáféréssel.
- PRE-044-01: hitelesített session, aktív tenant és szerveroldalon ellenőrzött szerepkör.
- PRE-044-02: a hivatkozott források ugyanahhoz a tenanthoz tartoznak.
- PRE-044-03: módosításkor `expected_revision`, íráskor `Idempotency-Key` rendelkezésre áll.

## 5. Funkcionális követelmények

- REQ-044-01 [MUST]: Kategória- és időszakalapú kiadási cél hozható létre.
- REQ-044-02 [MUST]: A haladás korrigált tényleges költésből számolódik.
- REQ-044-03 [MUST]: Ajánlás becsült hatással, bizonytalansággal és evidenciával jelenik meg.
- REQ-044-04 [MUST]: A felhasználó ajánlást elfogadhat, módosíthat, halaszthat vagy elutasíthat.
- REQ-044-05 [MUST]: Kevés adat nem eredményez túl magabiztos javaslatot.
- REQ-044-06 [MUST]: Más tenant céljai és evidenciái nem hozzáférhetők.
- REQ-044-07 [MUST]: Azonos generálási kérés nem duplikál ajánlást.
- REQ-044-08 [MUST]: Párhuzamos célmódosítás stale revision hibát ad.

## 6. Nem funkcionális követelmények

- NFR-044-01 [SECURITY]: minden olvasás és írás explicit tenant-filterrel, szerveroldali RBAC-kal és erőforrás-szintű ellenőrzéssel fut.
- NFR-044-02 [RELIABILITY]: módosítás atomi; timeout és retry nem hoz létre duplikátumot vagy félállapotot.
- NFR-044-03 [PERFORMANCE]: lista p95 ≤ 800 ms, parancs elfogadása p95 ≤ 1200 ms, hosszú munka 202 és követhető státusz.
- NFR-044-04 [ACCESSIBILITY]: WCAG 2.2 AA, billentyűzet, látható fókusz, programozott név, aria-live és legalább 44×44 CSS px cél.
- NFR-044-05 [PRIVACY]: log és telemetry nem tartalmaz teljes bizonylatképet, tokent vagy szükségtelen személyes pénzügyi adatot.
- NFR-044-06 [OBSERVABILITY]: correlation ID, audit actor, tenant, parancstípus, eredménykód, latency és retry számláló.

## 7. UI-szerződés

- UI-044-01: `savings_goals-page`, a `/savings-goals` kanonikus munkaterülete, loading/empty/error/ready állapotokkal.
- UI-044-02: `savings_goals-primary-action`, jogosultság- és állapotfüggő elsődleges művelet.
- UI-044-03: `savings_goals-evidence`, a döntés alapját és bizonytalanságát bemutató panel.
- UI-044-04: `savings_goals-status`, vizuális és aria-live állapotközlő.
- UI-044-05: `savings_goals-conflict`, adatvesztés nélküli konfliktus- és retry felület.

## 8. GUI-folyamat

1. A felhasználó megnyitja a `/savings-goals` útvonalat, a sessiont a `helpers/auth.ts` inicializálja.
2. A felület betöltési, majd tenant-szűrt ready vagy hasznos empty állapotot mutat.
3. A felhasználó megnyit egy tételt; a forrás, evidence, confidence, jogosultság és aktuális revízió látható.
4. Az elsődleges művelet előtt a kliens validál, veszélyes döntésnél megerősítést kér.
5. A kérés idempotenciakulccsal indul; in-flight állapotban ismételt aktiválás nem küld második parancsot.
6. Siker esetén az új revízió és állapot jelenik meg. 409 esetén konfliktusnézet, 4xx esetén javítható mezőhiba, hálózati hibánál adatmegőrző retry jelenik meg.
7. Frissítés és visszatérés után a szerverállapot reprodukálható, idegen tenant erőforrása nem látható.

## 9. Állapotmodell

Kanonikus állapotok: `DRAFT → ACTIVE → ON_TRACK → AT_RISK → ACHIEVED → PAUSED → ARCHIVED`.

- Csak a service által deklarált átmenet engedélyezett; ismeretlen vagy tiltott átmenetre domain hiba.
- Minden mutáció expected revisiont ellenőriz és új revisiont ad.
- Terminális állapotból korrekció csak külön, auditált parancson keresztül történhet.
- Sikertelen művelet az előző stabil állapotot őrzi; frontend loading állapot nem domain állapot.

### Teljes típusdefiníciók

### Python / Pydantic

```python
from datetime import datetime
from enum import StrEnum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

class FeatureStatus(StrEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ON_TRACK = "ON_TRACK"
    AT_RISK = "AT_RISK"
    ACHIEVED = "ACHIEVED"
    PAUSED = "PAUSED"
    ARCHIVED = "ARCHIVED"

class SpendingGoalCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tenant_id: str = Field(min_length=1, max_length=128)
    client_reference: str = Field(min_length=1, max_length=128)
    payload: dict[str, Any]
    idempotency_key: str = Field(min_length=16, max_length=128)

class SpendingGoalCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: int = Field(ge=0)
    action: str = Field(min_length=1, max_length=64)
    reason: str | None = Field(default=None, max_length=1000)
    payload: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str = Field(min_length=16, max_length=128)

class SpendingGoalRead(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    tenant_id: str
    status: FeatureStatus
    revision: int = Field(ge=0)
    data: dict[str, Any]
    evidence: dict[str, Any]
    created_at: datetime
    updated_at: datetime

class ApiProblem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str
    message: str
    field: str | None = None
    retryable: bool = False
    correlation_id: str

class FeatureDomainError(Exception):
    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable
```

A `payload`, `data` és `evidence` mezőket az implementációban a közvetlenül feljebb felsorolt feature-specifikus modellek váltják ki. `Any` nem kerülhet publikus végpont végleges OpenAPI-sémájába.

### TypeScript

```typescript
export type FeatureStatus = "DRAFT" | "ACTIVE" | "ON_TRACK" | "AT_RISK" | "ACHIEVED" | "PAUSED" | "ARCHIVED";

export interface SpendingGoalCreate {
  tenantId: string;
  clientReference: string;
  payload: Record<string, unknown>;
  idempotencyKey: string;
}

export interface SpendingGoalCommand {
  expectedRevision: number;
  action: string;
  reason?: string;
  payload: Record<string, unknown>;
  idempotencyKey: string;
}

export interface SpendingGoalRead {
  id: string;
  tenantId: string;
  status: FeatureStatus;
  revision: number;
  data: Record<string, unknown>;
  evidence: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
}

export interface ApiProblem {
  code: string;
  message: string;
  field?: string;
  retryable: boolean;
  correlationId: string;
}
```

## 10. Acceptance scenario-k

### AC-044-01: Kategória- és időszakalapú kiadási cél hozható létre.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-044-01 szerinti műveletet végrehajtja
Then kategória- és időszakalapú kiadási cél hozható létre.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-044-02: A haladás korrigált tényleges költésből számolódik.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-044-02 szerinti műveletet végrehajtja
Then a haladás korrigált tényleges költésből számolódik.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-044-03: Ajánlás becsült hatással, bizonytalansággal és evidenciával jelenik meg.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-044-03 szerinti műveletet végrehajtja
Then ajánlás becsült hatással, bizonytalansággal és evidenciával jelenik meg.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-044-04: A felhasználó ajánlást elfogadhat, módosíthat, halaszthat vagy elutasíthat.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-044-04 szerinti műveletet végrehajtja
Then a felhasználó ajánlást elfogadhat, módosíthat, halaszthat vagy elutasíthat.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-044-05: Kevés adat nem eredményez túl magabiztos javaslatot.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-044-05 szerinti műveletet végrehajtja
Then kevés adat nem eredményez túl magabiztos javaslatot.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-044-06: Más tenant céljai és evidenciái nem hozzáférhetők.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-044-06 szerinti műveletet végrehajtja
Then más tenant céljai és evidenciái nem hozzáférhetők.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-044-07: Azonos generálási kérés nem duplikál ajánlást.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-044-07 szerinti műveletet végrehajtja
Then azonos generálási kérés nem duplikál ajánlást.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-044-08: Párhuzamos célmódosítás stale revision hibát ad.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-044-08 szerinti műveletet végrehajtja
Then párhuzamos célmódosítás stale revision hibát ad.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

## 11. API-szerződés

- `GET /api/v2/savings-goals`: tenant-szűrt lista; cursor pagination; 200/401/403.
- `POST /api/v2/savings-goals`: létrehozás vagy elemzés; kötelező `Idempotency-Key`; 201 vagy 202/400/401/403/409/422.
- `GET /api/v2/savings-goals/{id}`: részlet és evidence; idegen tenant esetén 404-szerű válasz.
- `PATCH /api/v2/savings-goals/{id}`: `expected_revision` alapú módosítás; 200/409/422.
- `POST /api/v2/savings-goals/{id}/confirm`: kontrollált állapotátmenet; 200/403/409/422.
- Minden hiba `application/problem+json` alakú `ApiProblem`; minden siker tenant- és revision-azonosítót ad.

### Lépésről lépésre kidolgozott kontrollfolyamat

1. Cél csak érvényes kategóriára, nem átfedő vagy explicit engedélyezett időszakra és nem negatív összegekkel hozható létre.
2. A haladás jóváhagyott költésből, visszatérítésekből és aktív felosztásokból determinisztikusan számolódik.
3. Ajánlás evidencia, becsült hatás, időtáv és confidence nélkül nem jelenhet meg.
4. Szabályozott pénzügyi tanács, garantált eredmény vagy automatikus lemondás esetén raise UnsupportedAdviceError(...).
5. Elfogadás, módosítás, halasztás és elutasítás auditált; alapvető kiadás kizárása a következő futásokban érvényesül.
6. Kevés adat strukturált INSUFFICIENT_DATA állapotot eredményez; idempotens generálás nem duplikál ajánlást.

## 12. Adatmodell és perzisztencia

- Fő aggregátum: `SpendingGoal`; kötelező `id`, `tenant_id`, `status`, `revision`, `created_at`, `updated_at`.
- Írások tenant tranzakcióban, optimistic lockinggal és idempotency rekorddal történnek.
- Egyedi kulcs: `(tenant_id, idempotency_key, command_type)`; az eltárolt request hash eltérés konfliktus.
- Audit esemény tartalmazza az aggregátumot, előző/új revíziót, aktort, okot, correlation ID-t és időt, de nem másol érzékeny teljes payloadot.
- Törlés csak projektmegőrzési szabály szerint; pénzügyi bizonyíték logikai törléssel és referenciaintegritással.

## 13. Tesztterv és lefedettségi leképezés

- REQ-044-01 → AC-044-01 → `.agent-pipeline/03_e2e_suites/test_e2e_044.py`; unit cél: `tests/unit/test_savings_goals_service.py::test_req_044_01`.
- REQ-044-02 → AC-044-02 → `.agent-pipeline/03_e2e_suites/test_e2e_044.py`; unit cél: `tests/unit/test_savings_goals_service.py::test_req_044_02`.
- REQ-044-03 → AC-044-03 → `.agent-pipeline/03_e2e_suites/test_e2e_044.py`; unit cél: `tests/unit/test_savings_goals_service.py::test_req_044_03`.
- REQ-044-04 → AC-044-04 → `.agent-pipeline/03_e2e_suites/test_e2e_044.py`; unit cél: `tests/unit/test_savings_goals_service.py::test_req_044_04`.
- REQ-044-05 → AC-044-05 → `.agent-pipeline/03_e2e_suites/test_e2e_044.py`; unit cél: `tests/unit/test_savings_goals_service.py::test_req_044_05`.
- REQ-044-06 → AC-044-06 → `.agent-pipeline/03_e2e_suites/test_e2e_044.py`; unit cél: `tests/unit/test_savings_goals_service.py::test_req_044_06`.
- REQ-044-07 → AC-044-07 → `.agent-pipeline/03_e2e_suites/test_e2e_044.py`; unit cél: `tests/unit/test_savings_goals_service.py::test_req_044_07`.
- REQ-044-08 → AC-044-08 → `.agent-pipeline/03_e2e_suites/test_e2e_044.py`; unit cél: `tests/unit/test_savings_goals_service.py::test_req_044_08`.

### Kötelező pytest unit terv
- Paraméterezett domain-átmenetek és hibakódok.
- Tenant A/B fixture, közvetlen azonosító-próba és lista-szivárgás ellenőrzése.
- Azonos és eltérő payloadú idempotens retry.
- Két egyidejű expected revision: egy siker, egy determinisztikus 409.
- Atomi rollback külső függőség, perzisztencia és audit-hiba esetén.
- Dátum-, összeg-, pénznem-, kerekítési és méret-határértékek a domain szerint.

Minőségi kapu: először a célzott teszteket RED állapotban kell futtatni és igazolni, hogy valódi hiány miatt buknak; csak ezután módosítható production kód. GREEN után ugyanazok a célzott tesztek, majd a teljes unit, integration és E2E regresszió futtatandó tool-használattal. Skip, xfail vagy puszta deklaráció nem sikerbizonyíték.

## 14. Kockázatok és biztonsági megfontolások

- IDOR és tenant-szivárgás: 404-szerű erőforrásválasz és minden repository lekérdezésben tenant kulcs.
- Duplikált pénzügyi hatás: idempotency ledger, request hash és atomi tranzakció.
- Lost update: optimistic revision, 409 és felhasználói konfliktusfeloldás.
- Félrevezető automatizmus: evidence, confidence és explicit emberi döntés, ahol pénzügyi jelentés változik.
- Tömeges vagy visszafordíthatatlan hatás: előnézet, megerősítés, jogosultság, audit és szükség esetén jóváhagyás.
- Külső szolgáltatáshiba: timeout, retry budget, circuit breaker és csendes siker tilalma.
- Kiadási feltétel: 100% REQ→AC→teszt traceability, statikus ellenőrzés, célzott GREEN és teljes regresszió.
