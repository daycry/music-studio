// @vitest-environment jsdom
import React from 'react';
import {cleanup, fireEvent, render, screen} from '@testing-library/react';
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
