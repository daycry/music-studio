import {expect, test} from '@playwright/test';

test('E2E-08 carga la biblioteca, busca y cambia a lista', async ({page}) => {
  await page.route('http://127.0.0.1:8000/api/session/bootstrap', route => route.fulfill({json: {session_token: 'songs-session'}}));
  await page.route('http://127.0.0.1:8000/api/songs**', route => route.fulfill({json: {items: [{id: '01K70000000000000000000001', title: 'Libre', artist: 'Jordi', status: 'draft', style_prompt: 'hip hop', master_take_id: null, updated_at: '2026-01-01T00:00:00Z', created_at: '2026-01-01T00:00:00Z'}], next: null}}));
  await page.goto('/songs');
  await expect(page.getByRole('link', {name: 'Libre'})).toBeVisible();
  await page.getByRole('button', {name: 'Lista'}).click();
  await expect(page.getByRole('button', {name: 'Lista'})).toHaveAttribute('aria-pressed', 'true');
  await page.getByLabel('Buscar canciones').fill('Libre');
  await page.getByRole('button', {name: 'Buscar'}).click();
  await expect(page.getByRole('link', {name: 'Libre'})).toBeVisible();
});

test('E2E-08 abre la papelera y restaura una canción', async ({page}) => {
  let restored = false;
  await page.route('http://127.0.0.1:8000/api/session/bootstrap', route => route.fulfill({json: {session_token: 'songs-session'}}));
  await page.route('http://127.0.0.1:8000/api/songs/trash**', route => route.fulfill({json: {items: restored ? [] : [{id: '01K70000000000000000000001', title: 'Archivada', artist: null, status: 'draft', style_prompt: '', master_take_id: null, deleted_at: '2026-01-01T00:00:00Z', purge_after: '2026-01-31T00:00:00Z', updated_at: '2026-01-01T00:00:00Z', created_at: '2026-01-01T00:00:00Z'}], next: null}}));
  await page.route('http://127.0.0.1:8000/api/songs/01K70000000000000000000001/restore', async route => { restored = true; await route.fulfill({json: {id: '01K70000000000000000000001', title: 'Archivada'}}); });
  await page.route('http://127.0.0.1:8000/api/songs?*', route => route.fulfill({json: {items: [], next: null}}));
  await page.goto('/songs');
  await page.getByRole('button', {name: 'Abrir papelera'}).click();
  await expect(page.getByText('Archivada')).toBeVisible();
  await page.getByRole('button', {name: 'Restaurar'}).click();
  await expect(page.getByText('La papelera está vacía')).toBeVisible();
});
