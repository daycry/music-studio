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

