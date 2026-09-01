---
id: FEAT-041
title: Háztartási bevásárlási árfigyelés
status: spec_ready
version: 1
risk: high
owner: system-architect
related_brief: BRIEF-041
---

# FEAT-041: Háztartási bevásárlási árfigyelés

## 1. Cél és felhasználói eredmény

A BRIEF-041 képesség teljes, tenant-biztos, magyarázható és felhasználó által kontrollált megvalósítási szerződése. Kész akkor, ha mind a nyolc követelmény RED→GREEN bizonyítékkal, célzott teszttel és teljes regresszióval igazolt, és a felület hibánál nem állít valótlan sikert.

## 2. Kontextus és források

Kanonikus források: `briefs/BRIEF-041-haztartasi-bevasarlasi-arfigyeles.md`, `METHODOLOGY.md`, `.agents/rules/methodology.md`. Kapcsolódó platform-invariánsok: explicit tenant, szerveroldali RBAC, audit, revízió, idempotencia, stabil hibaszerződés és érzékeny adatok minimalizálása.

### Target Files

- `app/price_tracking_models.py (NEW)`
- `app/price_tracking_service.py (NEW)`
- `app/price_tracking_api.py (NEW)`
- `app/api_v2.py (MODIFY)`
- `frontend/app/price-tracking/page.tsx (NEW)`
- `frontend/components/price-tracking/PriceTrendPanel.tsx (NEW)`
- `frontend/lib/priceTracking.ts (NEW)`

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

- ACT-041-01: háztartási tag, aki saját jogosultságán belül használja a funkciót.
- ACT-041-02: tulajdonos vagy pénzügyi felelős, aki döntést és felülbírálást végez.
- ACT-041-03: könyvelő vagy ellenőrző, korlátozott, auditált hozzáféréssel.
- PRE-041-01: hitelesített session, aktív tenant és szerveroldalon ellenőrzött szerepkör.
- PRE-041-02: a hivatkozott források ugyanahhoz a tenanthoz tartoznak.
- PRE-041-03: módosításkor `expected_revision`, íráskor `Idempotency-Key` rendelkezésre áll.

## 5. Funkcionális követelmények

- REQ-041-01 [MUST]: A rendszer követhető termékjelölteket képez nyugtatételekből.
- REQ-041-02 [MUST]: A felhasználó aliasokat összevonhat vagy szétválaszthat.
- REQ-041-03 [MUST]: Kompatibilis mennyiségek egységárra normalizálhatók.
- REQ-041-04 [MUST]: A trend forrásmegfigyelésekkel és mintanagysággal látható.
- REQ-041-05 [MUST]: Szokatlan drágulás csak megfelelő adat és küszöb esetén jelezhető.
- REQ-041-06 [MUST]: Más tenant termék- és ártörténete nem hozzáférhető.
- REQ-041-07 [MUST]: Azonos elemzési futás nem duplikál riasztást.
- REQ-041-08 [MUST]: Felhasználói kizárás után a trend konzisztensen újraszámolódik.

## 6. Nem funkcionális követelmények

- NFR-041-01 [SECURITY]: minden olvasás és írás explicit tenant-filterrel, szerveroldali RBAC-kal és erőforrás-szintű ellenőrzéssel fut.
- NFR-041-02 [RELIABILITY]: módosítás atomi; timeout és retry nem hoz létre duplikátumot vagy félállapotot.
- NFR-041-03 [PERFORMANCE]: lista p95 ≤ 800 ms, parancs elfogadása p95 ≤ 1200 ms, hosszú munka 202 és követhető státusz.
- NFR-041-04 [ACCESSIBILITY]: WCAG 2.2 AA, billentyűzet, látható fókusz, programozott név, aria-live és legalább 44×44 CSS px cél.
- NFR-041-05 [PRIVACY]: log és telemetry nem tartalmaz teljes bizonylatképet, tokent vagy szükségtelen személyes pénzügyi adatot.
- NFR-041-06 [OBSERVABILITY]: correlation ID, audit actor, tenant, parancstípus, eredménykód, latency és retry számláló.

## 7. UI-szerződés

- UI-041-01: `price_tracking-page`, a `/price-tracking` kanonikus munkaterülete, loading/empty/error/ready állapotokkal.
- UI-041-02: `price_tracking-primary-action`, jogosultság- és állapotfüggő elsődleges művelet.
- UI-041-03: `price_tracking-evidence`, a döntés alapját és bizonytalanságát bemutató panel.
- UI-041-04: `price_tracking-status`, vizuális és aria-live állapotközlő.
- UI-041-05: `price_tracking-conflict`, adatvesztés nélküli konfliktus- és retry felület.

## 8. GUI-folyamat

1. A felhasználó megnyitja a `/price-tracking` útvonalat, a sessiont a `helpers/auth.ts` inicializálja.
2. A felület betöltési, majd tenant-szűrt ready vagy hasznos empty állapotot mutat.
3. A felhasználó megnyit egy tételt; a forrás, evidence, confidence, jogosultság és aktuális revízió látható.
4. Az elsődleges művelet előtt a kliens validál, veszélyes döntésnél megerősítést kér.
5. A kérés idempotenciakulccsal indul; in-flight állapotban ismételt aktiválás nem küld második parancsot.
6. Siker esetén az új revízió és állapot jelenik meg. 409 esetén konfliktusnézet, 4xx esetén javítható mezőhiba, hálózati hibánál adatmegőrző retry jelenik meg.
7. Frissítés és visszatérés után a szerverállapot reprodukálható, idegen tenant erőforrása nem látható.

## 9. Állapotmodell

Kanonikus állapotok: `CANDIDATE → TRACKED → NEEDS_REVIEW → PAUSED → ARCHIVED`.

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
    CANDIDATE = "CANDIDATE"
    TRACKED = "TRACKED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    PAUSED = "PAUSED"
    ARCHIVED = "ARCHIVED"

class TrackedProductCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tenant_id: str = Field(min_length=1, max_length=128)
    client_reference: str = Field(min_length=1, max_length=128)
    payload: dict[str, Any]
    idempotency_key: str = Field(min_length=16, max_length=128)

class TrackedProductCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: int = Field(ge=0)
    action: str = Field(min_length=1, max_length=64)
    reason: str | None = Field(default=None, max_length=1000)
    payload: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str = Field(min_length=16, max_length=128)

class TrackedProductRead(BaseModel):
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
export type FeatureStatus = "CANDIDATE" | "TRACKED" | "NEEDS_REVIEW" | "PAUSED" | "ARCHIVED";

export interface TrackedProductCreate {
  tenantId: string;
  clientReference: string;
  payload: Record<string, unknown>;
  idempotencyKey: string;
}

export interface TrackedProductCommand {
  expectedRevision: number;
  action: string;
  reason?: string;
  payload: Record<string, unknown>;
  idempotencyKey: string;
}

export interface TrackedProductRead {
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

### AC-041-01: A rendszer követhető termékjelölteket képez nyugtatételekből.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-041-01 szerinti műveletet végrehajtja
Then a rendszer követhető termékjelölteket képez nyugtatételekből.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-041-02: A felhasználó aliasokat összevonhat vagy szétválaszthat.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-041-02 szerinti műveletet végrehajtja
Then a felhasználó aliasokat összevonhat vagy szétválaszthat.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-041-03: Kompatibilis mennyiségek egységárra normalizálhatók.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-041-03 szerinti műveletet végrehajtja
Then kompatibilis mennyiségek egységárra normalizálhatók.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-041-04: A trend forrásmegfigyelésekkel és mintanagysággal látható.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-041-04 szerinti műveletet végrehajtja
Then a trend forrásmegfigyelésekkel és mintanagysággal látható.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-041-05: Szokatlan drágulás csak megfelelő adat és küszöb esetén jelezhető.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-041-05 szerinti műveletet végrehajtja
Then szokatlan drágulás csak megfelelő adat és küszöb esetén jelezhető.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-041-06: Más tenant termék- és ártörténete nem hozzáférhető.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-041-06 szerinti műveletet végrehajtja
Then más tenant termék- és ártörténete nem hozzáférhető.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-041-07: Azonos elemzési futás nem duplikál riasztást.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-041-07 szerinti műveletet végrehajtja
Then azonos elemzési futás nem duplikál riasztást.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-041-08: Felhasználói kizárás után a trend konzisztensen újraszámolódik.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-041-08 szerinti műveletet végrehajtja
Then felhasználói kizárás után a trend konzisztensen újraszámolódik.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

## 11. API-szerződés

- `GET /api/v2/price-tracking`: tenant-szűrt lista; cursor pagination; 200/401/403.
- `POST /api/v2/price-tracking`: létrehozás vagy elemzés; kötelező `Idempotency-Key`; 201 vagy 202/400/401/403/409/422.
- `GET /api/v2/price-tracking/{id}`: részlet és evidence; idegen tenant esetén 404-szerű válasz.
- `PATCH /api/v2/price-tracking/{id}`: `expected_revision` alapú módosítás; 200/409/422.
- `POST /api/v2/price-tracking/{id}/confirm`: kontrollált állapotátmenet; 200/403/409/422.
- Minden hiba `application/problem+json` alakú `ApiProblem`; minden siker tenant- és revision-azonosítót ad.

### Lépésről lépésre kidolgozott kontrollfolyamat

1. A termékjelöltek kizárólag tenanton belüli nyugtatételekből készülnek; alias-összevonás felhasználói jóváhagyást igényel.
2. A normalizálás csak kompatibilis mértékegységek között történhet; ellenkező esetben raise IncompatibleUnitError(...).
3. A baseline kizárt akciós, hibás vagy bizonytalan megfigyelést nem használhat, és közli a mintanagyságot.
4. Riasztás csak elegendő minta, küszöbátlépés és új evidencia esetén jön létre; dedupe kulcs védi az ismétlést.
5. A felhasználói kizárás újraszámolja a trendet, de megőrzi az auditnyomot és a forrásnyugta kapcsolatot.
6. Kevés adat esetén strukturált INSUFFICIENT_DATA eredmény jön, nem magabiztos drágulási állítás.

## 12. Adatmodell és perzisztencia

- Fő aggregátum: `TrackedProduct`; kötelező `id`, `tenant_id`, `status`, `revision`, `created_at`, `updated_at`.
- Írások tenant tranzakcióban, optimistic lockinggal és idempotency rekorddal történnek.
- Egyedi kulcs: `(tenant_id, idempotency_key, command_type)`; az eltárolt request hash eltérés konfliktus.
- Audit esemény tartalmazza az aggregátumot, előző/új revíziót, aktort, okot, correlation ID-t és időt, de nem másol érzékeny teljes payloadot.
- Törlés csak projektmegőrzési szabály szerint; pénzügyi bizonyíték logikai törléssel és referenciaintegritással.

## 13. Tesztterv és lefedettségi leképezés

- REQ-041-01 → AC-041-01 → `.agent-pipeline/03_e2e_suites/test_e2e_041.py`; unit cél: `tests/unit/test_price_tracking_service.py::test_req_041_01`.
- REQ-041-02 → AC-041-02 → `.agent-pipeline/03_e2e_suites/test_e2e_041.py`; unit cél: `tests/unit/test_price_tracking_service.py::test_req_041_02`.
- REQ-041-03 → AC-041-03 → `.agent-pipeline/03_e2e_suites/test_e2e_041.py`; unit cél: `tests/unit/test_price_tracking_service.py::test_req_041_03`.
- REQ-041-04 → AC-041-04 → `.agent-pipeline/03_e2e_suites/test_e2e_041.py`; unit cél: `tests/unit/test_price_tracking_service.py::test_req_041_04`.
- REQ-041-05 → AC-041-05 → `.agent-pipeline/03_e2e_suites/test_e2e_041.py`; unit cél: `tests/unit/test_price_tracking_service.py::test_req_041_05`.
- REQ-041-06 → AC-041-06 → `.agent-pipeline/03_e2e_suites/test_e2e_041.py`; unit cél: `tests/unit/test_price_tracking_service.py::test_req_041_06`.
- REQ-041-07 → AC-041-07 → `.agent-pipeline/03_e2e_suites/test_e2e_041.py`; unit cél: `tests/unit/test_price_tracking_service.py::test_req_041_07`.
- REQ-041-08 → AC-041-08 → `.agent-pipeline/03_e2e_suites/test_e2e_041.py`; unit cél: `tests/unit/test_price_tracking_service.py::test_req_041_08`.

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
