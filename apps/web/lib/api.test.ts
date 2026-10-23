// Dobles de fetch: no son E2E de red.
import {afterEach, expect, test, vi} from 'vitest';
import {getHealth, ApiError} from './api';
afterEach(()=>vi.unstubAllGlobals());
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
