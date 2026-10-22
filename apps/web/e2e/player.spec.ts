import {expect, test} from '@playwright/test';

test('E2E-01 conserva la toma seleccionada y los atajos al navegar', async ({page}) => {
  const songId = '01K70000000000000000000011';
  const takeA = '01K70000000000000000000012';
  await page.route('http://127.0.0.1:8000/api/session/bootstrap', route => route.fulfill({json: {session_token: 'player-session'}}));
  await page.route(`http://127.0.0.1:8000/api/songs/${songId}`, route => route.fulfill({json: {id: songId, title: 'Libre', artist: 'Jordi', status: 'ready', style_prompt: 'hip hop', master_take_id: takeA, updated_at: '2026-01-01T00:00:00Z', created_at: '2026-01-01T00:00:00Z'}}));
  await page.route(`http://127.0.0.1:8000/api/songs/${songId}/takes`, route => route.fulfill({json: {items: [
    {id: takeA, song_id: songId, status: 'ready', task: 'music.song', model_id: 'mock', seed: 1, params: {}, duration_s: 60, rating: null, favorite: false, label: 'A', error_code: null, assets: {listen: {url: `/api/takes/${takeA}/audio`, media_type: 'audio/mpeg', sha256: 'a'}}},
    {id: '01K70000000000000000000013', song_id: songId, status: 'ready', task: 'music.song', model_id: 'mock', seed: 2, params: {}, duration_s: 60, rating: null, favorite: false, label: 'B', error_code: null, assets: {listen: {url: '/api/takes/take-b/audio', media_type: 'audio/mpeg', sha256: 'b'}}},
  ]}}));
  await page.route(`http://127.0.0.1:8000/api/songs/${songId}/lyrics`, route => route.fulfill({json: {items: []}}));
  await page.route(`http://127.0.0.1:8000/api/takes/${takeA}/peaks`, route => route.fulfill({json: {data: []}}));
  await page.route('http://127.0.0.1:8000/api/songs?*', route => route.fulfill({json: {items: [], next: null}}));
  await page.goto(`/songs/${songId}`);
  await page.locator('.take-list button').first().click();
  await expect(page.getByRole('region', {name: 'Reproductor'})).toContainText('Libre');
  await page.goto('/songs');
  await expect(page.getByRole('region', {name: 'Reproductor'})).toContainText('Libre');
  await page.keyboard.press('?');
  await expect(page.getByRole('dialog', {name: 'Ayuda del reproductor'})).toBeVisible();
});
