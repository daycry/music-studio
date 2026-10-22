// @vitest-environment jsdom
import React from 'react';
import {expect, test, vi} from 'vitest';
import {render, screen} from '@testing-library/react';
import {NextIntlClientProvider} from 'next-intl';
import messages from '../messages/es.json';
import {GenerationFeed} from './GenerationFeed';

const base = {song_id: '01K70000000000000000000002', attempt_id: null, stage: 'generate', progress: .2, error_code: null};
test('agrupa variantes por grupo y conserva el orden A/B', () => {
  render(<NextIntlClientProvider locale="es" messages={messages}><GenerationFeed jobs={[
    {...base, job_id: '01K70000000000000000000003', status: 'running', group_id: 'batch-1', variant_index: 1},
    {...base, job_id: '01K70000000000000000000001', status: 'queued', group_id: 'batch-1', variant_index: 0},
  ]} onRetry={vi.fn()} onCancel={vi.fn()} /></NextIntlClientProvider>);
  expect(screen.getByRole('region', {name: messages.generation.feed})).toBeTruthy();
  expect(screen.getByText('A')).toBeTruthy();
  expect(screen.getByText('B')).toBeTruthy();
});
