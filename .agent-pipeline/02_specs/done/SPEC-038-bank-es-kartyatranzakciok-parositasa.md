---
id: FEAT-038
title: Bank- és kártyatranzakciók párosítása
status: spec_ready
version: 1
risk: high
owner: system-architect
related_brief: BRIEF-038
---

# FEAT-038: Bank- és kártyatranzakciók párosítása

## 1. Cél és felhasználói eredmény

A BRIEF-038 képesség teljes, tenant-biztos, magyarázható és felhasználó által kontrollált megvalósítási szerződése. Kész akkor, ha mind a nyolc követelmény RED→GREEN bizonyítékkal, célzott teszttel és teljes regresszióval igazolt, és a felület hibánál nem állít valótlan sikert.

## 2. Kontextus és források

Kanonikus források: `briefs/BRIEF-038-bank-es-kartyatranzakciok-parositasa.md`, `METHODOLOGY.md`, `.agents/rules/methodology.md`. Kapcsolódó platform-invariánsok: explicit tenant, szerveroldali RBAC, audit, revízió, idempotencia, stabil hibaszerződés és érzékeny adatok minimalizálása.

### Target Files

- `app/reconciliation_models.py (NEW)`
- `app/reconciliation_service.py (NEW)`
- `app/reconciliation_api.py (NEW)`
- `app/api_v2.py (MODIFY)`
- `frontend/app/reconciliation/page.tsx (NEW)`
- `frontend/components/reconciliation/MatchWorkbench.tsx (NEW)`
- `frontend/lib/reconciliation.ts (NEW)`

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

- ACT-038-01: háztartási tag, aki saját jogosultságán belül használja a funkciót.
- ACT-038-02: tulajdonos vagy pénzügyi felelős, aki döntést és felülbírálást végez.
- ACT-038-03: könyvelő vagy ellenőrző, korlátozott, auditált hozzáféréssel.
- PRE-038-01: hitelesített session, aktív tenant és szerveroldalon ellenőrzött szerepkör.
- PRE-038-02: a hivatkozott források ugyanahhoz a tenanthoz tartoznak.
- PRE-038-03: módosításkor `expected_revision`, íráskor `Idempotency-Key` rendelkezésre áll.

## 5. Funkcionális követelmények

- REQ-038-01 [MUST]: A rendszer rangsorolt, magyarázható párosítási javaslatokat ad.
- REQ-038-02 [MUST]: A felhasználó javaslatot jóváhagyhat, elutasíthat vagy kézzel másik kapcsolatot választhat.
- REQ-038-03 [MUST]: Az egy-több és több-egy kapcsolat összege és pénzneme validált.
- REQ-038-04 [MUST]: A kapcsolat felbontása indokolt és auditált.
- REQ-038-05 [MUST]: A tranzakció állapotváltozása duplikáció nélkül újraértékelődik.
- REQ-038-06 [MUST]: Más tenant adata nem olvasható és nem módosítható.
- REQ-038-07 [MUST]: Azonos idempotens kérés nem hoz létre második kapcsolatot.
- REQ-038-08 [MUST]: Párhuzamos döntésből legfeljebb egy érvényes revízió nyer.

## 6. Nem funkcionális követelmények

- NFR-038-01 [SECURITY]: minden olvasás és írás explicit tenant-filterrel, szerveroldali RBAC-kal és erőforrás-szintű ellenőrzéssel fut.
- NFR-038-02 [RELIABILITY]: módosítás atomi; timeout és retry nem hoz létre duplikátumot vagy félállapotot.
- NFR-038-03 [PERFORMANCE]: lista p95 ≤ 800 ms, parancs elfogadása p95 ≤ 1200 ms, hosszú munka 202 és követhető státusz.
- NFR-038-04 [ACCESSIBILITY]: WCAG 2.2 AA, billentyűzet, látható fókusz, programozott név, aria-live és legalább 44×44 CSS px cél.
- NFR-038-05 [PRIVACY]: log és telemetry nem tartalmaz teljes bizonylatképet, tokent vagy szükségtelen személyes pénzügyi adatot.
- NFR-038-06 [OBSERVABILITY]: correlation ID, audit actor, tenant, parancstípus, eredménykód, latency és retry számláló.

## 7. UI-szerződés

- UI-038-01: `reconciliation-page`, a `/reconciliation` kanonikus munkaterülete, loading/empty/error/ready állapotokkal.
- UI-038-02: `reconciliation-primary-action`, jogosultság- és állapotfüggő elsődleges művelet.
- UI-038-03: `reconciliation-evidence`, a döntés alapját és bizonytalanságát bemutató panel.
- UI-038-04: `reconciliation-status`, vizuális és aria-live állapotközlő.
- UI-038-05: `reconciliation-conflict`, adatvesztés nélküli konfliktus- és retry felület.

## 8. GUI-folyamat

1. A felhasználó megnyitja a `/reconciliation` útvonalat, a sessiont a `helpers/auth.ts` inicializálja.
2. A felület betöltési, majd tenant-szűrt ready vagy hasznos empty állapotot mutat.
3. A felhasználó megnyit egy tételt; a forrás, evidence, confidence, jogosultság és aktuális revízió látható.
4. Az elsődleges művelet előtt a kliens validál, veszélyes döntésnél megerősítést kér.
5. A kérés idempotenciakulccsal indul; in-flight állapotban ismételt aktiválás nem küld második parancsot.
6. Siker esetén az új revízió és állapot jelenik meg. 409 esetén konfliktusnézet, 4xx esetén javítható mezőhiba, hálózati hibánál adatmegőrző retry jelenik meg.
7. Frissítés és visszatérés után a szerverállapot reprodukálható, idegen tenant erőforrása nem látható.

## 9. Állapotmodell

Kanonikus állapotok: `UNMATCHED → SUGGESTED → CONFIRMED → REJECTED → REVERSED`.

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
    UNMATCHED = "UNMATCHED"
    SUGGESTED = "SUGGESTED"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    REVERSED = "REVERSED"

class TransactionMatchCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tenant_id: str = Field(min_length=1, max_length=128)
    client_reference: str = Field(min_length=1, max_length=128)
    payload: dict[str, Any]
    idempotency_key: str = Field(min_length=16, max_length=128)

class TransactionMatchCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: int = Field(ge=0)
    action: str = Field(min_length=1, max_length=64)
    reason: str | None = Field(default=None, max_length=1000)
    payload: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str = Field(min_length=16, max_length=128)

class TransactionMatchRead(BaseModel):
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
export type FeatureStatus = "UNMATCHED" | "SUGGESTED" | "CONFIRMED" | "REJECTED" | "REVERSED";

export interface TransactionMatchCreate {
  tenantId: string;
  clientReference: string;
  payload: Record<string, unknown>;
  idempotencyKey: string;
}

export interface TransactionMatchCommand {
  expectedRevision: number;
  action: string;
  reason?: string;
  payload: Record<string, unknown>;
  idempotencyKey: string;
}

export interface TransactionMatchRead {
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

### AC-038-01: A rendszer rangsorolt, magyarázható párosítási javaslatokat ad.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-038-01 szerinti műveletet végrehajtja
Then a rendszer rangsorolt, magyarázható párosítási javaslatokat ad.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-038-02: A felhasználó javaslatot jóváhagyhat, elutasíthat vagy kézzel másik kapcsolatot választhat.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-038-02 szerinti műveletet végrehajtja
Then a felhasználó javaslatot jóváhagyhat, elutasíthat vagy kézzel másik kapcsolatot választhat.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-038-03: Az egy-több és több-egy kapcsolat összege és pénzneme validált.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-038-03 szerinti műveletet végrehajtja
Then az egy-több és több-egy kapcsolat összege és pénzneme validált.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-038-04: A kapcsolat felbontása indokolt és auditált.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-038-04 szerinti műveletet végrehajtja
Then a kapcsolat felbontása indokolt és auditált.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-038-05: A tranzakció állapotváltozása duplikáció nélkül újraértékelődik.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-038-05 szerinti műveletet végrehajtja
Then a tranzakció állapotváltozása duplikáció nélkül újraértékelődik.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-038-06: Más tenant adata nem olvasható és nem módosítható.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-038-06 szerinti műveletet végrehajtja
Then más tenant adata nem olvasható és nem módosítható.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-038-07: Azonos idempotens kérés nem hoz létre második kapcsolatot.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-038-07 szerinti műveletet végrehajtja
Then azonos idempotens kérés nem hoz létre második kapcsolatot.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-038-08: Párhuzamos döntésből legfeljebb egy érvényes revízió nyer.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-038-08 szerinti műveletet végrehajtja
Then párhuzamos döntésből legfeljebb egy érvényes revízió nyer.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

## 11. API-szerződés

- `GET /api/v2/reconciliation/matches`: tenant-szűrt lista; cursor pagination; 200/401/403.
- `POST /api/v2/reconciliation/matches`: létrehozás vagy elemzés; kötelező `Idempotency-Key`; 201 vagy 202/400/401/403/409/422.
- `GET /api/v2/reconciliation/matches/{id}`: részlet és evidence; idegen tenant esetén 404-szerű válasz.
- `PATCH /api/v2/reconciliation/matches/{id}`: `expected_revision` alapú módosítás; 200/409/422.
- `POST /api/v2/reconciliation/matches/{id}/confirm`: kontrollált állapotátmenet; 200/403/409/422.
- Minden hiba `application/problem+json` alakú `ApiProblem`; minden siker tenant- és revision-azonosítót ad.

### Lépésről lépésre kidolgozott kontrollfolyamat

1. Betöltéskor kizárólag az aktív tenant párosítatlan nyugtái és könyvelt vagy függő tranzakciói kérdezhetők le.
2. A jelöltpontszám összeg-, pénznem-, dátum-, kereskedő- és fizetésimód-bizonyítékból determinisztikusan készül; a magyarázat ugyanebből az evidence objektumból származik.
3. Javaslat nem válik automatikusan véglegessé. A confirm művelet jogosultságot, revíziót, összegkonzisztenciát és kapcsolati kardinalitást ellenőriz.
4. Az idempotency_key tenanton belül egyedi; azonos kulcs és payload ugyanazt az eredményt adja, eltérő payload esetén raise IdempotencyConflictError(...).
5. Más tenant erőforrására raise MatchNotFoundError(...), elavult revízióra raise StaleMatchRevisionError(...); egyik ág sem ír részállapotot.
6. A tranzakció pending→posted vagy reversed változása újraértékelést indít, de nem duplikál kapcsolatot; felbontás indokkal és auditbejegyzéssel történik.

## 12. Adatmodell és perzisztencia

- Fő aggregátum: `TransactionMatch`; kötelező `id`, `tenant_id`, `status`, `revision`, `created_at`, `updated_at`.
- Írások tenant tranzakcióban, optimistic lockinggal és idempotency rekorddal történnek.
- Egyedi kulcs: `(tenant_id, idempotency_key, command_type)`; az eltárolt request hash eltérés konfliktus.
- Audit esemény tartalmazza az aggregátumot, előző/új revíziót, aktort, okot, correlation ID-t és időt, de nem másol érzékeny teljes payloadot.
- Törlés csak projektmegőrzési szabály szerint; pénzügyi bizonyíték logikai törléssel és referenciaintegritással.

## 13. Tesztterv és lefedettségi leképezés

- REQ-038-01 → AC-038-01 → `.agent-pipeline/03_e2e_suites/test_e2e_038.py`; unit cél: `tests/unit/test_reconciliation_service.py::test_req_038_01`.
- REQ-038-02 → AC-038-02 → `.agent-pipeline/03_e2e_suites/test_e2e_038.py`; unit cél: `tests/unit/test_reconciliation_service.py::test_req_038_02`.
- REQ-038-03 → AC-038-03 → `.agent-pipeline/03_e2e_suites/test_e2e_038.py`; unit cél: `tests/unit/test_reconciliation_service.py::test_req_038_03`.
- REQ-038-04 → AC-038-04 → `.agent-pipeline/03_e2e_suites/test_e2e_038.py`; unit cél: `tests/unit/test_reconciliation_service.py::test_req_038_04`.
- REQ-038-05 → AC-038-05 → `.agent-pipeline/03_e2e_suites/test_e2e_038.py`; unit cél: `tests/unit/test_reconciliation_service.py::test_req_038_05`.
- REQ-038-06 → AC-038-06 → `.agent-pipeline/03_e2e_suites/test_e2e_038.py`; unit cél: `tests/unit/test_reconciliation_service.py::test_req_038_06`.
- REQ-038-07 → AC-038-07 → `.agent-pipeline/03_e2e_suites/test_e2e_038.py`; unit cél: `tests/unit/test_reconciliation_service.py::test_req_038_07`.
- REQ-038-08 → AC-038-08 → `.agent-pipeline/03_e2e_suites/test_e2e_038.py`; unit cél: `tests/unit/test_reconciliation_service.py::test_req_038_08`.

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
