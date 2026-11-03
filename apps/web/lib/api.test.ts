// Dobles de fetch: no son E2E de red.
import {afterEach, expect, test, vi} from 'vitest';
import {getHealth, ApiError} from './api';
afterEach(()=>vi.unstubAllGlobals());

test('envío conserva code y detail de problem+json incluso con sesión expirada', async () => {
 const {createGeneration} = await import('./api');
 for (const status of [422, 401]) {
  vi.stubGlobal('fetch', vi.fn().mockImplementation(async (url: string) => String(url).endsWith('/api/session/bootstrap') ? new Response('{"session_token":"t"}') : new Response(JSON.stringify({code: 'RIGHTS_REQUIRED', detail: 'Declara tus derechos.'}), {status})));
  await expect(createGeneration({task:'music.song', style_prompt:'pop', n_outputs:1})).rejects.toMatchObject({status, code:'RIGHTS_REQUIRED', message:'Declara tus derechos.'});
 }
});

test('audio propaga AbortSignal hasta fetch para cancelar la carga anterior', async () => {
 const {getTakeAudioBlob} = await import('./api');
 const signal = new AbortController().signal;
 const fetcher = vi.fn().mockImplementation(async (url: string) => String(url).endsWith('/api/session/bootstrap') ? new Response('{"session_token":"t"}') : new Response('audio'));
 vi.stubGlobal('fetch', fetcher);
 await getTakeAudioBlob('TAKE', signal);
 expect(fetcher).toHaveBeenCalledWith(expect.stringContaining('/api/takes/TAKE/audio'), expect.objectContaining({signal}));
});
test('consulta el contrato health directamente con cancelación', async()=>{
 const signal=new AbortController().signal;
 const fetcher=vi.fn().mockResolvedValue(new Response(JSON.stringify({process:'server',status:'running'})));
 vi.stubGlobal('fetch',fetcher);
 expect(await getHealth(signal)).toEqual({process:'server',status:'running'});
 expect(fetcher).toHaveBeenCalledWith('http://127.0.0.1:8000/health',{signal,cache:'no-store',headers:{Accept:'application/json'}});
});
test('conserva el estado HTTP y rechaza respuestas inválidas',async()=>{
 vi.stubGlobal('fetch',vi.fn().mockResolvedValue(new Response('{}',{status:403})));
 await expect(getHealth()).rejects.toMatchObject({status:403});
 expect(new ApiError(500)).toBeInstanceOf(Error);
 vi.stubGlobal('fetch',vi.fn().mockResolvedValue(new Response('{"status":"idle","process":"other"}')));
 await expect(getHealth()).rejects.toThrow();
 vi.stubGlobal('fetch',vi.fn().mockResolvedValue(new Response('null')));
 await expect(getHealth()).rejects.toThrow();
});
test('propaga fallos de transporte y abortos sin simular éxito',async()=>{
 const error=new DOMException('aborted','AbortError');
 vi.stubGlobal('fetch',vi.fn().mockRejectedValue(error));
 await expect(getHealth()).rejects.toBe(error);
});

test('createGeneration, estimate y reintento validan la forma de la respuesta del contrato', async()=>{
 const reply=(body:unknown,status=200)=>vi.fn().mockImplementation(async(url:string)=>String(url).endsWith('/api/session/bootstrap')?new Response('{"session_token":"t","expires_in_s":60}'):new Response(JSON.stringify(body),{status}));
 const {createGeneration,estimateGeneration,retryJob,cancelJob,taskParamProperties,isFeatureVerified}=await import('./api');
 vi.stubGlobal('fetch',reply({song_id:'S',generation_job_id:'G',post_job_id:'P',take_ids:['T'],beat_job_ids:[]},202));
 expect((await createGeneration({task:'music.song',style_prompt:'',n_outputs:1})).generation_job_id).toBe('G');
 vi.stubGlobal('fetch',reply({generation_job_id:'G'},202));
 await expect(createGeneration({task:'music.song',style_prompt:'',n_outputs:1})).rejects.toThrow('invalidGeneration');
 vi.stubGlobal('fetch',reply({eta_s:3,vram_mb:100}));
 expect(await estimateGeneration({task:'music.song',model_id:'m'})).toEqual({eta_s:3,vram_mb:100});
 vi.stubGlobal('fetch',reply({eta_s:'x'}));
 await expect(estimateGeneration({task:'music.song',model_id:'m'})).rejects.toThrow('invalidEstimate');
 vi.stubGlobal('fetch',reply({job_id:'J',cancel_requested:true},202));
 expect(await cancelJob('J')).toEqual({job_id:'J',cancel_requested:true});
 vi.stubGlobal('fetch',reply({generation_job_id:'G2',post_job_id:'P2',take_ids:[],beat_job_ids:[]},202));
 expect((await retryJob('J')).generation_job_id).toBe('G2');
 vi.stubGlobal('fetch',reply(null,202));
 await expect(retryJob('J')).rejects.toThrow('invalidJobAction');
 const task={verified:true,features:{a:{verified:false},b:'x'},params_schema:{properties:{p:{type:'number'},q:3}}};
 expect(taskParamProperties(task)).toEqual({p:{type:'number'}});
 expect(taskParamProperties(undefined)).toBeUndefined();
 expect(isFeatureVerified(task,'a')).toBe(false);
 expect(isFeatureVerified(task,'b')).toBeUndefined();
});
test('cancel y retry rechazan cuerpos con forma inválida',async()=>{
 const reply=(body:unknown)=>vi.fn().mockImplementation(async(url:string)=>String(url).endsWith('/api/session/bootstrap')?new Response('{"session_token":"t","expires_in_s":60}'):new Response(JSON.stringify(body),{status:202}));
 const {cancelJob,retryJob}=await import('./api');
 vi.stubGlobal('fetch',reply({generation_job_id:'G',post_job_id:'P',take_ids:'x',beat_job_ids:[]}));
 await expect(retryJob('J')).rejects.toThrow('invalidJobAction');
 vi.stubGlobal('fetch',reply({job_id:'J'}));
 await expect(cancelJob('J')).rejects.toThrow('invalidJobAction');
});

test('acciones de trabajo conservan errores 409 y 503 del servidor', async()=>{
 const {cancelJob,retryJob}=await import('./api');
 for(const [action,status] of [[cancelJob,409],[retryJob,503]] as const){
  vi.stubGlobal('fetch',vi.fn().mockImplementation(async(url:string)=>String(url).endsWith('/api/session/bootstrap')?new Response('{"session_token":"t"}'):new Response(JSON.stringify({code:'JOB_BUSY',detail:'Espera al trabajo activo.'}),{status})));
  await expect(action('J')).rejects.toMatchObject({status,code:'JOB_BUSY',message:'Espera al trabajo activo.'});
 }
});

test('descarga autenticada pide attachment y respeta nombre RFC5987 y fallback seguro',async()=>{
 const {downloadTakeAsset}=await import('./api');
 const click=vi.fn();const anchor={href:'',download:'',click};
 vi.stubGlobal('document',{createElement:()=>anchor});vi.stubGlobal('window',{setTimeout:(fn:()=>void)=>fn()});
 const create=vi.spyOn(URL,'createObjectURL').mockReturnValue('blob:test');const revoke=vi.spyOn(URL,'revokeObjectURL').mockImplementation(()=>{});
 try {
  for(const [disposition,expected] of [["attachment; filename=\"fallback.mp3\"; filename*=UTF-8''Canci%C3%B3n%20final.mp3",'Canci\u00f3n final.mp3'],['attachment; filename="../safe.mp3"','safe.mp3'],["attachment; filename*=UTF-8''bad%ZZ; filename=\"fallback.flac\"",'fallback.flac'],['attachment','T-master.flac']] as const){
   const fetcher=vi.fn().mockImplementation(async(url:string)=>String(url).endsWith('/api/session/bootstrap')?new Response('{"session_token":"t"}'):new Response('audio',{headers:{'Content-Disposition':disposition}}));vi.stubGlobal('fetch',fetcher);
   await downloadTakeAsset('T','master');expect(anchor.download).toBe(expected);
   expect(fetcher).toHaveBeenCalledWith(expect.stringContaining('/api/takes/T/master?download=1'),expect.objectContaining({headers:expect.objectContaining({'X-Studio-Session-Token':'t'})}));
  }
  expect(click).toHaveBeenCalledTimes(4);expect(revoke).toHaveBeenCalledWith('blob:test');
 }finally{create.mockRestore();revoke.mockRestore();}
});

test('PATCH take y maestro conservan errores de dominio',async()=>{
 const {patchTake,setSongMaster}=await import('./api');
 vi.stubGlobal('fetch',vi.fn().mockImplementation(async(url:string)=>String(url).endsWith('/api/session/bootstrap')?new Response('{"session_token":"t"}'):new Response(JSON.stringify({code:'INVALID_PARAMS',detail:'La toma no esta lista.'}),{status:422})));
 await expect(patchTake('T',{rating:null})).rejects.toMatchObject({code:'INVALID_PARAMS',message:'La toma no esta lista.'});
 await expect(setSongMaster('S','T')).rejects.toMatchObject({code:'INVALID_PARAMS',message:'La toma no esta lista.'});
});

async function freshApi(body:unknown = {}, status=200) {
 vi.resetModules();
 const fetcher=vi.fn().mockImplementation(async(url:string)=>String(url).endsWith('/api/session/bootstrap') ? new Response('{"session_token":"session-fresh"}') : new Response(JSON.stringify(body),{status}));
 vi.stubGlobal('fetch',fetcher);
 return {api:await import('./api'),fetcher};
}
test('lecturas de biblioteca codifican IDs y transmiten sesion y filtros sin perder false',async()=>{
 const {api,fetcher}=await freshApi({items:[]});
 await api.listSongs({q:'pop & rock',cursor:'C+',limit:7,collection_id:'A/B',status:'final',model_id:'mock',favorite:false,tag:'uno dos',updated_after:'2026-01-01',updated_before:'2027-01-01'});
 const request=new URL(fetcher.mock.calls.at(-1)![0]);
 expect(Object.fromEntries(request.searchParams)).toEqual({q:'pop & rock',cursor:'C+',limit:'7',collection_id:'A/B',status:'final',model_id:'mock',favorite:'false',tag:'uno dos',updated_after:'2026-01-01',updated_before:'2027-01-01'});
 await api.listSongs();expect(new URL(fetcher.mock.calls.at(-1)![0]).searchParams.get('limit')).toBe('24');
 await api.listSongTrash({cursor:'C+',limit:8});expect(fetcher.mock.calls.at(-1)![0]).toContain('/api/songs/trash?cursor=C%2B&limit=8');
 await api.listSongTrash();expect(fetcher.mock.calls.at(-1)![0]).toContain('limit=24');
 for(const [read,path] of [[()=>api.getSong('A/B'),'/api/songs/A%2FB'],[()=>api.listSongTakes('A/B'),'/api/songs/A%2FB/takes'],[()=>api.listLyrics('A/B'),'/api/songs/A%2FB/lyrics'],[()=>api.getTakePeaks('A/B'),'/api/takes/A%2FB/peaks'],[()=>api.getTakeAnalysis('A/B'),'/api/takes/A%2FB/analysis'],[()=>api.listCollections(),'/api/collections']] as const){
  await expect(read()).resolves.toEqual({items:[]});expect(fetcher).toHaveBeenLastCalledWith(expect.stringContaining(path),expect.objectContaining({cache:'no-store',headers:{Accept:'application/json','X-Studio-Session-Token':'session-fresh'}}));
 }
});
test('mutaciones transmiten metodo, ID escapado y cuerpo exacto incluido rating null',async()=>{
 const {api,fetcher}=await freshApi({id:'ok'});
 for(const [invoke,path,method,body] of [[()=>api.createCollection('Coleccion'),'/api/collections','POST',{name:'Coleccion'}],[()=>api.renameCollection('A/B','Nueva'),'/api/collections/A%2FB','PATCH',{name:'Nueva'}],[()=>api.moveSong('A/B',null),'/api/songs/A%2FB','PATCH',{collection_id:null}],[()=>api.patchTake('A/B',{rating:null}),'/api/takes/A%2FB','PATCH',{rating:null}],[()=>api.setSongMaster('A/B','T'),'/api/songs/A%2FB/master','POST',{take_id:'T'}],[()=>api.restoreSong('A/B'),'/api/songs/A%2FB/restore','POST',{}]] as const){
  await expect(invoke()).resolves.toEqual({id:'ok'});expect(fetcher).toHaveBeenLastCalledWith(expect.stringContaining(path),expect.objectContaining({method,body:JSON.stringify(body),headers:expect.objectContaining({'Content-Type':'application/json','X-Studio-Session-Token':'session-fresh'})}));
 }
 await api.deleteSong('A/B');expect(fetcher).toHaveBeenLastCalledWith(expect.stringContaining('/api/songs/A%2FB'),expect.objectContaining({method:'DELETE'}));
 await api.purgeSong('A/B');expect(fetcher).toHaveBeenLastCalledWith(expect.stringContaining('/api/songs/A%2FB/purge'),expect.objectContaining({method:'POST'}));
});
test('sistema valida respuestas reales, conserva señal y descarga master solicita FLAC',async()=>{
 let context=await freshApi({queue:{},engines:[]});const signal=new AbortController().signal;
 await expect(context.api.getSystemInfo(signal)).resolves.toEqual({queue:{},engines:[]});expect(context.fetcher).toHaveBeenLastCalledWith(expect.stringContaining('/api/system'),expect.objectContaining({signal}));
 for(const body of [null,{queue:{},engines:3},{queue:3,engines:[]}]){context=await freshApi(body);await expect(context.api.getSystemInfo()).rejects.toThrow('invalidSystemInfo');}
 context=await freshApi({freed_mb:123});await expect(context.api.unloadSystem()).resolves.toEqual({freed_mb:123});expect(context.fetcher).toHaveBeenLastCalledWith(expect.stringContaining('/api/system/unload'),expect.objectContaining({method:'POST'}));
 for(const body of [null,{freed_mb:'bad'},{}]){context=await freshApi(body);await expect(context.api.unloadSystem()).rejects.toThrow('invalidUnload');}
 context=await freshApi({});expect(await context.api.getTakeMasterBlob('A/B')).toBeInstanceOf(Blob);expect(context.fetcher).toHaveBeenLastCalledWith(expect.stringContaining('/api/takes/A%2FB/master'),expect.objectContaining({headers:expect.objectContaining({Accept:'audio/flac'})}));
});
test('cada familia autenticada propaga 401, renueva sesion y conserva otros estados HTTP',async()=>{
 const actions:((api:typeof import('./api'))=>Promise<unknown>)[]=[a=>a.estimateGeneration({task:'music.song',model_id:'m'}),a=>a.getSystemInfo(),a=>a.unloadSystem(),a=>a.cancelJob('J'),a=>a.listSongs(),a=>a.listSongTrash(),a=>a.patchTake('T',{rating:1}),a=>a.deleteSong('S'),a=>a.purgeSong('S'),a=>a.getSong('S'),a=>a.getTakeAudioBlob('T')];
 for(const action of actions){
  for(const status of [401,403]){
   const {api,fetcher}=await freshApi({code:'FORBIDDEN_SCOPE'},status);
   await expect(action(api)).rejects.toMatchObject({status});
   if(status===401){await expect(action(api)).rejects.toMatchObject({status});expect(fetcher.mock.calls.filter(call=>String(call[0]).endsWith('/api/session/bootstrap'))).toHaveLength(2);}
  }
 }
});
test('bootstrap rechaza error HTTP y credenciales malformadas sin llamar endpoint protegido',async()=>{
 for(const [body,status,expected] of [[{},503,'503'],[{},200,'invalidSession'],[null,200,'invalidSession']] as const){
  vi.resetModules();const api=await import('./api');const fetcher=vi.fn().mockResolvedValue(new Response(JSON.stringify(body),{status}));vi.stubGlobal('fetch',fetcher);
  await expect(api.getSong('S')).rejects.toThrow(expected);expect(fetcher).toHaveBeenCalledTimes(1);expect(fetcher).toHaveBeenCalledWith(expect.stringContaining('/api/session/bootstrap'),expect.objectContaining({method:'POST',credentials:'omit',headers:{'X-Studio-Session-Bootstrap':'1'}}));
 }
});
test('errores no JSON y titulos problem conservan el estado sin ocultar rechazo',async()=>{
 for(const makeBody of [()=>new Response('not json',{status:503}),()=>new Response(JSON.stringify({title:'Servicio ocupado'}),{status:503}),()=>new Response('null',{status:503}),()=>new Response('[]',{status:503}),()=>new Response('"problem"',{status:503})]){
  const {api}=await freshApi();vi.stubGlobal('fetch',vi.fn().mockImplementation(async(url:string)=>String(url).endsWith('/api/session/bootstrap')?new Response('{"session_token":"t"}'):makeBody()));
  for(const action of [()=>api.createGeneration({task:'music.song',style_prompt:'',n_outputs:1}),()=>api.cancelJob('J'),()=>api.patchTake('T',{rating:1}),()=>api.estimateGeneration({task:'music.song',model_id:'m'}),()=>api.purgeSong('S')])await expect(action()).rejects.toMatchObject({status:503});
 }
});
