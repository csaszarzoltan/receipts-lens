---
id: FEAT-039
title: Hiányzó nyugták követése
status: spec_ready
version: 1
risk: high
owner: system-architect
related_brief: BRIEF-039
---

# FEAT-039: Hiányzó nyugták követése

## 1. Cél és felhasználói eredmény

A BRIEF-039 képesség teljes, tenant-biztos, magyarázható és felhasználó által kontrollált megvalósítási szerződése. Kész akkor, ha mind a nyolc követelmény RED→GREEN bizonyítékkal, célzott teszttel és teljes regresszióval igazolt, és a felület hibánál nem állít valótlan sikert.

## 2. Kontextus és források

Kanonikus források: `briefs/BRIEF-039-hianyzo-nyugtak-kovetese.md`, `METHODOLOGY.md`, `.agents/rules/methodology.md`. Kapcsolódó platform-invariánsok: explicit tenant, szerveroldali RBAC, audit, revízió, idempotencia, stabil hibaszerződés és érzékeny adatok minimalizálása.

### Target Files

- `app/missing_receipt_models.py (NEW)`
- `app/missing_receipt_service.py (NEW)`
- `app/missing_receipt_api.py (NEW)`
- `app/api_v2.py (MODIFY)`
- `frontend/app/missing-receipts/page.tsx (NEW)`
- `frontend/components/missing-receipts/MissingReceiptInbox.tsx (NEW)`
- `frontend/lib/missingReceipts.ts (NEW)`

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

- ACT-039-01: háztartási tag, aki saját jogosultságán belül használja a funkciót.
- ACT-039-02: tulajdonos vagy pénzügyi felelős, aki döntést és felülbírálást végez.
- ACT-039-03: könyvelő vagy ellenőrző, korlátozott, auditált hozzáféréssel.
- PRE-039-01: hitelesített session, aktív tenant és szerveroldalon ellenőrzött szerepkör.
- PRE-039-02: a hivatkozott források ugyanahhoz a tenanthoz tartoznak.
- PRE-039-03: módosításkor `expected_revision`, íráskor `Idempotency-Key` rendelkezésre áll.

## 5. Funkcionális követelmények

- REQ-039-01 [MUST]: A rendszer felismeri a bizonylatot igénylő, nyugta nélküli tranzakciót.
- REQ-039-02 [MUST]: A feladat felelőshöz, határidőhöz és prioritáshoz rendelhető.
- REQ-039-03 [MUST]: Nyugta vagy helyettesítő dokumentum a feladatból kapcsolható.
- REQ-039-04 [MUST]: Nem beszerezhető nyugta indokolt kivételként kezelhető.
- REQ-039-05 [MUST]: Az emlékeztetők szabályozhatók és deduplikáltak.
- REQ-039-06 [MUST]: Más tenant feladata nem hozzáférhető.
- REQ-039-07 [MUST]: Azonos feloldási kérés nem duplikál kapcsolatot vagy értesítést.
- REQ-039-08 [MUST]: Forráskapcsolat felbontása következetesen újranyitja a feladatot.

## 6. Nem funkcionális követelmények

- NFR-039-01 [SECURITY]: minden olvasás és írás explicit tenant-filterrel, szerveroldali RBAC-kal és erőforrás-szintű ellenőrzéssel fut.
- NFR-039-02 [RELIABILITY]: módosítás atomi; timeout és retry nem hoz létre duplikátumot vagy félállapotot.
- NFR-039-03 [PERFORMANCE]: lista p95 ≤ 800 ms, parancs elfogadása p95 ≤ 1200 ms, hosszú munka 202 és követhető státusz.
- NFR-039-04 [ACCESSIBILITY]: WCAG 2.2 AA, billentyűzet, látható fókusz, programozott név, aria-live és legalább 44×44 CSS px cél.
- NFR-039-05 [PRIVACY]: log és telemetry nem tartalmaz teljes bizonylatképet, tokent vagy szükségtelen személyes pénzügyi adatot.
- NFR-039-06 [OBSERVABILITY]: correlation ID, audit actor, tenant, parancstípus, eredménykód, latency és retry számláló.

## 7. UI-szerződés

- UI-039-01: `missing_receipts-page`, a `/missing-receipts` kanonikus munkaterülete, loading/empty/error/ready állapotokkal.
- UI-039-02: `missing_receipts-primary-action`, jogosultság- és állapotfüggő elsődleges művelet.
- UI-039-03: `missing_receipts-evidence`, a döntés alapját és bizonytalanságát bemutató panel.
- UI-039-04: `missing_receipts-status`, vizuális és aria-live állapotközlő.
- UI-039-05: `missing_receipts-conflict`, adatvesztés nélküli konfliktus- és retry felület.

## 8. GUI-folyamat

1. A felhasználó megnyitja a `/missing-receipts` útvonalat, a sessiont a `helpers/auth.ts` inicializálja.
2. A felület betöltési, majd tenant-szűrt ready vagy hasznos empty állapotot mutat.
3. A felhasználó megnyit egy tételt; a forrás, evidence, confidence, jogosultság és aktuális revízió látható.
4. Az elsődleges művelet előtt a kliens validál, veszélyes döntésnél megerősítést kér.
5. A kérés idempotenciakulccsal indul; in-flight állapotban ismételt aktiválás nem küld második parancsot.
6. Siker esetén az új revízió és állapot jelenik meg. 409 esetén konfliktusnézet, 4xx esetén javítható mezőhiba, hálózati hibánál adatmegőrző retry jelenik meg.
7. Frissítés és visszatérés után a szerverállapot reprodukálható, idegen tenant erőforrása nem látható.

## 9. Állapotmodell

Kanonikus állapotok: `OPEN → ASSIGNED → SNOOZED → EXEMPTED → RESOLVED → REOPENED`.

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
    SNOOZED = "SNOOZED"
    EXEMPTED = "EXEMPTED"
    RESOLVED = "RESOLVED"
    REOPENED = "REOPENED"

class MissingReceiptTaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tenant_id: str = Field(min_length=1, max_length=128)
    client_reference: str = Field(min_length=1, max_length=128)
    payload: dict[str, Any]
    idempotency_key: str = Field(min_length=16, max_length=128)

class MissingReceiptTaskCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: int = Field(ge=0)
    action: str = Field(min_length=1, max_length=64)
    reason: str | None = Field(default=None, max_length=1000)
    payload: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str = Field(min_length=16, max_length=128)

class MissingReceiptTaskRead(BaseModel):
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
export type FeatureStatus = "OPEN" | "ASSIGNED" | "SNOOZED" | "EXEMPTED" | "RESOLVED" | "REOPENED";

export interface MissingReceiptTaskCreate {
  tenantId: string;
  clientReference: string;
  payload: Record<string, unknown>;
  idempotencyKey: string;
}

export interface MissingReceiptTaskCommand {
  expectedRevision: number;
  action: string;
  reason?: string;
  payload: Record<string, unknown>;
  idempotencyKey: string;
}

export interface MissingReceiptTaskRead {
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

### AC-039-01: A rendszer felismeri a bizonylatot igénylő, nyugta nélküli tranzakciót.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-039-01 szerinti műveletet végrehajtja
Then a rendszer felismeri a bizonylatot igénylő, nyugta nélküli tranzakciót.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-039-02: A feladat felelőshöz, határidőhöz és prioritáshoz rendelhető.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-039-02 szerinti műveletet végrehajtja
Then a feladat felelőshöz, határidőhöz és prioritáshoz rendelhető.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-039-03: Nyugta vagy helyettesítő dokumentum a feladatból kapcsolható.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-039-03 szerinti műveletet végrehajtja
Then nyugta vagy helyettesítő dokumentum a feladatból kapcsolható.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-039-04: Nem beszerezhető nyugta indokolt kivételként kezelhető.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-039-04 szerinti műveletet végrehajtja
Then nem beszerezhető nyugta indokolt kivételként kezelhető.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-039-05: Az emlékeztetők szabályozhatók és deduplikáltak.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-039-05 szerinti műveletet végrehajtja
Then az emlékeztetők szabályozhatók és deduplikáltak.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-039-06: Más tenant feladata nem hozzáférhető.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-039-06 szerinti műveletet végrehajtja
Then más tenant feladata nem hozzáférhető.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-039-07: Azonos feloldási kérés nem duplikál kapcsolatot vagy értesítést.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-039-07 szerinti műveletet végrehajtja
Then azonos feloldási kérés nem duplikál kapcsolatot vagy értesítést.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-039-08: Forráskapcsolat felbontása következetesen újranyitja a feladatot.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-039-08 szerinti műveletet végrehajtja
Then forráskapcsolat felbontása következetesen újranyitja a feladatot.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

## 11. API-szerződés

- `GET /api/v2/missing-receipts`: tenant-szűrt lista; cursor pagination; 200/401/403.
- `POST /api/v2/missing-receipts`: létrehozás vagy elemzés; kötelező `Idempotency-Key`; 201 vagy 202/400/401/403/409/422.
- `GET /api/v2/missing-receipts/{id}`: részlet és evidence; idegen tenant esetén 404-szerű válasz.
- `PATCH /api/v2/missing-receipts/{id}`: `expected_revision` alapú módosítás; 200/409/422.
- `POST /api/v2/missing-receipts/{id}/confirm`: kontrollált állapotátmenet; 200/403/409/422.
- Minden hiba `application/problem+json` alakú `ApiProblem`; minden siker tenant- és revision-azonosítót ad.

### Lépésről lépésre kidolgozott kontrollfolyamat

1. A detektor csak könyvelt, bizonylatot igénylő és aktív tenantba tartozó, érvényes nyugtával nem kapcsolt tranzakcióból hoz létre feladatot.
2. A felismerési ok és szabályverzió elmentendő; a felhasználó bizonylatot nem igénylő kivételt dokumentálhat.
3. Assign művelet tenant-tagságot, szerepkört és revíziót ellenőriz; érvénytelen felelősre raise InvalidAssigneeError(...).
4. Az emlékeztető a policy, esedékesség, quiet hours és korábbi kézbesítés alapján deduplikált; azonos reminder event nem küldhető kétszer.
5. Receipt vagy helyettesítő dokumentum kapcsolása atomi módon RESOLVED állapotot ad; a kapcsolat felbontása REOPENED állapotot eredményez.
6. Idempotens újrapróbálás az eredeti választ adja; jogosulatlan hozzáférés 403, idegen tenant erőforrása 404-szerű válasz és nulla adatváltozás.

## 12. Adatmodell és perzisztencia

- Fő aggregátum: `MissingReceiptTask`; kötelező `id`, `tenant_id`, `status`, `revision`, `created_at`, `updated_at`.
- Írások tenant tranzakcióban, optimistic lockinggal és idempotency rekorddal történnek.
- Egyedi kulcs: `(tenant_id, idempotency_key, command_type)`; az eltárolt request hash eltérés konfliktus.
- Audit esemény tartalmazza az aggregátumot, előző/új revíziót, aktort, okot, correlation ID-t és időt, de nem másol érzékeny teljes payloadot.
- Törlés csak projektmegőrzési szabály szerint; pénzügyi bizonyíték logikai törléssel és referenciaintegritással.

## 13. Tesztterv és lefedettségi leképezés

- REQ-039-01 → AC-039-01 → `.agent-pipeline/03_e2e_suites/test_e2e_039.py`; unit cél: `tests/unit/test_missing_receipts_service.py::test_req_039_01`.
- REQ-039-02 → AC-039-02 → `.agent-pipeline/03_e2e_suites/test_e2e_039.py`; unit cél: `tests/unit/test_missing_receipts_service.py::test_req_039_02`.
- REQ-039-03 → AC-039-03 → `.agent-pipeline/03_e2e_suites/test_e2e_039.py`; unit cél: `tests/unit/test_missing_receipts_service.py::test_req_039_03`.
- REQ-039-04 → AC-039-04 → `.agent-pipeline/03_e2e_suites/test_e2e_039.py`; unit cél: `tests/unit/test_missing_receipts_service.py::test_req_039_04`.
- REQ-039-05 → AC-039-05 → `.agent-pipeline/03_e2e_suites/test_e2e_039.py`; unit cél: `tests/unit/test_missing_receipts_service.py::test_req_039_05`.
- REQ-039-06 → AC-039-06 → `.agent-pipeline/03_e2e_suites/test_e2e_039.py`; unit cél: `tests/unit/test_missing_receipts_service.py::test_req_039_06`.
- REQ-039-07 → AC-039-07 → `.agent-pipeline/03_e2e_suites/test_e2e_039.py`; unit cél: `tests/unit/test_missing_receipts_service.py::test_req_039_07`.
- REQ-039-08 → AC-039-08 → `.agent-pipeline/03_e2e_suites/test_e2e_039.py`; unit cél: `tests/unit/test_missing_receipts_service.py::test_req_039_08`.

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
