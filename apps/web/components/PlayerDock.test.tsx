// @vitest-environment jsdom
import React from 'react';
import {act, cleanup, fireEvent, render, screen, waitFor} from '@testing-library/react';
import {afterEach, beforeEach, expect, test, vi} from 'vitest';
import {NextIntlClientProvider} from 'next-intl';
import messages from '../messages/es.json';
import {PlayerDock} from './PlayerDock';
import {PlayerProvider, usePlayer} from './PlayerContext';
import {getTakeAudioBlob} from '../lib/api';
import {StudioShell} from './StudioShell';
import {usePathname} from 'next/navigation';

const push = vi.hoisted(() => vi.fn());
vi.mock('next/navigation', () => ({useRouter: () => ({push}), usePathname: vi.fn(() => '/songs')}));
vi.mock('../lib/api', () => ({getTakeAudioBlob: vi.fn(() => new Promise<Blob>(() => {}))}));
afterEach(cleanup);
beforeEach(() => {
 vi.spyOn(HTMLMediaElement.prototype, 'pause').mockImplementation(() => {});
 vi.spyOn(HTMLMediaElement.prototype, 'play').mockResolvedValue();
});
afterEach(() => push.mockClear());
afterEach(() => {window.localStorage.clear(); vi.restoreAllMocks(); vi.mocked(getTakeAudioBlob).mockReset(); vi.mocked(getTakeAudioBlob).mockImplementation(() => new Promise<Blob>(() => {}));});

test('no usa la URL privada y espera al blob autenticado antes de habilitar Play', async () => {
 let resolve!: (blob: Blob) => void;
 vi.mocked(getTakeAudioBlob).mockReturnValue(new Promise(done => {resolve = done;}));
 vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:authenticated');
 vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => {});
 window.localStorage.setItem('music-studio.player.queue', JSON.stringify([{id:'a', title:'Pista', url:'/api/takes/a/audio', duration_s:10}]));
 const view=render(<NextIntlClientProvider locale="es" messages={messages}><PlayerProvider><PlayerDock/></PlayerProvider></NextIntlClientProvider>);
 expect(view.container.querySelector('audio')?.getAttribute('src')).toBeNull();
 expect((screen.getByRole('button', {name:messages.player.play}) as HTMLButtonElement).disabled).toBe(true);
 await act(async () => resolve(new Blob(['audio'])));
 expect(view.container.querySelector('audio')?.getAttribute('src')).toBe('blob:authenticated');
 expect((screen.getByRole('button', {name:messages.player.play}) as HTMLButtonElement).disabled).toBe(false);
});

test('la misma pista y el audio siguen reproduciéndose entre /songs y /create', async () => {
 vi.mocked(getTakeAudioBlob).mockResolvedValue(new Blob(['audio']));
 vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:persistent');
 vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => {});
 function Select() {const player = usePlayer(); return <button onClick={() => player.select({id:'persist', title:'Persistente', url:'/private', duration_s:30})}>Seleccionar</button>;}
 const tree = (route: string) => <NextIntlClientProvider locale="es" messages={messages}><StudioShell><div key={route}>{route}<Select/></div></StudioShell></NextIntlClientProvider>;
 const view = render(tree('/songs'));
 fireEvent.click(screen.getByRole('button', {name:'Seleccionar'}));
 await waitFor(() => expect((screen.getByRole('button', {name:messages.player.play}) as HTMLButtonElement).disabled).toBe(false));
 fireEvent.click(screen.getByRole('button', {name:messages.player.play}));
 const audio = view.container.querySelector('audio')!;
 audio.currentTime = 12;
 vi.mocked(usePathname).mockReturnValue('/create');
 view.rerender(tree('/create'));
 expect(screen.getByRole('link', {name:messages.nav.create}).getAttribute('aria-current')).toBe('page');
 expect(screen.getByText('Persistente')).toBeTruthy();
 expect(view.container.querySelector('audio')).toBe(audio);
 expect(audio.currentTime).toBe(12);
 expect(screen.getByRole('button', {name:messages.player.pause})).toBeTruthy();
 vi.mocked(usePathname).mockReturnValue('/songs');
 view.rerender(tree('/songs'));
 expect(view.container.querySelector('audio')).toBe(audio);
 expect(getTakeAudioBlob).toHaveBeenCalledTimes(1);
});

test('cancela cargas antiguas, ignora respuestas tardías y revoca blobs al rotar', async () => {
 const loads: {resolve:(blob:Blob)=>void; signal?:AbortSignal}[] = [];
 vi.mocked(getTakeAudioBlob).mockImplementation((_id, signal) => new Promise(resolve => loads.push({resolve, signal})));
 const create = vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:latest');
 const revoke = vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => {});
 window.localStorage.setItem('music-studio.player.queue', JSON.stringify([
  {id:'a', title:'Primera', url:'/private/a', duration_s:10},
  {id:'b', title:'Segunda', url:'/private/b', duration_s:10},
  {id:'c', title:'Tercera', url:'/private/c', duration_s:10},
 ]));
 const view = render(<NextIntlClientProvider locale="es" messages={messages}><PlayerProvider><PlayerDock/></PlayerProvider></NextIntlClientProvider>);
 fireEvent.keyDown(window, {key:' '});
 expect(HTMLMediaElement.prototype.play).not.toHaveBeenCalled();
 fireEvent.click(screen.getByRole('button', {name:messages.player.next}));
 expect(loads[0].signal?.aborted).toBe(true);
 await act(async () => loads[0].resolve(new Blob(['old'])));
 expect(create).not.toHaveBeenCalled();
 await act(async () => loads[1].resolve(new Blob(['latest'])));
 expect(view.container.querySelector('audio')?.getAttribute('src')).toBe('blob:latest');
 fireEvent.click(screen.getByRole('button', {name:messages.player.next}));
 expect(revoke).toHaveBeenCalledWith('blob:latest');
 expect(view.container.querySelector('audio')?.getAttribute('src')).toBeNull();
 await act(async () => loads[2].resolve(new Blob(['final'])));
 view.unmount();
 expect(revoke).toHaveBeenCalledTimes(2);
});

test('explica el fallo autenticado y mantiene Play deshabilitado', async () => {
 vi.mocked(getTakeAudioBlob).mockRejectedValue(new Error('401'));
 window.localStorage.setItem('music-studio.player.queue', JSON.stringify([{id:'error', title:'Error', url:'/private', duration_s:10}]));
 const view = render(<NextIntlClientProvider locale="es" messages={messages}><PlayerProvider><PlayerDock/></PlayerProvider></NextIntlClientProvider>);
 expect((await screen.findByRole('alert')).textContent).toBe(messages.player.audioError);
 expect(view.container.querySelector('audio')?.getAttribute('src')).toBeNull();
 expect((screen.getByRole('button', {name:messages.player.play}) as HTMLButtonElement).disabled).toBe(true);
});

test('los controles sincronizan pausa, búsqueda, cola, orden y eliminación', async () => {
 vi.mocked(getTakeAudioBlob).mockResolvedValue(new Blob(['audio']));
 vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:controls');
 vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => {});
 window.localStorage.setItem('music-studio.player.queue', JSON.stringify([
  {id:'controls-a', title:'Control A', url:'/a', duration_s:30},
  {id:'controls-b', title:'Control B', url:'/b', duration_s:30},
 ]));
 const view=render(<NextIntlClientProvider locale="es" messages={messages}><PlayerProvider><PlayerDock/></PlayerProvider></NextIntlClientProvider>);
 await waitFor(() => expect((screen.getByRole('button', {name:messages.player.play}) as HTMLButtonElement).disabled).toBe(false));
 const audio=view.container.querySelector('audio')!;
 fireEvent.click(screen.getByRole('button', {name:messages.player.play}));
 expect(audio.play).toHaveBeenCalled();
 fireEvent.keyDown(window, {key:' '});
 expect(screen.getByRole('button', {name:messages.player.play})).toBeTruthy();
 fireEvent.change(screen.getByRole('slider'), {target:{value:'14'}});
 expect(audio.currentTime).toBe(14);
 audio.currentTime=8;
 fireEvent.timeUpdate(audio);
 expect((screen.getByRole('slider') as HTMLInputElement).value).toBe('8');
 fireEvent.keyDown(window, {key:'ArrowLeft'});
 expect(audio.currentTime).toBe(3);
 fireEvent.keyDown(window, {key:'ArrowRight'});
 expect(audio.currentTime).toBe(8);
 act(() => window.dispatchEvent(new CustomEvent('studio:seek', {detail:11})));
 expect(audio.currentTime).toBe(11);
 act(() => window.dispatchEvent(new CustomEvent('studio:seek', {detail:NaN})));
 expect(audio.currentTime).toBe(11);
 fireEvent.click(screen.getByRole('button', {name:messages.player.queue}));
 expect(screen.getByRole('complementary', {name:messages.player.queue})).toBeTruthy();
 fireEvent.click(screen.getAllByRole('button', {name:messages.player.moveDown})[0]);
 fireEvent.click(screen.getAllByRole('button', {name:messages.player.moveUp})[1]);
 fireEvent.click(screen.getAllByRole('button', {name:messages.player.remove})[1]);
 expect(view.container.querySelectorAll('.player-queue li')).toHaveLength(1);
 fireEvent.click(screen.getByRole('button', {name:messages.player.help}));
 expect(screen.getByRole('dialog')).toBeTruthy();
 fireEvent.click(screen.getByRole('button', {name:messages.player.help}));
 expect(screen.queryByRole('dialog')).toBeNull();
});
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
