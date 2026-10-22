import {defineConfig, devices} from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  // E2E-06 reinicia el server compartido; serializar el modo recovery evita
  // que otra prueba deje una custodia CPU abierta durante ese reinicio.
  fullyParallel: process.env.E2E_RECOVERY !== '1',
  workers: process.env.E2E_RECOVERY === '1' ? 1 : undefined,
  reporter: [['list']],
  use: {
    baseURL: 'http://127.0.0.1:3000',
    trace: 'retain-on-failure',
    ...devices['Desktop Chrome'],
  },
});
