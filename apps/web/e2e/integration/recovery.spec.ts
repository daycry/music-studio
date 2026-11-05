import {spawn} from 'node:child_process';
import {resolve} from 'node:path';
import {expect, test, type TestInfo} from '@playwright/test';
import {apiOrigin, composer, generate, ready, takes, observeBrowserSessions, revokeSessions} from './helpers';

const repoRoot = resolve(import.meta.dirname, '../../../..');
async function stack(command: 'kill-server' | 'start-server', testInfo: TestInfo) {
  const python = resolve(repoRoot, process.platform === 'win32' ? '.venv/Scripts/python.exe' : '.venv/bin/python');
  const output: string[] = [];
  let exitCode: number | null = null;
  try {
    await new Promise<void>((resolvePromise, reject) => {
      // El helper resuelve E2E_PROJECT_NAME/E2E_COMPOSE_FILE/E2E_ENV_FILE/STUDIO_DATA_ROOT.
      const child = spawn(python, ['scripts/e2e_stack.py', command], {cwd: repoRoot, env: process.env, stdio: ['ignore', 'pipe', 'pipe'], windowsHide: true});
      child.stdout.on('data', bytes => output.push(`stdout: ${String(bytes)}`));
      child.stderr.on('data', bytes => output.push(`stderr: ${String(bytes)}`));
      const timeout = setTimeout(() => {child.kill(); reject(new Error(`${command}: excedió 120 s`));}, 120_000);
      child.once('error', error => {clearTimeout(timeout); reject(error);});
      child.once('close', code => {exitCode = code; clearTimeout(timeout); if (code === 0) resolvePromise(); else reject(new Error(`${command}: exit ${code}`));});
    });
  } finally {
    await testInfo.attach(`stack-${command}`, {body: JSON.stringify({command, exitCode, output}), contentType: 'application/json'});
  }
}

test.beforeEach(async ({page}) => {observeBrowserSessions(page);});
test.afterEach(async ({page, request}, testInfo) => {await revokeSessions(page, request, testInfo);});

test('E2E-06 conserva identidad, semilla y SSE tras caída real del servidor', async ({page, request}, testInfo) => {
  test.skip(process.env.E2E_RECOVERY !== '1', 'Requiere coordinación del stack dedicado y MOCK_STAGE_DELAY_MS=5000');
  test.setTimeout(240_000);
  await composer(page, `recuperacion ${Date.now()}`);
  const result = await generate(page);
  const card = page.locator(`[data-take-id="${result.take_ids[0]}"]`);
  await expect(card.locator('[data-stage="generating"].current')).toBeVisible();
  const original = (await takes(request, result.song_id)).find(take => take.id === result.take_ids[0])!;
  expect(original.status).not.toBe('ready');
  await testInfo.attach('before-recovery', {body: JSON.stringify({result, take: original}), contentType: 'application/json'});
  await testInfo.attach('recovery-before-crash', {body: await page.screenshot({fullPage: true}), contentType: 'image/png'});
  let started = false;
  try {
    await stack('kill-server', testInfo);
    // start-server es síncrono: su salida confirma Docker y /health, sin sleeps.
    await stack('start-server', testInfo);
    started = true;
  } finally {
    // Incluso tras un fallo de la prueba, restaura exclusivamente el server de pruebas.
    if (!started) await stack('start-server', testInfo);
  }
  const reconnected = page.waitForResponse(response => response.url().startsWith(`${apiOrigin}/api/events?`) && response.status() === 200);
  await page.reload();
  expect((await reconnected).headers()['content-type']).toContain('text/event-stream');
  await ready(page, request, result);
  const recovered = (await takes(request, result.song_id)).find(take => take.id === original.id)!;
  expect(recovered.seed).toBe(original.seed);
  expect(recovered.song_id).toBe(original.song_id);
  await expect(page.locator('.generation-card')).toHaveCount(1);
  await testInfo.attach('recovery-ready', {body: await page.screenshot({fullPage: true}), contentType: 'image/png'});
  await testInfo.attach('after-recovery', {body: JSON.stringify(recovered), contentType: 'application/json'});
});
