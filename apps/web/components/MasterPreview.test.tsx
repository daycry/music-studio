// @vitest-environment jsdom
import React from 'react';
import {act, cleanup, fireEvent, render, screen, waitFor} from '@testing-library/react';
import {afterEach, beforeEach, expect, test, vi} from 'vitest';
import {NextIntlClientProvider} from 'next-intl';
import messages from '../messages/es.json';
import {MasterPreview} from './MasterPreview';
import {getTakeAudioBlob, listSongTakes} from '../lib/api';

vi.mock('../lib/api', () => ({
  listSongTakes: vi.fn(async () => ({items: [{id: 'take-1', status: 'ready', assets: {listen: {url: '/audio'}}}]})),
  getTakeAudioBlob: vi.fn(async () => new Blob(['audio'], {type: 'audio/mpeg'})),
}));

beforeEach(() => {
  vi.mocked(listSongTakes).mockReset().mockImplementation(async () => ({items: [{id: 'take-1', status: 'ready', assets: {listen: {url: '/audio'}}}] as never}));
  vi.mocked(getTakeAudioBlob).mockReset().mockImplementation(async () => new Blob(['audio'], {type: 'audio/mpeg'}));
});
afterEach(() => { cleanup(); vi.restoreAllMocks(); vi.useRealTimers(); });

test('programa la preescucha a 400 ms y permite desactivarla', async () => {
  vi.useFakeTimers();
  vi.spyOn(HTMLMediaElement.prototype, 'play').mockResolvedValue(undefined);
  vi.spyOn(HTMLMediaElement.prototype, 'pause').mockImplementation(() => undefined);
  vi.stubGlobal('URL', {...URL, createObjectURL: vi.fn(() => 'blob:preview'), revokeObjectURL: vi.fn()});
  const view = render(<NextIntlClientProvider locale="es" messages={messages}><MasterPreview song={{id:'song-1', title:'Libre', master_take_id:'take-1'} as never} enabled /></NextIntlClientProvider>);
  const button = screen.getByRole('button', {name: messages.songs.preview});
  fireEvent.mouseEnter(button);
  await vi.advanceTimersByTimeAsync(399);
  expect(listSongTakes).not.toHaveBeenCalled();
  await vi.advanceTimersByTimeAsync(1);
  expect(listSongTakes).toHaveBeenCalledWith('song-1');
  view.rerender(<NextIntlClientProvider locale="es" messages={messages}><MasterPreview song={{id:'song-1', title:'Libre', master_take_id:'take-1'} as never} enabled={false} /></NextIntlClientProvider>);
  expect((screen.getByRole('button', {name: messages.songs.preview}) as HTMLButtonElement).disabled).toBe(true);
  vi.useRealTimers();
});


test('invalida una carga pendiente cuando se abandona la preescucha', async () => {
  vi.useFakeTimers();
  const play = vi.spyOn(HTMLMediaElement.prototype, 'play').mockResolvedValue(undefined);
  vi.spyOn(HTMLMediaElement.prototype, 'pause').mockImplementation(() => undefined);
  const pending = new Promise<{items: Array<{id: string; status: string; assets: {listen: {url: string}}}>}>(resolve => {
    (globalThis as {resolvePreview?: typeof resolve}).resolvePreview = resolve;
  });
  vi.mocked(listSongTakes).mockReturnValueOnce(pending as never);
  render(<NextIntlClientProvider locale="es" messages={messages}><MasterPreview song={{id:'song-1', title:'Libre', master_take_id:'take-1'} as never} enabled /></NextIntlClientProvider>);
  const button = screen.getByRole('button', {name: messages.songs.preview});
  fireEvent.mouseEnter(button);
  await vi.advanceTimersByTimeAsync(400);
  fireEvent.mouseLeave(button);
  (globalThis as {resolvePreview?: (value: {items: Array<{id: string; status: string; assets: {listen: {url: string}}}>}) => void}).resolvePreview?.({items: [{id: 'take-1', status: 'ready', assets: {listen: {url: '/audio'}}}]});
  await vi.runAllTicks();
  expect(play).not.toHaveBeenCalled();
});

test('sin maestro reproduce la última toma ready e indica la alternativa', async () => {
  vi.mocked(listSongTakes).mockResolvedValueOnce({items: [
    {id: 'old', status: 'ready', created_at: '2026-01-01T00:00:00Z'},
    {id: 'new', status: 'ready', created_at: '2026-03-01T00:00:00Z'},
    {id: 'pending', status: 'pending', created_at: '2026-04-01T00:00:00Z'},
  ] as never});
  vi.spyOn(HTMLMediaElement.prototype, 'play').mockResolvedValue(undefined);
  vi.spyOn(HTMLMediaElement.prototype, 'pause').mockImplementation(() => undefined);
  vi.stubGlobal('URL', {...URL, createObjectURL: vi.fn(() => 'blob:preview'), revokeObjectURL: vi.fn()});
  render(<NextIntlClientProvider locale="es" messages={messages}><MasterPreview song={{id:'song-1', title:'Libre', master_take_id:null}} enabled /></NextIntlClientProvider>);
  fireEvent.click(screen.getByRole('button', {name: messages.songs.preview}));
  await waitFor(() => expect(getTakeAudioBlob).toHaveBeenCalledWith('new'));
  expect(screen.getByText(messages.songs.previewLatestReady)).toBeTruthy();
});

test('sin ninguna toma ready explica por qué no hay preescucha', async () => {
  vi.mocked(listSongTakes).mockResolvedValueOnce({items: [{id: 'pending', status: 'pending'}] as never});
  vi.spyOn(HTMLMediaElement.prototype, 'pause').mockImplementation(() => undefined);
  render(<NextIntlClientProvider locale="es" messages={messages}><MasterPreview song={{id:'song-1', title:'Libre', master_take_id:null}} enabled /></NextIntlClientProvider>);
  fireEvent.click(screen.getByRole('button', {name: messages.songs.preview}));
  expect(await screen.findByText(messages.songs.previewNoReady)).toBeTruthy();
  expect(getTakeAudioBlob).not.toHaveBeenCalled();
});


function preview() {return render(<NextIntlClientProvider locale="es" messages={messages}><MasterPreview song={{id:'song-1', title:'Libre', master_take_id:'take-1'}} enabled /></NextIntlClientProvider>);}
function media() {
  vi.spyOn(HTMLMediaElement.prototype, 'play').mockResolvedValue(undefined);
  vi.spyOn(HTMLMediaElement.prototype, 'pause').mockImplementation(() => undefined);
  vi.stubGlobal('URL', {...URL, createObjectURL: vi.fn(() => 'blob:preview'), revokeObjectURL: vi.fn()});
}
test('la reproduccion termina a los diez segundos y libera el audio', async () => {
  vi.useFakeTimers(); media(); preview();
  const button = screen.getByRole('button', {name: messages.songs.preview});
  fireEvent.focus(button); fireEvent.mouseEnter(button);
  await act(async () => {await vi.advanceTimersByTimeAsync(400);});
  expect(button.getAttribute('data-state')).toBe('playing');
  await act(async () => {await vi.advanceTimersByTimeAsync(10000);});
  expect(button.getAttribute('data-state')).toBe('idle');
  expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:preview');
  fireEvent.click(button); await act(async () => {await vi.advanceTimersByTimeAsync(0);}); fireEvent.click(button);
  expect(button.getAttribute('data-state')).toBe('idle');
});
test('errores de carga son explicados y una nueva peticion permite recuperar', async () => {
  media(); vi.mocked(getTakeAudioBlob).mockRejectedValueOnce(new Error('offline')); preview();
  const button = screen.getByRole('button', {name: messages.songs.preview});
  fireEvent.click(button);
  expect(await screen.findByText(messages.songs.previewUnavailable)).toBeTruthy();
  fireEvent.click(button);
  await waitFor(() => expect(button.getAttribute('data-state')).toBe('playing'));
  fireEvent.ended(document.querySelector('audio')!);
  expect(button.getAttribute('data-state')).toBe('idle');
});
test('abandonar mientras descarga el audio invalida el blob tardio', async () => {
  media(); let resolve!: (blob: Blob) => void;
  vi.mocked(getTakeAudioBlob).mockReturnValueOnce(new Promise(done => {resolve = done;}));
  preview(); const button = screen.getByRole('button', {name: messages.songs.preview});
  fireEvent.click(button); await waitFor(() => expect(getTakeAudioBlob).toHaveBeenCalled());
  fireEvent.blur(button); resolve(new Blob(['audio']));
  await waitFor(() => expect(button.getAttribute('data-state')).toBe('idle'));
  expect(URL.createObjectURL).not.toHaveBeenCalled();
});
