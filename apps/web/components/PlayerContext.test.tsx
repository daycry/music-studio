// @vitest-environment jsdom
import React from 'react';
import {cleanup, fireEvent, render, screen} from '@testing-library/react';
import {afterEach, expect, test} from 'vitest';
import {PlayerProvider, usePlayer, type PlayerTrack} from './PlayerContext';

afterEach(() => {
  cleanup();
  window.localStorage.clear();
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
