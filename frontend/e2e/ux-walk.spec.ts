import { test, expect, Page, Route } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import fs from 'node:fs';
import path from 'node:path';

// Walk of the primary task on mocked API responses (no backend, no real data).
const cors = { 'access-control-allow-origin': 'http://127.0.0.1:3040', 'access-control-allow-methods': 'GET,POST,PUT,PATCH,DELETE,OPTIONS', 'access-control-allow-headers': 'Content-Type,Authorization,Idempotency-Key,X-Tenant-ID,X-Role' };
function fulfill(route: Route, payload: Parameters<Route['fulfill']>[0]) {
  return route.fulfill(route.request().method() === 'OPTIONS' ? { status: 204, headers: cors } : { ...payload, headers: { ...cors, ...payload?.headers } });
}
const fixture = (name: string) => fs.readFileSync(path.join(__dirname, 'fixtures', name));

async function seed(page: Page) {
  await page.addInitScript(() => { localStorage.setItem('receiptlens.session', 'ux-token'); localStorage.setItem('receiptlens.locale', 'hu'); });
  await page.route('**/auth/session/me', r => fulfill(r, { json: { tenant_id: 'ux', role: 'owner', email: 'ux@example.test' } }));
  await page.route('**/product/preferences', r => fulfill(r, { json: { onboarding_done: true, language: 'hu', base_currency: 'HUF', base_currency_source: 'saved' } }));
  await page.route('**/auth/google/status', r => fulfill(r, { json: { enabled: false } }));
  await page.route('**/api/v1/quota', r => fulfill(r, { json: { used: 0, limit: 25, pro: false } }));
  await page.route('**/product/receipts?*', r => fulfill(r, { json: { items: [], total: 0, limit: 50, offset: 0, categories: [] } }));
}

async function uploads(page: Page) {
  const posts: string[] = [];
  await page.route('**/product/receipts/upload', async route => {
    if (route.request().method() === 'OPTIONS') { await fulfill(route, {}); return; }
    posts.push(route.request().headers()['idempotency-key'] || '');
    await fulfill(route, { status: 201, json: { receipt_id: 'r' + posts.length, status: 'completed', receipt: { vendor: 'Coop', total: 1200, currency: 'HUF' } } });
  });
  return posts;
}

test('I1 a blurry photo is held until the user chooses; a sharp one uploads at once', async ({ page }) => {
  await seed(page);
  const posts = await uploads(page);
  await page.goto('/upload');
  const input = page.getByTestId('dropzone-input');
  await input.setInputFiles({ name: 'blurry.jpg', mimeType: 'image/jpeg', buffer: fixture('test-receipt-coop-blurry.jpg') });
  const warning = page.getByRole('alert').filter({ hasText: 'nehezen olvasható' });
  await expect(warning).toBeVisible();
  await expect(warning.getByRole('button', { name: 'Újra fotózom' })).toBeVisible();
  expect(posts).toHaveLength(0);
  const axe = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']).analyze();
  expect(axe.violations.map(v => `${v.id}: ${v.nodes.length}`)).toEqual([]);
  await warning.getByRole('button', { name: 'Így is feltöltöm' }).click();
  await expect.poll(() => posts.length).toBe(1);
  await expect(page.getByRole('alert').filter({ hasText: 'nehezen olvasható' })).toHaveCount(0);

  await input.setInputFiles({ name: 'sharp.jpg', mimeType: 'image/jpeg', buffer: fixture('test-receipt-coop.jpg') });
  await expect.poll(() => posts.length).toBe(2);
  await expect(page.getByRole('alert').filter({ hasText: 'nehezen olvasható' })).toHaveCount(0);
});

const reviewItems = {
  items: [
    { receipt_id: 'ok1', version: 1, receipt: { vendor: 'Spar', date: '2026-10-16', total: 12490, currency: 'HUF', confidence: { total: 0.7 }, confidence_level: 'medium' }, checks: { lines_match: true, line_sum: 12490 } },
    { receipt_id: 'bad1', version: 1, receipt: { vendor: 'Lidl', date: '2026-10-15', total: 8730, currency: 'HUF', confidence: { total: 0.6 }, confidence_level: 'medium' }, checks: { lines_match: false, line_sum: 8100 } },
  ],
};

async function reviewSeed(page: Page) {
  await seed(page);
  await page.route('**/product/review-items*', r => fulfill(r, { json: reviewItems }));
  await page.route('**/product/receipts/*/image', r => fulfill(r, { status: 404, body: 'none' }));
}

test('I4 the receipt whose lines do not add up is first and shows the mismatch before the amount', async ({ page }) => {
  await reviewSeed(page);
  await page.goto('/review');
  const cards = page.getByRole('list', { name: 'Ellenőrzés' }).getByRole('listitem');
  await expect(cards).toHaveCount(2);
  await expect(cards.first()).toContainText('Lidl');
  const mismatch = cards.first().getByTestId('review-mismatch');
  await expect(mismatch).toBeVisible();
  const mismatchBox = await mismatch.boundingBox();
  const amountBox = await cards.first().getByRole('textbox').boundingBox();
  expect(mismatchBox!.y).toBeLessThan(amountBox!.y);
  await expect(cards.nth(1)).toContainText('Spar');
  await expect(cards.nth(1).getByTestId('review-mismatch')).toHaveCount(0);
});

for (const [name, url, ready] of [
  ['upload', '/upload', 'Nyugta hozzáadása'],
  ['review', '/review', 'Ellenőrzés'],
  ['receipts', '/receipts', 'Nyugták'],
  ['more', '/more', 'Továbbiak'],
  ['finances', '/finances', 'Pénzügyeim'],
] as const) {
  test(`I2 ${name} has no axe violations and no horizontal scroll at 390 and 1280 px`, async ({ page }) => {
    await reviewSeed(page);
    for (const width of [390, 1280]) {
      await page.setViewportSize({ width, height: 900 });
      await page.goto(url);
      await expect(page.getByRole('heading', { name: ready, exact: true }).first()).toBeVisible();
      const results = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']).analyze();
      expect(results.violations.map(v => `${v.id}: ${v.nodes.length}`)).toEqual([]);
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
      expect(overflow).toBeLessThanOrEqual(0);
    }
  });
}

test('I2 keyboard only: the file button opens the chooser and the mismatch review is reachable', async ({ page }) => {
  await reviewSeed(page);
  await page.goto('/upload');
  await page.waitForLoadState('networkidle'); // the keypress must not land before hydration attaches handlers
  const button = page.getByRole('button', { name: 'Fájl kiválasztása', exact: true });
  await button.focus();
  await expect(button).toBeFocused();
  const chooser = page.waitForEvent('filechooser');
  await page.keyboard.press('Enter');
  await chooser;
  await page.goto('/review');
  await expect(page.getByTestId('review-mismatch')).toBeVisible();
  await page.keyboard.press('Tab');
  const focusable: string[] = [];
  for (let i = 0; i < 25; i++) {
    focusable.push(await page.evaluate(() => { const e = document.activeElement as HTMLElement | null; return e ? `${e.tagName}:${(e.getAttribute('aria-label') || e.textContent || '').trim().slice(0, 30)}` : 'none'; }));
    await page.keyboard.press('Tab');
  }
  expect(focusable.some(x => x.includes('Összeg megerősítése') || x.includes('Rendben'))).toBe(true);
});

/** Width and height of the first JPEG inside a multipart body (SOF marker). */
function jpegSize(body: Buffer): { width: number; height: number } {
  let i = body.indexOf(Buffer.from([0xff, 0xd8]));
  i += 2;
  while (i < body.length - 9) {
    if (body[i] !== 0xff) { i++; continue; }
    const marker = body[i + 1];
    if (marker >= 0xc0 && marker <= 0xcf && ![0xc4, 0xc8, 0xcc].includes(marker)) {
      return { height: body.readUInt16BE(i + 5), width: body.readUInt16BE(i + 7) };
    }
    i += 2 + body.readUInt16BE(i + 2);
  }
  throw new Error('no JPEG size found');
}

test('I5 a receipt photographed on a dark table is cropped to the paper; a full-frame receipt is untouched', async ({ page }) => {
  await seed(page);
  const sizes: { width: number; height: number; name: string }[] = [];
  await page.route('**/product/receipts/upload', async route => {
    if (route.request().method() === 'OPTIONS') { await fulfill(route, {}); return; }
    const body = route.request().postDataBuffer()!;
    sizes.push({ ...jpegSize(body), name: /filename="([^"]+)"/.exec(body.toString('latin1'))?.[1] ?? '' });
    await fulfill(route, { status: 201, json: { receipt_id: 'r' + sizes.length, status: 'completed', receipt: { vendor: 'Coop', total: 1200, currency: 'HUF' } } });
  });
  await page.goto('/upload');
  const input = page.getByTestId('dropzone-input');
  await input.setInputFiles({ name: 'table.jpg', mimeType: 'image/jpeg', buffer: fixture('test-receipt-coop-on-table.jpg') });
  await expect.poll(() => sizes.length).toBe(1);
  expect(sizes[0].width).toBeLessThan(800);   // original is 1100 wide, the paper is 600 wide
  expect(sizes[0].height).toBeLessThan(950);  // original is 1100 high, the paper is 800 high
  expect(sizes[0].width).toBeGreaterThanOrEqual(600);
  expect(sizes[0].height).toBeGreaterThanOrEqual(800);
  await input.setInputFiles({ name: 'full.jpg', mimeType: 'image/jpeg', buffer: fixture('test-receipt-coop.jpg') });
  await expect.poll(() => sizes.length).toBe(2);
  expect(sizes[1]).toMatchObject({ width: 600, height: 800, name: 'full.jpg' });
});
