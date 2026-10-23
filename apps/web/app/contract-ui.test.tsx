// @vitest-environment jsdom
// M1/T-08 CA-1/CA-4: la UI consume los campos reales del contrato y traduce los valores crudos.
import React from 'react';
import {cleanup, render, screen} from '@testing-library/react';
import {afterEach, expect, test, vi} from 'vitest';
import {NextIntlClientProvider} from 'next-intl';
import messages from '../messages/es.json';
import SystemPage from './system/page';
import SongDetailPage from './songs/[id]/page';
vi.mock('next/navigation', () => ({useParams: () => ({id: 'S1'}), redirect: vi.fn()}));
vi.mock('../components/PlayerContext', () => ({usePlayer: () => ({select: vi.fn(), enqueue: vi.fn()})}));
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });
const wrap = (children: React.ReactNode) => <NextIntlClientProvider locale="es" messages={messages}>{children}</NextIntlClientProvider>;
const json = (body: unknown) => new Response(JSON.stringify(body));

test('Sistema muestra el tope real (cap_mb) y un guion traducido cuando no hay dato', async () => {
  vi.stubGlobal('fetch', vi.fn().mockImplementation(async (url: string) => {
    if (url.endsWith('/api/session/bootstrap')) return json({session_token: 's', expires_in_s: 60});
    if (url.endsWith('/api/system')) return json({
      queue: {queued: false, blocked: false, running: false},
      engines: [{state: 'ready', engine_id: 'mock'}], gpu: {free_mb: 8000, total_mb: 12288, cap_mb: 10240},
      ram: {free_bytes: 1048576 * 100, total_bytes: 1048576 * 200}, disk: {free_bytes: null, total_bytes: null}, models: [],
    });
    return json({process: 'server', status: 'running'});
  }));
  render(wrap(<SystemPage />));
  const cap = await screen.findByText(/Tope: 10240 MiB/);
  expect(cap.textContent).toBe('Libre: 8000 MiB · Total: 12288 MiB · Tope: 10240 MiB');
  expect(screen.getByText('100 MiB / 200 MiB')).toBeTruthy();
  expect(screen.getByText(`${messages.units.none} / ${messages.units.none}`)).toBeTruthy();
  expect(screen.queryByText(/\?/)).toBeNull();
});

test('Detalle de canción traduce estado y tarea y tolera un asset sin url', async () => {
  const take = {id: 'T1', song_id: 'S1', status: 'ready', task: 'music.song', label: null, model_id: 'mock', seed: null, params: {}, duration_s: 3, rating: null, favorite: false, error_code: null, batch_id: null, root_id: null, variant_index: 0, lyrics_version_id: null,
    assets: {listen: {role: 'listen', media_type: 'audio/mpeg', bytes: 1, sha256: 'a'.repeat(64)}}};
  vi.stubGlobal('fetch', vi.fn().mockImplementation(async (url: string) => {
    if (url.endsWith('/api/session/bootstrap')) return json({session_token: 's', expires_in_s: 60});
    if (url.endsWith('/api/songs/S1')) return json({id: 'S1', title: 'Canción', artist: null, status: 'in_progress', style_prompt: 'pop', master_take_id: null, collection_id: null, updated_at: 'x', created_at: 'x'});
    if (url.endsWith('/takes')) return json({items: [take]});
    if (url.endsWith('/lyrics')) return json({items: []});
    if (url.endsWith('/peaks')) return json({data: [[[0.1]]]});
    return json({items: []});
  }));
  render(wrap(<SongDetailPage />));
  await screen.findByText(`${messages.songDetail.statusLabel} ${messages.enums.songStatus.in_progress}`);
  const select = await screen.findByRole('button', {name: new RegExp(`${messages.enums.task.music_song} ${messages.songDetail.separator} ${messages.enums.takeStatus.ready}`)});
  expect(select.textContent).not.toMatch(/music\.song|ready/);
  select.click();
});
