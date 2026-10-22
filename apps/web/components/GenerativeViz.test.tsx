// @vitest-environment jsdom
import React from 'react';
import {afterEach, expect, test, vi} from 'vitest';
import {render, screen} from '@testing-library/react';
import {NextIntlClientProvider} from 'next-intl';
import messages from '../messages/es.json';
import {GenerativeViz} from './GenerativeViz';

afterEach(() => vi.restoreAllMocks());

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
