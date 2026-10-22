// @vitest-environment jsdom
import React from 'react';
import {cleanup, fireEvent, render, screen, waitFor} from '@testing-library/react';
import {afterEach, expect, test, vi} from 'vitest';
import {NextIntlClientProvider} from 'next-intl';
import messages from '../messages/es.json';
import {PlayerDock} from './PlayerDock';
import {PlayerProvider} from './PlayerContext';

const push = vi.hoisted(() => vi.fn());
vi.mock('next/navigation', () => ({useRouter: () => ({push})}));
afterEach(cleanup);
afterEach(() => push.mockClear());
test('explica la ausencia de toma y deshabilita el transporte sin audio inventado',()=>{
 const view=render(<NextIntlClientProvider locale="es" messages={messages}><PlayerProvider><PlayerDock/></PlayerProvider></NextIntlClientProvider>);
 expect(screen.getByText(messages.player.empty)).toBeTruthy();
 expect(screen.getByText(messages.player.reason)).toBeTruthy();
 for(const label of ['previous','play','next','volume','queue'] as const){
  const button=screen.getByRole('button',{name:messages.player[label]}) as HTMLButtonElement;
  expect(button.disabled).toBe(true);
  expect(button.getAttribute('aria-describedby')).toBe('player-reason');
 }
 expect((screen.getByRole('slider',{name:messages.player.seek}) as HTMLInputElement).disabled).toBe(true);
 expect(view.container.querySelector('audio')).toBeNull();
 expect(view.container.querySelector('[role="progressbar"]')).toBeNull();
});



test('abre la hoja de atajos con la tecla de ayuda', async () => {
 const view=render(<NextIntlClientProvider locale="es" messages={messages}><PlayerProvider><PlayerDock/></PlayerProvider></NextIntlClientProvider>);
 fireEvent.keyDown(window, {key: '?'});
 await waitFor(() => expect(screen.getByRole('dialog', {name: messages.player.help})).toBeTruthy());
 view.unmount();
});

test('atajos navegan, cambian variante y pista, y activan el bucle', () => {
 const view=render(<NextIntlClientProvider locale="es" messages={messages}><PlayerProvider><PlayerDock/></PlayerProvider></NextIntlClientProvider>);
 window.localStorage.setItem('music-studio.player.queue', JSON.stringify([
   {id:'take-a', pairId:'batch-1', variantIndex:0, title:'Libre · A', url:'/a', duration_s:10},
   {id:'take-b', pairId:'batch-1', variantIndex:1, title:'Libre · B', url:'/b', duration_s:10},
 ]));
 view.unmount();
 render(<NextIntlClientProvider locale="es" messages={messages}><PlayerProvider><PlayerDock/></PlayerProvider></NextIntlClientProvider>);
 fireEvent.keyDown(window, {key:'v'});
 expect(screen.getByText('Libre · B')).toBeTruthy();
 fireEvent.keyDown(window, {key:'C'});
 fireEvent.keyDown(window, {key:'B'});
 expect(push).toHaveBeenNthCalledWith(1, '/create');
 expect(push).toHaveBeenNthCalledWith(2, '/songs');
 fireEvent.keyDown(window, {key:'L'});
 fireEvent.keyDown(window, {key:'ArrowRight', shiftKey:true});
 expect(screen.getByText('Libre · B')).toBeTruthy();
});

test('el siguiente salta a la variante hermana aunque haya otra pista entre medias', () => {
 const view=render(<NextIntlClientProvider locale="es" messages={messages}><PlayerProvider><PlayerDock/></PlayerProvider></NextIntlClientProvider>);
 window.localStorage.setItem('music-studio.player.queue', JSON.stringify([
   {id:'take-a-next', pairId:'batch-next', variantIndex:0, title:'Libre · A', url:'/a', duration_s:10},
   {id:'other-next', title:'Otra canción', url:'/other', duration_s:10},
   {id:'take-b-next', pairId:'batch-next', variantIndex:1, title:'Libre · B', url:'/b', duration_s:10},
 ]));
 view.unmount();
 render(<NextIntlClientProvider locale="es" messages={messages}><PlayerProvider><PlayerDock/></PlayerProvider></NextIntlClientProvider>);
 fireEvent.click(screen.getByRole('button', {name: messages.player.next}));
 expect(screen.getByText('Libre · B')).toBeTruthy();
});

test('el siguiente mantiene el salto de pareja desde B aunque haya una pista posterior', () => {
 const view=render(<NextIntlClientProvider locale="es" messages={messages}><PlayerProvider><PlayerDock/></PlayerProvider></NextIntlClientProvider>);
 window.localStorage.setItem('music-studio.player.queue', JSON.stringify([
   {id:'take-a-cycle', pairId:'batch-cycle', variantIndex:0, title:'Libre · A', url:'/a', duration_s:10},
   {id:'take-b-cycle', pairId:'batch-cycle', variantIndex:1, title:'Libre · B', url:'/b', duration_s:10},
   {id:'other-cycle', title:'Otra canción', url:'/other', duration_s:10},
 ]));
 view.unmount();
 render(<NextIntlClientProvider locale="es" messages={messages}><PlayerProvider><PlayerDock/></PlayerProvider></NextIntlClientProvider>);
 fireEvent.keyDown(window, {key:'v'});
 fireEvent.click(screen.getByRole('button', {name: messages.player.next}));
 expect(screen.getByText('Libre · A')).toBeTruthy();
});

test('el fin automático de A/B continúa con la siguiente pista después de la pareja', () => {
 const view=render(<NextIntlClientProvider locale="es" messages={messages}><PlayerProvider><PlayerDock/></PlayerProvider></NextIntlClientProvider>);
 window.localStorage.setItem('music-studio.player.queue', JSON.stringify([
   {id:'take-a-ended', pairId:'batch-ended', variantIndex:0, title:'Libre · A', url:'/a', duration_s:10},
   {id:'take-b-ended', pairId:'batch-ended', variantIndex:1, title:'Libre · B', url:'/b', duration_s:10},
   {id:'other-ended', title:'Otra canción', url:'/other', duration_s:10},
 ]));
 view.unmount();
 const rendered=render(<NextIntlClientProvider locale="es" messages={messages}><PlayerProvider><PlayerDock/></PlayerProvider></NextIntlClientProvider>);
 const audio=rendered.container.querySelector('audio');
 if (!audio) throw new Error('audio missing');
 fireEvent.ended(audio);
 expect(screen.getByText('Libre · B')).toBeTruthy();
 fireEvent.ended(rendered.container.querySelector('audio')!);
 expect(screen.getByText('Otra canción')).toBeTruthy();
});

test('no captura atajos dentro de campos editables', () => {
 const view=render(<NextIntlClientProvider locale="es" messages={messages}><PlayerProvider><PlayerDock/></PlayerProvider></NextIntlClientProvider>);
 const input=document.createElement('input'); document.body.appendChild(input); input.focus();
 fireEvent.keyDown(input, {key:'C'});
 fireEvent.keyDown(input, {key:'?'});
 expect(push).not.toHaveBeenCalled();
 expect(screen.queryByRole('dialog', {name: messages.player.help})).toBeNull();
 input.remove(); view.unmount();
});
