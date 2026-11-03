import {expect, test} from './fixtures';

test('E2E-07 muestra tomas, forma de onda, letra y procedencia', async ({page}) => {
  const songId = '01K70000000000000000000001';
  const takeId = '01K70000000000000000000002';
  const pairId = '01K70000000000000000000004';
  let rating: unknown;
  await page.route(`**/api/takes/${takeId}`, async route => {
    rating = route.request().postDataJSON().rating;
    return route.fulfill({json: {id: takeId, song_id: songId, batch_id: 'batch-1', variant_index: 0, status: 'ready', task: 'music.song', label: 'A', rating, favorite: true, duration_s: 60, params: {}, assets: {listen: {url: '/audio', media_type: 'audio/mpeg', sha256: 'abc'}}}});
  });
  await page.route('**/api/takes/*/analysis', route => route.fulfill({json: {items: []}}));
  await page.route('http://127.0.0.1:8000/api/session/bootstrap', route => route.fulfill({json: {expires_in_s: 3600, session_token: 'song-session'}}));
  await page.route(`http://127.0.0.1:8000/api/songs/${songId}`, route => route.fulfill({json: {id: songId, title: 'Libre', artist: 'Jordi', status: 'final', style_prompt: 'hip hop', master_take_id: takeId, updated_at: '2026-01-01T00:00:00Z', created_at: '2026-01-01T00:00:00Z'}}));
  await page.route(`http://127.0.0.1:8000/api/songs/${songId}/takes`, route => route.fulfill({json: {items: [{id: takeId, song_id: songId, batch_id: 'batch-1', variant_index: 0, status: 'ready', task: 'music.song', model_id: 'mock', seed: 1, params: {}, duration_s: 60, rating: 5, favorite: true, label: 'A', error_code: null, assets: {listen: {url: '/audio', media_type: 'audio/mpeg', sha256: 'abc'}}}, {id: pairId, song_id: songId, batch_id: 'batch-1', variant_index: 1, status: 'ready', task: 'music.song', model_id: 'mock', seed: 2, params: {}, duration_s: 60, rating: null, favorite: false, label: 'B', error_code: null, assets: {listen: {url: '/audio-b', media_type: 'audio/mpeg', sha256: 'ghi'}}}]}}));
  await page.route(`http://127.0.0.1:8000/api/songs/${songId}/lyrics`, route => route.fulfill({json: {items: [{id: '01K70000000000000000000003', song_id: songId, text: '[Verse]\nLibre', declaration: 'own', source: 'manual', sha256: 'def'}]}}));
  await page.route(/http:\/\/127\.0\.0\.1:8000\/api\/takes\/(01K70000000000000000000002|01K70000000000000000000004)\/peaks/, route => route.fulfill({json: {data: [[[.1, .4, .8, .3]]]}}));
  await page.route(/http:\/\/127\.0\.0\.1:8000\/api\/takes\/(01K70000000000000000000002|01K70000000000000000000004)\/(audio|master)/, route => route.fulfill({status: 200, contentType: route.request().url().endsWith('/master') ? 'audio/flac' : 'audio/mpeg', body: route.request().url().endsWith('/master') ? 'flac' : 'mp3'}));
  await page.goto(`/songs/${songId}`);
  await expect(page.getByRole('heading', {name: 'Libre'})).toBeVisible();
  await expect(page.locator('.take-list button').first()).toContainText('A');
  await page.getByRole('button', {name: 'Valorar 5/5 A', exact: true}).click();
  await expect.poll(() => rating).toBeNull();
  await expect(page.getByRole('button', {name: 'Valorar 5/5 A', exact: true})).toHaveAttribute('aria-pressed', 'false');
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

test('CPU-UI sólo permite maestro ready y muestra fallos de descarga', async ({page}) => {
  const song = {id: '01K70000000000000000000041', title: 'Pruebas de maestro', status: 'draft', master_take_id: null};
  const takes = [{id: '01K70000000000000000000042', status: 'failed', label: 'Fallida'}, {id: '01K70000000000000000000043', status: 'ready', label: 'Lista'}];
  let master: string | undefined;
  await page.route(`**/api/songs/${song.id}`, route => route.fulfill({json: song}));
  await page.route(`**/api/songs/${song.id}/takes`, route => route.fulfill({json: {items: takes.map(take => ({...take, song_id: song.id, task: 'music.song', rating: null, favorite: false, params: {}, assets: {}}))}}));
  await page.route(`**/api/songs/${song.id}/lyrics`, route => route.fulfill({json: {items: []}}));
  await page.route(`**/api/songs/${song.id}/master`, route => { master = route.request().postDataJSON().take_id; return route.fulfill({json: {...song, master_take_id: master}}); });
  await page.goto(`/songs/${song.id}`);
  const items = page.locator('.take-list li');
  await expect(items.nth(0).getByRole('button', {name: 'Marcar maestro'})).toBeDisabled();
  await items.nth(1).getByRole('button', {name: 'Marcar maestro'}).click();
  await expect(page.getByText('Maestro: Lista', {exact: true})).toBeVisible();
  expect(master).toBe(takes[1].id);
  await items.nth(1).getByRole('button', {name: 'Descargar MP3'}).click();
  await expect(page.getByRole('alert').filter({hasText: /^No se pudo descargar el audio\.$/})).toBeVisible();
});
