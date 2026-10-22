import {expect,test,vi} from 'vitest';
import {EventParser,MAX_FRAME_BYTES,parseCursor} from './event-parser';
const epoch='a'.repeat(32),encoder=new TextEncoder();
test('líneas UTF8 fragmentadas y CRLF/LF preservan datos y heartbeat no entrega',()=>{
 const receive=vi.fn(),p=new EventParser(receive);
 const bytes=encoder.encode(`: keep-alive\r\n\r\nevent: job.delta\r\nid: ${epoch}:3\r\ndata: {"text":\r\ndata: "música 🎵"}\r\n\r\n`);
 for(const byte of bytes)p.push(new Uint8Array([byte]));p.finish();
 expect(receive).toHaveBeenCalledExactlyOnceWith({event:'job.delta',id:`${epoch}:3`,data:{text:'música 🎵'}});
 const message=new EventParser(receive);message.push(encoder.encode('data: {}\n\n'));message.finish();
 expect(receive).toHaveBeenLastCalledWith({event:'message',id:undefined,data:{}});
});
test('cap real64KiB antes append incluyendo comentarios y bytesmultibyte',()=>{
 const p=new EventParser(vi.fn());p.push(encoder.encode(':'+ 'x'.repeat(MAX_FRAME_BYTES-3)+'\n\n'));p.finish();
 const huge=new EventParser(vi.fn());expect(()=>huge.push(encoder.encode('x'.repeat(MAX_FRAME_BYTES+1)))).toThrow('FRAME_LIMIT');
 const unicode=new EventParser(vi.fn());expect(()=>unicode.push(encoder.encode('🎵'.repeat(17000)))).toThrow('FRAME_LIMIT');
});
test.each([`id: ${epoch}:1\nid: ${epoch}:1\ndata: {}\n\n`,'event: x\nevent: y\ndata: {}\n\n','event:\ndata: {}\n\n','retry: 1\n\n','id: nope\n\n','event: x\n\n','data: nope\n\n'])('rechaza campos ambiguos y JSON inválido',wire=>{
 expect(()=>new EventParser(vi.fn()).push(encoder.encode(wire))).toThrow();
});
test('no acepta UTF8 roto ni frame truncado',()=>{
 expect(()=>new EventParser(vi.fn()).push(new Uint8Array([0xff,10]))).toThrow();
 const p=new EventParser(vi.fn());p.push(encoder.encode('data: {}\n'));expect(()=>p.finish()).toThrow('PARTIAL_FRAME');
});
test.each(['','a:1',`${epoch}:0`,`${epoch}:01`,`${epoch}:9007199254740992`,`${epoch}:1\n`])('cursor unsafe o ambiguo se rechaza',value=>expect(()=>parseCursor(value)).toThrow('INVALID_CURSOR'));
test('cursor permite máximoJS seguro',()=>expect(parseCursor(`${epoch}:9007199254740991`)).toEqual({epoch,seq:Number.MAX_SAFE_INTEGER}));
