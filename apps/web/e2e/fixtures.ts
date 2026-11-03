import {test as base, expect, type Page} from '@playwright/test';

export const API = 'http://127.0.0.1:8000';
export const ids = {song: '01K70000000000000000000031', job: '01K70000000000000000000032', post: '01K70000000000000000000033', take: '01K70000000000000000000034'};
export const generation = {song_id: ids.song, generation_job_id: ids.job, post_job_id: ids.post, take_ids: [ids.take], beat_job_ids: []};
// PCM silencioso reproducible por Chromium; no se afirma calidad musical.
export function silentWav() {
  const samples = 16000;
  const wav = Buffer.alloc(44 + samples * 2);
  wav.write('RIFF', 0); wav.writeUInt32LE(wav.length - 8, 4); wav.write('WAVEfmt ', 8);
  wav.writeUInt32LE(16, 16); wav.writeUInt16LE(1, 20); wav.writeUInt16LE(1, 22);
  wav.writeUInt32LE(8000, 24); wav.writeUInt32LE(16000, 28); wav.writeUInt16LE(2, 32); wav.writeUInt16LE(16, 34);
  wav.write('data', 36); wav.writeUInt32LE(samples * 2, 40);
  return wav;
}
export const systemFixture = {
  disk: {free_bytes: 1000000000}, ram: {total_mb: 32000, available_mb: 16000},
  // Telemetría SINTÉTICA: no se consulta ni usa una GPU en esta suite.
  gpu: {name: 'MOCK — sin GPU', total_mb: 12000, free_mb: 10000, cap_mb: 9000},
  queue: {queued: false, blocked: false, running: false}, engines: [],
  models: [{id: 'mock', provider: {type: 'local'}, commercial_use: true, license: 'MIT', hash_verified: true,
    tasks: Object.fromEntries(['music.song', 'music.instrumental'].map(task => [task, {verified: true, features: {}, params_schema: {properties: {duration_s: {type: 'number', minimum: 10, maximum: 600}, inference_steps: {type: 'integer', minimum: 1, maximum: 8}, vocal_language: {type: 'string'}}}}]))}],
};

export async function fillComposer(page: Page) {
  await page.getByRole('textbox', {name: 'Letra'}).fill('[Verse]\nUna letra propia');
  await page.getByRole('textbox', {name: 'Estilo musical'}).fill('hip hop luminoso');
  await page.locator('input[name="declaration"][value="own"]').check();
}

export const test = base.extend<{isolatedApi: void}>({
  isolatedApi: [async ({page}, use) => {
    // Todo endpoint no declarado queda cerrado: las pruebas UI no escriben en el server.
    await page.route(`${API}/**`, route => route.fulfill({status: 404, json: {code: 'UI_FIXTURE_NOT_DECLARED'}}));
    await page.route(`${API}/api/session/bootstrap`, route => route.fulfill({json: {expires_in_s: 3600, session_token: 'synthetic-ui-session'}}));
    await page.route(`${API}/health`, route => route.fulfill({json: {process: 'server', status: 'running'}}));
    await page.route(`${API}/api/system`, route => route.fulfill({json: systemFixture}));
    await page.route(`${API}/api/system/unload`, route => route.fulfill({json: {freed_mb: 0}}));
    await page.route(`${API}/api/generations/estimate`, route => route.fulfill({json: {eta_s: 8, vram_mb: 7000}}));
    await page.route(`${API}/api/generations`, route => route.fulfill({status: 202, json: generation}));
    await page.route(`${API}/api/events**`, route => route.fulfill({status: 503, json: {code: 'UI_FIXTURE_NO_STREAM'}}));
    await use();
  }, {auto: true}],
});
export {expect};
