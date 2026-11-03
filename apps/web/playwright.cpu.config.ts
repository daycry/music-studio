import {defineConfig} from '@playwright/test';
import base from './playwright.config';

// UI Windows con API interceptada; API smoke usa el HTTP aislado existente.
// Nunca arranca servicios ni ejecuta recovery/Docker.
export default defineConfig(base, {
  testIgnore: ['**/recovery.spec.ts', '**/analysis.spec.ts', '**/collections.spec.ts'],
  workers: 1,
  outputDir: '../../.cache/playwright-ui/results',
  reporter: [['list'], ['json', {outputFile: '../../.cache/playwright-ui/results.json'}], ['html', {outputFolder: '../../.cache/playwright-ui/report', open: 'never'}]],
  use: {launchOptions: {args: ['--disable-gpu']}, screenshot: 'only-on-failure'},
});
