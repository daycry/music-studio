// @vitest-environment jsdom
import React from 'react';
import {afterEach, expect, test, vi} from 'vitest';
import {cleanup, render, screen} from '@testing-library/react';
import {NextIntlClientProvider} from 'next-intl';
import messages from '../messages/es.json';
import {GenerationCard} from './GenerationCard';

const job = {job_id: '01K70000000000000000000001', song_id: '01K70000000000000000000002', status: 'failed', attempt_id: null, stage: 'generate', progress: .5, error_code: 'VRAM_EXCEEDED'} as const;
const wrap = (children: React.ReactNode) => <NextIntlClientProvider locale="es" messages={messages}>{children}</NextIntlClientProvider>;
afterEach(cleanup);

test('muestra etapa, error, job y reintento', () => {
  const retry = vi.fn();
  render(wrap(<GenerationCard job={job} variant="A" onRetry={retry} onCancel={vi.fn()} />));
  expect(screen.getByText('A')).toBeTruthy();
  expect(screen.getByRole('alert').textContent).toContain('VRAM_EXCEEDED');
  expect(screen.getByRole('alert').textContent).toContain(job.job_id);
  screen.getByRole('button', {name: messages.generation.retry}).click();
  expect(retry).toHaveBeenCalledOnce();
});

test('permite cancelar un job activo', () => {
  const cancel = vi.fn();
  render(wrap(<GenerationCard job={{...job, status: 'running', error_code: null}} variant="B" onRetry={vi.fn()} onCancel={cancel} />));
  screen.getByRole('button', {name: messages.generation.cancel}).click();
  expect(cancel).toHaveBeenCalledOnce();
});

test('muestra la etapa Modelo cuando el servidor anuncia stage=model', () => {
  render(wrap(<GenerationCard job={{...job, status: 'running', stage: 'model', error_code: null}} variant="A" onRetry={vi.fn()} onCancel={vi.fn()} />));
  const model = screen.getByText(messages.generation.stage.model);
  expect(model.className).toContain('current');
  expect(model.closest('article')?.getAttribute('data-model-loading')).toBe('true');
});

test.each(['loading_model', 'generating', 'decoding', 'post', 'engine_future'])('CA-1 marca una etapa real o desconocida: %s', stage => {
  const {container} = render(wrap(<GenerationCard job={{...job, status: 'running', stage}} variant="A" onRetry={vi.fn()} onCancel={vi.fn()} />));
  expect(container.querySelectorAll('li.current')).toHaveLength(1);
  expect(container.querySelector('li.current')?.getAttribute('data-stage')).toBe(stage === 'engine_future' ? 'unknown' : stage);
});

test('CA-2 generación terminada no es Lista sin take ready', () => {
  render(wrap(<GenerationCard job={{...job, status: 'succeeded'}} variant="A" onRetry={vi.fn()} onCancel={vi.fn()} />));
  expect(screen.queryByText(messages.generation.status.succeeded)).toBeNull();
});
