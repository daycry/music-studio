import {existsSync, realpathSync, statSync} from 'node:fs';
import {resolve, join, relative, isAbsolute, dirname} from 'node:path';
import {defineConfig, devices} from '@playwright/test';

// Servicios externos ya levantados por el orquestador sobre datos privados.
// Esta configuración sólo descubre pruebas con HTTP/SSE/audio reales.
const repoRoot = realpathSync(resolve(import.meta.dirname, '../..'));
function required(name: string) {
  const value = process.env[name];
  if (!value?.trim()) throw new Error(`E2E_SCOPE_REQUIRED: ${name}; configura explícitamente el stack de pruebas antes de ejecutar o descubrir la suite`);
  return value;
}
for (const name of ['E2E_PROJECT_NAME', 'E2E_COMPOSE_FILE', 'E2E_ENV_FILE', 'STUDIO_DATA_ROOT', 'E2E_ARTIFACT_ROOT', 'E2E_API_ORIGIN', 'E2E_WEB_ORIGIN']) required(name);
if (!/^music-studio-e2e(?:-[a-z0-9][a-z0-9_-]*)?$/.test(required('E2E_PROJECT_NAME'))) throw new Error('E2E_PROJECT_REQUIRED: usa un proyecto Compose exclusivo music-studio-e2e');
const within = (base: string, target: string) => {const path = relative(base, target); return path !== '..' && !path.startsWith(`..${process.platform === 'win32' ? '\\' : '/'}`) && !isAbsolute(path);};
function privatePath(name: string, file = false) {
  const target = resolve(repoRoot, required(name));
  const cacheRoot = realpathSync(join(repoRoot, '.cache'));
  let ancestor = target;
  while (!existsSync(ancestor) && dirname(ancestor) !== ancestor) ancestor = dirname(ancestor);
  const canonical = resolve(realpathSync(ancestor), relative(ancestor, target));
  if (!within(cacheRoot, target) || !within(cacheRoot, canonical)) throw new Error(`E2E_PRIVATE_PATH_REQUIRED: ${name} debe estar dentro de .cache del repositorio`);
  if (file && (!existsSync(target) || !statSync(target).isFile())) throw new Error(`E2E_SCOPE_FILE_REQUIRED: ${name}`);
  if (!file && existsSync(target) && !statSync(target).isDirectory()) throw new Error(`E2E_SCOPE_DIRECTORY_REQUIRED: ${name}`);
  return target;
}
privatePath('E2E_COMPOSE_FILE', true);
privatePath('E2E_ENV_FILE', true);
privatePath('STUDIO_DATA_ROOT');
const artifactRoot = privatePath('E2E_ARTIFACT_ROOT');
function loopbackOrigin(name: string) {
  const value = required(name);
  const url = new URL(value);
  if (url.protocol !== 'http:' || !['127.0.0.1', 'localhost', '[::1]'].includes(url.hostname) || url.username || url.password || url.pathname !== '/' || url.search || url.hash) throw new Error(`E2E_LOOPBACK_ORIGIN_REQUIRED: ${name}`);
  return url.origin;
}
loopbackOrigin('E2E_API_ORIGIN');
const webOrigin = loopbackOrigin('E2E_WEB_ORIGIN');

export default defineConfig({
  testDir: './e2e/integration',
  testMatch: '**/*.spec.ts',
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 120_000,
  expect: {timeout: 30_000},
  outputDir: join(artifactRoot, 'results'),
  reporter: [['list'], ['json', {outputFile: join(artifactRoot, 'results.json')}], ['html', {outputFolder: join(artifactRoot, 'report'), open: 'never'}]],
  use: {
    ...devices['Desktop Chrome'],
    baseURL: webOrigin,
    launchOptions: {args: ['--disable-gpu']},
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
});
