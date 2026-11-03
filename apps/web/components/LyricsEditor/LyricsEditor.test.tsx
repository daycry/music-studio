// @vitest-environment jsdom
import React from 'react';
import {cleanup, fireEvent, render, screen} from '@testing-library/react';
import {NextIntlClientProvider} from 'next-intl';
import {afterEach, expect, test, vi} from 'vitest';
import {LyricsEditor} from './LyricsEditor';
import messages from '../../messages/es.json';
afterEach(() => { cleanup(); vi.restoreAllMocks(); });
function editor(value: string, disabled = false) {
  const onChange = vi.fn();
  const view = render(<NextIntlClientProvider locale="es" messages={messages}><form><LyricsEditor value={value} onChange={onChange} disabled={disabled} /></form></NextIntlClientProvider>);
  return {onChange, ...view};
}
test('texto libre, negrita válida y etiquetas desconocidas conservan offsets y resumen', () => {
  editor('🎵 prólogo\n**[Verso 2 - suave]**\nLuz y sol\n[Desconocida]\nMás texto');
  const mirror = document.querySelector('.lyrics-mirror')!;
  expect(mirror.textContent).toBe('🎵 prólogo\n**[Verso 2 - suave]**\nLuz y sol\n[Desconocida]\nMás texto');
  expect(mirror.querySelector('mark.invalid-tag')?.textContent).toBe('[Desconocida]\n');
  expect(screen.getByLabelText(messages.create.statsAriaLabel).textContent).toContain('Verso');
});
test('inserta una sección en la selección, conserva resto y enfoca posición siguiente', () => {
  vi.spyOn(window, 'requestAnimationFrame').mockImplementation(callback => { callback(0); return 0; });
  const {onChange} = editor('Una línea');
  const textarea = screen.getByRole('textbox') as HTMLTextAreaElement;
  textarea.setSelectionRange(3, 3);
  fireEvent.click(screen.getByRole('button', {name: '[Chorus]'}));
  expect(onChange).toHaveBeenCalledWith('Una\n[Chorus]\n línea');
  expect(document.activeElement).toBe(textarea);
});
test('teclear actualiza y Ctrl o Meta Enter envía; Enter normal no', () => {
  const {onChange} = editor('');
  const textarea = screen.getByRole('textbox');
  const request = vi.spyOn(HTMLFormElement.prototype, 'requestSubmit').mockImplementation(() => {});
  fireEvent.change(textarea, {target: {value: 'Nueva letra'}});
  expect(onChange).toHaveBeenCalledWith('Nueva letra');
  fireEvent.keyDown(textarea, {key: 'Enter'}); expect(request).not.toHaveBeenCalled();
  fireEvent.keyDown(textarea, {key: 'Enter', ctrlKey: true});
  fireEvent.keyDown(textarea, {key: 'Enter', metaKey: true}); expect(request).toHaveBeenCalledTimes(2);
});
test('deshabilitado conserva letra y bloquea inserción', () => {
  const {onChange} = editor('[Verse]\nHola', true);
  expect(screen.getByRole('textbox').hasAttribute('disabled')).toBe(true);
  fireEvent.click(screen.getByRole('button', {name: '[Verse]'}));
  expect(onChange).not.toHaveBeenCalled();
});
