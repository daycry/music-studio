import {expect, test, vi} from 'vitest';
import {EventReducer} from './event-reducer';
const epoch='a'.repeat(32),ts='2026-10-08T04:00:00.123Z',job='01ARZ3NDEKTSV4RRFFQ69G5FAV',sid='b'.repeat(32);
const dto={job_id:job,song_id:job,status:'queued',attempt_id:null,stage:null,progress:null,error_code:null};
const common={status:'snapshot',snapshot_id:sid};
const frame=(data:unknown,id?:string)=>({event:'system.status',id,data:{id:1,type:'system.status',ts,data}});
const begin=()=>frame({...common,phase:'begin',reason:'bootstrap',active_count:1,known_count:0,chunk_count:1});
const chunk=()=>frame({...common,phase:'chunk',index:0,jobs:[dto]});
const end=()=>frame({...common,phase:'end',chunk_count:1,cursor:`${epoch}:1`},`${epoch}:1`);
test('snapshot abortado conserva mapa/cursor y completo confirma una sola vez',()=>{
 const notify=vi.fn(),receive=vi.fn(),reducer=new EventReducer(receive,notify);
 reducer.accept(begin());reducer.accept(chunk());
 expect(reducer.cursor).toBeUndefined();expect(notify).not.toHaveBeenCalled();
 reducer.discard();expect(reducer.cursor).toBeUndefined();
 expect(()=>reducer.accept(end())).toThrow();
 reducer.accept(begin());reducer.accept(chunk());reducer.accept(end());
 expect(notify).toHaveBeenCalledExactlyOnceWith([dto]);expect(receive).not.toHaveBeenCalled();
 expect(reducer.cursor).toBe(`${epoch}:1`);
});
test.each([
 {...common,phase:'chunk',index:1,jobs:[dto]},
 {...common,snapshot_id:'c'.repeat(32),phase:'chunk',index:0,jobs:[dto]},
 {...common,phase:'chunk',index:0,jobs:[dto,dto]},
 {...common,phase:'chunk',index:0,jobs:[{...dto,secret:'private'}]},
 {...common,phase:'chunk',index:0,jobs:[{...dto,progress:2}]},
 {...common,phase:'chunk',index:0,jobs:[{...dto,job_id:'foreign'}]},
])('rechaza chunk incoherente sin confirmar cursor',data=>{
 const notify=vi.fn(),r=new EventReducer(vi.fn(),notify);r.accept(begin());
 expect(()=>r.accept(frame(data))).toThrow();expect(r.cursor).toBeUndefined();expect(notify).not.toHaveBeenCalled();
});
test('end exige counts/H/epoch e id SSE concordantes',()=>{
 for(const ending of [frame({...common,phase:'end',chunk_count:0,cursor:`${epoch}:1`},`${epoch}:1`),frame({...common,phase:'end',chunk_count:1,cursor:`${epoch}:2`},`${epoch}:2`),frame({...common,phase:'end',chunk_count:1,cursor:`${epoch}:1`},`${'c'.repeat(32)}:1`)]){
  const r=new EventReducer(vi.fn(),vi.fn());r.accept(begin());r.accept(chunk());expect(()=>r.accept(ending)).toThrow();expect(r.cursor).toBeUndefined();
 }
});
test('todos los tipos públicos reales conservan sobre/fecha y saltos de secuencia',()=>{
 const receive=vi.fn(),r=new EventReducer(receive,vi.fn());
 const variants=[['job.created',{job_id:job,status:'queued'}],['job.stage',{job_id:job,attempt_id:job,song_id:job,stage:'generate',status:'running'}],['job.progress',{job_id:job,fraction:.4}],['job.delta',{job_id:job,text:'literal'}],['job.done',{job_id:job,status:'succeeded'}],['job.failed',{job_id:job,code:'INTERNAL',retryable:true}],['job.cancelled',{job_id:job}],['entity.updated',{type:'take',id:job}],['system.status',{status:'running'}]];
 for(const [i,[type,data]] of variants.entries()){
  const value={id:2*i+1,type,ts,data};r.accept({event:i%2?'message':type as string,id:`${epoch}:${value.id}`,data:value});expect(receive).toHaveBeenLastCalledWith(value);
 }
 expect(receive).toHaveBeenCalledTimes(9);expect(r.cursor).toBe(`${epoch}:17`);
});
test('rechaza engine/private/fechas inexistentes/IDs inseguros antes de entregar',()=>{
 const valid={id:1,type:'job.created',ts,data:{job_id:job}};
 const invalid=[null,[],true,{}, {seq:1,job_id:job,type:'progress',ts,data:{fraction:.4}},
 ...[-1,0,1.5,'1',Number.MAX_SAFE_INTEGER+1,null,Infinity].map(id=>({...valid,id})),
 ...['2026-02-30T04:00:00.123Z','2026-10-08T24:00:00.123Z','2026-10-08T04:00:00.123+00:00','2026-10-08','2026-13-01T00:00:00.000Z','2026-10-08T04:00:00Z',123].map(ts=>({...valid,ts})),
 ...[null,[],42,'private',true,{job_id:job,request:'private'},{job_id:'x'},{job_id:job,status:42}].map(data=>({...valid,data})),{...valid,type:'future'},{...valid,secret:'private'}];
 const receive=vi.fn(),r=new EventReducer(receive,vi.fn());for(const data of invalid)expect(()=>r.accept({event:'message',id:`${epoch}:1`,data})).toThrow();
 expect(receive).not.toHaveBeenCalled();expect(r.cursor).toBeUndefined();
 const maximum={...valid,id:Number.MAX_SAFE_INTEGER,ts:'2024-02-29T23:59:59.999Z'};r.accept({event:'job.created',id:`${epoch}:${maximum.id}`,data:maximum});expect(receive).toHaveBeenCalledExactlyOnceWith(maximum);
});
test.each([
 ['job.stage',{job_id:job,stage:'bad space'}],['job.progress',{job_id:job,fraction:2}],['job.progress',{job_id:job,fraction:NaN}],
 ['job.failed',{job_id:job,retryable:'true'}],['job.delta',{job_id:job,text:42}],['entity.updated',{id:job,type:'future'}],['entity.updated',{id:'x',type:'take'}],['system.status',{status:'private text'}],
])('rechaza datos públicos tipados inválidos %s',(type,data)=>expect(()=>new EventReducer(vi.fn(),vi.fn()).accept({event:type,id:`${epoch}:1`,data:{id:1,type,ts,data}})).toThrow());
test('no admite ID/type contradictorio, duplicado o epoch ajeno',()=>{
 const r=new EventReducer(vi.fn(),vi.fn()),value={id:1,type:'job.done',ts,data:{job_id:job}};
 for(const f of [{event:'job.created',id:`${epoch}:1`,data:value},{event:'job.done',id:`${epoch}:2`,data:value},{event:'job.done',data:value}])expect(()=>r.accept(f)).toThrow();
 r.accept({event:'job.done',id:`${epoch}:1`,data:value});
 expect(()=>r.accept({event:'job.done',id:`${epoch}:1`,data:value})).toThrow();
 expect(()=>r.accept({event:'job.done',id:`${'c'.repeat(32)}:2`,data:{...value,id:2}})).toThrow();
});
test.each([{active_count:1001},{known_count:65},{chunk_count:18},{chunk_count:0},{reason:'unknown'},{snapshot_id:'x'},{private:'secret'}])('begin limita counts/identidad antes staging',change=>{
 const r=new EventReducer(vi.fn(),vi.fn());expect(()=>r.accept(frame({...common,phase:'begin',reason:'bootstrap',active_count:1,known_count:0,chunk_count:1,...change}))).toThrow();expect(r.cursor).toBeUndefined();
});
test('snapshot vacío confirmado y clear de filtro borra cursor y estado',()=>{
 const notify=vi.fn(),r=new EventReducer(vi.fn(),notify);
 r.accept(frame({...common,phase:'begin',reason:'epoch',active_count:0,known_count:0,chunk_count:0}));
 r.accept(frame({...common,phase:'end',chunk_count:0,cursor:`${epoch}:1`},`${epoch}:1`));expect(notify).toHaveBeenCalledExactlyOnceWith([]);r.clear();expect(r.cursor).toBeUndefined();expect(notify).toHaveBeenCalledTimes(2);
});
test('parcial impide eventos normales y conteo activo contradicho no confirma',()=>{
 const r=new EventReducer(vi.fn(),vi.fn());r.accept(begin());
 expect(()=>r.accept({event:'job.done',id:`${epoch}:2`,data:{id:2,type:'job.done',ts,data:{job_id:job}}})).toThrow();
 r.accept(frame({...common,phase:'chunk',index:0,jobs:[{...dto,status:'succeeded'}]}));expect(()=>r.accept(end())).toThrow();expect(r.cursor).toBeUndefined();
});
test('1064 estados en17chunks se sustituyen una sola vez con1000activos64terminales',()=>{
 const notify=vi.fn(),r=new EventReducer(vi.fn(),notify);
 const jobs=Array.from({length:1064},(_,i)=>({...dto,job_id:String(i).padStart(26,'0'),status:i<1000?'running':'succeeded'}));
 r.accept(frame({...common,phase:'begin',reason:'expired',active_count:1000,known_count:64,chunk_count:17}));
 for(let i=0;i<17;i++){r.accept(frame({...common,phase:'chunk',index:i,jobs:jobs.slice(i*64,(i+1)*64)}));expect(notify).not.toHaveBeenCalled();}
 r.accept(frame({...common,phase:'end',chunk_count:17,cursor:`${epoch}:1`},`${epoch}:1`));expect(notify).toHaveBeenCalledExactlyOnceWith(jobs);
});
test('snapshot callback fallido no confirma cursor ni sustituye staging por éxito',()=>{
 const r=new EventReducer(vi.fn(),()=>{throw new Error('local callback');});r.accept(begin());r.accept(chunk());expect(()=>r.accept(end())).toThrow('local callback');expect(r.cursor).toBeUndefined();r.discard();
});
