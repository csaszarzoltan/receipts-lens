---
id: FEAT-045
title: Offline nyugtarögzítés és későbbi szinkronizálás
status: spec_ready
version: 1
risk: high
owner: system-architect
related_brief: BRIEF-045
---

# FEAT-045: Offline nyugtarögzítés és későbbi szinkronizálás

## 1. Cél és felhasználói eredmény

A BRIEF-045 képesség teljes, tenant-biztos, magyarázható és felhasználó által kontrollált megvalósítási szerződése. Kész akkor, ha mind a nyolc követelmény RED→GREEN bizonyítékkal, célzott teszttel és teljes regresszióval igazolt, és a felület hibánál nem állít valótlan sikert.

## 2. Kontextus és források

Kanonikus források: `briefs/BRIEF-045-offline-nyugtarogzites-es-kesobbi-szinkronizalas.md`, `METHODOLOGY.md`, `.agents/rules/methodology.md`. Kapcsolódó platform-invariánsok: explicit tenant, szerveroldali RBAC, audit, revízió, idempotencia, stabil hibaszerződés és érzékeny adatok minimalizálása.

### Target Files

- `app/offline_sync_models.py (NEW)`
- `app/offline_sync_service.py (NEW)`
- `app/offline_sync_api.py (NEW)`
- `app/api_v2.py (MODIFY)`
- `frontend/app/receipts/offline/page.tsx (NEW)`
- `frontend/components/offline/OfflineQueue.tsx (NEW)`
- `frontend/lib/offlineQueue.ts (NEW)`
- `frontend/lib/indexedDbReceipts.ts (NEW)`
- `frontend/public/sw.js (NEW)`

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

- ACT-045-01: háztartási tag, aki saját jogosultságán belül használja a funkciót.
- ACT-045-02: tulajdonos vagy pénzügyi felelős, aki döntést és felülbírálást végez.
- ACT-045-03: könyvelő vagy ellenőrző, korlátozott, auditált hozzáféréssel.
- PRE-045-01: hitelesített session, aktív tenant és szerveroldalon ellenőrzött szerepkör.
- PRE-045-02: a hivatkozott források ugyanahhoz a tenanthoz tartoznak.
- PRE-045-03: módosításkor `expected_revision`, íráskor `Idempotency-Key` rendelkezésre áll.

## 5. Funkcionális követelmények

- REQ-045-01 [MUST]: Nyugta és minimális metaadat hálózat nélkül piszkozatként megőrizhető.
- REQ-045-02 [MUST]: A helyi várólista állapota egyértelműen látható.
- REQ-045-03 [MUST]: Kapcsolat visszatérésekor a feltöltés folytatható.
- REQ-045-04 [MUST]: Elemhiba nem blokkolja a teljes batch-et.
- REQ-045-05 [MUST]: Konfliktusnál mindkét változat összehasonlítható és nincs csendes felülírás.
- REQ-045-06 [MUST]: Tenantváltás nem szinkronizál adatot más háztartásba.
- REQ-045-07 [MUST]: Azonos draft ismételt szinkronja nem duplikál nyugtát.
- REQ-045-08 [MUST]: Háttérbe helyezés és újraindítás után a draft és progressz megmarad.

## 6. Nem funkcionális követelmények

- NFR-045-01 [SECURITY]: minden olvasás és írás explicit tenant-filterrel, szerveroldali RBAC-kal és erőforrás-szintű ellenőrzéssel fut.
- NFR-045-02 [RELIABILITY]: módosítás atomi; timeout és retry nem hoz létre duplikátumot vagy félállapotot.
- NFR-045-03 [PERFORMANCE]: lista p95 ≤ 800 ms, parancs elfogadása p95 ≤ 1200 ms, hosszú munka 202 és követhető státusz.
- NFR-045-04 [ACCESSIBILITY]: WCAG 2.2 AA, billentyűzet, látható fókusz, programozott név, aria-live és legalább 44×44 CSS px cél.
- NFR-045-05 [PRIVACY]: log és telemetry nem tartalmaz teljes bizonylatképet, tokent vagy szükségtelen személyes pénzügyi adatot.
- NFR-045-06 [OBSERVABILITY]: correlation ID, audit actor, tenant, parancstípus, eredménykód, latency és retry számláló.

## 7. UI-szerződés

- UI-045-01: `offline_sync-page`, a `/receipts/offline` kanonikus munkaterülete, loading/empty/error/ready állapotokkal.
- UI-045-02: `offline_sync-primary-action`, jogosultság- és állapotfüggő elsődleges művelet.
- UI-045-03: `offline_sync-evidence`, a döntés alapját és bizonytalanságát bemutató panel.
- UI-045-04: `offline_sync-status`, vizuális és aria-live állapotközlő.
- UI-045-05: `offline_sync-conflict`, adatvesztés nélküli konfliktus- és retry felület.

## 8. GUI-folyamat

1. A felhasználó megnyitja a `/receipts/offline` útvonalat, a sessiont a `helpers/auth.ts` inicializálja.
2. A felület betöltési, majd tenant-szűrt ready vagy hasznos empty állapotot mutat.
3. A felhasználó megnyit egy tételt; a forrás, evidence, confidence, jogosultság és aktuális revízió látható.
4. Az elsődleges művelet előtt a kliens validál, veszélyes döntésnél megerősítést kér.
5. A kérés idempotenciakulccsal indul; in-flight állapotban ismételt aktiválás nem küld második parancsot.
6. Siker esetén az új revízió és állapot jelenik meg. 409 esetén konfliktusnézet, 4xx esetén javítható mezőhiba, hálózati hibánál adatmegőrző retry jelenik meg.
7. Frissítés és visszatérés után a szerverállapot reprodukálható, idegen tenant erőforrása nem látható.

## 9. Állapotmodell

Kanonikus állapotok: `LOCAL_ONLY → QUEUED → UPLOADING → PROCESSING → CONFLICT → SYNCED → FAILED → DISCARDED`.

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
    LOCAL_ONLY = "LOCAL_ONLY"
    QUEUED = "QUEUED"
    UPLOADING = "UPLOADING"
    PROCESSING = "PROCESSING"
    CONFLICT = "CONFLICT"
    SYNCED = "SYNCED"
    FAILED = "FAILED"
    DISCARDED = "DISCARDED"

class OfflineReceiptDraftCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tenant_id: str = Field(min_length=1, max_length=128)
    client_reference: str = Field(min_length=1, max_length=128)
    payload: dict[str, Any]
    idempotency_key: str = Field(min_length=16, max_length=128)

class OfflineReceiptDraftCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: int = Field(ge=0)
    action: str = Field(min_length=1, max_length=64)
    reason: str | None = Field(default=None, max_length=1000)
    payload: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str = Field(min_length=16, max_length=128)

class OfflineReceiptDraftRead(BaseModel):
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
export type FeatureStatus = "LOCAL_ONLY" | "QUEUED" | "UPLOADING" | "PROCESSING" | "CONFLICT" | "SYNCED" | "FAILED" | "DISCARDED";

export interface OfflineReceiptDraftCreate {
  tenantId: string;
  clientReference: string;
  payload: Record<string, unknown>;
  idempotencyKey: string;
}

export interface OfflineReceiptDraftCommand {
  expectedRevision: number;
  action: string;
  reason?: string;
  payload: Record<string, unknown>;
  idempotencyKey: string;
}

export interface OfflineReceiptDraftRead {
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

### AC-045-01: Nyugta és minimális metaadat hálózat nélkül piszkozatként megőrizhető.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-045-01 szerinti műveletet végrehajtja
Then nyugta és minimális metaadat hálózat nélkül piszkozatként megőrizhető.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-045-02: A helyi várólista állapota egyértelműen látható.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-045-02 szerinti műveletet végrehajtja
Then a helyi várólista állapota egyértelműen látható.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-045-03: Kapcsolat visszatérésekor a feltöltés folytatható.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-045-03 szerinti műveletet végrehajtja
Then kapcsolat visszatérésekor a feltöltés folytatható.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-045-04: Elemhiba nem blokkolja a teljes batch-et.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-045-04 szerinti műveletet végrehajtja
Then elemhiba nem blokkolja a teljes batch-et.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-045-05: Konfliktusnál mindkét változat összehasonlítható és nincs csendes felülírás.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-045-05 szerinti műveletet végrehajtja
Then konfliktusnál mindkét változat összehasonlítható és nincs csendes felülírás.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-045-06: Tenantváltás nem szinkronizál adatot más háztartásba.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-045-06 szerinti műveletet végrehajtja
Then tenantváltás nem szinkronizál adatot más háztartásba.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-045-07: Azonos draft ismételt szinkronja nem duplikál nyugtát.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-045-07 szerinti műveletet végrehajtja
Then azonos draft ismételt szinkronja nem duplikál nyugtát.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-045-08: Háttérbe helyezés és újraindítás után a draft és progressz megmarad.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-045-08 szerinti műveletet végrehajtja
Then háttérbe helyezés és újraindítás után a draft és progressz megmarad.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

## 11. API-szerződés

- `GET /api/v2/offline-sync`: tenant-szűrt lista; cursor pagination; 200/401/403.
- `POST /api/v2/offline-sync`: létrehozás vagy elemzés; kötelező `Idempotency-Key`; 201 vagy 202/400/401/403/409/422.
- `GET /api/v2/offline-sync/{id}`: részlet és evidence; idegen tenant esetén 404-szerű válasz.
- `PATCH /api/v2/offline-sync/{id}`: `expected_revision` alapú módosítás; 200/409/422.
- `POST /api/v2/offline-sync/{id}/confirm`: kontrollált állapotátmenet; 200/403/409/422.
- Minden hiba `application/problem+json` alakú `ApiProblem`; minden siker tenant- és revision-azonosítót ad.

### Lépésről lépésre kidolgozott kontrollfolyamat

1. A kliens local_id és image_hash mellett tartós helyi piszkozatot hoz létre, mielőtt hálózati művelet indul.
2. A sync envelope tenant-, device-, batch- és idempotency-azonosítót hordoz; azonos payload újrapróbálása ugyanazt a receipt_id-t adja.
3. Eltérő payload azonos idempotency kulccsal raise SyncPayloadMismatchError(...); részleges batch eredmény elemenként explicit.
4. A szerver minden draftot tenant-jogosultsággal és tartalmi limitekkel validál, majd atomi elem-műveletben ment.
5. Revízióütközés CONFLICT eredményt és mindkét biztonságos snapshotot ad; csendes last-write-wins tilos.
6. Kijelentkezés vagy tenantváltás előtt a LOCAL_ONLY elemekről figyelmeztetés kell; automatikus törlés csak explicit döntéssel.

## 12. Adatmodell és perzisztencia

- Fő aggregátum: `OfflineReceiptDraft`; kötelező `id`, `tenant_id`, `status`, `revision`, `created_at`, `updated_at`.
- Írások tenant tranzakcióban, optimistic lockinggal és idempotency rekorddal történnek.
- Egyedi kulcs: `(tenant_id, idempotency_key, command_type)`; az eltárolt request hash eltérés konfliktus.
- Audit esemény tartalmazza az aggregátumot, előző/új revíziót, aktort, okot, correlation ID-t és időt, de nem másol érzékeny teljes payloadot.
- Törlés csak projektmegőrzési szabály szerint; pénzügyi bizonyíték logikai törléssel és referenciaintegritással.

## 13. Tesztterv és lefedettségi leképezés

- REQ-045-01 → AC-045-01 → `.agent-pipeline/03_e2e_suites/test_e2e_045.py`; unit cél: `tests/unit/test_offline_sync_service.py::test_req_045_01`.
- REQ-045-02 → AC-045-02 → `.agent-pipeline/03_e2e_suites/test_e2e_045.py`; unit cél: `tests/unit/test_offline_sync_service.py::test_req_045_02`.
- REQ-045-03 → AC-045-03 → `.agent-pipeline/03_e2e_suites/test_e2e_045.py`; unit cél: `tests/unit/test_offline_sync_service.py::test_req_045_03`.
- REQ-045-04 → AC-045-04 → `.agent-pipeline/03_e2e_suites/test_e2e_045.py`; unit cél: `tests/unit/test_offline_sync_service.py::test_req_045_04`.
- REQ-045-05 → AC-045-05 → `.agent-pipeline/03_e2e_suites/test_e2e_045.py`; unit cél: `tests/unit/test_offline_sync_service.py::test_req_045_05`.
- REQ-045-06 → AC-045-06 → `.agent-pipeline/03_e2e_suites/test_e2e_045.py`; unit cél: `tests/unit/test_offline_sync_service.py::test_req_045_06`.
- REQ-045-07 → AC-045-07 → `.agent-pipeline/03_e2e_suites/test_e2e_045.py`; unit cél: `tests/unit/test_offline_sync_service.py::test_req_045_07`.
- REQ-045-08 → AC-045-08 → `.agent-pipeline/03_e2e_suites/test_e2e_045.py`; unit cél: `tests/unit/test_offline_sync_service.py::test_req_045_08`.

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
