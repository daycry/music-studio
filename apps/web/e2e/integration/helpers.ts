import {setTimeout as pause} from 'node:timers/promises';
import {expect, type APIRequestContext, type Page, type Response, type TestInfo} from '@playwright/test';
import type {GenerationResponse, Take, Song, SystemInfo} from '../../lib/api';
import {EventParser, type SSEFrame} from '../../lib/event-parser';
import {EventReducer, type JobState, type ServerEvent} from '../../lib/event-reducer';

export const apiOrigin = process.env.E2E_API_ORIGIN ?? 'http://127.0.0.1:8000';
const webOrigin = process.env.E2E_WEB_ORIGIN ?? 'http://127.0.0.1:3000';
const credentials = new WeakMap<APIRequestContext, Promise<string>>();
const browserCredentials = new WeakMap<Page, {tokens: Set<string>; pending: Set<Promise<void>>; errors: string[]}>();

async function bootstrap(request: APIRequestContext): Promise<string> {
  const response = await request.post(`${apiOrigin}/api/session/bootstrap`, {headers: {Origin: webOrigin, 'X-Studio-Session-Bootstrap': '1'}});
  const dto = await response.json();
  expect(response.status(), `bootstrap HTTP ${response.status()} code=${dto.code ?? 'unknown'}`).toBe(200);
  expect(typeof dto.session_token).toBe('string');
  return dto.session_token;
}
function credential(request: APIRequestContext) {
  let pending = credentials.get(request);
  if (!pending) {
    pending = bootstrap(request).catch(error => {credentials.delete(request); throw error;});
    credentials.set(request, pending);
  }
  return pending;
}
export async function api(request: APIRequestContext, path: string, options: {method?: string; data?: unknown; headers?: Record<string, string>} = {}) {
  const first = credential(request);
  const send = async (token: string) => request.fetch(`${apiOrigin}${path}`, {...options, headers: {Origin: webOrigin, ...options.headers, 'X-Studio-Session-Token': token}});
  const response = await send(await first);
  if (response.status() !== 401) return response;
  // Una sola renovación; los 401 concurrentes comparten la misma promesa.
  if (credentials.get(request) === first) credentials.delete(request);
  return send(await credential(request));
}
export function observeBrowserSessions(page: Page) {
  const state = {tokens: new Set<string>(), pending: new Set<Promise<void>>(), errors: [] as string[]};
  browserCredentials.set(page, state);
  page.on('response', (response: Response) => {
    if (response.url() !== `${apiOrigin}/api/session/bootstrap`) return;
    const pending = (async () => {
      try {
        const dto = await response.json();
        if (response.ok() && typeof dto.session_token === 'string') state.tokens.add(dto.session_token);
        else state.errors.push(`bootstrap HTTP ${response.status()} code=${dto.code ?? 'unknown'}`);
      } catch {state.errors.push(`bootstrap HTTP ${response.status()}: respuesta no legible`);}
    })();
    state.pending.add(pending);
    void pending.finally(() => state.pending.delete(pending));
  });
}
export async function revokeSessions(page: Page, request: APIRequestContext, testInfo: TestInfo) {
  const state = browserCredentials.get(page);
  // Detiene las suscripciones antes de revocar; no intercepta tráfico del navegador.
  if (!page.isClosed()) await page.goto('about:blank');
  if (state) await Promise.all([...state.pending]);
  const tokens = new Set(state?.tokens);
  const pending = credentials.get(request);
  credentials.delete(request);
  if (pending) tokens.add(await pending);
  const statuses: number[] = [];
  for (const token of tokens) {
    const response = await request.delete(`${apiOrigin}/api/session`, {headers: {Origin: webOrigin, 'X-Studio-Session-Token': token}});
    statuses.push(response.status());
  }
  await testInfo.attach('session-cleanup', {body: JSON.stringify({credentials: tokens.size, statuses, bootstrapErrors: state?.errors ?? []}), contentType: 'application/json'});
  for (const status of statuses) expect([204, 401], 'Revocación real o credencial ya revocada/invalidada por reinicio').toContain(status);
}
export async function takes(request: APIRequestContext, songId: string): Promise<Take[]> {
  const response = await api(request, `/api/songs/${songId}/takes`);
  expect(response.ok()).toBeTruthy();
  return (await response.json()).items;
}
export async function song(request: APIRequestContext, songId: string): Promise<Song> {
  const response = await api(request, `/api/songs/${songId}`);
  expect(response.ok()).toBeTruthy();
  return response.json();
}
export async function verifiedModel(request: APIRequestContext) {
  const response = await api(request, '/api/system');
  expect(response.ok()).toBeTruthy();
  const info: SystemInfo = await response.json();
  const model = info.models.find(item => item.provider?.type === 'local' && item.tasks?.['music.song']?.verified && item.tasks?.['music.song']?.device === 'cpu');
  expect(model, 'El stack de integración debe anunciar una tarea CPU verificada').toBeTruthy();
  return model!.id;
}
export async function openComposer(page: Page) {
  const system = page.waitForResponse(response => response.url() === `${apiOrigin}/api/system`, {timeout: 30_000});
  const deniedBootstrap = page.waitForResponse(response => response.url() === `${apiOrigin}/api/session/bootstrap` && !response.ok(), {timeout: 30_000}).then(async response => {
    const dto = await response.json();
    throw new Error(`bootstrap HTTP ${response.status()} code=${dto.code ?? 'unknown'}`);
  });
  // Registra ambos handlers antes de navegar; un SESSION_LIMIT falla con su código.
  const loaded = Promise.race([system, deniedBootstrap]);
  void loaded.catch(() => {});
  await page.goto('/create');
  try {
    const response = await loaded;
    expect(response.status(), `system HTTP ${response.status()}`).toBe(200);
    const info: SystemInfo = await response.json();
    expect(info.models.some(model => model.tasks?.['music.song']?.verified && model.tasks['music.song'].device === 'cpu')).toBe(true);
    await expect(page.locator('.advanced'), 'Capacidades reales hidratadas en el compositor').toBeVisible();
  } catch (error) {
    const failures = browserCredentials.get(page)?.errors;
    if (failures?.length) throw new Error(failures.join('; '));
    throw error;
  }
}
export async function composer(page: Page, style: string, instrumental = false) {
  await openComposer(page);
  await page.getByLabel('Estilo musical', {exact: true}).fill(style);
  await page.getByLabel('Letra', {exact: true}).fill('[Verse]\nHorizonte de integración\n[Chorus]\nUna canción local');
  if (instrumental) await page.getByLabel('Generar instrumental (sin usar la letra)').check();
  else await page.getByLabel('Es mía', {exact: true}).check();
  await page.getByText('Avanzado', {exact: true}).click();
  await page.getByLabel('Duración (s)', {exact: true}).fill('10');
  await page.getByLabel('Semilla', {exact: true}).fill('1701');
}
export async function generate(page: Page): Promise<GenerationResponse> {
  const response = page.waitForResponse(response => response.url() === `${apiOrigin}/api/generations` && response.request().method() === 'POST');
  await page.getByRole('button', {name: 'Generar', exact: true}).click();
  const result = await response;
  expect(result.status()).toBe(202);
  return result.json();
}
export async function ready(page: Page, request: APIRequestContext, result: GenerationResponse) {
  await expect.poll(async () => (await takes(request, result.song_id)).filter(take => result.take_ids.includes(take.id)).map(take => take.status), {timeout: 90_000}).toEqual(result.take_ids.map(() => 'ready'));
  for (const id of result.take_ids) await expect(page.locator(`[data-take-id="${id}"]`)).toHaveClass(/generation-succeeded/);
}

/** Observadores de DOM y SSE real, instalados antes de enviar la generación. */
export async function observeGeneration(page: Page, request: APIRequestContext, testInfo: TestInfo) {
  await page.evaluate(() => {
    const target = window as typeof window & {integrationStages?: Record<string, string[]>; integrationObserver?: MutationObserver};
    target.integrationStages = {};
    const record = () => document.querySelectorAll<HTMLElement>('.generation-card[data-take-id]').forEach(card => {
      const id = card.dataset.takeId!;
      const stage = card.classList.contains('generation-succeeded') ? 'ready' : card.querySelector<HTMLElement>('[data-stage].current')?.dataset.stage;
      const history = target.integrationStages![id] ??= [];
      if (stage && history.at(-1) !== stage) history.push(stage);
    });
    target.integrationObserver = new MutationObserver(record);
    target.integrationObserver.observe(document.body, {subtree: true, childList: true, attributes: true, attributeFilter: ['class']});
    record();
  });
  let controller = new AbortController();
  let reader: ReadableStreamDefaultReader<Uint8Array> | undefined;
  let reading: Promise<void> = Promise.resolve();
  let streamError: string | undefined;
  let lifetimeTimer: ReturnType<typeof setTimeout> | undefined;
  const frames: SSEFrame[] = [];
  const events: ServerEvent[] = [];
  const snapshots: JobState[][] = [];
  const connections: {endpoint: string; cursor?: string; outcome: string}[] = [];
  // El reductor publica el snapshot sólo tras validar begin/chunk/end y su cursor.
  const reducer = new EventReducer(event => events.push(event), jobs => snapshots.push(jobs));
  async function stop() {
    clearTimeout(lifetimeTimer);
    controller.abort();
    await reader?.cancel().catch(() => {});
    await reading;
    reader = undefined;
    reducer.discard();
  }
  async function start(endpoint: string) {
    await stop();
    controller = new AbortController();
    const signal = controller.signal;
    const before = connections.length;
    lifetimeTimer = setTimeout(() => {streamError = 'SSE_OBSERVER_DEADLINE'; controller.abort();}, 90_000);
    reading = (async () => {
      let consecutiveFailures = 0;
      while (!signal.aborted) {
        reducer.discard();
        let snapshotPending = false;
        let protocolError = false;
        const parser = new EventParser(frame => {
          reducer.accept(frame);
          frames.push(frame);
          const event = frame.data as ServerEvent;
          if (event.type === 'system.status' && event.data.status === 'snapshot') snapshotPending = event.data.phase !== 'end';
        });
        const connection = {endpoint, cursor: reducer.cursor, outcome: 'opening'};
        try {
          const deadline = setTimeout(() => {streamError = 'SSE_OPEN_TIMEOUT'; controller.abort();}, 30_000);
          let response: globalThis.Response;
          try {
            response = await fetch(endpoint, {headers: {Origin: webOrigin, 'X-Studio-Session-Token': await credential(request), ...(reducer.cursor ? {'Last-Event-ID': reducer.cursor} : {})}, signal});
          } finally {clearTimeout(deadline);}
          if (response.status !== 200 || !response.headers.get('content-type')?.startsWith('text/event-stream') || !response.body) {protocolError = true; throw new Error(`SSE HTTP ${response.status}`);}
          connection.outcome = 'streaming';
          connections.push(connection);
          reader = response.body.getReader();
          for (;;) {
            const {done, value} = await reader.read();
            if (done) break;
            try {parser.push(value);} catch (error) {protocolError = true; throw error;}
          }
          connection.outcome = 'eof';
          // Una publicación puede cerrar limpiamente el bus al invalidar su epoch.
          // Un EOF parcial tampoco confirma el snapshot: conserva el cursor anterior.
          try {parser.finish();} catch {connection.outcome = 'partial-eof';}
          if (snapshotPending) connection.outcome = 'partial-eof';
          // EOF completo es una conexión correcta; no consume el presupuesto de errores.
          consecutiveFailures = connection.outcome === 'eof' ? 0 : consecutiveFailures + 1;
        } catch (error) {
          if (signal.aborted) return;
          connection.outcome = 'error';
          if (protocolError) {streamError = String(error); return;}
          consecutiveFailures++;
        } finally {
          await reader?.cancel().catch(() => {});
          reader = undefined;
          reducer.discard();
        }
        if (consecutiveFailures >= 5) {streamError = 'SSE_RECONNECT_LIMIT'; return;}
        // Evita un bucle ocupado cuando el servidor cierra sucesivamente el bus.
        await pause(50, undefined, {signal}).catch(() => {});
      }
    })();
    await expect.poll(() => connections.length > before || streamError !== undefined).toBe(true);
    expect(streamError).toBeUndefined();
  }
  try {
    await start(`${apiOrigin}/api/events`);
    await expect.poll(() => reducer.cursor !== undefined).toBe(true);
  } catch (error) {await stop(); throw error;}
  const terminal = (result: GenerationResponse) => {
    const event = events.find(event => event.type === 'job.done' && event.data.job_id === result.post_job_id && event.data.status === 'succeeded');
    if (event) return {source: 'event', event};
    const snapshot = snapshots.find(jobs => [result.generation_job_id, result.post_job_id].every(id => jobs.some(job => job.job_id === id && job.song_id === result.song_id && job.status === 'succeeded')));
    return snapshot ? {source: 'confirmed-snapshot', jobs: snapshot} : undefined;
  };
  return {
    async follow(result: GenerationResponse) {
      // Scope de ambos jobs y cursor pre-POST para recuperar los eventos de cola.
      await start(`${apiOrigin}/api/events?song_id=${result.song_id}&known_job_id=${result.generation_job_id}&known_job_id=${result.post_job_id}`);
    },
    async verify(result: GenerationResponse) {
      const histories = await page.evaluate(() => (window as typeof window & {integrationStages?: Record<string, string[]>}).integrationStages);
      await expect.poll(() => terminal(result) !== undefined || streamError !== undefined).toBe(true);
      await testInfo.attach('generation-stage-history', {body: JSON.stringify({histories, frames, snapshots, connections, terminal: terminal(result), streamError}), contentType: 'application/json'});
      expect(streamError).toBeUndefined();
      for (const id of result.take_ids) {
        const history = histories?.[id] ?? [];
        let index = -1;
        for (const stage of ['queued', 'generating', 'post', 'ready']) {
          const next = history.indexOf(stage, index + 1);
          expect(next, `${id}: etapa ${stage} en ${JSON.stringify(history)}`).toBeGreaterThan(index);
          index = next;
        }
      }
      expect(events.some(event => event.type === 'job.stage' && event.data.job_id === result.generation_job_id && event.data.stage === 'generating')).toBe(true);
      expect(terminal(result), 'Post succeeded por evento o snapshot completo de ambos jobs; takes ready comprobados por ready() y DOM').toBeDefined();
    },
    async close() {
      await stop();
      const histories = await page.evaluate(() => (window as typeof window & {integrationStages?: Record<string, string[]>}).integrationStages).catch(() => undefined);
      await testInfo.attach('observed-generation-evidence', {body: JSON.stringify({histories, frames, snapshots, connections, streamError}), contentType: 'application/json'});
    },
  };
}

export async function browserRange(page: Page, request: APIRequestContext, takeId: string) {
  const token = await credential(request);
  return page.evaluate(async ({url, token}) => {
    const response = await fetch(url, {headers: {'X-Studio-Session-Token': token, Range: 'bytes=0-127'}});
    return {status: response.status, bytes: (await response.arrayBuffer()).byteLength};
  }, {url: `${apiOrigin}/api/takes/${takeId}/audio`, token});
}
