// @vitest-environment jsdom
import React from 'react';
import {cleanup, fireEvent, render, screen} from '@testing-library/react';
import {afterEach, expect, test, vi} from 'vitest';
import {NextIntlClientProvider} from 'next-intl';
import messages from '../messages/es.json';
import {CollectionsPanel} from './CollectionsPanel';

afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

test('permite elegir y crear una colección', async () => {
  const fetcher = vi.fn().mockImplementation(async (url:string, options?:RequestInit) => {
    if (String(url).endsWith('/api/session/bootstrap')) return new Response('{"session_token":"collections-session"}');
    if (options?.method === 'POST') return new Response(JSON.stringify({id:'collection-new', name:'Cierres'}), {status:201});
    return new Response(JSON.stringify({items:[{id:'collection-1', name:'Favoritas'}]}));
  });
  vi.stubGlobal('fetch', fetcher);
  render(<NextIntlClientProvider locale="es" messages={messages}><CollectionsPanel selected={null} onSelect={vi.fn()}/></NextIntlClientProvider>);
  fireEvent.click(screen.getByRole('button', {name:messages.collections.open}));
  expect(await screen.findByRole('button', {name:'Favoritas'})).toBeTruthy();
  fireEvent.click(screen.getByRole('button', {name:messages.collections.new}));
  fireEvent.change(screen.getByLabelText(messages.collections.name), {target:{value:'Cierres'}});
  fireEvent.click(screen.getByRole('button', {name:messages.collections.create}));
  expect(await screen.findByText('Cierres')).toBeTruthy();
});
