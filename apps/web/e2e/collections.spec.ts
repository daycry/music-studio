import {expect, test} from '@playwright/test';

test('E2E-10 filtra, crea y mueve canciones entre colecciones', async ({page}) => {
  const requests: string[] = [];
  await page.route('http://127.0.0.1:8000/api/session/bootstrap', route => route.fulfill({json: {session_token: 'collections-session'}}));
  await page.route('http://127.0.0.1:8000/api/collections', async route => {
    if (route.request().method() === 'POST') return route.fulfill({status: 201, json: {id: 'collection-new', name: 'Cierres'}});
    return route.fulfill({json: {items: [{id: 'collection-1', name: 'Favoritas'}]}});
  });
  await page.route('http://127.0.0.1:8000/api/songs?*', async route => {
    requests.push(route.request().url());
    return route.fulfill({json: {items: [{id: 'song-1', title: 'Libre', artist: null, status: 'ready', style_prompt: 'hip hop', collection_id: null, master_take_id: null, updated_at: '2026-01-01T00:00:00Z', created_at: '2026-01-01T00:00:00Z'}, {id: 'song-2', title: 'Todav?a', artist: null, status: 'ready', style_prompt: 'rap', collection_id: null, master_take_id: null, updated_at: '2026-01-01T00:00:00Z', created_at: '2026-01-01T00:00:00Z'}], next: null}});
  });
  await page.route(/http:\/\/127\.0\.0\.1:8000\/api\/songs\/(song-1|song-2)/, route => route.fulfill({json: {id: route.request().url().endsWith('song-1') ? 'song-1' : 'song-2', collection_id:'collection-1'}}));
  await page.goto('/songs');
  await page.getByRole('button', {name: 'Colecciones'}).click();
  await page.getByRole('button', {name: 'Favoritas', exact: true}).click();
  await expect.poll(() => requests.some(url => url.includes('collection_id=collection-1'))).toBe(true);
  await page.getByRole('button', {name: /Nueva colecci/}).click();
  await page.getByLabel('Nombre').fill('Cierres');
  await page.getByRole('button', {name: 'Crear', exact: true}).click();
  await expect(page.getByText('Cierres')).toBeVisible();
  await page.locator('.song-card select').first().selectOption('collection-1');
  await page.getByRole('checkbox', {name: 'Seleccionar Libre'}).check();
  await page.getByRole('checkbox', {name: 'Seleccionar Todav?a'}).check();
  await page.getByLabel('Colecci?n destino').selectOption('collection-1');
  await page.getByRole('button', {name: /Mover seleccionadas/}).click();
  await expect(page.getByRole('checkbox', {name: 'Seleccionar Libre'})).not.toBeChecked();
});
