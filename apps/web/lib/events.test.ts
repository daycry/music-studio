import {afterEach, expect, test, vi} from 'vitest';
import {subscribeEvents} from './events';
const epoch='a'.repeat(32), ts='2026-10-08T04:00:00.123Z', job='01ARZ3NDEKTSV4RRFFQ69G5FAV';
type Init={method?:string;headers:Record<string,string>;signal:AbortSignal};
const event={id:1,type:'job.created',ts,data:{job_id:job,status:'queued'}};
const wire=(value:unknown,id=`${epoch}:1`)=>`event: ${(value as {type:string}).type}\r\n${id?`id: ${id}\r\n`:''}data: ${JSON.stringify(value)}\r\n\r\n`;
const encoder=new TextEncoder(), stops:(()=>void)[]=[];
afterEach(()=>{for(const stop of stops.splice(0)) stop();vi.unstubAllGlobals();vi.useRealTimers();});
function transport(){
 let controller!:ReadableStreamDefaultController<Uint8Array>;
 const stream=new ReadableStream<Uint8Array>({start(c){controller=c;}});
 const response=new Response(stream,{headers:{'Content-Type':'text/event-stream'}});
 const fetcher=vi.fn().mockImplementation((url:string,init:Init)=>Promise.resolve(url.endsWith('bootstrap')?new Response(JSON.stringify({session_token:'private_token',expires_in_s:100})):init.method==='DELETE'?new Response(null,{status:204}):response));
 vi.stubGlobal('fetch',fetcher);
 vi.stubGlobal('EventSource',class {addEventListener(){} close(){}});
 return {fetcher,controller};
}
test('fetch autentica por header y entrega UTF8 fragmentado sin credenciales en URL',async()=>{
 const {fetcher,controller}=transport(),receive=vi.fn();
 stops.push(subscribeEvents('http://127.0.0.1:8000/api/events',receive,{snapshot:vi.fn()}));
 await vi.waitFor(()=>expect(fetcher).toHaveBeenCalledTimes(2));
 expect(fetcher.mock.calls[0][0]).toBe('http://127.0.0.1:8000/api/session/bootstrap');
 expect(fetcher.mock.calls[0][1]).toMatchObject({method:'POST',credentials:'omit',headers:{'X-Studio-Session-Bootstrap':'1'}});
 expect(fetcher.mock.calls[1][1]).toMatchObject({credentials:'omit',headers:{'X-Studio-Session-Token':'private_token'}});
 const delta={...event,type:'job.delta',data:{job_id:job,text:'música 🎵'}};
 for(const byte of encoder.encode(wire(delta)))controller.enqueue(new Uint8Array([byte]));
 await vi.waitFor(()=>expect(receive).toHaveBeenCalledExactlyOnceWith(delta));
});
test('snapshot sólo notifica una sustitución atómica tras end y no entrega chunks',async()=>{
 const {fetcher,controller}=transport(),receive=vi.fn(),snapshot=vi.fn();
 const subscribe=subscribeEvents;
 stops.push(subscribe('http://127.0.0.1:8000/api/events',receive,{snapshot}));
 await vi.waitFor(()=>expect(fetcher).toHaveBeenCalledTimes(2));
 const common={status:'snapshot',snapshot_id:'b'.repeat(32)},control=(data:unknown)=>({id:1,type:'system.status',ts,data});
 controller.enqueue(encoder.encode(wire(control({...common,phase:'begin',reason:'bootstrap',active_count:1,known_count:0,chunk_count:1}),'')));
 controller.enqueue(encoder.encode(wire(control({...common,phase:'chunk',index:0,jobs:[{job_id:job,song_id:job,status:'queued',attempt_id:null,stage:null,progress:null,error_code:null}]}),'')));
 await new Promise(resolve=>setTimeout(resolve,10));
 expect(snapshot).not.toHaveBeenCalled();expect(receive).not.toHaveBeenCalled();
 controller.enqueue(encoder.encode(wire(control({...common,phase:'end',chunk_count:1,cursor:`${epoch}:1`}))));
 await vi.waitFor(()=>expect(snapshot).toHaveBeenCalledTimes(1));
 expect(snapshot.mock.calls[0][0]).toHaveLength(1);expect(receive).not.toHaveBeenCalled();
});
test('rechaza secretos/query/filtros ajenos antes de abrir conexiones',()=>{
 const {fetcher}=transport();
 for(const url of ['https://example.com/api/events','http://user@127.0.0.1:8000/api/events','http://:secret@127.0.0.1:8000/api/events','http://127.0.0.1:8000/api/events#x','http://127.0.0.1:8000/events','http://127.0.0.1:8000/api/events?token=private_token','http://127.0.0.1:8000/api/events?owner_id=x','http://127.0.0.1:8000/api/events?song_id=x',`http://127.0.0.1:8000/api/events?song_id=${job}&song_id=${job}`,`http://127.0.0.1:8000/api/events?known_job_id=${job}&known_job_id=${job}`])expect(()=>subscribeEvents(url,vi.fn(),{snapshot:vi.fn()})).toThrow('INVALID_EVENT_URL');
 expect(fetcher).not.toHaveBeenCalled();
});
test('reconecta con cursor confirmado sin repetir bootstrap y close es idempotente',async()=>{
 vi.useFakeTimers();
 const fetcher=vi.fn().mockResolvedValueOnce(new Response(JSON.stringify({session_token:'private_token',expires_in_s:100})))
 .mockResolvedValueOnce(new Response(encoder.encode(wire(event)),{headers:{'Content-Type':'text/event-stream'}}));
 let controller!:ReadableStreamDefaultController<Uint8Array>;
 const response=new Response(new ReadableStream({start(c){controller=c;}}),{headers:{'Content-Type':'text/event-stream'}});
 fetcher.mockImplementation((_url:string,init:Init)=>Promise.resolve(init.method==='DELETE'?new Response(null,{status:204}):response));
 vi.stubGlobal('fetch',fetcher);const receive=vi.fn(),close=subscribeEvents('http://127.0.0.1:8000/api/events',receive,{snapshot:vi.fn()});stops.push(close);
 await vi.advanceTimersByTimeAsync(300);
 expect(fetcher).toHaveBeenCalledTimes(3);expect(fetcher.mock.calls[2][1].headers['Last-Event-ID']).toBe(`${epoch}:1`);
 expect(receive).toHaveBeenCalledExactlyOnceWith(event);
 close();close();await vi.advanceTimersByTimeAsync(0);expect(()=>controller.enqueue(encoder.encode(wire({...event,id:2},`${epoch}:2`)))).toThrow();
 await vi.advanceTimersByTimeAsync(10000);expect(fetcher).toHaveBeenCalledTimes(4);expect(fetcher.mock.calls[3][1].method).toBe('DELETE');expect(receive).toHaveBeenCalledTimes(1);
});
test('idle reconecta con cursor confirmado y explicitclose cancela su timer',async()=>{
 vi.useFakeTimers();
 const streams:ReadableStream<Uint8Array>[]=[],cancel=vi.fn();
 const f=vi.fn().mockImplementation((url:string,init:Init)=>{
  if(url.endsWith('bootstrap'))return Promise.resolve(new Response(JSON.stringify({session_token:'ok',expires_in_s:100})));
  if(init.method==='DELETE')return Promise.resolve(new Response(null,{status:204}));
  const stream=new ReadableStream<Uint8Array>({start(c){if(!streams.length)c.enqueue(encoder.encode(wire(event)));},cancel});streams.push(stream);
  return Promise.resolve(new Response(stream,{headers:{'Content-Type':'text/event-stream'}}));
 });vi.stubGlobal('fetch',f);const close=subscribeEvents('http://127.0.0.1:8000/api/events',vi.fn(),{snapshot:vi.fn()});stops.push(close);
 await vi.advanceTimersByTimeAsync(45300);expect(f).toHaveBeenCalledTimes(3);expect(f.mock.calls[2][1].headers['Last-Event-ID']).toBe(`${epoch}:1`);expect(cancel).toHaveBeenCalledTimes(1);
 close();await vi.advanceTimersByTimeAsync(100000);expect(f).toHaveBeenCalledTimes(4);expect(f.mock.calls[3][1].method).toBe('DELETE');expect(vi.getTimerCount()).toBe(0);
});
test('callback que falla termina conexión sin retries ni promise unhandled',async()=>{
 vi.useFakeTimers();const cancel=vi.fn();
 const f=vi.fn().mockResolvedValueOnce(new Response(JSON.stringify({session_token:'ok',expires_in_s:100}))).mockImplementation((_url:string,init:Init)=>Promise.resolve(init.method==='DELETE'?new Response(null,{status:204}):new Response(new ReadableStream({start(c){c.enqueue(encoder.encode(wire(event)));},cancel}),{headers:{'Content-Type':'text/event-stream'}})));
 vi.stubGlobal('fetch',f);stops.push(subscribeEvents('http://127.0.0.1:8000/api/events',()=>{throw new Error('private callback error');},{snapshot:vi.fn(),error:()=>{throw new Error('private error handler');}}));
 await vi.advanceTimersByTimeAsync(20000);expect(f).toHaveBeenCalledTimes(3);expect(f.mock.calls[2][1].method).toBe('DELETE');expect(cancel).toHaveBeenCalledTimes(1);expect(vi.getTimerCount()).toBe(0);
});
test.each([401,403,422,503])('estado%d termina finitamente y401 renueva bootstrap sólo una vez',async status=>{
 vi.useFakeTimers();const error=vi.fn();
 const f=vi.fn().mockImplementation((url:string,init:Init)=>Promise.resolve(url.endsWith('bootstrap')?new Response(JSON.stringify({session_token:'ok',expires_in_s:100})):init.method==='DELETE'?new Response(null,{status:204}):new Response('',{status})));
 vi.stubGlobal('fetch',f);stops.push(subscribeEvents('http://127.0.0.1:8000/api/events',vi.fn(),{snapshot:vi.fn(),error}));await vi.advanceTimersByTimeAsync(20000);
 expect(f).toHaveBeenCalledTimes(status===401?6:3);expect(f.mock.calls.filter(([,init])=>init.method==='DELETE')).toHaveLength(status===401?2:1);expect(error).toHaveBeenCalledExactlyOnceWith('EVENT_STREAM_UNAVAILABLE');expect(vi.getTimerCount()).toBe(0);
});
test('errores de red acotan cinco conexiones y no filtran mensajes privados',async()=>{
 vi.useFakeTimers();const error=vi.fn();const f=vi.fn().mockRejectedValue(new Error('private_token http://secret'));vi.stubGlobal('fetch',f);
 stops.push(subscribeEvents('http://127.0.0.1:8000/api/events',vi.fn(),{snapshot:vi.fn(),error}));await vi.advanceTimersByTimeAsync(20000);expect(f).toHaveBeenCalledTimes(5);expect(error).toHaveBeenCalledExactlyOnceWith('EVENT_RETRY_LIMIT');expect(vi.getTimerCount()).toBe(0);
});
test('cambiar filtro cancela conexión anterior y borra mapa/cursor antes del nuevo scope',async()=>{
 vi.useFakeTimers();const snapshot=vi.fn(),cancel=vi.fn();
 const f=vi.fn().mockImplementation((url:string,init:Init)=>{
  if(url.endsWith('bootstrap'))return Promise.resolve(new Response(JSON.stringify({session_token:'ok',expires_in_s:100})));
  if(init.method==='DELETE')return Promise.resolve(new Response(null,{status:204}));
  return Promise.resolve(new Response(new ReadableStream<Uint8Array>({start(c){c.enqueue(encoder.encode(wire(event)));},cancel}),{headers:{'Content-Type':'text/event-stream'}}));
 });vi.stubGlobal('fetch',f);const close=subscribeEvents('http://127.0.0.1:8000/api/events',vi.fn(),{snapshot});stops.push(close);
 await vi.advanceTimersByTimeAsync(0);close.changeScope(`http://127.0.0.1:8000/api/events?song_id=${job}`);
 await vi.advanceTimersByTimeAsync(0);expect(cancel).toHaveBeenCalledTimes(1);expect(snapshot).toHaveBeenCalledExactlyOnceWith([]);
 expect(f).toHaveBeenCalledTimes(3);expect(f.mock.calls[2][0]).toBe(`http://127.0.0.1:8000/api/events?song_id=${job}`);expect(f.mock.calls[2][1].headers).not.toHaveProperty('Last-Event-ID');
 close.changeScope(`http://127.0.0.1:8000/api/events?song_id=${job}`);await vi.advanceTimersByTimeAsync(0);expect(f).toHaveBeenCalledTimes(3);
 close();close.changeScope('http://127.0.0.1:8000/api/events');await vi.advanceTimersByTimeAsync(0);expect(f).toHaveBeenCalledTimes(4);
});
test('snapshot parcial al cortar no avanza LastEventID y replay posterior sigue confirmado',async()=>{
 vi.useFakeTimers();const snapshot=vi.fn(),receive=vi.fn(),common={status:'snapshot',snapshot_id:'b'.repeat(32)};
 const partial=wire(event)+wire({id:2,type:'system.status',ts,data:{...common,phase:'begin',reason:'expired',active_count:1,known_count:0,chunk_count:1}},'');
 const f=vi.fn().mockResolvedValueOnce(new Response(JSON.stringify({session_token:'ok',expires_in_s:100})))
 .mockResolvedValueOnce(new Response(encoder.encode(partial),{headers:{'Content-Type':'text/event-stream'}}))
 .mockResolvedValueOnce(new Response(new ReadableStream<Uint8Array>({start(c){c.enqueue(encoder.encode(wire({...event,id:3},`${epoch}:3`)));}}),{headers:{'Content-Type':'text/event-stream'}}));
 f.mockImplementation((_url:string,init:Init)=>{if(init.method==='DELETE')return Promise.resolve(new Response(null,{status:204}));throw new Error('Unexpected extra GET');});
 vi.stubGlobal('fetch',f);stops.push(subscribeEvents('http://127.0.0.1:8000/api/events',receive,{snapshot}));await vi.advanceTimersByTimeAsync(300);
 expect(f.mock.calls[2][1].headers['Last-Event-ID']).toBe(`${epoch}:1`);expect(snapshot).not.toHaveBeenCalled();expect(receive.mock.calls.map(([value])=>value.id)).toEqual([1,3]);
});
test('límites64known, escape inválido y exceso de query se aplican antes de conexión',async()=>{
 const {fetcher}=transport();const known=Array.from({length:65},(_,i)=>`known_job_id=${String(i).padStart(26,'0')}`);
 for(const query of [known.join('&'),'known_job_id=%GG','song_id=%FF','x='+'a'.repeat(4096)])expect(()=>subscribeEvents('http://127.0.0.1:8000/api/events?'+query,vi.fn(),{snapshot:vi.fn()})).toThrow('INVALID_EVENT_URL');
 expect(fetcher).not.toHaveBeenCalled();stops.push(subscribeEvents('http://127.0.0.1:8000/api/events?'+known.slice(0,64).join('&'),vi.fn(),{snapshot:vi.fn()}));await vi.waitFor(()=>expect(fetcher).toHaveBeenCalledTimes(2));
});
test('HTTPtype/status inválidos y frameJSON inválido terminan en límite sin cursor inventado',async()=>{
 vi.useFakeTimers();
 for(const makeResponse of [()=>new Response('invalid',{status:500}),()=>new Response('invalid',{headers:{'Content-Type':'application/json'}}),()=>new Response('data: bad\n\n',{headers:{'Content-Type':'text/event-stream'}})]){
  const error=vi.fn(),receive=vi.fn();const f=vi.fn().mockImplementation((url:string,init:Init)=>Promise.resolve(url.endsWith('bootstrap')?new Response(JSON.stringify({session_token:'ok',expires_in_s:100})):init.method==='DELETE'?new Response(null,{status:204}):makeResponse()));
  vi.stubGlobal('fetch',f);stops.push(subscribeEvents('http://127.0.0.1:8000/api/events',receive,{snapshot:vi.fn(),error}));await vi.advanceTimersByTimeAsync(20000);
  expect(f).toHaveBeenCalledTimes(7);expect(f.mock.calls[6][1].method).toBe('DELETE');expect(receive).not.toHaveBeenCalled();expect(error).toHaveBeenCalledExactlyOnceWith('EVENT_RETRY_LIMIT');
  for(const [,init] of f.mock.calls)expect(init.headers).not.toHaveProperty('Last-Event-ID');
 }
});
test.each(['receive','snapshot'])('CLIENT01 %s reentrante cambia scope sin reinstalar cursor anterior',async kind=>{
 vi.useFakeTimers();
 const next=`http://127.0.0.1:8000/api/events?song_id=${job}`,common={status:'snapshot',snapshot_id:'b'.repeat(32)};
 const control=(data:unknown)=>({id:1,type:'system.status',ts,data});
 const full=wire(control({...common,phase:'begin',reason:'bootstrap',active_count:1,known_count:0,chunk_count:1}),'')+wire(control({...common,phase:'chunk',index:0,jobs:[{job_id:job,song_id:job,status:'queued',attempt_id:null,stage:null,progress:null,error_code:null}]}),'')+wire(control({...common,phase:'end',chunk_count:1,cursor:`${epoch}:1`}));
 let gets=0;const f=vi.fn().mockImplementation((url:string,init:Init)=>{
  if(url.endsWith('bootstrap'))return Promise.resolve(new Response(JSON.stringify({session_token:'ok',expires_in_s:100})));
  if(init.method==='DELETE')return Promise.resolve(new Response(null,{status:204}));
  gets++;return Promise.resolve(new Response(new ReadableStream<Uint8Array>({start(c){if(gets===1)c.enqueue(encoder.encode(kind==='receive'?wire(event):full));}}),{headers:{'Content-Type':'text/event-stream'}}));
 });vi.stubGlobal('fetch',f);
 const close=subscribeEvents('http://127.0.0.1:8000/api/events',()=>{if(kind==='receive')close.changeScope(next);},{snapshot:jobs=>{if(kind==='snapshot'&&jobs.length)close.changeScope(next);}});stops.push(close);
 await vi.advanceTimersByTimeAsync(0);
 const newGet=f.mock.calls.find(([url])=>url===next);expect(newGet).toBeDefined();expect(newGet![1].headers).not.toHaveProperty('Last-Event-ID');
});
test('CLIENT03 consumidor snapshot explícito es obligatorio antes de bootstrap',()=>{
 const {fetcher}=transport();
 // @ts-expect-error La firma exige consumidor atómico de snapshot.
 expect(()=>subscribeEvents(urlForTest(),vi.fn())).toThrow('SNAPSHOT_CONSUMER_REQUIRED');
 for(const args of [[urlForTest(),vi.fn()],[urlForTest(),vi.fn(),{}],[urlForTest(),vi.fn(),{snapshot:undefined}],[urlForTest(),vi.fn(),{snapshot:'invalid'}]])expect(()=>Reflect.apply(subscribeEvents,null,args)).toThrow('SNAPSHOT_CONSUMER_REQUIRED');
 expect(fetcher).not.toHaveBeenCalled();
});
function urlForTest(){return 'http://127.0.0.1:8000/api/events';}
test('CLIENT04 treinta y cinco scopes comparten credencial y cierre final revoca registro',async()=>{
 vi.useFakeTimers();const records=new Set<string>();let issued=0;
 const f=vi.fn().mockImplementation((url:string,init:RequestInit)=>{
  if(url.endsWith('bootstrap')){if(records.size===32)return Promise.resolve(new Response('',{status:503}));const token=`token_${++issued}`;records.add(token);return Promise.resolve(new Response(JSON.stringify({session_token:token,expires_in_s:28800})));}
  if(init.method==='DELETE'){records.delete((init.headers as Record<string,string>)['X-Studio-Session-Token']);return Promise.resolve(new Response(null,{status:204}));}
  return Promise.resolve(new Response(new ReadableStream<Uint8Array>(),{headers:{'Content-Type':'text/event-stream'}}));
 });vi.stubGlobal('fetch',f);const close=subscribeEvents(urlForTest(),vi.fn(),{snapshot:vi.fn()});stops.push(close);
 await vi.advanceTimersByTimeAsync(0);
 for(let i=0;i<35;i++){const next=`${urlForTest()}?song_id=${String(i).padStart(26,'0')}`;close.changeScope(next);await vi.advanceTimersByTimeAsync(0);expect(f.mock.calls.some(([address])=>address===next)).toBe(true);}
 expect(issued).toBe(1);expect(records.size).toBe(1);close();close();await vi.advanceTimersByTimeAsync(0);expect(records.size).toBe(0);
 const deletes=f.mock.calls.filter(([,init])=>init.method==='DELETE');expect(deletes).toHaveLength(1);expect(deletes[0][0]).toBe('http://127.0.0.1:8000/api/session');expect(deletes[0][1]).toMatchObject({credentials:'omit',headers:{'X-Studio-Session-Token':'token_1'}});
});
test.each(['rejected-response','parser','callback'])('CLIENT02 %s cancel pendiente halt finito sin reconexión y settlement tardío no reabre',async variant=>{
 vi.useFakeTimers();let release!:()=>void;const cancel=vi.fn(()=>new Promise<void>(resolve=>{release=resolve;}));
 const f=vi.fn().mockImplementation((url:string,init:RequestInit)=>{
  if(url.endsWith('bootstrap'))return Promise.resolve(new Response(JSON.stringify({session_token:'ok',expires_in_s:100})));
  if(init.method==='DELETE')return Promise.resolve(new Response(null,{status:204}));
  const stream=new ReadableStream<Uint8Array>({start(c){if(variant!=='rejected-response')c.enqueue(encoder.encode(variant==='parser'?'data: bad\n\n':wire(event)));},cancel});
  return Promise.resolve(new Response(stream,{status:variant==='rejected-response'?403:200,headers:{'Content-Type':'text/event-stream'}}));
 });vi.stubGlobal('fetch',f);const error=vi.fn(),close=subscribeEvents(urlForTest(),()=>{if(variant==='callback')throw new Error('private callback');},{snapshot:vi.fn(),error});stops.push(close);
 await vi.advanceTimersByTimeAsync(2001);expect(error).toHaveBeenCalledWith('EVENT_CANCEL_UNCONFIRMED');expect(Reflect.get(close,'state')).toBe('halted');
 expect(f.mock.calls.filter(([address])=>address.includes('/api/events'))).toHaveLength(1);expect(()=>close.changeScope(`${urlForTest()}?song_id=${job}`)).toThrow('EVENT_SUBSCRIPTION_HALTED');await vi.advanceTimersByTimeAsync(3000);expect(f.mock.calls.filter(([address])=>address.includes('/api/events'))).toHaveLength(1);
 release();await vi.advanceTimersByTimeAsync(0);expect(Reflect.get(close,'state')).toBe('halted');expect(f.mock.calls.filter(([address])=>address.includes('/api/events'))).toHaveLength(1);expect(vi.getTimerCount()).toBe(0);
});
test('CLIENT04 cuarenta reaperturas y cierres no llenan registry32 ni retienen tokens',async()=>{
 vi.useFakeTimers();const records=new Set<string>();let issued=0;
 const f=vi.fn().mockImplementation((url:string,init:RequestInit)=>{
  if(url.endsWith('bootstrap')){if(records.size>=32)return Promise.resolve(new Response('',{status:503}));const token=`token_${++issued}`;records.add(token);return Promise.resolve(new Response(JSON.stringify({session_token:token,expires_in_s:28800})));}
  if(init.method==='DELETE'){records.delete((init.headers as Record<string,string>)['X-Studio-Session-Token']);return Promise.resolve(new Response(null,{status:204}));}
  return Promise.resolve(new Response(new ReadableStream<Uint8Array>(),{headers:{'Content-Type':'text/event-stream'}}));
 });vi.stubGlobal('fetch',f);
 for(let i=0;i<40;i++){const close=subscribeEvents(urlForTest(),vi.fn(),{snapshot:vi.fn()});stops.push(close);await vi.advanceTimersByTimeAsync(0);expect(records.size).toBe(1);close();await vi.advanceTimersByTimeAsync(0);expect(records.size).toBe(0);}
 expect(issued).toBe(40);expect(f.mock.calls.filter(([,init])=>init.method==='DELETE')).toHaveLength(40);
});
test('CLIENT04 revocación sin respuesta se aborta2s y reporta estado no confirmado sin secreto',async()=>{
 vi.useFakeTimers();let revokeSignal!:AbortSignal;const error=vi.fn();
 const f=vi.fn().mockImplementation((url:string,init:RequestInit)=>{
  if(url.endsWith('bootstrap'))return Promise.resolve(new Response(JSON.stringify({session_token:'private_token',expires_in_s:100})));
  if(init.method==='DELETE'){revokeSignal=init.signal as AbortSignal;return new Promise(()=>{});}
  return Promise.resolve(new Response(new ReadableStream<Uint8Array>(),{headers:{'Content-Type':'text/event-stream'}}));
 });vi.stubGlobal('fetch',f);const close=subscribeEvents(urlForTest(),vi.fn(),{snapshot:vi.fn(),error});stops.push(close);await vi.advanceTimersByTimeAsync(0);close();close();await vi.advanceTimersByTimeAsync(2001);
 expect(error).toHaveBeenCalledExactlyOnceWith('EVENT_REVOKE_UNCONFIRMED');expect(revokeSignal.aborted).toBe(true);expect(Reflect.get(close,'state')).toBe('closed');expect(vi.getTimerCount()).toBe(0);
});
test('CLIENT04 revocación fallida sigue observable sin callback error opcional',async()=>{
 vi.useFakeTimers();const f=vi.fn().mockImplementation((url:string,init:Init)=>Promise.resolve(url.endsWith('bootstrap')?new Response(JSON.stringify({session_token:'private_token',expires_in_s:100})):init.method==='DELETE'?new Response('private failure',{status:503}):new Response(new ReadableStream<Uint8Array>(),{headers:{'Content-Type':'text/event-stream'}})));
 vi.stubGlobal('fetch',f);const close=subscribeEvents(urlForTest(),vi.fn(),{snapshot:vi.fn()});stops.push(close);await vi.advanceTimersByTimeAsync(0);close();await vi.advanceTimersByTimeAsync(0);
 expect(Reflect.get(close,'revocationState')).toBe('unknown');expect(close.haltReason).toBe('EVENT_REVOKE_UNCONFIRMED');expect(close.state).toBe('closed');
});
test.each([true,false])('CLIENT05 último401 tras cuatro500 halt observable sin sextoGET (errorconsumer=%s)',async withError=>{
 vi.useFakeTimers();let gets=0;const getSignals:AbortSignal[]=[],error=vi.fn();
 const f=vi.fn().mockImplementation((address:string,init:Init)=>{
  if(address.endsWith('bootstrap'))return Promise.resolve(new Response(JSON.stringify({session_token:'token_one',expires_in_s:100})));
  if(init.method==='DELETE')return Promise.resolve(new Response(null,{status:204}));
  gets++;getSignals.push(init.signal);return Promise.resolve(new Response('failure',{status:gets<=4?500:401}));
 });vi.stubGlobal('fetch',f);
 const close=subscribeEvents(urlForTest(),vi.fn(),{snapshot:vi.fn(),...(withError?{error}:{})});stops.push(close);
 await vi.advanceTimersByTimeAsync(20000);
 expect(close.state).toBe('halted');expect(close.haltReason).toBe('EVENT_RETRY_LIMIT');
 expect(gets).toBe(5);expect(f.mock.calls.filter(([address])=>address.endsWith('bootstrap'))).toHaveLength(1);
 expect(f.mock.calls.filter(([,init])=>init.method==='DELETE')).toHaveLength(1);expect(close.revocationState).toBe('confirmed');
 expect(getSignals.every(signal=>signal.aborted)).toBe(true);expect(vi.getTimerCount()).toBe(0);
 if(withError)expect(error).toHaveBeenCalledExactlyOnceWith('EVENT_RETRY_LIMIT');else expect(error).not.toHaveBeenCalled();
 expect(()=>close.changeScope(`${urlForTest()}?song_id=${job}`)).toThrow('EVENT_SUBSCRIPTION_HALTED');
});
