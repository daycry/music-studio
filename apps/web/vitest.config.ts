import { resolve } from 'node:path';
import { defineConfig } from 'vitest/config';
const runtimeRoot = resolve(process.env.STUDIO_WEB_TEST_ROOT ?? '../../.cache/web-runtime');
export default defineConfig({
  cacheDir: resolve(runtimeRoot, 'vitest-cache'),
  test: {
    environment: 'node',
    include: ['app/**/*.test.tsx', 'components/**/*.test.tsx', 'lib/**/*.test.ts'],
    exclude: ['e2e/**', 'node_modules/**', '.next/**'],
    coverage: {
      provider: 'v8',
      include: ['lib/lyrics.ts', 'lib/api.ts', 'lib/events.ts', 'lib/theme.ts', 'components/StudioShell.tsx', 'components/ThemeProvider.tsx', 'components/PlayerDock.tsx', 'app/layout.tsx', 'app/page.tsx', 'app/create/page.tsx', 'app/songs/page.tsx', 'app/system/page.tsx', 'i18n/request.ts'],
      exclude: [],
      reportsDirectory: resolve(runtimeRoot, 'coverage'),
      reporter: ['json', 'text'],
      thresholds: { perFile: true, lines: 80, statements: 80, functions: 80, branches: 80 },
    },
  },
});
