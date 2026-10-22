// @vitest-environment jsdom
import React from 'react';
import {cleanup, render, screen, fireEvent} from '@testing-library/react';
import {afterEach, expect, test, vi} from 'vitest';
import {NextIntlClientProvider} from 'next-intl';
import messages from '../messages/es.json';
import {Waveform} from './Waveform';

const addRegion = vi.fn();
const destroy = vi.fn();
const zoom = vi.fn();
const on = vi.fn();
const create = vi.fn();
afterEach(cleanup);

vi.mock('wavesurfer.js', () => ({
  default: {
    create: (...args: unknown[]) => {
      create(...args);
      return {destroy, getCurrentTime: () => 0, getDuration: () => 2, on, zoom};
    },
  },
}));

vi.mock('wavesurfer.js/dist/plugins/regions.esm.js', () => ({
  default: {create: vi.fn(() => ({addRegion}))},
}));

test('expone seek, zoom y regiones preparadas sobre peaks', () => {
  const onChange = vi.fn();
  render(<NextIntlClientProvider locale="es" messages={messages}><Waveform peaks={[.1, .8]} beats={[.5]} duration_s={2} onChange={onChange}/></NextIntlClientProvider>);
  expect(document.querySelector('[data-regions-ready="true"]')).toBeTruthy();
  const seek = screen.getByLabelText(messages.songDetail.seek);
  fireEvent.change(seek, {target: {value: '0.5'}});
  expect(onChange).toHaveBeenCalledWith(.5);
  const zoom = screen.getByLabelText(messages.songDetail.zoom);
  fireEvent.change(zoom, {target: {value: '2'}});
  expect((zoom as HTMLInputElement).value).toBe('2');
});

test('crea una región bloqueada por cada beat válido', async () => {
  addRegion.mockClear();
  render(<NextIntlClientProvider locale="es" messages={messages}><Waveform peaks={[.1, .8]} beats={[-1, .5, 1.5, 3, Number.NaN]} duration_s={2} /></NextIntlClientProvider>);
  await vi.waitFor(() => expect(addRegion).toHaveBeenCalledTimes(2));
  expect(addRegion).toHaveBeenNthCalledWith(1, expect.objectContaining({start: .5, drag: false, resize: false}));
  expect(addRegion).toHaveBeenNthCalledWith(2, expect.objectContaining({start: 1.5, drag: false, resize: false}));
});

test('no recrea WaveSurfer cuando el seek actualiza al padre', async () => {
  create.mockClear();
  destroy.mockClear();
  function Harness() {
    const [value, setValue] = React.useState(0);
    return <Waveform peaks={[.1, .8]} duration_s={2} value={value} onChange={setValue}/>;
  }
  const view = render(<NextIntlClientProvider locale="es" messages={messages}><Harness/></NextIntlClientProvider>);
  await vi.waitFor(() => expect(create).toHaveBeenCalledTimes(1));
  fireEvent.change(view.getByRole('slider', {name: messages.songDetail.seek}), {target: {value: '0.5'}});
  await vi.waitFor(() => expect(create).toHaveBeenCalledTimes(1));
  expect(destroy).not.toHaveBeenCalled();
});
