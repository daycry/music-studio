import {API, expect, fillComposer, generation, ids, test} from './fixtures';
import type {Page} from '@playwright/test';

async function stubGeneration(page: Page) {
  await page.route('http://127.0.0.1:8000/api/session/bootstrap', route => route.fulfill({json: {expires_in_s: 3600, session_token: 'e2e-session'}}));
  await page.route('http://127.0.0.1:8000/api/generations/estimate', route => route.fulfill({json: {eta_s: 8, vram_mb: 7000}}));
  await page.route('http://127.0.0.1:8000/api/generations', route => route.fulfill({status: 202, json: {song_id: '01K70000000000000000000031', generation_job_id: '01K70000000000000000000032', post_job_id: '01K70000000000000000000033', take_ids: [], beat_job_ids: []}}));
}

async function submit(page: Page) {
  // El HTML SSR permite fill antes de que React maneje los cambios. Avanzado
  // aparece sólo tras cargar la capacidad del sistema desde el efecto cliente.
  await expect(page.locator('details.advanced > summary')).toBeVisible();
  await page.getByRole('textbox', {name: 'Letra'}).fill('[Verse]\nUna letra propia');
  await page.getByRole('textbox', {name: 'Estilo musical'}).fill('hip hop luminoso');
  await page.locator('input[name="declaration"][value="own"]').check();
  await page.getByRole('button', {name: 'Generar'}).click();
}

test('E2E-04 muestra la tarjeta y la visualizaciÃ³n de 96 columnas', async ({page}) => {
  await stubGeneration(page);
  await page.goto('/create');
  await submit(page);
  await expect(page.getByRole('region', {name: 'Generaciones en curso'})).toBeVisible();
  await expect(page.getByRole('progressbar')).toHaveAttribute('data-columns', '96');
  await expect(page.locator('.generation-card').getByText('En cola').first()).toBeVisible();
});

test('CPU-UI feed distingue generación completada, post y take ready', async ({page}, testInfo) => {
  let ready = false;
  let sequence = 0;
  let deliver: ((event: {type: string; data: Record<string, unknown>}) => Promise<void>) | undefined;
  await page.route(`${API}/api/songs/${ids.song}/takes`, route => route.fulfill({json: {items: [{id: ids.take, status: ready ? 'ready' : 'processing'}]}}));
  await page.route(`${API}/api/takes/${ids.take}/peaks`, route => route.fulfill({json: {data: [[[0.1, 0.6, 0.3]]]}}));
  await page.route(`${API}/api/events**`, async route => {
    await new Promise<void>(resolve => {
      deliver = async event => {
        sequence++;
        const body = {id: sequence, type: event.type, ts: '2026-11-03T00:00:00.000Z', data: event.data};
        await route.fulfill({contentType: 'text/event-stream', body: `id: ${'a'.repeat(32)}:${sequence}\nevent: ${event.type}\ndata: ${JSON.stringify(body)}\n\n`});
        deliver = undefined;
        resolve();
      };
    });
  });
  async function send(type: string, data: Record<string, unknown>) {
    await expect.poll(() => Boolean(deliver)).toBe(true);
    await deliver!({type, data});
  }
  await page.goto('/create');
  await fillComposer(page);
  await page.getByRole('button', {name: 'Generar'}).click();
  const card = page.locator('.generation-card').first();
  await expect(card).toContainText('En cola');
  await send('job.stage', {job_id: ids.job, status: 'running', stage: 'generating'});
  await expect(card.locator('[data-stage="generating"]')).toHaveClass('current');
  await send('job.done', {job_id: ids.job, status: 'succeeded'});
  await expect(card.locator('[data-stage="post"]')).toHaveClass('current');
  await expect(card.locator('header')).not.toContainText('Lista');
  ready = true;
  await send('entity.updated', {type: 'take', id: ids.take});
  await expect(card.locator('header')).toContainText('Lista');
  await expect(card.locator('.generative-viz')).toBeVisible();
  await page.screenshot({path: testInfo.outputPath('feed-ready-sintetico.png'), fullPage: true});
});

test('CPU-UI feed conserva error de acción al cancelar', async ({page}) => {
  await page.route(`${API}/api/jobs/${ids.job}/cancel`, route => route.fulfill({status: 409, json: {code: 'JOB_CONFLICT', message: 'No se puede cancelar'}}));
  await page.goto('/create');
  await fillComposer(page);
  await page.getByRole('button', {name: 'Generar'}).click();
  await page.getByRole('button', {name: 'Cancelar'}).click();
  await expect(page.locator('.generation-card').getByRole('alert')).toContainText('JOB_CONFLICT');
});

test('CPU-UI feed reintenta sólo por acción explícita y conserva el take', async ({page}) => {
  await page.addInitScript(({ids}) => localStorage.setItem('music-studio:generation-feed', JSON.stringify([{song_id: ids.song, job_id: ids.job, take_id: ids.take, status: 'failed', error_code: 'INTERNAL', stage: null, progress: null}])), {ids});
  let retries = 0;
  const replacement = '01K70000000000000000000035';
  await page.route(`${API}/api/jobs/${ids.job}/retry`, route => {
    retries++;
    return route.fulfill({status: 202, json: {...generation, generation_job_id: replacement}});
  });
  await page.goto('/create');
  const card = page.locator('.generation-card');
  await expect(card.getByRole('alert')).toContainText('INTERNAL');
  await expect(card.getByRole('alert')).toContainText(ids.job);
  expect(retries).toBe(0);
  await card.getByRole('button', {name: 'Reintentar'}).click();
  await expect(card).toContainText('En cola');
  await expect(card).toHaveAttribute('data-take-id', ids.take);
  expect(retries).toBe(1);
});

test('E2E-05 cancela una tarjeta y conserva el job visible', async ({page}) => {
  await stubGeneration(page);
  let cancelled!: () => void;
  const terminal = new Promise<void>(resolve => { cancelled = resolve; });
  await page.route(`${API}/api/events**`, async route => {
    await terminal;
    const event = {id: 1, type: 'job.cancelled', ts: '2026-11-03T00:00:00.000Z', data: {job_id: ids.job, status: 'cancelled'}};
    await route.fulfill({contentType: 'text/event-stream', body: `id: ${'a'.repeat(32)}:1\nevent: job.cancelled\ndata: ${JSON.stringify(event)}\n\n`});
  });
  await page.route(`${API}/api/jobs/${ids.job}/cancel`, async route => {
    await route.fulfill({json: {job_id: ids.job, cancel_requested: true}});
    cancelled();
  });
  await page.goto('/create');
  await submit(page);
  await page.getByRole('button', {name: 'Cancelar'}).click();
  await expect(page.getByText('Cancelada')).toBeVisible();
  await expect(page.locator('.generation-card')).toHaveCount(1);
});
