---
id: FEAT-043
title: Megosztott vásárlások és költségfelosztás
status: spec_ready
version: 1
risk: high
owner: system-architect
related_brief: BRIEF-043
---

# FEAT-043: Megosztott vásárlások és költségfelosztás

## 1. Cél és felhasználói eredmény

A BRIEF-043 képesség teljes, tenant-biztos, magyarázható és felhasználó által kontrollált megvalósítási szerződése. Kész akkor, ha mind a nyolc követelmény RED→GREEN bizonyítékkal, célzott teszttel és teljes regresszióval igazolt, és a felület hibánál nem állít valótlan sikert.

## 2. Kontextus és források

Kanonikus források: `briefs/BRIEF-043-megosztott-vasarlasok-es-koltsegfelosztas.md`, `METHODOLOGY.md`, `.agents/rules/methodology.md`. Kapcsolódó platform-invariánsok: explicit tenant, szerveroldali RBAC, audit, revízió, idempotencia, stabil hibaszerződés és érzékeny adatok minimalizálása.

### Target Files

- `app/cost_split_models.py (NEW)`
- `app/cost_split_service.py (NEW)`
- `app/cost_split_api.py (NEW)`
- `app/api_v2.py (MODIFY)`
- `frontend/app/cost-splits/page.tsx (NEW)`
- `frontend/components/cost-splits/SplitEditor.tsx (NEW)`
- `frontend/lib/costSplits.ts (NEW)`

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

- ACT-043-01: háztartási tag, aki saját jogosultságán belül használja a funkciót.
- ACT-043-02: tulajdonos vagy pénzügyi felelős, aki döntést és felülbírálást végez.
- ACT-043-03: könyvelő vagy ellenőrző, korlátozott, auditált hozzáféréssel.
- PRE-043-01: hitelesített session, aktív tenant és szerveroldalon ellenőrzött szerepkör.
- PRE-043-02: a hivatkozott források ugyanahhoz a tenanthoz tartoznak.
- PRE-043-03: módosításkor `expected_revision`, íráskor `Idempotency-Key` rendelkezésre áll.

## 5. Funkcionális követelmények

- REQ-043-01 [MUST]: A vásárlás fix, százalékos, egyenlő vagy tételes módon felosztható.
- REQ-043-02 [MUST]: A részek összege pontosan a forrásösszeggel egyezik.
- REQ-043-03 [MUST]: A kerekítési maradvány explicit módon kezelhető.
- REQ-043-04 [MUST]: A résztvevő jóváhagyhat vagy vitathat.
- REQ-043-05 [MUST]: A módosítás verziózott és auditálható.
- REQ-043-06 [MUST]: Más tenant kedvezményezettje vagy forrása nem használható.
- REQ-043-07 [MUST]: Azonos mentési kérés egy felosztást eredményez.
- REQ-043-08 [MUST]: Riport és export nem számolja kétszer az eredetit és részeit.

## 6. Nem funkcionális követelmények

- NFR-043-01 [SECURITY]: minden olvasás és írás explicit tenant-filterrel, szerveroldali RBAC-kal és erőforrás-szintű ellenőrzéssel fut.
- NFR-043-02 [RELIABILITY]: módosítás atomi; timeout és retry nem hoz létre duplikátumot vagy félállapotot.
- NFR-043-03 [PERFORMANCE]: lista p95 ≤ 800 ms, parancs elfogadása p95 ≤ 1200 ms, hosszú munka 202 és követhető státusz.
- NFR-043-04 [ACCESSIBILITY]: WCAG 2.2 AA, billentyűzet, látható fókusz, programozott név, aria-live és legalább 44×44 CSS px cél.
- NFR-043-05 [PRIVACY]: log és telemetry nem tartalmaz teljes bizonylatképet, tokent vagy szükségtelen személyes pénzügyi adatot.
- NFR-043-06 [OBSERVABILITY]: correlation ID, audit actor, tenant, parancstípus, eredménykód, latency és retry számláló.

## 7. UI-szerződés

- UI-043-01: `cost_splits-page`, a `/cost-splits` kanonikus munkaterülete, loading/empty/error/ready állapotokkal.
- UI-043-02: `cost_splits-primary-action`, jogosultság- és állapotfüggő elsődleges művelet.
- UI-043-03: `cost_splits-evidence`, a döntés alapját és bizonytalanságát bemutató panel.
- UI-043-04: `cost_splits-status`, vizuális és aria-live állapotközlő.
- UI-043-05: `cost_splits-conflict`, adatvesztés nélküli konfliktus- és retry felület.

## 8. GUI-folyamat

1. A felhasználó megnyitja a `/cost-splits` útvonalat, a sessiont a `helpers/auth.ts` inicializálja.
2. A felület betöltési, majd tenant-szűrt ready vagy hasznos empty állapotot mutat.
3. A felhasználó megnyit egy tételt; a forrás, evidence, confidence, jogosultság és aktuális revízió látható.
4. Az elsődleges művelet előtt a kliens validál, veszélyes döntésnél megerősítést kér.
5. A kérés idempotenciakulccsal indul; in-flight állapotban ismételt aktiválás nem küld második parancsot.
6. Siker esetén az új revízió és állapot jelenik meg. 409 esetén konfliktusnézet, 4xx esetén javítható mezőhiba, hálózati hibánál adatmegőrző retry jelenik meg.
7. Frissítés és visszatérés után a szerverállapot reprodukálható, idegen tenant erőforrása nem látható.

## 9. Állapotmodell

Kanonikus állapotok: `DRAFT → PENDING_APPROVAL → APPROVED → DISPUTED → SUPERSEDED → CANCELLED`.

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
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    DISPUTED = "DISPUTED"
    SUPERSEDED = "SUPERSEDED"
    CANCELLED = "CANCELLED"

class CostSplitCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tenant_id: str = Field(min_length=1, max_length=128)
    client_reference: str = Field(min_length=1, max_length=128)
    payload: dict[str, Any]
    idempotency_key: str = Field(min_length=16, max_length=128)

class CostSplitCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: int = Field(ge=0)
    action: str = Field(min_length=1, max_length=64)
    reason: str | None = Field(default=None, max_length=1000)
    payload: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str = Field(min_length=16, max_length=128)

class CostSplitRead(BaseModel):
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
export type FeatureStatus = "DRAFT" | "PENDING_APPROVAL" | "APPROVED" | "DISPUTED" | "SUPERSEDED" | "CANCELLED";

export interface CostSplitCreate {
  tenantId: string;
  clientReference: string;
  payload: Record<string, unknown>;
  idempotencyKey: string;
}

export interface CostSplitCommand {
  expectedRevision: number;
  action: string;
  reason?: string;
  payload: Record<string, unknown>;
  idempotencyKey: string;
}

export interface CostSplitRead {
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

### AC-043-01: A vásárlás fix, százalékos, egyenlő vagy tételes módon felosztható.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-043-01 szerinti műveletet végrehajtja
Then a vásárlás fix, százalékos, egyenlő vagy tételes módon felosztható.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-043-02: A részek összege pontosan a forrásösszeggel egyezik.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-043-02 szerinti műveletet végrehajtja
Then a részek összege pontosan a forrásösszeggel egyezik.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-043-03: A kerekítési maradvány explicit módon kezelhető.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-043-03 szerinti műveletet végrehajtja
Then a kerekítési maradvány explicit módon kezelhető.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-043-04: A résztvevő jóváhagyhat vagy vitathat.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-043-04 szerinti műveletet végrehajtja
Then a résztvevő jóváhagyhat vagy vitathat.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-043-05: A módosítás verziózott és auditálható.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-043-05 szerinti műveletet végrehajtja
Then a módosítás verziózott és auditálható.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-043-06: Más tenant kedvezményezettje vagy forrása nem használható.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-043-06 szerinti műveletet végrehajtja
Then más tenant kedvezményezettje vagy forrása nem használható.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-043-07: Azonos mentési kérés egy felosztást eredményez.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-043-07 szerinti műveletet végrehajtja
Then azonos mentési kérés egy felosztást eredményez.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-043-08: Riport és export nem számolja kétszer az eredetit és részeit.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-043-08 szerinti műveletet végrehajtja
Then riport és export nem számolja kétszer az eredetit és részeit.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

## 11. API-szerződés

- `GET /api/v2/cost-splits`: tenant-szűrt lista; cursor pagination; 200/401/403.
- `POST /api/v2/cost-splits`: létrehozás vagy elemzés; kötelező `Idempotency-Key`; 201 vagy 202/400/401/403/409/422.
- `GET /api/v2/cost-splits/{id}`: részlet és evidence; idegen tenant esetén 404-szerű válasz.
- `PATCH /api/v2/cost-splits/{id}`: `expected_revision` alapú módosítás; 200/409/422.
- `POST /api/v2/cost-splits/{id}/confirm`: kontrollált állapotátmenet; 200/403/409/422.
- Minden hiba `application/problem+json` alakú `ApiProblem`; minden siker tenant- és revision-azonosítót ad.

### Lépésről lépésre kidolgozott kontrollfolyamat

1. A forrásnyugta vagy tranzakció tenant-szűréssel töltődik, és a split az eredeti összeget nem módosítja.
2. A módszer szerint számított részek összege pénznemi pontossággal pontosan total; eltérésre raise SplitTotalMismatchError(...).
3. Kerekítési maradvány explicit share mezőbe kerül, automatikus rejtett elosztás tilos.
4. Külső vagy háztartási kedvezményezett jogosultsága és hozzájárulása ellenőrzendő.
5. Jóváhagyás expected_revision és résztvevői állapot alapján atomi; vita DISPUTED állapotot hoz létre.
6. Módosítás új verziót hoz létre SUPERSEDED előddel; riportban az eredeti és aktív részek kettős számolása tilos.

## 12. Adatmodell és perzisztencia

- Fő aggregátum: `CostSplit`; kötelező `id`, `tenant_id`, `status`, `revision`, `created_at`, `updated_at`.
- Írások tenant tranzakcióban, optimistic lockinggal és idempotency rekorddal történnek.
- Egyedi kulcs: `(tenant_id, idempotency_key, command_type)`; az eltárolt request hash eltérés konfliktus.
- Audit esemény tartalmazza az aggregátumot, előző/új revíziót, aktort, okot, correlation ID-t és időt, de nem másol érzékeny teljes payloadot.
- Törlés csak projektmegőrzési szabály szerint; pénzügyi bizonyíték logikai törléssel és referenciaintegritással.

## 13. Tesztterv és lefedettségi leképezés

- REQ-043-01 → AC-043-01 → `.agent-pipeline/03_e2e_suites/test_e2e_043.py`; unit cél: `tests/unit/test_cost_splits_service.py::test_req_043_01`.
- REQ-043-02 → AC-043-02 → `.agent-pipeline/03_e2e_suites/test_e2e_043.py`; unit cél: `tests/unit/test_cost_splits_service.py::test_req_043_02`.
- REQ-043-03 → AC-043-03 → `.agent-pipeline/03_e2e_suites/test_e2e_043.py`; unit cél: `tests/unit/test_cost_splits_service.py::test_req_043_03`.
- REQ-043-04 → AC-043-04 → `.agent-pipeline/03_e2e_suites/test_e2e_043.py`; unit cél: `tests/unit/test_cost_splits_service.py::test_req_043_04`.
- REQ-043-05 → AC-043-05 → `.agent-pipeline/03_e2e_suites/test_e2e_043.py`; unit cél: `tests/unit/test_cost_splits_service.py::test_req_043_05`.
- REQ-043-06 → AC-043-06 → `.agent-pipeline/03_e2e_suites/test_e2e_043.py`; unit cél: `tests/unit/test_cost_splits_service.py::test_req_043_06`.
- REQ-043-07 → AC-043-07 → `.agent-pipeline/03_e2e_suites/test_e2e_043.py`; unit cél: `tests/unit/test_cost_splits_service.py::test_req_043_07`.
- REQ-043-08 → AC-043-08 → `.agent-pipeline/03_e2e_suites/test_e2e_043.py`; unit cél: `tests/unit/test_cost_splits_service.py::test_req_043_08`.

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
