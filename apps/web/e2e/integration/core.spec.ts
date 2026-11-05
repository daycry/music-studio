import {expect, test} from '@playwright/test';
import {readFile} from 'node:fs/promises';
import {api, apiOrigin, composer, generate, ready, song, takes, verifiedModel, openComposer, observeBrowserSessions, revokeSessions, observeGeneration, browserRange} from './helpers';

test.beforeEach(async ({page}) => {observeBrowserSessions(page);});
test.afterEach(async ({page, request}, testInfo) => {await revokeSessions(page, request, testInfo);});

test('E2E-02/03 valida letra y autoría en navegador y API reales', async ({page, request}) => {
  const modelId = await verifiedModel(request);
  await openComposer(page);
  await page.getByLabel('Letra', {exact: true}).fill('[verso]\nTexto válido\n[chrous');
  await expect(page.locator('.lyrics-mirror .invalid-tag')).toContainText('[chrous');
  await expect(page.getByRole('button', {name: 'Generar', exact: true})).toBeDisabled();
  await page.getByLabel('Letra', {exact: true}).fill('[Verse]\nMi canción local');
  await page.getByLabel('Estilo musical', {exact: true}).fill('autoría integración');
  await expect(page.getByRole('button', {name: 'Generar', exact: true})).toBeDisabled();
  await expect(page.locator('#create-disabled-reasons')).toContainText('Necesaria para generar');
  const denied = await api(request, '/api/generations', {method: 'POST', data: {task: 'music.song', model_id: modelId, lyrics: '[Verse]\nMi canción local', style_prompt: 'pop', language: 'es', params: {duration_s: 10}, n_outputs: 1}});
  expect(denied.status()).toBe(422);
  expect((await denied.json()).code).toBe('LYRICS_DECLARATION_REQUIRED');
});

test('E2E-01/07/08/11 genera dos takes, escucha, descarga y conserva maestro en biblioteca', async ({page, request}, testInfo) => {
  const marker = `integracion${Date.now()}`;
  await composer(page, `pop ${marker}`);
  await expect(page.getByLabel('Variantes', {exact: true})).toHaveValue('1');
  await expect(page.getByLabel('Variantes', {exact: true}).locator('option')).toHaveCount(2);
  await page.getByLabel('Variantes', {exact: true}).selectOption('2');
  const observation = await observeGeneration(page, request, testInfo);
  try {
    const result = await generate(page);
    await observation.follow(result);
    expect(result.take_ids).toHaveLength(2);
    await expect(page.locator('.generation-card')).toHaveCount(2);
    await expect(page.locator('.generation-card [data-stage="generating"].current').first()).toBeVisible();
    await testInfo.attach('composer-generating', {body: await page.screenshot({fullPage: true}), contentType: 'image/png'});
    await ready(page, request, result);
    await observation.verify(result);
    await testInfo.attach('composer-ready', {body: await page.screenshot({fullPage: true}), contentType: 'image/png'});
    const generated = await takes(request, result.song_id);
    expect(generated).toHaveLength(2);
    expect(generated.every(take => take.assets?.listen && take.assets?.master)).toBe(true);
    const peak = await api(request, `/api/takes/${generated[0].id}/peaks`);
    expect(peak.ok()).toBeTruthy();
    expect((await peak.json()).data[0].flat().length).toBeGreaterThan(0);
    const info = await song(request, result.song_id);
    expect(info.status).toBe('draft');
    await page.goto(`/songs/${result.song_id}`);
    await expect(page.getByRole('heading', {level: 1})).toHaveText(info.title);
    const rows = page.locator('.take-list > li');
    await expect(rows).toHaveCount(2);
    await rows.first().locator(':scope > button').click();
    const audio = page.locator('.player-dock audio');
    await expect(audio).toHaveAttribute('src', /^blob:/);
    await page.getByRole('region', {name: 'Reproductor', exact: true}).getByRole('button', {name: 'Reproducir', exact: true}).click();
    await expect.poll(() => audio.evaluate((node: HTMLAudioElement) => node.currentTime)).toBeGreaterThan(0);
    await page.getByRole('slider', {name: 'Posición del audio', exact: true}).fill('0.5');
    await expect.poll(() => audio.evaluate((node: HTMLAudioElement) => node.currentTime)).toBeGreaterThan(4);
    const firstTake = generated[0];
    const range = await api(request, `/api/takes/${firstTake.id}/audio`, {headers: {Range: 'bytes=0-127'}});
    expect(range.status()).toBe(206);
    expect(range.headers()['content-range']).toMatch(/^bytes 0-127\//);
    expect((await range.body()).length).toBe(128);
    expect(await browserRange(page, request, firstTake.id)).toEqual({status: 206, bytes: 128});
    for (const [name, extension, mime] of [['Descargar MP3', 'mp3', 'audio/mpeg'], ['Descargar FLAC', 'flac', 'audio/flac']]) {
      const downloaded = page.waitForEvent('download');
      await rows.first().getByRole('button', {name, exact: true}).click();
      const download = await downloaded;
      expect(download.suggestedFilename()).toBe(`${info.title}-${firstTake.id}.${extension}`);
      const bytes = await readFile((await download.path())!);
      expect(bytes.length).toBeGreaterThan(100);
      const asset = await api(request, `/api/takes/${firstTake.id}/${mime === 'audio/flac' ? 'master' : 'audio'}`);
      expect(asset.headers()['content-type']).toContain(mime);
      expect(await asset.body()).toEqual(bytes);
    }
    const rating = rows.nth(1).getByRole('button', {name: /^Valorar 4\/5/});
    await rating.click(); await expect(rating).toHaveAttribute('aria-pressed', 'true');
    await rating.click(); await expect(rating).toHaveAttribute('aria-pressed', 'false');
    expect((await takes(request, result.song_id))[1].rating).toBeNull();
    const master = generated[1];
    await rows.nth(1).getByRole('button', {name: 'Marcar maestro', exact: true}).click();
    await expect.poll(async () => (await song(request, result.song_id)).master_take_id).toBe(master.id);
    await expect(rows.nth(1).getByRole('button', {name: 'Marcar maestro', exact: true})).toBeDisabled();
    await page.getByRole('button', {name: 'Letra', exact: true}).click();
    await expect(page.locator('.lyrics-panel')).toContainText('Horizonte de integración');
    await testInfo.attach('song-ready-master', {body: await page.screenshot({fullPage: true}), contentType: 'image/png'});
    // La navegación cliente conserva el reproductor y su blob autenticado.
    await page.getByRole('link', {name: 'Volver a Canciones', exact: true}).click();
    await expect(audio).toHaveAttribute('src', /^blob:/);
    await page.getByRole('button', {name: 'Lista', exact: true}).click();
    await page.getByLabel('Buscar canciones', {exact: true}).fill(marker);
    await page.getByLabel('Buscar canciones', {exact: true}).press('Enter');
    const card = page.locator('.song-card').filter({has: page.getByRole('link', {name: info.title, exact: true})});
    await expect(card).toHaveCount(1);
    const previewResponse = page.waitForResponse(response => response.url() === `${apiOrigin}/api/takes/${master.id}/audio`);
    await card.getByRole('button', {name: 'Preescuchar', exact: true}).hover();
    expect((await previewResponse).ok()).toBeTruthy();
    await expect(card.getByRole('button', {name: 'Preescuchar', exact: true})).toHaveAttribute('data-state', 'playing');
    await expect.poll(() => card.locator('audio').evaluate((node: HTMLAudioElement) => node.currentTime)).toBeGreaterThan(0);
    await testInfo.attach('library-ready', {body: await page.screenshot({fullPage: true}), contentType: 'image/png'});
  } finally {await observation.close();}
});

test('E2E-11 instrumental conserva letra sin exigir autoría y termina ready', async ({page, request}) => {
  await composer(page, `ambient instrumental ${Date.now()}`, true);
  await expect(page.getByLabel('Letra', {exact: true})).toHaveValue('[Verse]\nHorizonte de integración\n[Chorus]\nUna canción local');
  await expect(page.getByLabel('Es mía', {exact: true})).not.toBeChecked();
  const submission = page.waitForRequest(request => request.url() === `${apiOrigin}/api/generations` && request.method() === 'POST');
  const result = await generate(page);
  const payload = (await submission).postDataJSON();
  expect(payload.task).toBe('music.instrumental');
  expect(payload).not.toHaveProperty('lyrics');
  expect(payload).not.toHaveProperty('lyrics_declaration');
  expect(payload.params).not.toHaveProperty('lyrics');
  await ready(page, request, result);
});

test('E2E-04 fallo PROVIDER_ERROR persiste sin retry automático y reintento explícito reutiliza take sin publicar', async ({page, request}) => {
  await composer(page, `synthwave ${Date.now()} @mock:fail_once=PROVIDER_ERROR`);
  const result = await generate(page);
  const card = page.locator(`[data-take-id="${result.take_ids[0]}"]`);
  await expect(card.getByRole('alert')).toContainText('PROVIDER_ERROR');
  await expect(card.getByRole('alert')).toContainText(result.generation_job_id);
  await expect.poll(async () => (await takes(request, result.song_id))[0].status).toBe('failed');
  const original = (await takes(request, result.song_id))[0];
  expect(Object.keys(original.assets ?? {})).toHaveLength(0);
  const response = page.waitForResponse(response => response.url() === `${apiOrigin}/api/jobs/${result.generation_job_id}/retry` && response.request().method() === 'POST');
  await card.getByRole('button', {name: 'Reintentar', exact: true}).click();
  const retry = await response; expect(retry.status()).toBe(202);
  const retried = await retry.json();
  expect(retried.generation_job_id).not.toBe(result.generation_job_id);
  expect(retried.take_ids).toEqual(result.take_ids);
  await ready(page, request, {...retried, song_id: result.song_id});
  const all = await takes(request, result.song_id);
  expect(all).toHaveLength(1);
  expect(all[0]).toMatchObject({id: original.id, status: 'ready', seed: original.seed, variant_index: original.variant_index});
  expect(all[0].assets?.listen).toBeTruthy();
  expect(all[0].assets?.master).toBeTruthy();
});

test('E2E-04 fallo INTERNAL permanente muestra error y conserva take fallido sin assets', async ({page, request}) => {
  await composer(page, `fallo permanente ${Date.now()} @mock:fail=INTERNAL`);
  const result = await generate(page);
  const card = page.locator(`[data-take-id="${result.take_ids[0]}"]`);
  await expect(card.getByRole('alert')).toContainText('INTERNAL');
  await expect(card.getByRole('alert')).toContainText(result.generation_job_id);
  await expect.poll(async () => (await takes(request, result.song_id))[0].status).toBe('failed');
  const failed = await takes(request, result.song_id);
  expect(failed).toHaveLength(1);
  expect(failed[0]).toMatchObject({id: result.take_ids[0], status: 'failed'});
  expect(Object.keys(failed[0].assets ?? {})).toHaveLength(0);
});

test('E2E-05 cancela desde tarjeta y confirma terminal real', async ({page, request}) => {
  await composer(page, `cancelar ${Date.now()}`);
  const result = await generate(page);
  const card = page.locator(`[data-take-id="${result.take_ids[0]}"]`);
  await card.getByRole('button', {name: 'Cancelar', exact: true}).click();
  await expect(card).toHaveClass(/generation-cancelled/);
  await expect.poll(async () => (await takes(request, result.song_id))[0].status).toBe('cancelled');
  await expect(card.getByRole('button', {name: 'Cancelar', exact: true})).toHaveCount(0);
});

test('E2E-04 VRAM_EXCEEDED imposible en CPU terminaliza take y libera toda la cola', async ({page, request}, testInfo) => {
  const modelId = await verifiedModel(request);
  await composer(page, `vram imposible ${Date.now()} @mock:fail=VRAM_EXCEEDED @mock:retryable`);
  const submitted = page.waitForRequest(request => request.url() === `${apiOrigin}/api/generations` && request.method() === 'POST');
  const result = await generate(page);
  expect((await submitted).postDataJSON().model_id).toBe(modelId);
  const card = page.locator(`[data-take-id="${result.take_ids[0]}"]`);
  await expect(card).toHaveClass(/generation-failed/);
  await expect(card.getByRole('alert')).toContainText('VRAM_EXCEEDED');
  await expect(card.getByRole('alert')).toContainText(result.generation_job_id);
  await expect.poll(async () => (await takes(request, result.song_id))[0].status).toBe('failed');
  const failed = await takes(request, result.song_id);
  expect(failed).toHaveLength(1);
  expect(failed[0]).toMatchObject({id: result.take_ids[0], status: 'failed'});
  expect(Object.keys(failed[0].assets ?? {})).toHaveLength(0);
  let queue: unknown;
  await expect.poll(async () => {
    const response = await api(request, '/api/system');
    expect(response.ok()).toBeTruthy();
    queue = (await response.json()).queue;
    return queue;
  }, {timeout: 60_000}).toEqual({queued: false, blocked: false, running: false});
  await testInfo.attach('impossible-vram-terminal', {body: JSON.stringify({result, takes: failed, queue}), contentType: 'application/json'});
});
