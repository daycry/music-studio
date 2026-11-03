// @vitest-environment jsdom
import React from 'react';
import {afterEach, expect, test, vi} from 'vitest';
import {act, cleanup, render, screen} from '@testing-library/react';
import {NextIntlClientProvider} from 'next-intl';
import messages from '../messages/es.json';
import {GenerativeViz} from './GenerativeViz';

afterEach(() => { cleanup(); vi.restoreAllMocks(); vi.unstubAllGlobals(); });

test('dibuja 96 columnas y expone el progreso real', () => {
  const context = {clearRect: vi.fn(), fillRect: vi.fn(), fillStyle: ''};
  vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(context as never);
  render(<NextIntlClientProvider locale="es" messages={messages}><GenerativeViz progress={0.42} /></NextIntlClientProvider>);
  const canvas = screen.getByRole('progressbar', {name: messages.generation.visualization}) as HTMLCanvasElement;
  expect(canvas.dataset.columns).toBe('96');
  expect(canvas.getAttribute('aria-valuenow')).toBe('42');
  expect(context.fillRect).toHaveBeenCalled();
});

test('adopta peaks al terminar sin animacion propia', () => {
  const context = {clearRect: vi.fn(), fillRect: vi.fn(), fillStyle: ''};
  vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(context as never);
  const raf = vi.spyOn(window, 'requestAnimationFrame');
  render(<NextIntlClientProvider locale="es" messages={messages}><GenerativeViz progress={1} peaks={[.1, .8, .4]} reducedMotion /></NextIntlClientProvider>);
  expect(raf).not.toHaveBeenCalled();
  expect(context.fillRect).toHaveBeenCalled();
});

test('CA-3 dibuja cada par min max respecto al cero central', () => {
  const context = {clearRect: vi.fn(), fillRect: vi.fn(), fillStyle: ''};
  vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(context as never);
  render(<NextIntlClientProvider locale="es" messages={messages}><GenerativeViz progress={1} peaks={[-.8, .3, -.2, .9]} columns={2} reducedMotion /></NextIntlClientProvider>);
  expect(context.fillRect.mock.calls[0][1]).toBeCloseTo(33.6);
  expect(context.fillRect.mock.calls[0][3]).toBeCloseTo(52.8);
  expect(context.fillRect.mock.calls[1][1]).toBeCloseTo(4.8);
});

test('interpola solo el progreso recibido y pausa fuera de pantalla', () => {
  const context = {clearRect: vi.fn(), fillRect: vi.fn(), fillStyle: ''};
  vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(context as never);
  const frames = new Map<number, FrameRequestCallback>(); let next = 0;
  vi.spyOn(window, 'requestAnimationFrame').mockImplementation(callback => { frames.set(++next, callback); return next; });
  const cancel = vi.spyOn(window, 'cancelAnimationFrame').mockImplementation(id => { frames.delete(id); });
  let mediaChange: (() => void) | undefined;
  const media = {matches: false, addEventListener: vi.fn((_name, callback) => {mediaChange = callback;}), removeEventListener: vi.fn()};
  vi.stubGlobal('matchMedia', () => media);
  let visibility: IntersectionObserverCallback | undefined;
  const disconnect = vi.fn();
  vi.stubGlobal('IntersectionObserver', class {constructor(callback: IntersectionObserverCallback) {visibility = callback;} observe() {} disconnect = disconnect;});
  const wrap = (progress: number) => <NextIntlClientProvider locale="es" messages={messages}><GenerativeViz progress={progress} /></NextIntlClientProvider>;
  const {rerender, unmount} = render(wrap(.2));
  rerender(wrap(.8));
  for (let time = 1; time < 1800 && frames.size; time += 40) {
    const callbacks = [...frames.values()]; frames.clear(); act(() => callbacks.forEach(callback => callback(time)));
  }
  expect(screen.getByRole('progressbar').getAttribute('aria-valuenow')).toBe('80');
  expect(frames.size).toBe(0);
  rerender(wrap(.9));
  act(() => visibility?.([{isIntersecting: false}] as IntersectionObserverEntry[], {} as IntersectionObserver));
  expect(cancel).toHaveBeenCalled();
  media.matches = true; act(() => mediaChange?.());
  unmount(); expect(disconnect).toHaveBeenCalled(); expect(media.removeEventListener).toHaveBeenCalled();
});
