## BRIEF-041: Háztartási bevásárlási árfigyelés

**Státusz:** READY_FOR_SPEC  
**Kapcsolódó feature:** FEAT-041  
**Forrás:** termékbővítési igény, a jelenlegi ReceiptLens képességeihez, adatmodelljéhez és RVAD 1.1 módszertanához illesztve

## Probléma

A gyakran vásárolt termékek ára és kiszerelése idővel változik, amit nyugták sokaságából nehéz észrevenni, ezért a háztartás későn reagálhat a szokatlan drágulásra.

## Célcsoport és kontextus

Háztartási felhasználó, aki rendszeresen vásárolt termékek árát és egységárát szeretné összehasonlítani.

## Kívánt eredmény

A felhasználó a teljes munkafolyamatot érthető, kontrollálható és megszakítás után folytatható módon tudja végigvinni. Az automatikus felismerés vagy javaslat nem válik észrevétlenül végleges pénzügyi döntéssé: a bizonytalanság, a forrás és a következmény látható, a felhasználó jóváhagyhat, javíthat, elutasíthat vagy kivételt dokumentálhat. Csak a ténylegesen sikeres művelet jelenik meg befejezettként, és a lényeges változások auditálhatók.

## Jelenlegi funkciókat lefedő felhasználói történetek

- **US-041-01:** Felhasználóként szeretném, hogy a rendszer a nyugtatételekből ismétlődően vásárolt termékeket javasoljon követésre, hogy ne kelljen listát kézzel felépítenem.
- **US-041-02:** Felhasználóként szeretném jóváhagyni, összevonni vagy szétválasztani a hasonló termékneveket, hogy a különböző márkák és kiszerelések ne torzítsák az összehasonlítást.
- **US-041-03:** Felhasználóként szeretném az árat egységárra normalizálva is látni, ha a mennyiség és mértékegység ismert, hogy eltérő kiszerelések összevethetők legyenek.
- **US-041-04:** Felhasználóként szeretném termékenként látni az ár időbeli alakulását, a legutóbbi, tipikus és korábbi legalacsonyabb árat, hogy értelmezzem a változást.
- **US-041-05:** Felhasználóként szeretnék jelzést kapni a saját vásárlási múltamhoz képest szokatlan drágulásról, hogy ellenőrizhessem vagy módosíthassam a vásárlási szokásaimat.
- **US-041-06:** Felhasználóként szeretném látni, mely nyugták és tételek támasztják alá az árváltozást, hogy a jelzés ellenőrizhető legyen.
- **US-041-07:** Felhasználóként szeretném kizárni az akciós, kuponos, hibásan felismert vagy nem összehasonlítható vásárlást a referenciaárból, hogy a trend ne legyen félrevezető.
- **US-041-08:** Felhasználóként szeretném a rendszertől kapott termékazonosítást és riasztási küszöböt felülbírálni, hogy a saját igényeim szerint kövessem az árakat.
- **US-041-09:** Felhasználóként szeretném megérteni, ha kevés vagy bizonytalan adat miatt nem állapítható meg megbízható árváltozás, hogy ne kezeljem tényként a becslést.

## Scope

- Saját nyugtákból származó termék- és egységár-előzmények.
- Termékazonosítás jóváhagyással, aliasok, kiszerelés- és mértékegység-kezelés.
- Trendek, magyarázható szokatlan áremelkedési jelzések és forrásnyugták.
- Felhasználói korrekció, kizárás és visszajelzés.
- A sikeres, üres, betöltési, bizonytalan, részleges, konfliktusos, jogosultság által korlátozott és újrapróbálható hibaállapotok.
- Felhasználói kontroll, javítás, megszakítás, idempotens újrapróbálás, auditálható változás és más háztartások adatainak elkülönítése.

## Non-scope

- Nyilvános webáruházak vagy versenytársak árainak internetes gyűjtése.
- Automatikus vásárlás vagy kereskedői árgarancia érvényesítése.
- Inflációs vagy befektetési tanácsadás.
- Belső komponensszerkezet, konkrét technológia, adatbázisséma vagy fejlesztési feladatlista; ezek a későbbi feature-specifikáció és ADR hatáskörébe tartoznak.

## Érintett rendszerek

- A nyugta-, tranzakció- és háztartási munkaterület kapcsolódó felületei.
- Az alkalmazási, tartós adatkezelési, keresési és auditálási réteg.
- Az értesítési, feldolgozási és integrációs szolgáltatások, ha a történet ezeket igényli.

## Kapcsolódó meglévő BRIEF-ek

- BRIEF-006: Nyugta feltöltése és feldolgozási sor.
- BRIEF-007: AI-alapú nyugtafelismerés és bizonytalanság.
- BRIEF-009: Nyugtaellenőrzés és javítás.
- BRIEF-016: Háztartási együttműködés és családi postafiók.
- BRIEF-019: Szinkronizálás és egyeztetés.
- BRIEF-020: Jóváhagyások és kontrollált változtatások.
- BRIEF-026: Értesítések és állapotüzenetek.
- BRIEF-027: Hozzáférhetőség és reszponzív navigáció.
- A kapcsolat nem jelent funkcionális átfedést: a jelen BRIEF saját felhasználói eredményét és életciklusát határozza meg.

## Bizonytalanságok

- A pontos üzleti küszöbök, határidők, alapértelmezések és jogosultsági mátrix termékdöntést igényelnek.
- A támogatott külső források, eszközök, csatornák és országfüggő szabályok köre külön kutatást vagy ADR-t igényelhet.
- A javaslatok bizonyossági szintjeit, magyarázatát, felülbírálását és tanulási hatását a SPEC-ben mérhető szerződésként kell rögzíteni.
- A SPEC-nek külön kell választania a blokkoló hibát, a felhasználó által elfogadható figyelmeztetést és az információs jelzést.
- A kötelező követelményekhez Given/When/Then acceptance scenario, RED tesztbizonyíték, célzott teszt és teljes regresszió szükséges a projekt módszertana szerint.
