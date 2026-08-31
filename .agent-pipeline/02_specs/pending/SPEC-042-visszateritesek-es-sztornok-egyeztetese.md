---
id: FEAT-042
title: Visszatérítések és sztornók egyeztetése
status: spec_ready
version: 1
risk: high
owner: system-architect
related_brief: BRIEF-042
---

# FEAT-042: Visszatérítések és sztornók egyeztetése

## 1. Cél és felhasználói eredmény

A BRIEF-042 képesség teljes, tenant-biztos, magyarázható és felhasználó által kontrollált megvalósítási szerződése. Kész akkor, ha mind a nyolc követelmény RED→GREEN bizonyítékkal, célzott teszttel és teljes regresszióval igazolt, és a felület hibánál nem állít valótlan sikert.

## 2. Kontextus és források

Kanonikus források: `briefs/BRIEF-042-visszateritesek-es-sztornok-egyeztetese.md`, `METHODOLOGY.md`, `.agents/rules/methodology.md`. Kapcsolódó platform-invariánsok: explicit tenant, szerveroldali RBAC, audit, revízió, idempotencia, stabil hibaszerződés és érzékeny adatok minimalizálása.

### Target Files

- `app/refund_models.py (NEW)`
- `app/refund_service.py (NEW)`
- `app/refund_api.py (NEW)`
- `app/api_v2.py (MODIFY)`
- `frontend/app/reconciliation/refunds/page.tsx (NEW)`
- `frontend/components/reconciliation/RefundWorkbench.tsx (NEW)`
- `frontend/lib/refunds.ts (NEW)`

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

- ACT-042-01: háztartási tag, aki saját jogosultságán belül használja a funkciót.
- ACT-042-02: tulajdonos vagy pénzügyi felelős, aki döntést és felülbírálást végez.
- ACT-042-03: könyvelő vagy ellenőrző, korlátozott, auditált hozzáféréssel.
- PRE-042-01: hitelesített session, aktív tenant és szerveroldalon ellenőrzött szerepkör.
- PRE-042-02: a hivatkozott források ugyanahhoz a tenanthoz tartoznak.
- PRE-042-03: módosításkor `expected_revision`, íráskor `Idempotency-Key` rendelkezésre áll.

## 5. Funkcionális követelmények

- REQ-042-01 [MUST]: A rendszer lehetséges jóváírást vagy sztornót felismer.
- REQ-042-02 [MUST]: Az eredeti vásárlás jelöltjei magyarázhatóan rangsoroltak.
- REQ-042-03 [MUST]: Teljes és részleges visszatérítés kapcsolható nyugtához és tételhez.
- REQ-042-04 [MUST]: A teljesült visszatérítés nettó hatása helyesen számolódik.
- REQ-042-05 [MUST]: Reversed jóváírás visszavezeti a pénzügyi hatást.
- REQ-042-06 [MUST]: Más tenant tranzakciója nem kapcsolható.
- REQ-042-07 [MUST]: Azonos allokációs kérés nem duplikál összeget.
- REQ-042-08 [MUST]: Párhuzamos allokáció nem enged túlvisszatérítést.

## 6. Nem funkcionális követelmények

- NFR-042-01 [SECURITY]: minden olvasás és írás explicit tenant-filterrel, szerveroldali RBAC-kal és erőforrás-szintű ellenőrzéssel fut.
- NFR-042-02 [RELIABILITY]: módosítás atomi; timeout és retry nem hoz létre duplikátumot vagy félállapotot.
- NFR-042-03 [PERFORMANCE]: lista p95 ≤ 800 ms, parancs elfogadása p95 ≤ 1200 ms, hosszú munka 202 és követhető státusz.
- NFR-042-04 [ACCESSIBILITY]: WCAG 2.2 AA, billentyűzet, látható fókusz, programozott név, aria-live és legalább 44×44 CSS px cél.
- NFR-042-05 [PRIVACY]: log és telemetry nem tartalmaz teljes bizonylatképet, tokent vagy szükségtelen személyes pénzügyi adatot.
- NFR-042-06 [OBSERVABILITY]: correlation ID, audit actor, tenant, parancstípus, eredménykód, latency és retry számláló.

## 7. UI-szerződés

- UI-042-01: `refunds-page`, a `/reconciliation/refunds` kanonikus munkaterülete, loading/empty/error/ready állapotokkal.
- UI-042-02: `refunds-primary-action`, jogosultság- és állapotfüggő elsődleges művelet.
- UI-042-03: `refunds-evidence`, a döntés alapját és bizonytalanságát bemutató panel.
- UI-042-04: `refunds-status`, vizuális és aria-live állapotközlő.
- UI-042-05: `refunds-conflict`, adatvesztés nélküli konfliktus- és retry felület.

## 8. GUI-folyamat

1. A felhasználó megnyitja a `/reconciliation/refunds` útvonalat, a sessiont a `helpers/auth.ts` inicializálja.
2. A felület betöltési, majd tenant-szűrt ready vagy hasznos empty állapotot mutat.
3. A felhasználó megnyit egy tételt; a forrás, evidence, confidence, jogosultság és aktuális revízió látható.
4. Az elsődleges művelet előtt a kliens validál, veszélyes döntésnél megerősítést kér.
5. A kérés idempotenciakulccsal indul; in-flight állapotban ismételt aktiválás nem küld második parancsot.
6. Siker esetén az új revízió és állapot jelenik meg. 409 esetén konfliktusnézet, 4xx esetén javítható mezőhiba, hálózati hibánál adatmegőrző retry jelenik meg.
7. Frissítés és visszatérés után a szerverállapot reprodukálható, idegen tenant erőforrása nem látható.

## 9. Állapotmodell

Kanonikus állapotok: `DETECTED → SUGGESTED → PARTIALLY_MATCHED → MATCHED → REVERSED → DISPUTED`.

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
    DETECTED = "DETECTED"
    SUGGESTED = "SUGGESTED"
    PARTIALLY_MATCHED = "PARTIALLY_MATCHED"
    MATCHED = "MATCHED"
    REVERSED = "REVERSED"
    DISPUTED = "DISPUTED"

class RefundMatchCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tenant_id: str = Field(min_length=1, max_length=128)
    client_reference: str = Field(min_length=1, max_length=128)
    payload: dict[str, Any]
    idempotency_key: str = Field(min_length=16, max_length=128)

class RefundMatchCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: int = Field(ge=0)
    action: str = Field(min_length=1, max_length=64)
    reason: str | None = Field(default=None, max_length=1000)
    payload: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str = Field(min_length=16, max_length=128)

class RefundMatchRead(BaseModel):
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
export type FeatureStatus = "DETECTED" | "SUGGESTED" | "PARTIALLY_MATCHED" | "MATCHED" | "REVERSED" | "DISPUTED";

export interface RefundMatchCreate {
  tenantId: string;
  clientReference: string;
  payload: Record<string, unknown>;
  idempotencyKey: string;
}

export interface RefundMatchCommand {
  expectedRevision: number;
  action: string;
  reason?: string;
  payload: Record<string, unknown>;
  idempotencyKey: string;
}

export interface RefundMatchRead {
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

### AC-042-01: A rendszer lehetséges jóváírást vagy sztornót felismer.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-042-01 szerinti műveletet végrehajtja
Then a rendszer lehetséges jóváírást vagy sztornót felismer.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-042-02: Az eredeti vásárlás jelöltjei magyarázhatóan rangsoroltak.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-042-02 szerinti műveletet végrehajtja
Then az eredeti vásárlás jelöltjei magyarázhatóan rangsoroltak.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-042-03: Teljes és részleges visszatérítés kapcsolható nyugtához és tételhez.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-042-03 szerinti műveletet végrehajtja
Then teljes és részleges visszatérítés kapcsolható nyugtához és tételhez.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-042-04: A teljesült visszatérítés nettó hatása helyesen számolódik.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-042-04 szerinti műveletet végrehajtja
Then a teljesült visszatérítés nettó hatása helyesen számolódik.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-042-05: Reversed jóváírás visszavezeti a pénzügyi hatást.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-042-05 szerinti műveletet végrehajtja
Then reversed jóváírás visszavezeti a pénzügyi hatást.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-042-06: Más tenant tranzakciója nem kapcsolható.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-042-06 szerinti műveletet végrehajtja
Then más tenant tranzakciója nem kapcsolható.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-042-07: Azonos allokációs kérés nem duplikál összeget.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-042-07 szerinti műveletet végrehajtja
Then azonos allokációs kérés nem duplikál összeget.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-042-08: Párhuzamos allokáció nem enged túlvisszatérítést.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-042-08 szerinti műveletet végrehajtja
Then párhuzamos allokáció nem enged túlvisszatérítést.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

## 11. API-szerződés

- `GET /api/v2/refunds`: tenant-szűrt lista; cursor pagination; 200/401/403.
- `POST /api/v2/refunds`: létrehozás vagy elemzés; kötelező `Idempotency-Key`; 201 vagy 202/400/401/403/409/422.
- `GET /api/v2/refunds/{id}`: részlet és evidence; idegen tenant esetén 404-szerű válasz.
- `PATCH /api/v2/refunds/{id}`: `expected_revision` alapú módosítás; 200/409/422.
- `POST /api/v2/refunds/{id}/confirm`: kontrollált állapotátmenet; 200/403/409/422.
- Minden hiba `application/problem+json` alakú `ApiProblem`; minden siker tenant- és revision-azonosítót ad.

### Lépésről lépésre kidolgozott kontrollfolyamat

1. Pozitív jóváírás vagy visszafordítás csak explicit tranzakciójel és tenant-szűrés után lesz jelölt.
2. A rangsorolás összeg-, pénznem-, kereskedő-, idő- és korábbi kapcsolati evidence alapján készül.
3. Confirm előtt a szolgáltatás ellenőrzi, hogy a teljesült visszatérítések összege nem haladja meg a visszatéríthető összeget; ellenkező esetben raise OverRefundError(...).
4. Részleges és több részletű visszatérítés allokációi atomiak; a pending összeg nem csökkenti a tényleges nettó költést.
5. A jóváírás reversed állapota visszavezeti a nettó hatást, de nem törli az auditkapcsolatot.
6. Idempotency key védi a dupla allokációt; idegen tenant és jogosulatlan szerepkör nem kap erőforrás-létezési információt.

## 12. Adatmodell és perzisztencia

- Fő aggregátum: `RefundMatch`; kötelező `id`, `tenant_id`, `status`, `revision`, `created_at`, `updated_at`.
- Írások tenant tranzakcióban, optimistic lockinggal és idempotency rekorddal történnek.
- Egyedi kulcs: `(tenant_id, idempotency_key, command_type)`; az eltárolt request hash eltérés konfliktus.
- Audit esemény tartalmazza az aggregátumot, előző/új revíziót, aktort, okot, correlation ID-t és időt, de nem másol érzékeny teljes payloadot.
- Törlés csak projektmegőrzési szabály szerint; pénzügyi bizonyíték logikai törléssel és referenciaintegritással.

## 13. Tesztterv és lefedettségi leképezés

- REQ-042-01 → AC-042-01 → `.agent-pipeline/03_e2e_suites/test_e2e_042.py`; unit cél: `tests/unit/test_refunds_service.py::test_req_042_01`.
- REQ-042-02 → AC-042-02 → `.agent-pipeline/03_e2e_suites/test_e2e_042.py`; unit cél: `tests/unit/test_refunds_service.py::test_req_042_02`.
- REQ-042-03 → AC-042-03 → `.agent-pipeline/03_e2e_suites/test_e2e_042.py`; unit cél: `tests/unit/test_refunds_service.py::test_req_042_03`.
- REQ-042-04 → AC-042-04 → `.agent-pipeline/03_e2e_suites/test_e2e_042.py`; unit cél: `tests/unit/test_refunds_service.py::test_req_042_04`.
- REQ-042-05 → AC-042-05 → `.agent-pipeline/03_e2e_suites/test_e2e_042.py`; unit cél: `tests/unit/test_refunds_service.py::test_req_042_05`.
- REQ-042-06 → AC-042-06 → `.agent-pipeline/03_e2e_suites/test_e2e_042.py`; unit cél: `tests/unit/test_refunds_service.py::test_req_042_06`.
- REQ-042-07 → AC-042-07 → `.agent-pipeline/03_e2e_suites/test_e2e_042.py`; unit cél: `tests/unit/test_refunds_service.py::test_req_042_07`.
- REQ-042-08 → AC-042-08 → `.agent-pipeline/03_e2e_suites/test_e2e_042.py`; unit cél: `tests/unit/test_refunds_service.py::test_req_042_08`.

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
