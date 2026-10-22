import {afterEach,expect,test,vi} from 'vitest';
import {EventSession} from './event-session';
import {EventParser,MAX_FRAME_BYTES} from './event-parser';
const url='http://127.0.0.1:8000/api/events';
const sessions:EventSession[]=[];
const session=()=>{const s=new EventSession();sessions.push(s);return s;};
afterEach(()=>{sessions.splice(0).forEach(s=>s.close());vi.unstubAllGlobals();vi.useRealTimers();});
test.each([null,[],{}, {session_token:'secret!',expires_in_s:1},{session_token:'ok',expires_in_s:0},{session_token:'ok',expires_in_s:28801},{session_token:'ok',expires_in_s:1.5},{session_token:'ok',expires_in_s:1,secret:'private'}])('bootstrap inválido no abre GET ni refleja secreto',async dto=>{
 const fetcher=vi.fn().mockResolvedValue(new Response(JSON.stringify(dto)));vi.stubGlobal('fetch',fetcher);
 await expect(session().open(url)).rejects.toThrow('INVALID_SESSION');expect(fetcher).toHaveBeenCalledTimes(1);
});
test('bootstrap HTTP failure finito y close previo no abre nada',async()=>{
 const f=vi.fn().mockResolvedValue(new Response('',{status:403}));vi.stubGlobal('fetch',f);
 await expect(session().open(url)).rejects.toThrow('BOOTSTRAP_FAILED');
 const s=session();s.close();await expect(s.open(url)).rejects.toThrow('CLOSED');expect(f).toHaveBeenCalledTimes(1);
});
test('close durante bootstrap cancela señal y no retiene credencial ni abre GET',async()=>{
 let complete!:(r:Response)=>void;
 const f=vi.fn().mockImplementation((_url:string,init:RequestInit)=>init.method==='DELETE'?Promise.resolve(new Response(null,{status:204})):new Promise<Response>(resolve=>{complete=resolve;}));vi.stubGlobal('fetch',f);
 const s=session(),pending=s.open(url);s.close();complete(new Response(JSON.stringify({session_token:'private_token',expires_in_s:1})));
 await expect(pending).rejects.toThrow('CLOSED');await Promise.resolve();expect(f).toHaveBeenCalledTimes(2);expect(f.mock.calls[1][1].method).toBe('DELETE');expect(f.mock.calls[0][1].signal!.aborted).toBe(true);
});
test('renovar sólo memoria y token exacto sólo header',async()=>{
 const f=vi.fn().mockImplementation((url:string,init:{method?:string;headers:Record<string,string>})=>Promise.resolve(url.endsWith('bootstrap')?new Response(JSON.stringify({session_token:'private_token',expires_in_s:1})):new Response(null,{status:init.method==='DELETE'?204:200})));vi.stubGlobal('fetch',f);
 const s=session();await s.open(url,'a'.repeat(32)+':1');await s.open(url);await s.renew();await s.open(url);
 expect(f).toHaveBeenCalledTimes(6);expect(f.mock.calls[2][1].method).toBeUndefined();expect(f.mock.calls[3][1].method).toBe('DELETE');expect(f.mock.calls[1][1].headers['Last-Event-ID']).toBe('a'.repeat(32)+':1');
 expect(f.mock.calls.every(([address])=>!String(address).includes('private_token'))).toBe(true);
});
test('reader/timer se libera ante error de callback y stream sin body se rechaza',async()=>{
 const s=session();await expect(s.read(new Response(null),vi.fn())).rejects.toThrow('MISSING_STREAM');
 const cancel=vi.fn(),stream=new ReadableStream<Uint8Array>({start(c){c.enqueue(new Uint8Array([1]));},cancel});
 await expect(s.read(new Response(stream),()=>{throw new Error('local callback');})).rejects.toThrow('local callback');
 expect(cancel).toHaveBeenCalledTimes(1);expect(stream.locked).toBe(false);
});
test('wait cancellable e idle45s no dejan readers o timers',async()=>{
 vi.useFakeTimers();const s=session();const waited=s.wait(1000);s.close();await waited;await s.wait(1000);expect(vi.getTimerCount()).toBe(0);
 const idle=session(),cancel=vi.fn(),stream=new ReadableStream<Uint8Array>({cancel});const read=idle.read(new Response(stream),vi.fn());
 const failure=expect(read).rejects.toThrow('READ_TIMEOUT');await vi.advanceTimersByTimeAsync(45000);await failure;expect(cancel).toHaveBeenCalledTimes(1);expect(idle.stopped).toBe(false);expect(stream.locked).toBe(false);expect(vi.getTimerCount()).toBe(0);
});
test('bootstrap/open/json que no responden terminan y abortan señal en30s',async()=>{
 vi.useFakeTimers();
 for(const slow of ['fetch','json','stream']){
  const signals:AbortSignal[]=[];
  const f=vi.fn().mockImplementation((address:string,init:RequestInit)=>{
   signals.push(init.signal as AbortSignal);
   if(slow==='fetch'||slow==='stream'&&address.endsWith('/events'))return new Promise(()=>{});
   if(slow==='json')return Promise.resolve({ok:true,json:()=>new Promise(()=>{})});
   return Promise.resolve(new Response(JSON.stringify({session_token:'ok',expires_in_s:100})));
  });vi.stubGlobal('fetch',f);
  const s=session(),pending=expect(s.open(url)).rejects.toThrow('OPEN_TIMEOUT');await vi.advanceTimersByTimeAsync(30000);await pending;
  expect(signals.every(signal=>signal.aborted)).toBe(true);expect(s.stopped).toBe(false);
 }
});
test('CLIENT02 cancel pendiente termina lectura con primera causa y retiene teardown desconocido',async()=>{
 vi.useFakeTimers();let release!:()=>void;
 const cancel=vi.fn(()=>new Promise<void>(resolve=>{release=resolve;}));
 const stream=new ReadableStream<Uint8Array>({start(c){c.enqueue(new Uint8Array([1]));},cancel});
 const s=session(),cause=new Error('PARSER_FAILURE');let failure:unknown;
 const reading=s.read(new Response(stream),()=>{throw cause;}).catch(error=>{failure=error;});
 await vi.advanceTimersByTimeAsync(2001);expect(failure).toBe(cause);expect(Reflect.get(s,'cleanupState')).toBe('unknown');expect(stream.locked).toBe(true);expect(vi.getTimerCount()).toBe(0);
 release();await vi.advanceTimersByTimeAsync(0);await reading;expect(Reflect.get(s,'cleanupState')).toBe('confirmed');expect(stream.locked).toBe(false);
});
test('CLIENT04 DELETE401 acredita credencial inactiva sin fingir revocación204',async()=>{
 const f=vi.fn().mockImplementation((address:string,init:RequestInit)=>Promise.resolve(address.endsWith('bootstrap')?new Response(JSON.stringify({session_token:'ok',expires_in_s:100})):init.method==='DELETE'?new Response('',{status:401}):new Response(null)));
 vi.stubGlobal('fetch',f);const s=session();await s.open(url);await s.renew();expect(s.revocationState).toBe('inactive');await s.open(url);expect(f.mock.calls.filter(([address])=>address.endsWith('bootstrap'))).toHaveLength(2);
});
test('CLIENT06 registros then del waiter de abort son acotados con frame válido64KiB fragmentado byte a byte',async()=>{
 const originalRace=Promise.race.bind(Promise);
 const registrations=new Map<Promise<unknown>,number>();
 const race=vi.spyOn(Promise,'race').mockImplementation(values=>{
  const entries=Array.from(values);
  if(entries.length===3&&entries[1] instanceof Promise){
   const pending=entries[1] as Promise<unknown>;
   if(!registrations.has(pending)){
    registrations.set(pending,0);const originalThen=pending.then;
    Object.defineProperty(pending,'then',{value:(...args:Parameters<Promise<unknown>['then']>)=>{
     registrations.set(pending,registrations.get(pending)!+1);return originalThen.apply(pending,args);
    }});
   }
  }
  return originalRace(entries);
 });
 const epoch='a'.repeat(32),job='01ARZ3NDEKTSV4RRFFQ69G5FAV',encoder=new TextEncoder();
 const envelope={id:1,type:'job.delta',ts:'2026-10-08T04:00:00.123Z',data:{job_id:job,text:''}};
 const wire=(text:string)=>`id: ${epoch}:1\nevent: job.delta\ndata: ${JSON.stringify({...envelope,data:{job_id:job,text}})}\n\n`;
 const padding=MAX_FRAME_BYTES-encoder.encode(wire('')).length;
 const bytes=encoder.encode(wire('x'.repeat(padding)));expect(bytes.byteLength).toBe(MAX_FRAME_BYTES);
 const receive=vi.fn(),parser=new EventParser(receive);
 const stream=new ReadableStream<Uint8Array>({start(c){for(const byte of bytes)c.enqueue(new Uint8Array([byte]));c.close();}});
 try{
  await session().read(new Response(stream),chunk=>parser.push(chunk));parser.finish();
  expect(receive).toHaveBeenCalledTimes(1);expect(receive.mock.calls[0][0].data.data.text).toHaveLength(padding);
  expect(Math.max(...registrations.values())).toBeLessThanOrEqual(1);
  expect(stream.locked).toBe(false);
 }finally{race.mockRestore();}
},10000);
