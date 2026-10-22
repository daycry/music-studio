// @vitest-environment jsdom
import React from 'react';
import {fireEvent, render, screen} from '@testing-library/react';
import {NextIntlClientProvider} from 'next-intl';
import {expect, test, vi} from 'vitest';
import messages from '../../messages/es.json';
import CreatePage from './page';

vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('offline')));

test('Crear expone las secciones de letra y los controles avanzados', () => {
  render(
    <NextIntlClientProvider locale="es" messages={messages}>
      <CreatePage />
    </NextIntlClientProvider>,
  );

  fireEvent.click(screen.getByRole('button', {name: '[Verse]'}));
  expect(
    (screen.getByLabelText(messages.create.lyricsLabel) as HTMLTextAreaElement).value,
  ).toContain('[Verse]');
  fireEvent.click(screen.getByText(messages.create.advancedLabel));
  expect(screen.queryByLabelText(messages.create.guidanceScaleLabel)).toBeNull();
  expect(screen.getByLabelText(messages.create.vocalLanguageLabel)).toBeTruthy();
});
