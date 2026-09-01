---
id: FEAT-046
title: Adatminőségi feladatközpont
status: spec_ready
version: 1
risk: high
owner: system-architect
related_brief: BRIEF-046
---

# FEAT-046: Adatminőségi feladatközpont

## 1. Cél és felhasználói eredmény

A BRIEF-046 képesség teljes, tenant-biztos, magyarázható és felhasználó által kontrollált megvalósítási szerződése. Kész akkor, ha mind a nyolc követelmény RED→GREEN bizonyítékkal, célzott teszttel és teljes regresszióval igazolt, és a felület hibánál nem állít valótlan sikert.

## 2. Kontextus és források

Kanonikus források: `briefs/BRIEF-046-adatminosegi-feladatkozpont.md`, `METHODOLOGY.md`, `.agents/rules/methodology.md`. Kapcsolódó platform-invariánsok: explicit tenant, szerveroldali RBAC, audit, revízió, idempotencia, stabil hibaszerződés és érzékeny adatok minimalizálása.

### Target Files

- `app/quality_task_models.py (NEW)`
- `app/quality_task_service.py (NEW)`
- `app/quality_task_api.py (NEW)`
- `app/api_v2.py (MODIFY)`
- `frontend/app/quality-inbox/page.tsx (NEW)`
- `frontend/components/quality/QualityTaskCenter.tsx (NEW)`
- `frontend/lib/qualityTasks.ts (NEW)`

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

- ACT-046-01: háztartási tag, aki saját jogosultságán belül használja a funkciót.
- ACT-046-02: tulajdonos vagy pénzügyi felelős, aki döntést és felülbírálást végez.
- ACT-046-03: könyvelő vagy ellenőrző, korlátozott, auditált hozzáféréssel.
- PRE-046-01: hitelesített session, aktív tenant és szerveroldalon ellenőrzött szerepkör.
- PRE-046-02: a hivatkozott források ugyanahhoz a tenanthoz tartoznak.
- PRE-046-03: módosításkor `expected_revision`, íráskor `Idempotency-Key` rendelkezésre áll.

## 5. Funkcionális követelmények

- REQ-046-01 [MUST]: Minden támogatott adatminőségi hiba közös listában jelenik meg.
- REQ-046-02 [MUST]: A feladatok súlyosság, felelős, hatás és forrás szerint szűrhetők.
- REQ-046-03 [MUST]: A feladatból közvetlen javítófolyamat indítható.
- REQ-046-04 [MUST]: Biztonságos tömeges művelet előnézettel végezhető.
- REQ-046-05 [MUST]: Indokolt kivétel és automatikus újraértékelés támogatott.
- REQ-046-06 [MUST]: Más tenant feladata és érzékeny evidenciája nem hozzáférhető.
- REQ-046-07 [MUST]: Azonos detektor- vagy bulk kérés nem duplikál állapotot.
- REQ-046-08 [MUST]: Forrásrevízió változásakor a stale javítás nem ír részállapotot.

## 6. Nem funkcionális követelmények

- NFR-046-01 [SECURITY]: minden olvasás és írás explicit tenant-filterrel, szerveroldali RBAC-kal és erőforrás-szintű ellenőrzéssel fut.
- NFR-046-02 [RELIABILITY]: módosítás atomi; timeout és retry nem hoz létre duplikátumot vagy félállapotot.
- NFR-046-03 [PERFORMANCE]: lista p95 ≤ 800 ms, parancs elfogadása p95 ≤ 1200 ms, hosszú munka 202 és követhető státusz.
- NFR-046-04 [ACCESSIBILITY]: WCAG 2.2 AA, billentyűzet, látható fókusz, programozott név, aria-live és legalább 44×44 CSS px cél.
- NFR-046-05 [PRIVACY]: log és telemetry nem tartalmaz teljes bizonylatképet, tokent vagy szükségtelen személyes pénzügyi adatot.
- NFR-046-06 [OBSERVABILITY]: correlation ID, audit actor, tenant, parancstípus, eredménykód, latency és retry számláló.

## 7. UI-szerződés

- UI-046-01: `data_quality-page`, a `/quality-inbox` kanonikus munkaterülete, loading/empty/error/ready állapotokkal.
- UI-046-02: `data_quality-primary-action`, jogosultság- és állapotfüggő elsődleges művelet.
- UI-046-03: `data_quality-evidence`, a döntés alapját és bizonytalanságát bemutató panel.
- UI-046-04: `data_quality-status`, vizuális és aria-live állapotközlő.
- UI-046-05: `data_quality-conflict`, adatvesztés nélküli konfliktus- és retry felület.

## 8. GUI-folyamat

1. A felhasználó megnyitja a `/quality-inbox` útvonalat, a sessiont a `helpers/auth.ts` inicializálja.
2. A felület betöltési, majd tenant-szűrt ready vagy hasznos empty állapotot mutat.
3. A felhasználó megnyit egy tételt; a forrás, evidence, confidence, jogosultság és aktuális revízió látható.
4. Az elsődleges művelet előtt a kliens validál, veszélyes döntésnél megerősítést kér.
5. A kérés idempotenciakulccsal indul; in-flight állapotban ismételt aktiválás nem küld második parancsot.
6. Siker esetén az új revízió és állapot jelenik meg. 409 esetén konfliktusnézet, 4xx esetén javítható mezőhiba, hálózati hibánál adatmegőrző retry jelenik meg.
7. Frissítés és visszatérés után a szerverállapot reprodukálható, idegen tenant erőforrása nem látható.

## 9. Állapotmodell

Kanonikus állapotok: `OPEN → ASSIGNED → IN_PROGRESS → SNOOZED → EXEMPTED → RESOLVED → REOPENED`.

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
    OPEN = "OPEN"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    SNOOZED = "SNOOZED"
    EXEMPTED = "EXEMPTED"
    RESOLVED = "RESOLVED"
    REOPENED = "REOPENED"

class QualityTaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tenant_id: str = Field(min_length=1, max_length=128)
    client_reference: str = Field(min_length=1, max_length=128)
    payload: dict[str, Any]
    idempotency_key: str = Field(min_length=16, max_length=128)

class QualityTaskCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: int = Field(ge=0)
    action: str = Field(min_length=1, max_length=64)
    reason: str | None = Field(default=None, max_length=1000)
    payload: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str = Field(min_length=16, max_length=128)

class QualityTaskRead(BaseModel):
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
export type FeatureStatus = "OPEN" | "ASSIGNED" | "IN_PROGRESS" | "SNOOZED" | "EXEMPTED" | "RESOLVED" | "REOPENED";

export interface QualityTaskCreate {
  tenantId: string;
  clientReference: string;
  payload: Record<string, unknown>;
  idempotencyKey: string;
}

export interface QualityTaskCommand {
  expectedRevision: number;
  action: string;
  reason?: string;
  payload: Record<string, unknown>;
  idempotencyKey: string;
}

export interface QualityTaskRead {
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

### AC-046-01: Minden támogatott adatminőségi hiba közös listában jelenik meg.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-046-01 szerinti műveletet végrehajtja
Then minden támogatott adatminőségi hiba közös listában jelenik meg.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-046-02: A feladatok súlyosság, felelős, hatás és forrás szerint szűrhetők.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-046-02 szerinti műveletet végrehajtja
Then a feladatok súlyosság, felelős, hatás és forrás szerint szűrhetők.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-046-03: A feladatból közvetlen javítófolyamat indítható.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-046-03 szerinti műveletet végrehajtja
Then a feladatból közvetlen javítófolyamat indítható.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-046-04: Biztonságos tömeges művelet előnézettel végezhető.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-046-04 szerinti műveletet végrehajtja
Then biztonságos tömeges művelet előnézettel végezhető.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-046-05: Indokolt kivétel és automatikus újraértékelés támogatott.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-046-05 szerinti műveletet végrehajtja
Then indokolt kivétel és automatikus újraértékelés támogatott.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-046-06: Más tenant feladata és érzékeny evidenciája nem hozzáférhető.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-046-06 szerinti műveletet végrehajtja
Then más tenant feladata és érzékeny evidenciája nem hozzáférhető.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-046-07: Azonos detektor- vagy bulk kérés nem duplikál állapotot.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-046-07 szerinti műveletet végrehajtja
Then azonos detektor- vagy bulk kérés nem duplikál állapotot.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-046-08: Forrásrevízió változásakor a stale javítás nem ír részállapotot.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-046-08 szerinti műveletet végrehajtja
Then forrásrevízió változásakor a stale javítás nem ír részállapotot.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

## 11. API-szerződés

- `GET /api/v2/quality-tasks`: tenant-szűrt lista; cursor pagination; 200/401/403.
- `POST /api/v2/quality-tasks`: létrehozás vagy elemzés; kötelező `Idempotency-Key`; 201 vagy 202/400/401/403/409/422.
- `GET /api/v2/quality-tasks/{id}`: részlet és evidence; idegen tenant esetén 404-szerű válasz.
- `PATCH /api/v2/quality-tasks/{id}`: `expected_revision` alapú módosítás; 200/409/422.
- `POST /api/v2/quality-tasks/{id}/confirm`: kontrollált állapotátmenet; 200/403/409/422.
- Minden hiba `application/problem+json` alakú `ApiProblem`; minden siker tenant- és revision-azonosítót ad.

### Lépésről lépésre kidolgozott kontrollfolyamat

1. A detektorok stabil rule_code és source revision alapján upsertelik a feladatot, így ugyanaz a probléma nem duplikálódik.
2. A lista minden lekérdezése tenant-, szerepkör- és láthatósági szűrést alkalmaz.
3. A task magyarázata rule evidence és blokkolt folyamat alapján készül, érzékeny adatot jogosulatlan szerepkörnek nem fed fel.
4. Bulk action előnézetet és tételenkénti biztonsági ellenőrzést igényel; veszélyes kevert műveletre raise UnsafeBulkActionError(...).
5. Forrásjavítás után újraértékelés RESOLVED vagy REOPENED állapotot állít, de az auditnyom megmarad.
6. Kivétel csak indokkal és engedélyezett rule esetén; stale revision részleges mentés nélkül hibázik.

## 12. Adatmodell és perzisztencia

- Fő aggregátum: `QualityTask`; kötelező `id`, `tenant_id`, `status`, `revision`, `created_at`, `updated_at`.
- Írások tenant tranzakcióban, optimistic lockinggal és idempotency rekorddal történnek.
- Egyedi kulcs: `(tenant_id, idempotency_key, command_type)`; az eltárolt request hash eltérés konfliktus.
- Audit esemény tartalmazza az aggregátumot, előző/új revíziót, aktort, okot, correlation ID-t és időt, de nem másol érzékeny teljes payloadot.
- Törlés csak projektmegőrzési szabály szerint; pénzügyi bizonyíték logikai törléssel és referenciaintegritással.

## 13. Tesztterv és lefedettségi leképezés

- REQ-046-01 → AC-046-01 → `.agent-pipeline/03_e2e_suites/test_e2e_046.py`; unit cél: `tests/unit/test_data_quality_service.py::test_req_046_01`.
- REQ-046-02 → AC-046-02 → `.agent-pipeline/03_e2e_suites/test_e2e_046.py`; unit cél: `tests/unit/test_data_quality_service.py::test_req_046_02`.
- REQ-046-03 → AC-046-03 → `.agent-pipeline/03_e2e_suites/test_e2e_046.py`; unit cél: `tests/unit/test_data_quality_service.py::test_req_046_03`.
- REQ-046-04 → AC-046-04 → `.agent-pipeline/03_e2e_suites/test_e2e_046.py`; unit cél: `tests/unit/test_data_quality_service.py::test_req_046_04`.
- REQ-046-05 → AC-046-05 → `.agent-pipeline/03_e2e_suites/test_e2e_046.py`; unit cél: `tests/unit/test_data_quality_service.py::test_req_046_05`.
- REQ-046-06 → AC-046-06 → `.agent-pipeline/03_e2e_suites/test_e2e_046.py`; unit cél: `tests/unit/test_data_quality_service.py::test_req_046_06`.
- REQ-046-07 → AC-046-07 → `.agent-pipeline/03_e2e_suites/test_e2e_046.py`; unit cél: `tests/unit/test_data_quality_service.py::test_req_046_07`.
- REQ-046-08 → AC-046-08 → `.agent-pipeline/03_e2e_suites/test_e2e_046.py`; unit cél: `tests/unit/test_data_quality_service.py::test_req_046_08`.

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
