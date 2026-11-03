// @vitest-environment jsdom
import React from 'react';
import {act, cleanup, fireEvent, render, renderHook, screen} from '@testing-library/react';
import {afterEach, expect, test, vi} from 'vitest';
import {renderToString} from 'react-dom/server';
import {PlayerProvider, usePlayer, type PlayerTrack} from './PlayerContext';

afterEach(() => {
  cleanup();
  window.localStorage.clear();
  vi.restoreAllMocks();
});

const track: PlayerTrack = {id: 'take-a', title: 'Libre · A', url: '/api/takes/take-a/audio', duration_s: 120};

function Harness() {
  const player = usePlayer();
  return <>
    <output data-testid="current">{player.current?.title ?? 'empty'}</output>
    <output data-testid="queue">{player.queue.map(item => item.id).join(',')}</output>
    <button type="button" onClick={() => player.select(track)}>select</button>
    <button type="button" onClick={() => player.enqueue({...track, id: 'take-b', title: 'Libre ? B'})}>enqueue</button>
    <button type="button" onClick={() => player.move(1, 0)}>move</button>
    <button type="button" onClick={() => player.step(1)}>next</button>
  </>;
}

test('el render inicial no lee storage y el efecto restaura antes de persistir', () => {
  const saved = JSON.stringify([track]);
  window.localStorage.setItem('music-studio.player.queue', saved);
  const read = vi.spyOn(Storage.prototype, 'getItem');
  const write = vi.spyOn(Storage.prototype, 'setItem');
  const html = renderToString(<PlayerProvider><Harness/></PlayerProvider>);
  expect(read).not.toHaveBeenCalled();
  expect(html).toContain('empty');
  render(<PlayerProvider><Harness/></PlayerProvider>);
  expect(screen.getByTestId('current').textContent).toBe(track.title);
  expect(write.mock.calls.every(([, value]) => value === saved)).toBe(true);
});

test('selecciona una toma y conserva la cola en localStorage', () => {
  const view = render(<PlayerProvider><Harness/></PlayerProvider>);
  fireEvent.click(screen.getByRole('button', {name: 'select'}));
  expect(screen.getByTestId('current').textContent).toBe('Libre · A');
  expect(screen.getByTestId('queue').textContent).toBe('take-a');
  view.unmount();
  render(<PlayerProvider><Harness/></PlayerProvider>);
  expect(screen.getByTestId('current').textContent).toBe('Libre · A');
});


test('reordena la cola y avanza por la toma siguiente', () => {
  render(<PlayerProvider><Harness/></PlayerProvider>);
  fireEvent.click(screen.getByRole('button', {name: 'select'}));
  fireEvent.click(screen.getByRole('button', {name: 'enqueue'}));
  fireEvent.click(screen.getByRole('button', {name: 'move'}));
  expect(screen.getByTestId('queue').textContent).toBe('take-b,take-a');
  fireEvent.click(screen.getByRole('button', {name: 'next'}));
  expect(screen.getByTestId('current').textContent).toBe(track.title);
});

test('restaura sólo pistas válidas y permite eliminar y mover sin perder la selección', () => {
  window.localStorage.setItem('music-studio.player.queue', JSON.stringify([null, {}, track, {...track, id:'b', title:'B'}]));
  const {result} = renderHook(usePlayer, {wrapper:PlayerProvider});
  expect(result.current.queue).toHaveLength(2);
  act(() => result.current.select({...track, title:'Actualizada'}));
  expect(result.current.current?.title).toBe('Actualizada');
  act(() => result.current.enqueue(track));
  expect(result.current.queue).toHaveLength(2);
  act(() => result.current.move(-1, 0));
  act(() => result.current.move(0, 9));
  act(() => result.current.move(0, 0));
  act(() => result.current.move(0, 1));
  expect(result.current.current?.id).toBe('take-a');
  act(() => result.current.remove('missing'));
  act(() => result.current.remove('b'));
  expect(result.current.current?.id).toBe('take-a');
  act(() => result.current.remove('take-a'));
  expect(result.current.current).toBeNull();
  act(() => {result.current.advance(); result.current.finish(); result.current.step(1); result.current.toggleVariant();});
  expect(result.current.canAdvance).toBe(false);
});

test.each(['{broken', '{}'])('almacenamiento inválido %s deja el reproductor vacío', (saved) => {
 window.localStorage.setItem('music-studio.player.queue', saved);
 render(<PlayerProvider><Harness/></PlayerProvider>);
 expect(screen.getByTestId('queue').textContent).toBe('');
});

test('la selección se ajusta al borrar la pista activa y la variante sin hermana permanece', () => {
 const {result} = renderHook(usePlayer, {wrapper:PlayerProvider});
 act(() => result.current.select({...track, pairId:'solo', variantIndex:0}));
 act(() => result.current.toggleVariant());
 expect(result.current.current?.id).toBe(track.id);
 act(() => result.current.enqueue({...track, id:'second'}));
 act(() => result.current.remove(track.id));
 expect(result.current.current?.id).toBe('second');
 act(() => result.current.finish());
 act(() => result.current.advance());
 expect(result.current.current?.id).toBe('second');
});
