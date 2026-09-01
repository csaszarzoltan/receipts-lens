---
id: FEAT-040
title: Garanciák és visszaküldési határidők
status: spec_ready
version: 1
risk: high
owner: system-architect
related_brief: BRIEF-040
---

# FEAT-040: Garanciák és visszaküldési határidők

## 1. Cél és felhasználói eredmény

A BRIEF-040 képesség teljes, tenant-biztos, magyarázható és felhasználó által kontrollált megvalósítási szerződése. Kész akkor, ha mind a nyolc követelmény RED→GREEN bizonyítékkal, célzott teszttel és teljes regresszióval igazolt, és a felület hibánál nem állít valótlan sikert.

## 2. Kontextus és források

Kanonikus források: `briefs/BRIEF-040-garanciak-es-visszakuldesi-hataridok.md`, `METHODOLOGY.md`, `.agents/rules/methodology.md`. Kapcsolódó platform-invariánsok: explicit tenant, szerveroldali RBAC, audit, revízió, idempotencia, stabil hibaszerződés és érzékeny adatok minimalizálása.

### Target Files

- `app/warranty_models.py (NEW)`
- `app/warranty_service.py (NEW)`
- `app/warranty_api.py (NEW)`
- `app/api_v2.py (MODIFY)`
- `frontend/app/warranties/page.tsx (NEW)`
- `frontend/components/warranties/WarrantyTimeline.tsx (NEW)`
- `frontend/lib/warranties.ts (NEW)`

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

- ACT-040-01: háztartási tag, aki saját jogosultságán belül használja a funkciót.
- ACT-040-02: tulajdonos vagy pénzügyi felelős, aki döntést és felülbírálást végez.
- ACT-040-03: könyvelő vagy ellenőrző, korlátozott, auditált hozzáféréssel.
- PRE-040-01: hitelesített session, aktív tenant és szerveroldalon ellenőrzött szerepkör.
- PRE-040-02: a hivatkozott források ugyanahhoz a tenanthoz tartoznak.
- PRE-040-03: módosításkor `expected_revision`, íráskor `Idempotency-Key` rendelkezésre áll.

## 5. Funkcionális követelmények

- REQ-040-01 [MUST]: Nyugtatételből garanciális vagy visszaküldési eset hozható létre.
- REQ-040-02 [MUST]: A javasolt határidő forrással látható és felülbírálható.
- REQ-040-03 [MUST]: Kapcsolódó bizonylat, sorozatszám és hivatkozás rögzíthető.
- REQ-040-04 [MUST]: Közelgő határidőhöz deduplikált emlékeztető tartozik.
- REQ-040-05 [MUST]: Az ügy teljes életciklusa követhető.
- REQ-040-06 [MUST]: Más tenant esete nem hozzáférhető.
- REQ-040-07 [MUST]: Azonos létrehozási kérés egy esetet eredményez.
- REQ-040-08 [MUST]: Párhuzamos állapotváltás revíziókonfliktust ad.

## 6. Nem funkcionális követelmények

- NFR-040-01 [SECURITY]: minden olvasás és írás explicit tenant-filterrel, szerveroldali RBAC-kal és erőforrás-szintű ellenőrzéssel fut.
- NFR-040-02 [RELIABILITY]: módosítás atomi; timeout és retry nem hoz létre duplikátumot vagy félállapotot.
- NFR-040-03 [PERFORMANCE]: lista p95 ≤ 800 ms, parancs elfogadása p95 ≤ 1200 ms, hosszú munka 202 és követhető státusz.
- NFR-040-04 [ACCESSIBILITY]: WCAG 2.2 AA, billentyűzet, látható fókusz, programozott név, aria-live és legalább 44×44 CSS px cél.
- NFR-040-05 [PRIVACY]: log és telemetry nem tartalmaz teljes bizonylatképet, tokent vagy szükségtelen személyes pénzügyi adatot.
- NFR-040-06 [OBSERVABILITY]: correlation ID, audit actor, tenant, parancstípus, eredménykód, latency és retry számláló.

## 7. UI-szerződés

- UI-040-01: `warranties-page`, a `/warranties` kanonikus munkaterülete, loading/empty/error/ready állapotokkal.
- UI-040-02: `warranties-primary-action`, jogosultság- és állapotfüggő elsődleges művelet.
- UI-040-03: `warranties-evidence`, a döntés alapját és bizonytalanságát bemutató panel.
- UI-040-04: `warranties-status`, vizuális és aria-live állapotközlő.
- UI-040-05: `warranties-conflict`, adatvesztés nélküli konfliktus- és retry felület.

## 8. GUI-folyamat

1. A felhasználó megnyitja a `/warranties` útvonalat, a sessiont a `helpers/auth.ts` inicializálja.
2. A felület betöltési, majd tenant-szűrt ready vagy hasznos empty állapotot mutat.
3. A felhasználó megnyit egy tételt; a forrás, evidence, confidence, jogosultság és aktuális revízió látható.
4. Az elsődleges művelet előtt a kliens validál, veszélyes döntésnél megerősítést kér.
5. A kérés idempotenciakulccsal indul; in-flight állapotban ismételt aktiválás nem küld második parancsot.
6. Siker esetén az új revízió és állapot jelenik meg. 409 esetén konfliktusnézet, 4xx esetén javítható mezőhiba, hálózati hibánál adatmegőrző retry jelenik meg.
7. Frissítés és visszatérés után a szerverállapot reprodukálható, idegen tenant erőforrása nem látható.

## 9. Állapotmodell

Kanonikus állapotok: `DRAFT → ACTIVE → RETURN_STARTED → CLAIM_STARTED → RESOLVED → EXPIRED → CANCELLED`.

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
    RETURN_STARTED = "RETURN_STARTED"
    CLAIM_STARTED = "CLAIM_STARTED"
    RESOLVED = "RESOLVED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"

class WarrantyCaseCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tenant_id: str = Field(min_length=1, max_length=128)
    client_reference: str = Field(min_length=1, max_length=128)
    payload: dict[str, Any]
    idempotency_key: str = Field(min_length=16, max_length=128)

class WarrantyCaseCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: int = Field(ge=0)
    action: str = Field(min_length=1, max_length=64)
    reason: str | None = Field(default=None, max_length=1000)
    payload: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str = Field(min_length=16, max_length=128)

class WarrantyCaseRead(BaseModel):
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
export type FeatureStatus = "DRAFT" | "ACTIVE" | "RETURN_STARTED" | "CLAIM_STARTED" | "RESOLVED" | "EXPIRED" | "CANCELLED";

export interface WarrantyCaseCreate {
  tenantId: string;
  clientReference: string;
  payload: Record<string, unknown>;
  idempotencyKey: string;
}

export interface WarrantyCaseCommand {
  expectedRevision: number;
  action: string;
  reason?: string;
  payload: Record<string, unknown>;
  idempotencyKey: string;
}

export interface WarrantyCaseRead {
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

### AC-040-01: Nyugtatételből garanciális vagy visszaküldési eset hozható létre.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-040-01 szerinti műveletet végrehajtja
Then nyugtatételből garanciális vagy visszaküldési eset hozható létre.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-040-02: A javasolt határidő forrással látható és felülbírálható.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-040-02 szerinti műveletet végrehajtja
Then a javasolt határidő forrással látható és felülbírálható.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-040-03: Kapcsolódó bizonylat, sorozatszám és hivatkozás rögzíthető.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-040-03 szerinti műveletet végrehajtja
Then kapcsolódó bizonylat, sorozatszám és hivatkozás rögzíthető.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-040-04: Közelgő határidőhöz deduplikált emlékeztető tartozik.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-040-04 szerinti műveletet végrehajtja
Then közelgő határidőhöz deduplikált emlékeztető tartozik.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-040-05: Az ügy teljes életciklusa követhető.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-040-05 szerinti műveletet végrehajtja
Then az ügy teljes életciklusa követhető.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-040-06: Más tenant esete nem hozzáférhető.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-040-06 szerinti műveletet végrehajtja
Then más tenant esete nem hozzáférhető.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-040-07: Azonos létrehozási kérés egy esetet eredményez.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-040-07 szerinti műveletet végrehajtja
Then azonos létrehozási kérés egy esetet eredményez.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-040-08: Párhuzamos állapotváltás revíziókonfliktust ad.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-040-08 szerinti műveletet végrehajtja
Then párhuzamos állapotváltás revíziókonfliktust ad.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

## 11. API-szerződés

- `GET /api/v2/warranties`: tenant-szűrt lista; cursor pagination; 200/401/403.
- `POST /api/v2/warranties`: létrehozás vagy elemzés; kötelező `Idempotency-Key`; 201 vagy 202/400/401/403/409/422.
- `GET /api/v2/warranties/{id}`: részlet és evidence; idegen tenant esetén 404-szerű válasz.
- `PATCH /api/v2/warranties/{id}`: `expected_revision` alapú módosítás; 200/409/422.
- `POST /api/v2/warranties/{id}/confirm`: kontrollált állapotátmenet; 200/403/409/422.
- Minden hiba `application/problem+json` alakú `ApiProblem`; minden siker tenant- és revision-azonosítót ad.

### Lépésről lépésre kidolgozott kontrollfolyamat

1. A felhasználó nyugtatételből hoz létre esetet; javasolt dátum csak forrással és javaslatként jelenhet meg.
2. return_deadline nem előzheti meg a vásárlást, warranty_end nem lehet értelmezhetetlen; hibánál raise InvalidWarrantyDeadlineError(...).
3. Minden kézi felülbírálás megőrzi az eredeti javaslatot, új értéket, indokot és szerzőt.
4. Dokumentumkapcsolás csak azonos tenant erőforrásai között és atomi tranzakcióban történhet.
5. Az emlékeztetők dedupe_key alapján egyszer kézbesülnek; lejárt ügy nem jelenthető aktívnak.
6. Állapotátmenet expected_revision ellenőrzéssel történik; lezárt ügy újranyitása külön jogosultságot és indokot igényel.

## 12. Adatmodell és perzisztencia

- Fő aggregátum: `WarrantyCase`; kötelező `id`, `tenant_id`, `status`, `revision`, `created_at`, `updated_at`.
- Írások tenant tranzakcióban, optimistic lockinggal és idempotency rekorddal történnek.
- Egyedi kulcs: `(tenant_id, idempotency_key, command_type)`; az eltárolt request hash eltérés konfliktus.
- Audit esemény tartalmazza az aggregátumot, előző/új revíziót, aktort, okot, correlation ID-t és időt, de nem másol érzékeny teljes payloadot.
- Törlés csak projektmegőrzési szabály szerint; pénzügyi bizonyíték logikai törléssel és referenciaintegritással.

## 13. Tesztterv és lefedettségi leképezés

- REQ-040-01 → AC-040-01 → `.agent-pipeline/03_e2e_suites/test_e2e_040.py`; unit cél: `tests/unit/test_warranties_service.py::test_req_040_01`.
- REQ-040-02 → AC-040-02 → `.agent-pipeline/03_e2e_suites/test_e2e_040.py`; unit cél: `tests/unit/test_warranties_service.py::test_req_040_02`.
- REQ-040-03 → AC-040-03 → `.agent-pipeline/03_e2e_suites/test_e2e_040.py`; unit cél: `tests/unit/test_warranties_service.py::test_req_040_03`.
- REQ-040-04 → AC-040-04 → `.agent-pipeline/03_e2e_suites/test_e2e_040.py`; unit cél: `tests/unit/test_warranties_service.py::test_req_040_04`.
- REQ-040-05 → AC-040-05 → `.agent-pipeline/03_e2e_suites/test_e2e_040.py`; unit cél: `tests/unit/test_warranties_service.py::test_req_040_05`.
- REQ-040-06 → AC-040-06 → `.agent-pipeline/03_e2e_suites/test_e2e_040.py`; unit cél: `tests/unit/test_warranties_service.py::test_req_040_06`.
- REQ-040-07 → AC-040-07 → `.agent-pipeline/03_e2e_suites/test_e2e_040.py`; unit cél: `tests/unit/test_warranties_service.py::test_req_040_07`.
- REQ-040-08 → AC-040-08 → `.agent-pipeline/03_e2e_suites/test_e2e_040.py`; unit cél: `tests/unit/test_warranties_service.py::test_req_040_08`.

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
