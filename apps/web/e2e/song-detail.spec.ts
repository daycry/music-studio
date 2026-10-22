import {expect, test} from '@playwright/test';

test('E2E-07 muestra tomas, forma de onda, letra y procedencia', async ({page}) => {
  const songId = '01K70000000000000000000001';
  const takeId = '01K70000000000000000000002';
  const pairId = '01K70000000000000000000004';
  await page.route('http://127.0.0.1:8000/api/session/bootstrap', route => route.fulfill({json: {session_token: 'song-session'}}));
  await page.route(`http://127.0.0.1:8000/api/songs/${songId}`, route => route.fulfill({json: {id: songId, title: 'Libre', artist: 'Jordi', status: 'final', style_prompt: 'hip hop', master_take_id: takeId, updated_at: '2026-01-01T00:00:00Z', created_at: '2026-01-01T00:00:00Z'}}));
  await page.route(`http://127.0.0.1:8000/api/songs/${songId}/takes`, route => route.fulfill({json: {items: [{id: takeId, song_id: songId, batch_id: 'batch-1', variant_index: 0, status: 'ready', task: 'music.song', model_id: 'mock', seed: 1, params: {}, duration_s: 60, rating: 5, favorite: true, label: 'A', error_code: null, assets: {listen: {url: '/audio', media_type: 'audio/mpeg', sha256: 'abc'}}}, {id: pairId, song_id: songId, batch_id: 'batch-1', variant_index: 1, status: 'ready', task: 'music.song', model_id: 'mock', seed: 2, params: {}, duration_s: 60, rating: null, favorite: false, label: 'B', error_code: null, assets: {listen: {url: '/audio-b', media_type: 'audio/mpeg', sha256: 'ghi'}}}]}}));
  await page.route(`http://127.0.0.1:8000/api/songs/${songId}/lyrics`, route => route.fulfill({json: {items: [{id: '01K70000000000000000000003', song_id: songId, text: '[Verse]\nLibre', declaration: 'own', source: 'manual', sha256: 'def'}]}}));
  await page.route(/http:\/\/127\.0\.0\.1:8000\/api\/takes\/(01K70000000000000000000002|01K70000000000000000000004)\/peaks/, route => route.fulfill({json: {data: [[[.1, .4, .8, .3]]]}}));
  await page.route(/http:\/\/127\.0\.0\.1:8000\/api\/takes\/(01K70000000000000000000002|01K70000000000000000000004)\/(audio|master)/, route => route.fulfill({status: 200, contentType: route.request().url().endsWith('/master') ? 'audio/flac' : 'audio/mpeg', body: route.request().url().endsWith('/master') ? 'flac' : 'mp3'}));
  await page.goto(`/songs/${songId}`);
  await expect(page.getByRole('heading', {name: 'Libre'})).toBeVisible();
  await expect(page.locator('.take-list button').first()).toContainText('A');
  await page.getByRole('button', {name: 'Ir a la pareja'}).first().click();
  await expect(page.locator('.take-list li.selected')).toContainText('B');
  await expect(page.getByRole('heading', {name: 'Procedencia'})).toBeVisible();
  await page.getByRole('button', {name: 'Letra'}).click();
  await expect(page.getByText('[Verse]')).toBeVisible();
  await page.getByRole('button', {name: 'Audio'}).click();
  const mp3 = page.waitForEvent('download');
  await page.getByRole('button', {name: 'Descargar MP3'}).first().click();
  await expect((await mp3).suggestedFilename()).toContain('-listen.mp3');
  const flac = page.waitForEvent('download');
  await page.getByRole('button', {name: 'Descargar FLAC'}).first().click();
  await expect((await flac).suggestedFilename()).toContain('-master.flac');
});
