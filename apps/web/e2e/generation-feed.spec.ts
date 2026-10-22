import {expect, test, type Page} from '@playwright/test';

async function stubGeneration(page: Page) {
  await page.route('http://127.0.0.1:8000/api/session/bootstrap', route => route.fulfill({json: {session_token: 'e2e-session'}}));
  await page.route('http://127.0.0.1:8000/api/system', route => route.fulfill({json: {gpu: null, queue: {queued: false, blocked: false, running: false}, engines: []}}));
  await page.route('http://127.0.0.1:8000/api/generations/estimate', route => route.fulfill({json: {eta_s: 8}}));
  await page.route('http://127.0.0.1:8000/api/generations', route => route.fulfill({status: 202, json: {song_id: 'song-e2e', generation_job_id: 'job-e2e', post_job_id: 'post-e2e', take_ids: [], beat_job_ids: []}}));
}

async function submit(page: Page) {
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

test('E2E-05 cancela una tarjeta y conserva el job visible', async ({page}) => {
  await stubGeneration(page);
  await page.route('http://127.0.0.1:8000/api/jobs/job-e2e/cancel', route => route.fulfill({json: {job_id: 'job-e2e', status: 'cancelled'}}));
  await page.goto('/create');
  await submit(page);
  await page.getByRole('button', {name: 'Cancelar'}).click();
  await expect(page.getByText('Cancelada')).toBeVisible();
  await expect(page.getByText('job-e2e')).toBeVisible();
});
