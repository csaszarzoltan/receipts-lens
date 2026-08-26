# US-000 sablon — JTBD + Gherkin + gui_flow kontraktus

- Epic: {...}
- Priority: P0 / P1 / P2
- Source: docs/research/YYYY-MM-DD-*.md + ADR-NNN
- Prototípus: {Figma link / preview URL} — státusz: draft | approved

## Story (As a … I want … So that …)

**Happy:** As a {...} I want {...} So that {... — JTBD}.
**Error:** As a {...} I want {...} So that {...}.
**Edge:** As a {...} I want {...} So that {...}.
**Gui:** As a {...} I want {...} So that {...}.

## Acceptance Criteria (Gherkin — given/when/then)

### AC1: Happy path
- **given** {előfeltétel} | **when** {akció} | **then** {elvárás, mérhető}
### AC2: Error state
- **given** {előfeltétel} | **when** {akció} | **then** {elvárás}
### AC3: Edge / onboarding
- **given** {előfeltétel} | **when** {akció} | **then** {elvárás}
### AC4: GUI layout / interaction
- **given** {desktop viewport} | **when** {betölt} | **then** {layout assertions}

## gui_flow (UI kontraktus — a developer EZT követi)

### Happy flow:
1. Open `/{route}` → látom: {heading, CTA, blokkok}
2. Click {gomb — pozíció, szín, label} → {mi történik}
3. Modal/Toast: {pontos szöveg} → {következő lépés}
4. Assert: {URL / toast / lista tartalma / számérték (nem skeleton)}

### Error flow:
1. Open `/{route}` {hiba előfeltétellel} → {hibaüzenet + CTA}
2. NEM látom: {skeleton / blank / crash}

### Edge / onboarding flow:
1. Open `/{route}` {edge előfeltétellel} → {speciális UI}
2. Click {CTA} → {állapotváltozás}

## Megjegyzés
- Max 400 sor/file.
- gui_flow lépést csak US-frissítéssel szabad változtatni.
- E2E skeleton: `frontend/e2e/us_NNN_*.spec.ts`
- Áti tesztek: `tests/test_us_NNN_*.py`
