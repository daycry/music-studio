import {expect, silentWav, test} from './fixtures';

test('E2E-08 carga la biblioteca, busca y cambia a lista', async ({page}) => {
  await page.route('http://127.0.0.1:8000/api/session/bootstrap', route => route.fulfill({json: {expires_in_s: 3600, session_token: 'songs-session'}}));
  await page.route('http://127.0.0.1:8000/api/songs**', route => route.fulfill({json: {items: [{id: '01K70000000000000000000001', title: 'Libre', artist: 'Jordi', status: 'draft', style_prompt: 'hip hop', master_take_id: null, updated_at: '2026-01-01T00:00:00Z', created_at: '2026-01-01T00:00:00Z'}], next: null}}));
  await page.goto('/songs');
  await expect(page.getByRole('link', {name: 'Libre'})).toBeVisible();
  await page.getByRole('button', {name: 'Lista'}).click();
  await expect(page.getByRole('button', {name: 'Lista'})).toHaveAttribute('aria-pressed', 'true');
  await page.getByLabel('Buscar canciones').fill('Libre');
  const search = page.waitForRequest(request => request.url().includes('q=Libre'));
  await page.getByLabel('Buscar canciones').press('Enter');
  await search;
  await expect(page.getByRole('link', {name: 'Libre'})).toBeVisible();
});

test('CPU-UI preescucha sin maestro usa última toma ready y explica fallback', async ({page}) => {
  const songId = '01K70000000000000000000001';
  let audioTake: string | undefined;
  await page.route('**/api/songs?*', route => route.fulfill({json: {items: [{id: songId, title: 'Sin maestro', status: 'draft', style_prompt: 'pop', master_take_id: null}], next: null}}));
  await page.route(`**/api/songs/${songId}/takes`, route => route.fulfill({json: {items: [
    {id: 'older', status: 'ready', created_at: '2026-01-01T00:00:00Z'},
    {id: 'newest', status: 'failed', created_at: '2026-01-03T00:00:00Z'},
    {id: 'latest-ready', status: 'ready', created_at: '2026-01-02T00:00:00Z'},
  ]}}));
  await page.route('**/api/takes/*/audio', route => { audioTake = route.request().url().split('/').at(-2); return route.fulfill({contentType: 'audio/wav', body: silentWav()}); });
  await page.goto('/songs');
  await page.getByRole('button', {name: 'Preescuchar', exact: true}).click();
  await expect.poll(() => audioTake).toBe('latest-ready');
  await expect(page.getByText(/última toma disponible/i)).toBeVisible();
});

test('E2E-08 abre la papelera y restaura una canción', async ({page}) => {
  let restored = false;
  await page.route('http://127.0.0.1:8000/api/session/bootstrap', route => route.fulfill({json: {expires_in_s: 3600, session_token: 'songs-session'}}));
  await page.route('http://127.0.0.1:8000/api/songs/trash**', route => route.fulfill({json: {items: restored ? [] : [{id: '01K70000000000000000000001', title: 'Archivada', artist: null, status: 'draft', style_prompt: '', master_take_id: null, deleted_at: '2026-01-01T00:00:00Z', purge_after: '2026-01-31T00:00:00Z', updated_at: '2026-01-01T00:00:00Z', created_at: '2026-01-01T00:00:00Z'}], next: null}}));
  await page.route('http://127.0.0.1:8000/api/songs/01K70000000000000000000001/restore', async route => { restored = true; await route.fulfill({json: {id: '01K70000000000000000000001', title: 'Archivada'}}); });
  await page.route('http://127.0.0.1:8000/api/songs?*', route => route.fulfill({json: {items: [], next: null}}));
  await page.goto('/songs');
  await page.getByRole('button', {name: 'Abrir papelera'}).click();
  await expect(page.getByText('Archivada')).toBeVisible();
  await page.getByRole('button', {name: 'Restaurar'}).click();
  await expect(page.getByText('La papelera está vacía')).toBeVisible();
});
