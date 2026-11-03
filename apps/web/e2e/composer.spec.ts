import {API, expect, fillComposer, test} from './fixtures';

test('E2E-02 crea una canción con letra y declaración de autoría', async ({page}) => {
  let generationBody: Record<string, unknown> | undefined;
  await page.route('http://127.0.0.1:8000/api/session/bootstrap', route => route.fulfill({json: {expires_in_s: 3600, session_token: 'e2e-session'}}));
  await page.route('http://127.0.0.1:8000/api/generations/estimate', route => route.fulfill({json: {eta_s: 12, vram_mb: 7000}}));
  await page.route('http://127.0.0.1:8000/api/generations', async route => {
    generationBody = JSON.parse(route.request().postData() ?? '{}') as Record<string, unknown>;
    await route.fulfill({status: 202, json: {song_id: '01K70000000000000000000031', generation_job_id: '01K70000000000000000000032', post_job_id: '01K70000000000000000000033', take_ids: [], beat_job_ids: []}});
  });
  await page.goto('/create');
  await expect(page.getByLabel('Duración (s)')).toHaveValue('');
  await expect(page.getByLabel('Duración (s)')).toHaveAttribute('placeholder', '30');
  await page.getByRole('textbox', {name: 'Letra'}).fill('[Verse]\nUna letra propia');
  await page.getByRole('textbox', {name: 'Estilo musical'}).fill('hip hop luminoso');
  await page.locator('input[name="declaration"][value="own"]').check();
  await page.getByLabel('Variantes').selectOption('2');
  await page.getByRole('button', {name: 'Generar'}).click();
  await expect(page.getByRole('status')).toContainText(/Generaci.n encolada/, {timeout: 15_000});
  expect(generationBody).toMatchObject({task: 'music.song', lyrics: '[Verse]\nUna letra propia', lyrics_declaration: 'own', n_outputs: 2});
  expect(generationBody?.params).not.toHaveProperty('duration_s');
});

test('CPU-UI Crear exige autoría con explicación accesible', async ({page}) => {
  await page.goto('/create');
  await page.getByRole('textbox', {name: 'Letra'}).fill('[Verse]\nPropia');
  await page.getByRole('textbox', {name: 'Estilo musical'}).fill('pop');
  const submit = page.getByRole('button', {name: 'Generar'});
  await expect(submit).toBeDisabled();
  await expect(submit).toHaveAccessibleDescription('Necesaria para generar una canción con letra.');
});

test('CPU-UI Crear sin sistema disponible explica bloqueo y no genera', async ({page}) => {
  let submissions = 0;
  await page.route(`${API}/api/system`, route => route.abort('failed'));
  await page.route(`${API}/api/generations`, route => { submissions++; return route.abort(); });
  await page.goto('/create');
  await fillComposer(page);
  await expect(page.getByRole('button', {name: 'Generar'})).toBeDisabled();
  await expect(page.getByText(/sistema no está disponible/i)).toBeVisible();
  expect(submissions).toBe(0);
});

test('CPU-UI dos variantes requieren estimación válida que cabe en VRAM sintética', async ({page}) => {
  await page.route(`${API}/api/generations/estimate`, route => route.fulfill({json: {eta_s: 8, vram_mb: 11000}}));
  await page.goto('/create');
  await fillComposer(page);
  await expect(page.getByLabel('Variantes')).toHaveValue('1');
  await expect(page.getByLabel('Variantes').locator('option')).toHaveCount(1);
  await page.route(`${API}/api/generations/estimate`, route => route.fulfill({json: {eta_s: 8, vram_mb: 7000}}));
  await page.getByRole('textbox', {name: 'Estilo musical'}).fill('jazz');
  await expect(page.getByLabel('Variantes').locator('option')).toHaveCount(2);
  await page.getByLabel('Variantes').selectOption('2');
});

test('E2E-03 mantiene la letra al cambiar a instrumental', async ({page}) => {
  await page.goto('/create');
  const lyrics = page.getByRole('textbox', {name: 'Letra'});
  await lyrics.fill('Borrador que no se borra');
  await page.getByRole('textbox', {name: 'Estilo musical'}).fill('hip hop luminoso');
  await page.getByLabel('Generar instrumental (sin usar la letra)').check();
  await expect(lyrics).toHaveValue('Borrador que no se borra');
  await expect(page.getByRole('button', {name: 'Generar'})).toBeEnabled();
});

test('E2E-03 bloquea una etiqueta de letra desconocida', async ({page}) => {
  await page.goto('/create');
  await page.getByRole('textbox', {name: 'Letra'}).fill('[chrous]\nUna letra');
  await page.getByRole('textbox', {name: 'Estilo musical'}).fill('hip hop luminoso');
  await expect(page.locator('mark.invalid-tag')).toContainText('[chrous]');
  await expect(page.getByRole('button', {name: 'Generar'})).toBeDisabled();
});

test('E2E-11 permite instrumental sin declaraciÃ³n y vuelve a exigirla', async ({page}) => {
  let generationBody: Record<string, unknown> | undefined;
  await page.route('http://127.0.0.1:8000/api/session/bootstrap', route => route.fulfill({json: {expires_in_s: 3600, session_token: 'e2e-session'}}));
  await page.route('http://127.0.0.1:8000/api/generations/estimate', route => route.fulfill({json: {eta_s: 8, vram_mb: 7000}}));
  await page.route('http://127.0.0.1:8000/api/generations', async route => {
    generationBody = JSON.parse(route.request().postData() ?? '{}') as Record<string, unknown>;
    await route.fulfill({status: 202, json: {song_id: '01K70000000000000000000031', generation_job_id: '01K70000000000000000000032', post_job_id: '01K70000000000000000000033', take_ids: [], beat_job_ids: []}});
  });
  await page.goto('/create');
  await page.getByRole('textbox', {name: 'Letra'}).fill('Borrador que se conserva');
  await page.getByRole('textbox', {name: 'Estilo musical'}).fill('hip hop luminoso');
  await page.getByLabel('Generar instrumental (sin usar la letra)').check();
  await page.getByRole('button', {name: 'Generar'}).click();
  await expect(page.getByRole('status')).toContainText(/Generaci.n encolada/, {timeout: 15_000});
  expect(generationBody).toMatchObject({task: 'music.instrumental'});
  expect(generationBody).not.toHaveProperty('lyrics');
  await page.getByLabel('Generar instrumental (sin usar la letra)').uncheck();
  await expect(page.getByRole('textbox', {name: 'Letra'})).toHaveValue('Borrador que se conserva');
  await expect(page.getByRole('button', {name: 'Generar'})).toBeDisabled();
});
