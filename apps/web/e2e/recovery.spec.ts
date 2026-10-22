import {spawn} from 'node:child_process';
import {existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {expect, test} from '@playwright/test';

test('E2E-06 recupera un job después de reiniciar el server', async ({page}) => {
  test.skip(process.env.E2E_RECOVERY !== '1', 'requiere stack levantado con MOCK_STAGE_DELAY_MS=5000');
  await page.route('http://127.0.0.1:8000/api/generations', async route => {
    const request = route.request();
    const body = JSON.parse(request.postData() ?? '{}') as Record<string, unknown>;
    await route.continue({postData: JSON.stringify({...body, model_id: 'mock'})});
  });
  await page.goto('/create');
  await page.getByRole('textbox', {name: 'Letra'}).fill('[Verse]\nUna letra propia');
  await page.getByRole('textbox', {name: 'Estilo musical'}).fill('hip hop luminoso');
  await page.locator('input[name="declaration"][value="own"]').check();
  await page.getByRole('button', {name: 'Generar'}).click();
  const card = page.locator('.generation-card').first();
  await expect(card).toBeVisible();
  await page.waitForTimeout(250);
  const packageRoot = resolve(process.cwd());
  const repoRoot = existsSync(resolve(packageRoot, 'scripts/e2e_stack.py'))
    ? packageRoot
    : resolve(packageRoot, '..', '..');
  const python = process.platform === 'win32'
    ? resolve(repoRoot, '.venv', 'Scripts', 'python.exe')
    : resolve(repoRoot, '.venv', 'bin', 'python');
  if (!existsSync(python)) {
    throw new Error(`No existe el intérprete gestionado requerido: ${python}`);
  }
  const restart = spawn(python, ['scripts/e2e_stack.py', 'restart-server'], {cwd: repoRoot, stdio: 'ignore', detached: true});
  restart.unref();
  await page.waitForTimeout(4_000);
  await page.waitForTimeout(12_000);
  await page.reload();
  await expect(card).toContainText('Lista', {timeout: 30_000});
});
