// @vitest-environment jsdom
import React from 'react';
import {renderToString} from 'react-dom/server';
import {act, cleanup, fireEvent, render, screen, waitFor} from '@testing-library/react';
import {NextIntlClientProvider} from 'next-intl';
import {afterEach, beforeEach, expect, test, vi} from 'vitest';
import messages from '../../messages/es.json';
import CreatePage from './page';
import {ApiError, createGeneration, estimateGeneration, getSystemInfo, cancelJob, retryJob, listSongTakes, getTakePeaks, type SystemInfo} from '../../lib/api';

vi.mock('../../lib/api', async importOriginal => ({...await importOriginal<typeof import('../../lib/api')>(), getSystemInfo: vi.fn(), estimateGeneration: vi.fn(), createGeneration: vi.fn(), cancelJob: vi.fn(), retryJob: vi.fn(), listSongTakes: vi.fn(), getTakePeaks: vi.fn()}));
vi.mock('../../lib/events', () => ({subscribeEvents: vi.fn(() => vi.fn())}));
import {subscribeEvents, type ServerEvent} from '../../lib/events';
const system = (free_mb: number | null = 8000): SystemInfo => ({disk: {}, ram: {}, queue: {queued: false, running: false, blocked: false}, engines: [], gpu: {free_mb}, models: [{id: 'verified-local', provider: {type: 'local'}, commercial_use: true, license: 'MIT', tasks: {'music.song': {verified: true, features: {}, params_schema: {properties: {duration_s: {type: 'number', minimum: 10, maximum: 600}, inference_steps: {type: 'integer', minimum: 1, maximum: 8}, vocal_language: {type: 'string'}}}}, 'music.instrumental': {verified: true, features: {}, params_schema: {properties: {duration_s: {type: 'number', minimum: 10, maximum: 600}}}}}}]});
beforeEach(() => {
  vi.mocked(getSystemInfo).mockResolvedValue(system());
  vi.mocked(estimateGeneration).mockResolvedValue({eta_s: 4, vram_mb: 7000});
  vi.mocked(createGeneration).mockResolvedValue({song_id: 'S', generation_job_id: 'G', post_job_id: 'P', take_ids: [], beat_job_ids: []});
  vi.mocked(listSongTakes).mockResolvedValue({items: []});
  vi.mocked(getTakePeaks).mockResolvedValue({data: []} as never);
  vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(null);
  window.localStorage.clear();
});
afterEach(() => { cleanup(); vi.clearAllMocks(); });
function mount() { return render(<NextIntlClientProvider locale="es" messages={messages}><CreatePage /></NextIntlClientProvider>); }
async function ready() { mount(); await waitFor(() => expect(screen.getByLabelText(messages.create.stepsLabel)).toBeTruthy()); }
function fill() {
  fireEvent.change(screen.getByLabelText(messages.create.lyricsLabel), {target: {value: '[Verse]\nHola mundo'}});
  fireEvent.change(screen.getByLabelText(messages.create.styleLabel), {target: {value: 'pop'}});
  fireEvent.click(screen.getByLabelText(messages.create.declarationOwn));
}
const submit = () => screen.getByRole('button', {name: messages.create.submit});

test('Crear expone las secciones de letra y los controles avanzados', async () => {
  render(
    <NextIntlClientProvider locale="es" messages={messages}>
      <CreatePage />
    </NextIntlClientProvider>,
  );

  fireEvent.click(screen.getByRole('button', {name: '[Verse]'}));
  expect(
    (screen.getByLabelText(messages.create.lyricsLabel) as HTMLTextAreaElement).value,
  ).toContain('[Verse]');
  fireEvent.click(await screen.findByText(messages.create.advancedLabel));
  expect(screen.queryByLabelText(messages.create.guidanceScaleLabel)).toBeNull();
  await waitFor(() => expect(screen.getByLabelText(messages.create.vocalLanguageLabel)).toBeTruthy());
});

test('CA-1 duración vacía con placeholder 30 omite duration_s al enviar', async () => {
  await ready(); fill();
  const duration = screen.getByLabelText(messages.create.durationLabel) as HTMLInputElement;
  expect(duration.value).toBe(''); expect(duration.placeholder).toBe('30');
  fireEvent.click(submit());
  await waitFor(() => expect(createGeneration).toHaveBeenCalled());
  expect(vi.mocked(createGeneration).mock.calls[0][0].params).not.toHaveProperty('duration_s');
});
test('CA-2 variantes empieza en uno y dos requiere estimación que cabe', async () => {
  vi.mocked(estimateGeneration).mockResolvedValue({eta_s: 4, vram_mb: 9000});
  await ready(); fill();
  const variants = screen.getByLabelText(messages.create.variantsLabel) as HTMLSelectElement;
  expect(variants.value).toBe('1');
  await waitFor(() => expect(estimateGeneration).toHaveBeenCalledWith(expect.objectContaining({n_outputs: 2, model_id: 'verified-local'})));
  expect([...variants.options].map(option => option.value)).toEqual(['1']);
});
test('CA-3 todos los motivos deshabilitados están enlazados accesiblemente', async () => {
  await ready();
  const id = submit().getAttribute('aria-describedby');
  expect(id).toBeTruthy();
  const reasons = document.getElementById(id!);
  expect(reasons?.textContent).toContain('Escribe una letra');
  expect(reasons?.textContent).toContain(messages.create.styleRequired);
  expect(reasons?.textContent).toContain(messages.create.declarationHelp);
  fill();
  fireEvent.change(screen.getByLabelText(messages.create.languageLabel), {target: {value: ''}});
  fireEvent.change(screen.getByLabelText(messages.create.stepsLabel), {target: {value: '1.5'}});
  expect(document.getElementById(id!)?.textContent).toContain('idioma');
  expect(document.getElementById(id!)?.textContent).toContain(messages.create.advancedInvalid);
});
test('dos variantes sólo con estimación actual; cambiar parámetros invalida inmediatamente', async () => {
  await ready(); fill();
  const variants = screen.getByLabelText(messages.create.variantsLabel) as HTMLSelectElement;
  await waitFor(() => expect([...variants.options].map(option => option.value)).toEqual(['1', '2']));
  fireEvent.change(variants, {target: {value: '2'}});
  fireEvent.click(submit());
  await waitFor(() => expect(createGeneration).toHaveBeenCalledWith(expect.objectContaining({n_outputs: 2})));
  await waitFor(() => expect(submit().hasAttribute('disabled')).toBe(false));
  vi.mocked(estimateGeneration).mockImplementation(() => new Promise(() => {}));
  fireEvent.change(screen.getByLabelText(messages.create.styleLabel), {target: {value: 'jazz'}});
  expect(variants.value).toBe('1');
  expect([...variants.options].map(option => option.value)).toEqual(['1']);
});
test.each([null, 0, -1, NaN])('sin VRAM libre válida (%s) no solicita ni ofrece dos variantes', async free => {
  vi.mocked(getSystemInfo).mockResolvedValue(system(free));
  await ready(); fill();
  expect(estimateGeneration).not.toHaveBeenCalled();
  expect([...screen.getByLabelText<HTMLSelectElement>(messages.create.variantsLabel).options].map(option => option.value)).toEqual(['1']);
});
test.each([0, -1, NaN, Infinity])('estimación inválida (%s) no ofrece dos variantes', async vram_mb => {
  vi.mocked(estimateGeneration).mockResolvedValue({eta_s: 4, vram_mb});
  await ready(); fill();
  await waitFor(() => expect(estimateGeneration).toHaveBeenCalled());
  expect([...screen.getByLabelText<HTMLSelectElement>(messages.create.variantsLabel).options].map(option => option.value)).toEqual(['1']);
});
test('fallo de estimación conserva generación de una variante sin ETA inventada', async () => {
  vi.mocked(estimateGeneration).mockRejectedValue(new Error('offline'));
  await ready(); fill(); fireEvent.click(submit());
  await waitFor(() => expect(createGeneration).toHaveBeenCalledWith(expect.objectContaining({n_outputs: 1})));
  expect(screen.queryByText(/Estimación local/)).toBeNull();
});

test('CPU verificada permite dos variantes con estimación cero aunque no haya VRAM libre', async () => {
  const info = system(0);
  info.models[0].tasks!['music.song'].device = 'cpu';
  vi.mocked(getSystemInfo).mockResolvedValue(info);
  vi.mocked(estimateGeneration).mockResolvedValue({eta_s: 4, vram_mb: 0});
  await ready(); fill();
  const variants = screen.getByLabelText<HTMLSelectElement>(messages.create.variantsLabel);
  expect(variants.value).toBe('1');
  await waitFor(() => expect([...variants.options].map(option => option.value)).toEqual(['1', '2']));
  fireEvent.change(variants, {target: {value: '2'}});
  fireEvent.click(submit());
  await waitFor(() => expect(createGeneration).toHaveBeenCalledWith(expect.objectContaining({n_outputs: 2})));
});

test.each([-1, 1, NaN, Infinity])('CPU rechaza estimación distinta de cero finito (%s)', async vram_mb => {
  const info = system(null); info.gpu = null;
  info.models[0].tasks!['music.song'].device = 'cpu';
  vi.mocked(getSystemInfo).mockResolvedValue(info);
  vi.mocked(estimateGeneration).mockResolvedValue({eta_s: 4, vram_mb});
  await ready(); fill();
  await waitFor(() => expect(estimateGeneration).toHaveBeenCalled());
  expect([...screen.getByLabelText<HTMLSelectElement>(messages.create.variantsLabel).options].map(option => option.value)).toEqual(['1']);
});

test('CPU sin telemetría invalida estimación al cambiar parámetros y conserva uno si falla', async () => {
  const info = system(null); info.gpu = null;
  info.models[0].tasks!['music.song'].device = 'cpu';
  vi.mocked(getSystemInfo).mockResolvedValue(info);
  vi.mocked(estimateGeneration).mockResolvedValue({eta_s: 4, vram_mb: 0});
  await ready(); fill();
  const variants = screen.getByLabelText<HTMLSelectElement>(messages.create.variantsLabel);
  await waitFor(() => expect(variants.options).toHaveLength(2));
  fireEvent.change(variants, {target: {value: '2'}});
  vi.mocked(estimateGeneration).mockRejectedValue(new Error('offline'));
  fireEvent.change(screen.getByLabelText(messages.create.styleLabel), {target: {value: 'jazz'}});
  expect(variants.value).toBe('1');
  await act(async () => {});
  expect(variants.options).toHaveLength(1);
  fireEvent.click(submit());
  await waitFor(() => expect(createGeneration).toHaveBeenCalledWith(expect.objectContaining({n_outputs: 1})));
});
test('instrumental conserva letra pero no la envía ni exige autoría o idioma', async () => {
  await ready();
  fireEvent.change(screen.getByLabelText(messages.create.lyricsLabel), {target: {value: '[Verse]'}});
  fireEvent.change(screen.getByLabelText(messages.create.styleLabel), {target: {value: 'ambient'}});
  fireEvent.click(screen.getByLabelText(messages.create.instrumentalLabel));
  fireEvent.change(screen.getByLabelText(messages.create.durationLabel), {target: {value: '45'}});
  fireEvent.change(screen.getByLabelText(messages.create.seedLabel), {target: {value: '123'}});
  fireEvent.click(submit());
  await waitFor(() => expect(createGeneration).toHaveBeenCalled());
  const input = vi.mocked(createGeneration).mock.calls[0][0];
  expect(input).toMatchObject({task: 'music.instrumental', seed: 123, params: {duration_s: 45}});
  expect(input).not.toHaveProperty('lyrics'); expect(input.params).not.toHaveProperty('lyrics');
  expect(screen.getByLabelText<HTMLTextAreaElement>(messages.create.lyricsLabel).value).toBe('[Verse]');
});
test('duración cero y semillas fraccionarias se explican y nunca se envían', async () => {
  await ready(); fill();
  for (const [label, value] of [[messages.create.durationLabel, '0'], [messages.create.seedLabel, '0.1']]) {
    fireEvent.change(screen.getByLabelText(label), {target: {value}});
    expect(submit().hasAttribute('disabled')).toBe(true);
    fireEvent.submit(submit().closest('form')!);
    expect(createGeneration).not.toHaveBeenCalled();
    fireEvent.change(screen.getByLabelText(label), {target: {value: ''}});
  }
});
test('parámetros avanzados enviados y validados proceden del descriptor verificado', async () => {
  const info = system();
  info.models[0].tasks!['music.song'].params_schema = {properties: {
    duration_s: {type: 'number', minimum: 10, maximum: 600},
    bpm: {type: 'number', minimum: 30, maximum: 300}, key: {type: 'string', enum: ['C major']},
    time_signature: {type: 'string', pattern: '^[1-9]/[248]$'}, negative_prompt: {type: 'string'},
    inference_steps: {type: 'integer', minimum: 1, maximum: 8}, vocal_language: {type: 'string'},
    shift: {type: 'number', minimum: 1, maximum: 5}, guidance_scale: {type: 'number', minimum: 1, maximum: 20},
  }};
  vi.mocked(getSystemInfo).mockResolvedValue(info);
  await ready(); fill();
  for (const [label, value] of [[messages.create.bpmLabel, '94'], [messages.create.keyLabel, 'C major'], [messages.create.timeSignatureLabel, '4/4'], [messages.create.negativePromptLabel, 'metal'], [messages.create.stepsLabel, '4'], [messages.create.vocalLanguageLabel, 'en'], [messages.create.shiftLabel, '2'], [messages.create.guidanceScaleLabel, '7']]) {
    fireEvent.change(screen.getByLabelText(label), {target: {value}});
  }
  fireEvent.click(submit());
  await waitFor(() => expect(createGeneration).toHaveBeenCalledWith(expect.objectContaining({params: expect.objectContaining({bpm: 94, key: 'C major', time_signature: '4/4', negative_prompt: 'metal', inference_steps: 4, vocal_language: 'en', shift: 2, guidance_scale: 7})})));
  await waitFor(() => expect(submit().hasAttribute('disabled')).toBe(false));
  for (const [label, invalid, valid] of [[messages.create.stepsLabel, '9', '4'], [messages.create.keyLabel, 'D minor', 'C major'], [messages.create.timeSignatureLabel, 'abc', '4/4'], [messages.create.bpmLabel, '20', '94']]) {
    fireEvent.change(screen.getByLabelText(label), {target: {value: invalid}});
    expect(submit().hasAttribute('disabled')).toBe(true);
    fireEvent.change(screen.getByLabelText(label), {target: {value: valid}});
  }
});
test('un descriptor sin schema o con feature no verificada no inventa controles', async () => {
  const info = system();
  info.models[0].tasks!['music.song'].features = {inference_steps: {verified: false}};
  vi.mocked(getSystemInfo).mockResolvedValue(info);
  mount();
  await screen.findByLabelText(messages.create.durationLabel);
  expect(screen.queryByLabelText(messages.create.stepsLabel)).toBeNull();
});
test('un fallo de transporte al enviar se conserva visible', async () => {
  vi.mocked(createGeneration).mockRejectedValue(new Error('Conexión interrumpida'));
  await ready(); fill(); fireEvent.click(submit());
  expect((await screen.findByRole('alert')).textContent).toBe('Conexión interrumpida');
});
test('CA-4 muestra código y texto del error de envío', async () => {
  vi.mocked(createGeneration).mockRejectedValue(new ApiError(422, 'LYRICS_DECLARATION_REQUIRED', 'Declara los derechos antes de generar.'));
  await ready(); fill(); fireEvent.click(submit());
  const alert = await screen.findByRole('alert');
  expect(alert.textContent).toContain('LYRICS_DECLARATION_REQUIRED');
  expect(alert.textContent).toContain('Declara los derechos antes de generar.');
});
test('CA-5 resaltado sigue rangos del parser con negrita, inline y malformadas', async () => {
  await ready();
  fireEvent.change(screen.getByLabelText(messages.create.lyricsLabel), {target: {value: '**[Verse]**\nHola [Chorus]\n[Bridge\nTexto'}});
  const marks = [...document.querySelectorAll('.lyrics-mirror mark')];
  expect(marks.map(mark => mark.textContent)).toEqual(['**[Verse]**\n', '[Bridge\n']);
  expect(marks[0].className).toBe(''); expect(marks[1].className).toBe('invalid-tag');
});
test('CA-6 sistema caído explica indisponibilidad sin avanzado ni modelo inventados', async () => {
  vi.mocked(getSystemInfo).mockRejectedValue(new Error('offline'));
  mount(); fill();
  await waitFor(() => expect(getSystemInfo).toHaveBeenCalled());
  expect(screen.queryByLabelText(messages.create.stepsLabel)).toBeNull();
  expect(screen.queryByLabelText(messages.create.durationLabel)).toBeNull();
  expect(screen.getByText(/sistema no está disponible/i)).toBeTruthy();
  fireEvent.click(submit());
  expect(createGeneration).not.toHaveBeenCalled(); expect(estimateGeneration).not.toHaveBeenCalled();
});

test('T13 feed no lee storage en render y restaura antes de persistir', async () => {
  const key = 'music-studio:generation-feed';
  const stored = [{song_id: 'S', job_id: 'G', status: 'queued'}];
  window.localStorage.setItem(key, JSON.stringify(stored));
  const reads = vi.spyOn(Storage.prototype, 'getItem');
  const writes = vi.spyOn(Storage.prototype, 'setItem');
  renderToString(<NextIntlClientProvider locale="es" messages={messages}><CreatePage /></NextIntlClientProvider>);
  expect(reads).not.toHaveBeenCalled();
  await ready();
  expect(writes).toHaveBeenCalledWith(key, JSON.stringify(stored));
  expect(writes).not.toHaveBeenCalledWith(key, '[]');
  reads.mockRestore(); writes.mockRestore();
});


const feedJob = {song_id: '01K70000000000000000000001', job_id: '01K70000000000000000000002', post_job_id: '01K70000000000000000000003', take_id: '01K70000000000000000000004', status: 'running', stage: 'generating', progress: .3, attempt_id: null, error_code: null};
function distinctFeed(count: number) {
  return Array.from({length: count}, (_, index) => ({...feedJob,
    song_id: `01K70000000000000000000${String(index * 4 + 1).padStart(3, '0')}`,
    job_id: `01K70000000000000000000${String(index * 4 + 2).padStart(3, '0')}`,
    post_job_id: `01K70000000000000000000${String(index * 4 + 3).padStart(3, '0')}`,
    take_id: `01K70000000000000000000${String(index * 4 + 4).padStart(3, '0')}`,
  }));
}
test('D1 ten snapshots revalidate only their originating song', async () => {
  const jobs = distinctFeed(10);
  window.localStorage.setItem('music-studio:generation-feed', JSON.stringify(jobs));
  await ready();
  expect(listSongTakes).toHaveBeenCalledTimes(10);
  const subscriptions = [...vi.mocked(subscribeEvents).mock.calls];
  await act(async () => {for (const subscription of subscriptions) subscription[2]!.snapshot([]);});
  expect(listSongTakes).toHaveBeenCalledTimes(20);
  for (const job of jobs) expect(vi.mocked(listSongTakes).mock.calls.filter(([id]) => id === job.song_id)).toHaveLength(2);
});
test('D1 restored song with 65 known jobs respects the server limit of 64', async () => {
  const jobs = distinctFeed(33).map((job, index) => ({...job, song_id: feedJob.song_id, ...(index === 32 ? {post_job_id: undefined} : {})}));
  window.localStorage.setItem('music-studio:generation-feed', JSON.stringify(jobs));
  await ready();
  expect(subscribeEvents).toHaveBeenCalledTimes(1);
  const url = new URL(vi.mocked(subscribeEvents).mock.calls[0][0]);
  expect(url.searchParams.get('song_id')).toBe(feedJob.song_id);
  expect(url.searchParams.getAll('known_job_id')).toHaveLength(64);
  expect(new Set(url.searchParams.getAll('known_job_id')).size).toBe(64);
});
test.each(['job.done', 'entity.updated'] as const)('D1 %s revalidates only the subscription song', async type => {
  const jobs = distinctFeed(3);
  window.localStorage.setItem('music-studio:generation-feed', JSON.stringify(jobs));
  await ready();
  vi.mocked(listSongTakes).mockClear();
  const subscription = vi.mocked(subscribeEvents).mock.calls.find(([url]) => url.includes(`song_id=${jobs[1].song_id}`))!;
  await act(async () => subscription[1]({id: 1, ts: '', type, data: type === 'job.done' ? {job_id: jobs[1].job_id} : {type: 'take', id: jobs[1].take_id, song_id: jobs[0].song_id}}));
  expect(vi.mocked(listSongTakes).mock.calls).toEqual([[jobs[1].song_id]]);
});
test('D2 three sequential ready takes download peaks only once each', async () => {
  const jobs = distinctFeed(3);
  window.localStorage.setItem('music-studio:generation-feed', JSON.stringify(jobs));
  vi.mocked(getTakePeaks).mockResolvedValue({data: [[[-.7, .8]]]} as never);
  await ready();
  for (let index = 0; index < jobs.length; index++) {
    vi.mocked(listSongTakes).mockResolvedValueOnce({items: [{id: jobs[index].take_id, status: 'ready'}]} as never);
    const subscription = vi.mocked(subscribeEvents).mock.calls.find(([url]) => url.includes(`song_id=${jobs[index].song_id}`))!;
    await act(async () => subscription[2]!.snapshot([]));
    await waitFor(() => expect(JSON.parse(window.localStorage.getItem('music-studio:generation-feed')!).find((job: typeof feedJob) => job.take_id === jobs[index].take_id).peaks).toEqual([-.7, .8]));
  }
  expect(vi.mocked(getTakePeaks).mock.calls).toEqual(jobs.map(job => [job.take_id]));
});
test('D2 cancelled pending peaks restart and ignore stale completion', async () => {
  const jobs = distinctFeed(2);
  window.localStorage.setItem('music-studio:generation-feed', JSON.stringify(jobs));
  let resolveOld!: (value: Awaited<ReturnType<typeof getTakePeaks>>) => void;
  vi.mocked(getTakePeaks).mockImplementationOnce(() => new Promise(resolve => {resolveOld = resolve;}));
  vi.mocked(getTakePeaks).mockResolvedValue({data: [[[-.4, .5]]]} as never);
  await ready();
  for (const job of jobs) {
    vi.mocked(listSongTakes).mockResolvedValueOnce({items: [{id: job.take_id, status: 'ready'}]} as never);
    const subscription = vi.mocked(subscribeEvents).mock.calls.find(([url]) => url.includes(`song_id=${job.song_id}`))!;
    await act(async () => subscription[2]!.snapshot([]));
  }
  await waitFor(() => expect(vi.mocked(getTakePeaks).mock.calls.filter(([id]) => id === jobs[0].take_id)).toHaveLength(2));
  await act(async () => resolveOld({data: [[[-.9, 1]]]} as never));
  const saved = JSON.parse(window.localStorage.getItem('music-studio:generation-feed')!);
  expect(saved.map((job: {peaks: number[]}) => job.peaks)).toEqual([[-.4, .5], [-.4, .5]]);
});
test.each(['error', 'empty'])('D2 peaks retry after %s until analysis is available', async failure => {
  let retry!: () => void;
  const originalTimeout = window.setTimeout.bind(window);
  const timer = vi.spyOn(window, 'setTimeout').mockImplementation((callback, delay, ...args) => {
    if (delay === 1000 && String(callback).includes('poll')) {retry = callback as () => void; return 456 as unknown as ReturnType<typeof window.setTimeout>;}
    return originalTimeout(callback, delay, ...args) as unknown as ReturnType<typeof window.setTimeout>;
  });
  try {
    storedFeed();
    if (failure === 'error') vi.mocked(getTakePeaks).mockRejectedValueOnce(new Error('analysis pending'));
    else vi.mocked(getTakePeaks).mockResolvedValueOnce({data: []} as never);
    vi.mocked(listSongTakes).mockResolvedValue({items: [{id: feedJob.take_id, status: 'ready'}]} as never);
    await ready();
    await waitFor(() => expect(retry).toBeTypeOf('function'));
    vi.mocked(getTakePeaks).mockResolvedValue({data: [[[-.2, .3]]]} as never);
    await act(async () => retry());
    expect(getTakePeaks).toHaveBeenCalledTimes(2);
    expect(JSON.parse(window.localStorage.getItem('music-studio:generation-feed')!)[0].peaks).toEqual([-.2, .3]);
  } finally { timer.mockRestore(); }
});
function storedFeed(status = 'running') { window.localStorage.setItem('music-studio:generation-feed', JSON.stringify([{...feedJob, status}])); }
function emit(type: ServerEvent['type'], data: ServerEvent['data']) {
  const call = vi.mocked(subscribeEvents).mock.calls.at(-1)!;
  call[1]({id: 1, ts: '2026-11-03T00:00:00.000Z', type, data});
}
test('T10 CA-2 sigue post_job y take ready, nunca solo job.done', async () => {
  storedFeed(); await ready();
  emit('job.done', {job_id: feedJob.job_id, status: 'succeeded'});
  await waitFor(() => expect(listSongTakes).toHaveBeenCalled());
  expect(screen.queryByText(messages.generation.status.succeeded)).toBeNull();
  vi.mocked(listSongTakes).mockResolvedValue({items: [{id: feedJob.take_id, status: 'ready'}]} as never);
  emit('job.done', {job_id: feedJob.post_job_id, status: 'succeeded'});
  await screen.findByText(messages.generation.status.succeeded);
  await waitFor(() => expect(getTakePeaks).toHaveBeenCalledWith(feedJob.take_id));
});
test.each([['cancel', 409, 'JOB_TERMINAL'], ['retry', 503, 'ENGINE_UNAVAILABLE']] as const)('T10 CA-4 %s muestra c?digo %i', async (action, status, code) => {
  storedFeed(action === 'retry' ? 'failed' : 'running');
  vi.mocked(action === 'retry' ? retryJob : cancelJob).mockRejectedValue(new ApiError(status, code, 'Acci?n rechazada'));
  await ready();
  fireEvent.click(screen.getByRole('button', {name: messages.generation[action]}));
  await waitFor(() => expect(screen.getByRole('alert').textContent).toContain(code));
});

test('T10 snapshot reconnection preserves identity and reconciles take readiness', async () => {
  storedFeed(); await ready();
  const snapshot = vi.mocked(subscribeEvents).mock.calls.at(-1)![2]!.snapshot;
  expect(vi.mocked(subscribeEvents).mock.calls.at(-1)![0]).toContain(`known_job_id=${feedJob.post_job_id}`);
  act(() => snapshot([{...feedJob, status: 'succeeded'}, {...feedJob, job_id: feedJob.post_job_id, status: 'running', stage: 'normalize', progress: .6}]));
  await waitFor(() => expect(document.querySelector('li.current')?.getAttribute('data-stage')).toBe('post'));
  expect(screen.queryByText(messages.generation.status.succeeded)).toBeNull();
  act(() => snapshot([{...feedJob, status: 'running', stage: 'decoding', progress: .8}]));
  await waitFor(() => expect(document.querySelector('li.current')?.getAttribute('data-stage')).toBe('decoding'));
  act(() => snapshot([]));
  act(() => emit('job.progress', {job_id: 'other', fraction: .4}));
  act(() => emit('system.status', {status: 'ok'}));
  act(() => emit('job.progress', {job_id: feedJob.job_id, fraction: .9}));
  await waitFor(() => expect(screen.getByRole('progressbar').getAttribute('aria-valuenow')).toBe('90'));
  vi.mocked(listSongTakes).mockResolvedValue({items: [{id: feedJob.take_id, status: 'ready'}]} as never);
  vi.mocked(getTakePeaks).mockResolvedValue({data: [[[-.7, .8]]]} as never);
  act(() => emit('entity.updated', {type: 'take', id: feedJob.take_id}));
  await screen.findByText(messages.generation.status.succeeded);
  await waitFor(() => expect(JSON.parse(window.localStorage.getItem('music-studio:generation-feed')!)[0].peaks).toEqual([-.7, .8]));
});
test('T10 cancel waits terminal SSE and retry replaces job preserving song', async () => {
  storedFeed(); vi.mocked(cancelJob).mockResolvedValue({job_id: feedJob.post_job_id, cancel_requested: true});
  await ready(); act(() => emit('job.done', {job_id: feedJob.job_id}));
  fireEvent.click(screen.getByRole('button', {name: messages.generation.cancel}));
  await waitFor(() => expect(cancelJob).toHaveBeenCalledWith(feedJob.post_job_id));
  expect(screen.queryByText(messages.generation.status.cancelled)).toBeNull();
  act(() => emit('job.cancelled', {job_id: feedJob.post_job_id}));
  await screen.findByText(messages.generation.status.cancelled);
  act(() => emit('job.failed', {job_id: feedJob.job_id, code: 'VRAM_EXCEEDED'}));
  await screen.findByRole('alert');
  vi.mocked(retryJob).mockResolvedValue({generation_job_id: '01K70000000000000000000005', post_job_id: '01K70000000000000000000006', take_ids: ['01K70000000000000000000007'], beat_job_ids: []});
  fireEvent.click(screen.getByRole('button', {name: messages.generation.retry}));
  await waitFor(() => expect(document.querySelector('article')?.getAttribute('data-take-id')).toBe('01K70000000000000000000007'));
  expect(JSON.parse(window.localStorage.getItem('music-studio:generation-feed')!)[0].song_id).toBe(feedJob.song_id);
});
test('T10 failed take read never invents ready and snapshot recovers', async () => {
  storedFeed('succeeded'); vi.mocked(listSongTakes).mockRejectedValue(new Error('offline'));
  await ready(); expect(screen.queryByText(messages.generation.status.succeeded)).toBeNull();
  vi.mocked(listSongTakes).mockResolvedValue({items: [{id: feedJob.take_id, status: 'ready'}]} as never);
  act(() => vi.mocked(subscribeEvents).mock.calls.at(-1)![2]!.snapshot([{...feedJob, status: 'succeeded'}]));
  await screen.findByText(messages.generation.status.succeeded);
});
test.each(['network', 'unknown'])('T10 transport action error %s remains visible', async kind => {
  storedFeed(); vi.mocked(cancelJob).mockRejectedValue(kind === 'network' ? new Error('offline') : null);
  await ready(); fireEvent.click(screen.getByRole('button', {name: messages.generation.cancel}));
  await waitFor(() => expect(screen.getByRole('alert').textContent).toContain(kind === 'network' ? 'offline' : 'UNKNOWN'));
});

test('T10 stale take read cannot overwrite a newer ready response', async () => {
  storedFeed(); let resolveOld!: (value: Awaited<ReturnType<typeof listSongTakes>>) => void;
  vi.mocked(listSongTakes).mockImplementationOnce(() => new Promise(resolve => {resolveOld = resolve;}));
  await ready();
  vi.mocked(listSongTakes).mockResolvedValue({items: [{id: feedJob.take_id, status: 'ready'}]} as never);
  act(() => emit('entity.updated', {type: 'take', id: feedJob.take_id}));
  await screen.findByText(messages.generation.status.succeeded);
  await act(async () => resolveOld({items: [{id: feedJob.take_id, status: 'generating'}]} as never));
  expect(screen.queryByText(messages.generation.status.succeeded)).toBeTruthy();
});

test.each(['rejection', 'fulfillment'])('B1 stale system polling %s preserves current descriptor', async completion => {
  let poll!: () => void;
  const originalInterval = window.setInterval.bind(window);
  const interval = vi.spyOn(window, 'setInterval').mockImplementation((callback, delay, ...args) => {if (delay === 5000) {poll = callback as () => void; return 321 as unknown as ReturnType<typeof window.setInterval>;} return originalInterval(callback, delay, ...args) as unknown as ReturnType<typeof window.setInterval>;});
  let rejectOld!: (cause: Error) => void;
  let resolveOld!: (info: SystemInfo) => void;
  try {
    await ready(); fill();
    vi.mocked(getSystemInfo).mockImplementationOnce(() => new Promise((resolve, reject) => {resolveOld = resolve; rejectOld = reject;}));
    act(() => poll());
    vi.mocked(getSystemInfo).mockImplementationOnce(() => new Promise(() => {}));
    act(() => poll());
    expect(vi.mocked(getSystemInfo).mock.calls.at(-2)![0]!.aborted).toBe(true);
    await act(async () => {if (completion === 'rejection') rejectOld(new Error('aborted')); else resolveOld({...system(), models: []});});
    expect(screen.queryByLabelText(messages.create.durationLabel)).toBeTruthy();
    expect(submit().hasAttribute('disabled')).toBe(false);
  } finally {interval.mockRestore();}
});
test.each(['failed', 'cancelled'] as const)('B2 post succeeded keeps mixed ready and %s take terminals', async status => {
  const otherTake = '01K70000000000000000000008';
  window.localStorage.setItem('music-studio:generation-feed', JSON.stringify([feedJob, {...feedJob, take_id: otherTake, variant_index: 1}]));
  vi.mocked(listSongTakes).mockResolvedValue({items: [{id: feedJob.take_id, status: 'ready', error_code: null}, {id: otherTake, status, error_code: status === 'failed' ? 'INVALID_AUDIO' : null}]} as never);
  await ready(); act(() => emit('job.done', {job_id: feedJob.post_job_id, status: 'succeeded'}));
  await waitFor(() => expect(screen.queryByText(messages.generation.status[status])).toBeTruthy());
  expect(screen.getByText(messages.generation.status.succeeded)).toBeTruthy();
  expect(screen.queryByRole('button', {name: messages.generation.cancel})).toBeNull();
  if (status === 'failed') {
    expect(screen.getByRole('alert').textContent).toContain('INVALID_AUDIO');
    expect(screen.getByRole('button', {name: messages.generation.retry})).toBeTruthy();
  } else expect(screen.queryByRole('button', {name: messages.generation.retry})).toBeNull();
});
