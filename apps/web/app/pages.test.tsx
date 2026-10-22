// @vitest-environment jsdom
import React from 'react';
import {cleanup, render, screen, fireEvent, waitFor, act} from '@testing-library/react';
import {renderToString} from 'react-dom/server';
import {afterEach, expect, test, vi} from 'vitest';
import {NextIntlClientProvider} from 'next-intl';
import messages from '../messages/es.json';
import CreatePage from './create/page';
import SongsPage from './songs/page';
import SystemPage from './system/page';
import HomePage from './page';
import * as eventTransport from '../lib/events';
import type {EventSubscription, ServerEvent} from '../lib/events';
vi.mock('next/navigation',()=>({redirect:vi.fn(()=>{throw Error('redirect');})}));
import {redirect} from 'next/navigation';
afterEach(()=>{cleanup();localStorage.clear();vi.unstubAllGlobals();vi.clearAllMocks();});
function wrap(children:React.ReactNode){return <NextIntlClientProvider locale="es" messages={messages}>{children}</NextIntlClientProvider>;}
test('la entrada dirige a Crear',()=>{
 expect(()=>HomePage()).toThrow('redirect');
 expect(redirect).toHaveBeenCalledWith('/create');
});
test('Crear muestra el compositor y Canciones conserva su estado vacio',async()=>{
 vi.stubGlobal('fetch',vi.fn().mockRejectedValue(Error('offline')));
 const view=render(wrap(<CreatePage/>));
 expect(screen.getByRole('heading',{level:1}).textContent).toBe(messages.create.title);
 expect(screen.getByLabelText(messages.create.lyricsLabel)).toBeTruthy();
  expect((screen.getByLabelText(messages.create.variantsLabel) as HTMLSelectElement).value).toBe('2');
 fireEvent.click(screen.getByRole('button',{name:'[Verse]'}));
 expect((screen.getByLabelText(messages.create.lyricsLabel) as HTMLTextAreaElement).value).toContain('[Verse]');
 expect((screen.getByRole('button',{name:messages.create.submit}) as HTMLButtonElement).disabled).toBe(true);
 expect(screen.getByRole('link',{name:messages.create.system}).getAttribute('href')).toBe('/system');
 view.rerender(wrap(<SongsPage/>));
 expect(screen.getByRole('heading',{level:1}).textContent).toBe(messages.songs.title);
 await screen.findByText(messages.songs.unavailable);
 expect(screen.getByRole('button',{name:messages.songs.retryAction})).toBeTruthy();
 expect(view.container.querySelector('audio')).toBeNull();
});

test('Crear suscribe el feed de cada canción conocida', async () => {
 localStorage.clear();
 const songA = '01K70000000000000000000000';
 const songB = '01K70000000000000000000001';
 const jobA = '01K70000000000000000000010';
 const jobB = '01K70000000000000000000011';
 localStorage.setItem('music-studio:generation-feed', JSON.stringify([
   {song_id: songA, job_id: jobA, status: 'running', stage: 'model', progress: 0.2},
   {song_id: songB, job_id: jobB, status: 'running', stage: 'model', progress: 0.4},
 ]));
 vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{"queue":{},"engines":[],"gpu":null,"ram":null,"disk":null,"models":[]}')));
 const subscribe = vi.spyOn(eventTransport, 'subscribeEvents').mockReturnValue(vi.fn() as unknown as EventSubscription);
 render(wrap(<CreatePage/>));
 await waitFor(() => expect(subscribe).toHaveBeenCalledTimes(2));
 expect(subscribe.mock.calls.map(([url]) => String(url))).toEqual(expect.arrayContaining([
   expect.stringContaining(`song_id=${songA}`),
   expect.stringContaining(`song_id=${songB}`),
 ]));
});

test('Crear conserva las suscripciones SSE al recibir progreso', async () => {
 localStorage.clear();
 const songA = '01K70000000000000000000000';
 const songB = '01K70000000000000000000001';
 const jobA = '01K70000000000000000000010';
 const jobB = '01K70000000000000000000011';
 localStorage.setItem('music-studio:generation-feed', JSON.stringify([
   {song_id: songA, job_id: jobA, status: 'running', stage: 'model', progress: 0.2},
   {song_id: songB, job_id: jobB, status: 'running', stage: 'model', progress: 0.4},
 ]));
 vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{"queue":{},"engines":[],"gpu":null,"ram":null,"disk":null,"models":[]}')));
 const receives: Array<(event: ServerEvent) => void> = [];
 const subscribe = vi.spyOn(eventTransport, 'subscribeEvents').mockImplementation((_url, receive) => {
   receives.push(receive);
   return vi.fn() as unknown as EventSubscription;
 });
 render(wrap(<CreatePage/>));
 await waitFor(() => expect(subscribe).toHaveBeenCalledTimes(2));
 act(() => receives[0]?.({id: 1, ts: '2026-10-10T14:00:00Z', type: 'job.progress', data: {job_id: jobA, status: 'running', fraction: 0.7}}));
 await waitFor(() => expect(subscribe).toHaveBeenCalledTimes(2));
});
test('Crear envia letra, declaracion y variantes, y muestra el job',async()=>{
 const fetcher=vi.fn().mockImplementation(async(url:string)=> url.endsWith('/api/session/bootstrap')
   ? new Response('{"session_token":"session-1"}',{status:200})
   : url.endsWith('/api/system')
     ? new Response('{"queue":{},"engines":[],"gpu":null,"ram":null,"disk":null,"models":[{"id":"mock","provider":{"type":"local"},"commercial_use":true,"license":"MIT","tasks":{"music.song":{"verified":true}}}]}')
     : new Response('{"song_id":"song-1","generation_job_id":"job-1","post_job_id":"post-1","take_ids":[],"beat_job_ids":[]}',{status:202}));
 vi.stubGlobal('fetch',fetcher);
 render(wrap(<CreatePage/>));
 fireEvent.change(screen.getByLabelText(messages.create.lyricsLabel),{target:{value:'[Verse]\nUna letra propia'}});
 fireEvent.change(screen.getByLabelText(messages.create.styleLabel),{target:{value:'hip hop luminoso'}});
 fireEvent.click(screen.getByLabelText(messages.create.declarationOwn));
 fireEvent.change(screen.getByLabelText(messages.create.variantsLabel),{target:{value:'2'}});
 await waitFor(()=>expect(fetcher.mock.calls.some(([url])=>String(url).endsWith('/api/system'))).toBe(true));
 fireEvent.click(screen.getByRole('button',{name:messages.create.submit}));
 await screen.findByText(messages.create.queued);
 const generationCall=fetcher.mock.calls.find(([url])=>String(url).endsWith('/api/generations'));
 expect(generationCall).toBeTruthy();
 if (!generationCall) throw new Error('generation request missing');
 const body=JSON.parse(generationCall[1].body as string);
 expect(body).toMatchObject({task:'music.song',model_id:'mock',lyrics:'[Verse]\nUna letra propia',lyrics_declaration:'own',n_outputs:2});
 expect(screen.getByRole('status').textContent).toContain('job-1');
 expect(JSON.parse(localStorage.getItem('music-studio:generation-feed') ?? '[]')[0].job_id).toBe('job-1');
});
test('Crear instrumental conserva la letra visible pero la omite en la peticion',async()=>{
 const fetcher=vi.fn().mockImplementation(async(url:string)=> String(url).endsWith('/api/session/bootstrap')
   ? new Response('{"session_token":"session-2"}',{status:200})
   : new Response('{"song_id":"song-2","generation_job_id":"job-2","post_job_id":"post-2","take_ids":[],"beat_job_ids":[]}',{status:202}));
 vi.stubGlobal('fetch',fetcher);
 render(wrap(<CreatePage/>));
 const lyrics=screen.getByLabelText(messages.create.lyricsLabel);
 fireEvent.change(lyrics,{target:{value:'Borrador que conservo'}});
 fireEvent.change(screen.getByLabelText(messages.create.styleLabel),{target:{value:'hip hop luminoso'}});
 fireEvent.click(screen.getByLabelText(messages.create.instrumentalLabel));
 fireEvent.click(screen.getByRole('button',{name:messages.create.submit}));
 await screen.findByText(messages.create.queued);
 const generationCall=fetcher.mock.calls.find(([url])=>String(url).endsWith('/api/generations'));
 if (!generationCall) throw new Error('generation request missing');
 const body=JSON.parse(generationCall[1].body as string);
 expect(body.task).toBe('music.instrumental');
 expect(body).not.toHaveProperty('lyrics');
 expect((lyrics as HTMLTextAreaElement).value).toBe('Borrador que conservo');
});
test('Crear envia los controles avanzados declarados por ACE-Step',async()=>{
 const fetcher=vi.fn().mockImplementation(async(url:string)=> {
   if(String(url).endsWith('/api/session/bootstrap')) return new Response('{"session_token":"session-advanced"}');
   if(String(url).endsWith('/api/generations/estimate')) return new Response('{"eta_s":12}');
   return new Response('{"song_id":"song-advanced","generation_job_id":"job-advanced","post_job_id":"post-advanced","take_ids":[],"beat_job_ids":[]}',{status:202});
 });
 vi.stubGlobal('fetch',fetcher);
 render(wrap(<CreatePage/>));
 fireEvent.change(screen.getByLabelText(messages.create.lyricsLabel),{target:{value:'[Verse]\nUna letra'}});
 fireEvent.change(screen.getByLabelText(messages.create.styleLabel),{target:{value:'hip hop luminoso'}});
 fireEvent.click(screen.getByLabelText(messages.create.declarationOwn));
 fireEvent.click(screen.getByText(messages.create.advancedLabel));
 fireEvent.change(screen.getByLabelText(messages.create.languageLabel),{target:{value:'en'}});
 fireEvent.change(screen.getByLabelText(messages.create.vocalLanguageLabel),{target:{value:'es'}});
 fireEvent.change(screen.getByLabelText(messages.create.shiftLabel),{target:{value:'2'}});
 expect(screen.queryByLabelText(messages.create.guidanceScaleLabel)).toBeNull();
 fireEvent.click(screen.getByRole('button',{name:messages.create.submit}));
 await screen.findByText(messages.create.queued);
 const estimateCall=fetcher.mock.calls.find(([url])=>String(url).endsWith('/api/generations/estimate'));
 const generationCall=fetcher.mock.calls.find(([url])=>String(url).endsWith('/api/generations'));
 expect(estimateCall).toBeTruthy();
 expect(generationCall).toBeTruthy();
 if (!estimateCall || !generationCall) throw new Error('generation calls missing');
 expect(JSON.parse(estimateCall[1].body as string)).toMatchObject({model_id:'ace-step-1.5-turbo'});
 expect(JSON.parse(estimateCall[1].body as string).params).toMatchObject({lyrics:'[Verse]\nUna letra',language:'en',vocal_language:'es',shift:2});
 expect('guidance_scale' in JSON.parse(estimateCall[1].body as string).params).toBe(false);
 expect(JSON.parse(generationCall[1].body as string)).toMatchObject({model_id:'ace-step-1.5-turbo'});
 expect(JSON.parse(generationCall[1].body as string).params).toMatchObject({language:'en',vocal_language:'es',shift:2});
 expect('guidance_scale' in JSON.parse(generationCall[1].body as string).params).toBe(false);
});
test('Crear respeta el esquema y las features verificadas del modelo seleccionado',async()=>{
 const fetcher=vi.fn().mockImplementation(async(url:string)=> {
   if(String(url).endsWith('/api/session/bootstrap')) return new Response('{"session_token":"session-schema"}');
   if(String(url).endsWith('/api/system')) return new Response(JSON.stringify({queue:{},engines:[],gpu:null,ram:null,disk:null,models:[{id:'mock',provider:{type:'local'},commercial_use:true,license:'MIT',tasks:{'music.song':{verified:true,params_schema:{properties:{style:{},duration_s:{},lyrics:{},language:{},inference_steps:{type:'integer',minimum:1,maximum:8}}},features:{}}}}]}));
   if(String(url).endsWith('/api/generations/estimate')) return new Response('{"eta_s":3}');
   return new Response('{"song_id":"song-schema","generation_job_id":"job-schema","post_job_id":"post-schema","take_ids":[],"beat_job_ids":[]}',{status:202});
 });
 vi.stubGlobal('fetch',fetcher);
 render(wrap(<CreatePage/>));
 fireEvent.change(screen.getByLabelText(messages.create.lyricsLabel),{target:{value:'[Verse]\nUna letra'}});
 fireEvent.change(screen.getByLabelText(messages.create.styleLabel),{target:{value:'hip hop'}});
 fireEvent.click(screen.getByLabelText(messages.create.declarationOwn));
 await waitFor(()=>expect(fetcher.mock.calls.some(([url])=>String(url).endsWith('/api/system'))).toBe(true));
 fireEvent.click(screen.getByText(messages.create.advancedLabel));
 expect(screen.queryByLabelText(messages.create.guidanceScaleLabel)).toBeNull();
 expect(screen.queryByLabelText(messages.create.bpmLabel)).toBeNull();
 fireEvent.change(screen.getByLabelText(messages.create.stepsLabel),{target:{value:'99'}});
 expect((screen.getByRole('button',{name:messages.create.submit}) as HTMLButtonElement).disabled).toBe(true);
 expect(screen.getByText(messages.create.advancedInvalid)).toBeTruthy();
 fireEvent.change(screen.getByLabelText(messages.create.stepsLabel),{target:{value:'8'}});
 fireEvent.click(screen.getByRole('button',{name:messages.create.submit}));
 await screen.findByText(messages.create.queued);
 const generationCall=fetcher.mock.calls.find(([url])=>String(url).endsWith('/api/generations'));
 if (!generationCall) throw new Error('generation request missing');
 const params=JSON.parse(generationCall[1].body as string).params;
 expect(params).toMatchObject({style:'hip hop',duration_s:180,lyrics:'[Verse]\nUna letra',language:'es'});
 expect('guidance_scale' in params).toBe(false);
 expect('bpm' in params).toBe(false);
});
test('Crear actualiza el estado de cola y GPU mientras permanece abierto', async () => {
  vi.useFakeTimers();
  let systemReads = 0;
  const fetcher = vi.fn().mockImplementation(async (url: string) => {
    if (url.endsWith('/api/session/bootstrap')) return new Response('{"session_token":"session-status"}');
    if (url.endsWith('/api/system')) {
      systemReads += 1;
      return new Response(JSON.stringify({
        queue: {queued: systemReads > 1, running: systemReads > 1},
        engines: [{state: 'idle'}],
        gpu: systemReads > 1 ? {free_mb: 100, total_mb: 12000} : {free_mb: 12000, total_mb: 12000},
        ram: null, disk: null, models: [],
      }));
    }
    return new Response('{"process":"server","status":"running"}');
  });
  vi.stubGlobal('fetch', fetcher);
  render(wrap(<CreatePage/>));
  await act(async () => { await Promise.resolve(); await Promise.resolve(); });
  expect(screen.getByText(/Cola: 0 en espera/)).toBeTruthy();
  await act(async () => { await vi.advanceTimersByTimeAsync(5000); });
  expect(screen.getByText(/Cola: 1 en espera/)).toBeTruthy();
  vi.useRealTimers();
});
test('Canciones conserva el estado de error si la biblioteca no responde',async()=>{
 vi.stubGlobal('fetch',vi.fn().mockRejectedValue(Error('offline')));
 render(wrap(<SongsPage/>));
 expect(screen.getByRole('heading',{level:1}).textContent).toBe(messages.songs.title);
 await screen.findByText(messages.songs.unavailable);
});
test('Biblioteca permite buscar y cambiar entre cuadrícula y lista',async()=>{
 const fetcher=vi.fn().mockImplementation(async(url:string)=>String(url).endsWith('/api/session/bootstrap')
   ? new Response('{"session_token":"songs-session"}')
   : new Response(JSON.stringify({items:[{id:'01K70000000000000000000001',title:'Libre',artist:null,status:'draft',style_prompt:'hip hop',master_take_id:null,updated_at:'2026-01-01T00:00:00Z',created_at:'2026-01-01T00:00:00Z'}],next:null})));
 vi.stubGlobal('fetch',fetcher);
 render(wrap(<SongsPage/>));
 await screen.findByRole('link',{name:'Libre'});
 fireEvent.click(screen.getByRole('button',{name:messages.songs.list}));
 expect(screen.getByRole('button',{name:messages.songs.list}).getAttribute('aria-pressed')).toBe('true');
 fireEvent.change(screen.getByLabelText(messages.songs.searchLabel),{target:{value:'Libre'}});
 fireEvent.click(screen.getByRole('button',{name:messages.songs.search}));
 await waitFor(()=>expect(fetcher.mock.calls.some(([url])=>String(url).includes('q=Libre'))).toBe(true));
});
test('Biblioteca abre la papelera y restaura una canciÃ³n',async()=>{
 const fetcher=vi.fn().mockImplementation(async(url:string, options?:RequestInit)=>{
   if (url.endsWith('/api/session/bootstrap')) return new Response('{"session_token":"songs-session"}');
   if (url.includes('/api/songs/trash')) return new Response(JSON.stringify({items:[{id:'01K70000000000000000000001',title:'Archivada',artist:null,status:'draft',style_prompt:'',master_take_id:null,deleted_at:'2026-01-01T00:00:00Z',purge_after:'2026-01-31T00:00:00Z',updated_at:'2026-01-01T00:00:00Z',created_at:'2026-01-01T00:00:00Z'}],next:null}));
   if (options?.method === 'POST') return new Response(JSON.stringify({id:'01K70000000000000000000001',title:'Archivada'}));
   return new Response(JSON.stringify({items:[],next:null}));
 });
 vi.stubGlobal('fetch',fetcher);
 render(wrap(<SongsPage/>));
 await screen.findByRole('button',{name:messages.songs.openTrash});
 fireEvent.click(screen.getByRole('button',{name:messages.songs.openTrash}));
 await screen.findByText('Archivada');
 fireEvent.click(screen.getByRole('button',{name:messages.songs.restore}));
 await waitFor(()=>expect(fetcher.mock.calls.some(([url, options])=>String(url).includes('/restore') && options?.method === 'POST')).toBe(true));
});
test('Biblioteca muestra miniatura de generación y permite desactivar preescucha',async()=>{
 const fetcher=vi.fn().mockImplementation(async(url:string)=>String(url).endsWith('/api/session/bootstrap')
   ? new Response('{"session_token":"songs-session"}')
   : new Response(JSON.stringify({items:[{id:'01K70000000000000000000001',title:'En curso',artist:null,status:'in_progress',style_prompt:'',master_take_id:'take-1',updated_at:'2026-01-01T00:00:00Z',created_at:'2026-01-01T00:00:00Z'}],next:null})));
 vi.stubGlobal('fetch',fetcher);
 render(wrap(<SongsPage/>));
 await screen.findByText('En curso');
 expect(screen.getByRole('progressbar')).toBeTruthy();
 const toggle=screen.getByRole('button',{name:messages.songs.disablePreview});
 fireEvent.click(toggle);
 expect(screen.getByRole('button',{name:messages.songs.enablePreview})).toBeTruthy();
});
test('Sistema consulta desde el navegador, muestra respuesta real y permite actualizar',async()=>{
 const fetcher=vi.fn().mockImplementation(async()=>new Response(JSON.stringify({process:'server',status:'running'})));
 vi.stubGlobal('fetch',fetcher);
 const html=renderToString(wrap(<SystemPage/>));
 expect(html).toContain(messages.system.loading);
 expect(fetcher).not.toHaveBeenCalled();
 const view=render(wrap(<SystemPage/>));
 expect((screen.getByRole('button',{name:messages.system.refresh}) as HTMLButtonElement).disabled).toBe(true);
 await screen.findByText(messages.system.ready);
 expect(fetcher).toHaveBeenCalledTimes(2);
 expect(screen.getByText(messages.system.noTelemetry)).toBeTruthy();
 fireEvent.click(screen.getByRole('button',{name:messages.system.refresh}));
 await waitFor(()=>expect(fetcher).toHaveBeenCalledTimes(4));
 await screen.findByText(messages.system.ready);
 const signal=fetcher.mock.calls.find(([, options]) => options?.signal)?.[1].signal as AbortSignal;
 view.unmount();expect(signal.aborted).toBe(true);
});
test('Sistema permite descargar el modelo de la VRAM y refresca las mediciones',async()=>{
 const fetcher=vi.fn().mockImplementation(async(url:string)=> {
   if (url.endsWith('/api/session/bootstrap')) return new Response('{"session_token":"system-session"}');
   if (url.endsWith('/api/system/unload')) return new Response('{"freed_mb":128}');
   if (url.endsWith('/api/system')) return new Response(JSON.stringify({queue:{},engines:[],gpu:null,ram:null,disk:null,models:[]}));
   return new Response('{"process":"server","status":"running"}');
 });
 vi.stubGlobal('fetch',fetcher);
 render(wrap(<SystemPage/>));
 await screen.findByText(messages.system.ready);
 const unload=screen.getByRole('button',{name:messages.system.unload});
 expect((unload as HTMLButtonElement).disabled).toBe(false);
 fireEvent.click(unload);
 await screen.findByText(messages.system.unloaded.replace('{freed}','128'));
 expect(fetcher.mock.calls.some(([url, options])=>String(url).endsWith('/api/system/unload') && options?.method === 'POST')).toBe(true);
});test('Sistema conserva error visible y reintenta sin inventar telemetría',async()=>{
 vi.stubGlobal('fetch',vi.fn().mockRejectedValueOnce(Error('offline')).mockResolvedValueOnce(new Response('{"process":"server","status":"running"}')));
 render(wrap(<SystemPage/>));
 expect((await screen.findByRole('alert')).textContent).toBe(messages.system.error);
 fireEvent.click(screen.getByRole('button',{name:messages.system.refresh}));
 await screen.findByText(messages.system.ready);
 expect(screen.queryByRole('alert')).toBeNull();
 expect(screen.queryByRole('progressbar')).toBeNull();
});
test('Sistema ignora respuestas tardías y rechazos tras desmontar',async()=>{
 let resolve!:(r:Response)=>void;
 let reject!:(e:Error)=>void;
 vi.stubGlobal('fetch',vi.fn(()=>new Promise<Response>(r=>{resolve=r;})));
 let view=render(wrap(<SystemPage/>));expect(fetch).toHaveBeenCalledTimes(1);view.unmount();
 resolve(new Response('{"process":"server","status":"running"}'));await Promise.resolve();
 vi.stubGlobal('fetch',vi.fn(()=>new Promise<Response>((_,r)=>{reject=r;})));
 view=render(wrap(<SystemPage/>));view.unmount();
 reject(Error('late'));await Promise.resolve();
 expect(screen.queryByText(messages.system.ready)).toBeNull();
});
