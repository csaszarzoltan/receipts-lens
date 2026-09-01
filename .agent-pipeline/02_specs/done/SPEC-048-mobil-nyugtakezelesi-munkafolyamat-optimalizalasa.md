---
id: FEAT-048
title: Mobil nyugtakezelési munkafolyamat optimalizálása
status: spec_ready
version: 1
risk: high
owner: system-architect
related_brief: BRIEF-048
---

# FEAT-048: Mobil nyugtakezelési munkafolyamat optimalizálása

## 1. Cél és felhasználói eredmény

A BRIEF-048 képesség teljes, tenant-biztos, magyarázható és felhasználó által kontrollált megvalósítási szerződése. Kész akkor, ha mind a nyolc követelmény RED→GREEN bizonyítékkal, célzott teszttel és teljes regresszióval igazolt, és a felület hibánál nem állít valótlan sikert.

## 2. Kontextus és források

Kanonikus források: `briefs/BRIEF-048-mobil-nyugtakezelesi-munkafolyamat-optimalizalasa.md`, `METHODOLOGY.md`, `.agents/rules/methodology.md`. Kapcsolódó platform-invariánsok: explicit tenant, szerveroldali RBAC, audit, revízió, idempotencia, stabil hibaszerződés és érzékeny adatok minimalizálása.

### Target Files

- `app/mobile_receipt_models.py (NEW)`
- `app/mobile_receipt_service.py (NEW)`
- `app/mobile_receipt_api.py (NEW)`
- `app/api_v2.py (MODIFY)`
- `frontend/app/receipts/capture/page.tsx (NEW)`
- `frontend/components/mobile/MobileCaptureFlow.tsx (NEW)`
- `frontend/components/mobile/ThumbActionBar.tsx (NEW)`
- `frontend/lib/mobileReceiptJourney.ts (NEW)`
- `frontend/e2e/mobile-fixtures.ts (NEW)`

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

- ACT-048-01: háztartási tag, aki saját jogosultságán belül használja a funkciót.
- ACT-048-02: tulajdonos vagy pénzügyi felelős, aki döntést és felülbírálást végez.
- ACT-048-03: könyvelő vagy ellenőrző, korlátozott, auditált hozzáféréssel.
- PRE-048-01: hitelesített session, aktív tenant és szerveroldalon ellenőrzött szerepkör.
- PRE-048-02: a hivatkozott források ugyanahhoz a tenanthoz tartoznak.
- PRE-048-03: módosításkor `expected_revision`, íráskor `Idempotency-Key` rendelkezésre áll.

## 5. Funkcionális követelmények

- REQ-048-01 [MUST]: A mobil kamerás rögzítés capture, preview, retake és accept lépésekkel működik.
- REQ-048-02 [MUST]: A feltöltési és feldolgozási állapot mobilon folytathatóan látható.
- REQ-048-03 [MUST]: A kép és felismert adat kis képernyőn gyorsan összevethető.
- REQ-048-04 [MUST]: A bizonytalan mezők nagy célterülettel és megfelelő billentyűzettel javíthatók.
- REQ-048-05 [MUST]: Hálózatvesztés vagy háttérbe helyezés nem veszít piszkozatot.
- REQ-048-06 [MUST]: A teljes folyamat képernyőolvasóval és egykezes elrendezéssel használható.
- REQ-048-07 [MUST]: Azonos resume vagy approve kérés nem duplikál nyugtát.
- REQ-048-08 [MUST]: Valódi telefonméretű E2E út lefedi a rögzítéstől a visszakeresésig tartó folyamatot.

## 6. Nem funkcionális követelmények

- NFR-048-01 [SECURITY]: minden olvasás és írás explicit tenant-filterrel, szerveroldali RBAC-kal és erőforrás-szintű ellenőrzéssel fut.
- NFR-048-02 [RELIABILITY]: módosítás atomi; timeout és retry nem hoz létre duplikátumot vagy félállapotot.
- NFR-048-03 [PERFORMANCE]: lista p95 ≤ 800 ms, parancs elfogadása p95 ≤ 1200 ms, hosszú munka 202 és követhető státusz.
- NFR-048-04 [ACCESSIBILITY]: WCAG 2.2 AA, billentyűzet, látható fókusz, programozott név, aria-live és legalább 44×44 CSS px cél.
- NFR-048-05 [PRIVACY]: log és telemetry nem tartalmaz teljes bizonylatképet, tokent vagy szükségtelen személyes pénzügyi adatot.
- NFR-048-06 [OBSERVABILITY]: correlation ID, audit actor, tenant, parancstípus, eredménykód, latency és retry számláló.

## 7. UI-szerződés

- UI-048-01: `mobile_receipts-page`, a `/receipts/capture` kanonikus munkaterülete, loading/empty/error/ready állapotokkal.
- UI-048-02: `mobile_receipts-primary-action`, jogosultság- és állapotfüggő elsődleges művelet.
- UI-048-03: `mobile_receipts-evidence`, a döntés alapját és bizonytalanságát bemutató panel.
- UI-048-04: `mobile_receipts-status`, vizuális és aria-live állapotközlő.
- UI-048-05: `mobile_receipts-conflict`, adatvesztés nélküli konfliktus- és retry felület.

## 8. GUI-folyamat

1. A felhasználó megnyitja a `/receipts/capture` útvonalat, a sessiont a `helpers/auth.ts` inicializálja.
2. A felület betöltési, majd tenant-szűrt ready vagy hasznos empty állapotot mutat.
3. A felhasználó megnyit egy tételt; a forrás, evidence, confidence, jogosultság és aktuális revízió látható.
4. Az elsődleges művelet előtt a kliens validál, veszélyes döntésnél megerősítést kér.
5. A kérés idempotenciakulccsal indul; in-flight állapotban ismételt aktiválás nem küld második parancsot.
6. Siker esetén az új revízió és állapot jelenik meg. 409 esetén konfliktusnézet, 4xx esetén javítható mezőhiba, hálózati hibánál adatmegőrző retry jelenik meg.
7. Frissítés és visszatérés után a szerverállapot reprodukálható, idegen tenant erőforrása nem látható.

## 9. Állapotmodell

Kanonikus állapotok: `CAPTURING → PREVIEW → DRAFT → UPLOADING → PROCESSING → NEEDS_REVIEW → APPROVED → FAILED`.

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
    CAPTURING = "CAPTURING"
    PREVIEW = "PREVIEW"
    DRAFT = "DRAFT"
    UPLOADING = "UPLOADING"
    PROCESSING = "PROCESSING"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    APPROVED = "APPROVED"
    FAILED = "FAILED"

class MobileReceiptJourneyCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tenant_id: str = Field(min_length=1, max_length=128)
    client_reference: str = Field(min_length=1, max_length=128)
    payload: dict[str, Any]
    idempotency_key: str = Field(min_length=16, max_length=128)

class MobileReceiptJourneyCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: int = Field(ge=0)
    action: str = Field(min_length=1, max_length=64)
    reason: str | None = Field(default=None, max_length=1000)
    payload: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str = Field(min_length=16, max_length=128)

class MobileReceiptJourneyRead(BaseModel):
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
export type FeatureStatus = "CAPTURING" | "PREVIEW" | "DRAFT" | "UPLOADING" | "PROCESSING" | "NEEDS_REVIEW" | "APPROVED" | "FAILED";

export interface MobileReceiptJourneyCreate {
  tenantId: string;
  clientReference: string;
  payload: Record<string, unknown>;
  idempotencyKey: string;
}

export interface MobileReceiptJourneyCommand {
  expectedRevision: number;
  action: string;
  reason?: string;
  payload: Record<string, unknown>;
  idempotencyKey: string;
}

export interface MobileReceiptJourneyRead {
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

### AC-048-01: A mobil kamerás rögzítés capture, preview, retake és accept lépésekkel működik.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-048-01 szerinti műveletet végrehajtja
Then a mobil kamerás rögzítés capture, preview, retake és accept lépésekkel működik.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-048-02: A feltöltési és feldolgozási állapot mobilon folytathatóan látható.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-048-02 szerinti műveletet végrehajtja
Then a feltöltési és feldolgozási állapot mobilon folytathatóan látható.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-048-03: A kép és felismert adat kis képernyőn gyorsan összevethető.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-048-03 szerinti műveletet végrehajtja
Then a kép és felismert adat kis képernyőn gyorsan összevethető.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-048-04: A bizonytalan mezők nagy célterülettel és megfelelő billentyűzettel javíthatók.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-048-04 szerinti műveletet végrehajtja
Then a bizonytalan mezők nagy célterülettel és megfelelő billentyűzettel javíthatók.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-048-05: Hálózatvesztés vagy háttérbe helyezés nem veszít piszkozatot.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-048-05 szerinti műveletet végrehajtja
Then hálózatvesztés vagy háttérbe helyezés nem veszít piszkozatot.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-048-06: A teljes folyamat képernyőolvasóval és egykezes elrendezéssel használható.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-048-06 szerinti műveletet végrehajtja
Then a teljes folyamat képernyőolvasóval és egykezes elrendezéssel használható.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-048-07: Azonos resume vagy approve kérés nem duplikál nyugtát.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-048-07 szerinti műveletet végrehajtja
Then azonos resume vagy approve kérés nem duplikál nyugtát.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

### AC-048-08: Valódi telefonméretű E2E út lefedi a rögzítéstől a visszakeresésig tartó folyamatot.

Given hitelesített, megfelelő szerepkörű felhasználó és tenant-szűrt kiinduló állapot
When a felhasználó a REQ-048-08 szerinti műveletet végrehajtja
Then valódi telefonméretű E2E út lefedi a rögzítéstől a visszakeresésig tartó folyamatot.
And jogosulatlan, idegen tenantbeli, ismételt vagy konfliktusos kérés nem okoz rejtett vagy részleges állapotváltozást.

## 11. API-szerződés

- `GET /api/v2/mobile-receipts`: tenant-szűrt lista; cursor pagination; 200/401/403.
- `POST /api/v2/mobile-receipts`: létrehozás vagy elemzés; kötelező `Idempotency-Key`; 201 vagy 202/400/401/403/409/422.
- `GET /api/v2/mobile-receipts/{id}`: részlet és evidence; idegen tenant esetén 404-szerű válasz.
- `PATCH /api/v2/mobile-receipts/{id}`: `expected_revision` alapú módosítás; 200/409/422.
- `POST /api/v2/mobile-receipts/{id}/confirm`: kontrollált állapotátmenet; 200/403/409/422.
- Minden hiba `application/problem+json` alakú `ApiProblem`; minden siker tenant- és revision-azonosítót ad.

### Lépésről lépésre kidolgozott kontrollfolyamat

1. A kamerafolyamat minimális lépésben capture→preview→accept/retake átmenetet biztosít, a draftot képelfogadáskor azonnal megőrzi.
2. A képtömörítés profil alapján történik, de olvashatósági minimumot és eredeti metaadatot megőriz; túl gyenge kép raise ImageUnreadableError(...).
3. Feltöltési és feldolgozási állapot route-váltás, háttérbe helyezés és visszatérés után a draftazonosítóval folytatható.
4. A review a bizonytalan mezőket sorrendezi, megfelelő input mode-ot és billentyűzet feletti látható műveletet ír elő.
5. Alsó műveletsáv safe-area aware, legalább 44×44 CSS px célokkal; minden állapot és hiba képernyőolvasónak bejelentendő.
6. Hálózatvesztés nem töröl draftot; idempotens resume nem duplikál nyugtát. Jóváhagyás után a létrejött nyugta visszakereshető.

## 12. Adatmodell és perzisztencia

- Fő aggregátum: `MobileReceiptJourney`; kötelező `id`, `tenant_id`, `status`, `revision`, `created_at`, `updated_at`.
- Írások tenant tranzakcióban, optimistic lockinggal és idempotency rekorddal történnek.
- Egyedi kulcs: `(tenant_id, idempotency_key, command_type)`; az eltárolt request hash eltérés konfliktus.
- Audit esemény tartalmazza az aggregátumot, előző/új revíziót, aktort, okot, correlation ID-t és időt, de nem másol érzékeny teljes payloadot.
- Törlés csak projektmegőrzési szabály szerint; pénzügyi bizonyíték logikai törléssel és referenciaintegritással.

## 13. Tesztterv és lefedettségi leképezés

- REQ-048-01 → AC-048-01 → `.agent-pipeline/03_e2e_suites/test_e2e_048.py`; unit cél: `tests/unit/test_mobile_receipts_service.py::test_req_048_01`.
- REQ-048-02 → AC-048-02 → `.agent-pipeline/03_e2e_suites/test_e2e_048.py`; unit cél: `tests/unit/test_mobile_receipts_service.py::test_req_048_02`.
- REQ-048-03 → AC-048-03 → `.agent-pipeline/03_e2e_suites/test_e2e_048.py`; unit cél: `tests/unit/test_mobile_receipts_service.py::test_req_048_03`.
- REQ-048-04 → AC-048-04 → `.agent-pipeline/03_e2e_suites/test_e2e_048.py`; unit cél: `tests/unit/test_mobile_receipts_service.py::test_req_048_04`.
- REQ-048-05 → AC-048-05 → `.agent-pipeline/03_e2e_suites/test_e2e_048.py`; unit cél: `tests/unit/test_mobile_receipts_service.py::test_req_048_05`.
- REQ-048-06 → AC-048-06 → `.agent-pipeline/03_e2e_suites/test_e2e_048.py`; unit cél: `tests/unit/test_mobile_receipts_service.py::test_req_048_06`.
- REQ-048-07 → AC-048-07 → `.agent-pipeline/03_e2e_suites/test_e2e_048.py`; unit cél: `tests/unit/test_mobile_receipts_service.py::test_req_048_07`.
- REQ-048-08 → AC-048-08 → `.agent-pipeline/03_e2e_suites/test_e2e_048.py`; unit cél: `tests/unit/test_mobile_receipts_service.py::test_req_048_08`.

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
