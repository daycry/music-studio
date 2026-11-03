// @vitest-environment jsdom
import React from 'react';
import {cleanup,fireEvent,render,screen,waitFor,within} from '@testing-library/react';
import {NextIntlClientProvider} from 'next-intl';
import {afterEach,beforeEach,expect,test,vi} from 'vitest';
import messages from '../../../messages/es.json';
import Page from './page';
import * as api from '../../../lib/api';
const select=vi.hoisted(()=>vi.fn());
vi.mock('next/navigation',()=>({useParams:()=>({id:'S'})}));
vi.mock('../../../components/PlayerContext',()=>({usePlayer:()=>({select,enqueue:vi.fn()})}));
vi.mock('../../../components/ProvenancePanel',()=>({ProvenancePanel:()=>null}));
vi.mock('../../../components/Waveform',()=>({Waveform:({peaks,onChange}:{peaks:number[];onChange:(n:number)=>void})=><button onClick={()=>onChange(.5)} data-testid="wave">{JSON.stringify(peaks)}</button>}));
vi.mock('../../../lib/api',async original=>({...await original<typeof import('../../../lib/api')>(),getSong:vi.fn(),listSongTakes:vi.fn(),listLyrics:vi.fn(),getTakePeaks:vi.fn(),getTakeAnalysis:vi.fn(),patchTake:vi.fn(),setSongMaster:vi.fn(),downloadTakeAsset:vi.fn()}));
const take: api.Take={id:'T',song_id:'S',label:'Primera',status:'ready',task:'music.song',rating:null,favorite:false,duration_s:10,params:{},batch_id:null,commercial_use:true,created_at:'2026-11-03',updated_at:'2026-11-03',derivation:'original',error_code:null,job_id:'J',lyrics_version_id:null,model_id:'mock',model_version:'1',root_id:'T',sample_rate:48000,seed:1,variant_index:0,assets:{listen:{url:'/audio',role:'listen',bytes:1,media_type:'audio/mpeg',sha256:'hash'}}};
beforeEach(()=>{
 vi.mocked(api.getSong).mockResolvedValue({id:'S',title:'Canción',status:'draft'} as api.Song);
 vi.mocked(api.listSongTakes).mockResolvedValue({items:[take,{...take,id:'Q',label:'Pendiente',status:'queued'}]});
 vi.mocked(api.listLyrics).mockResolvedValue({items:[]});
 vi.mocked(api.getTakePeaks).mockResolvedValue({data:[[[.1,.2],[.3,.4]],[[.9,.8]]]} as api.Peaks);
 vi.mocked(api.getTakeAnalysis).mockResolvedValue({items:[]});
 vi.mocked(api.patchTake).mockImplementation(async(_,changes)=>({...take,...changes,favorite:changes.favorite ?? take.favorite}));
});
afterEach(()=>{cleanup();vi.resetAllMocks();});
async function mount(){render(<NextIntlClientProvider locale="es" messages={messages}><Page/></NextIntlClientProvider>);await screen.findByText('Canción');return screen.getByText(/^Primera /).closest('li')!;}
test('CA-1 onda usa todos los bins del canal cero y permite seek',async()=>{
 await mount();await waitFor(()=>expect(screen.getByTestId('wave').textContent).toBe('[0.1,0.2,0.3,0.4]'));
 const seek=vi.fn();window.addEventListener('studio:seek',seek);fireEvent.click(screen.getByTestId('wave'));expect(seek.mock.calls[0][0].detail).toBe(5);window.removeEventListener('studio:seek',seek);
});
test('CA-2 valoración permite 1 a 5 y repetir borra con null',async()=>{
 const row=await mount();
 for(const value of [1,2,3,4,5]) expect(within(row).getByRole('button',{name:`Valorar ${value}/5 Primera`})).toBeTruthy();
 const button=within(row).getByRole('button',{name:'Valorar 3/5 Primera'});fireEvent.click(button);
 await waitFor(()=>expect(button.getAttribute('aria-pressed')).toBe('true'));fireEvent.click(button);
 await waitFor(()=>expect(api.patchTake).toHaveBeenLastCalledWith('T',{rating:null}));
});
test('CA-3 valorar conserva reproducción y CA-4 maestro sólo ready muestra errores',async()=>{
 const row=await mount();const pending=screen.getByText(/^Pendiente /).closest('li')!;
 expect((within(pending).getByText(messages.songDetail.masterAction) as HTMLButtonElement).disabled).toBe(true);
 vi.mocked(api.patchTake).mockResolvedValue({...take,rating:2,assets:undefined});
 fireEvent.click(within(row).getByRole('button',{name:'Valorar 2/5 Primera'}));await waitFor(()=>expect(api.patchTake).toHaveBeenCalled());
 fireEvent.click(within(row).getByText(/^Primera /));expect(select).toHaveBeenCalledWith(expect.objectContaining({url:api.API_ORIGIN+'/audio'}));
 vi.mocked(api.setSongMaster).mockRejectedValue(new Error('failed'));fireEvent.click(within(row).getByText(messages.songDetail.masterAction));
 expect(await screen.findByRole('alert')).toBeTruthy();
});
test('errores de valoración y descarga son visibles',async()=>{
 const row=await mount();vi.mocked(api.patchTake).mockRejectedValue(new Error('failed'));fireEvent.click(within(row).getByRole('button',{name:'Valorar 1/5 Primera'}));expect(await screen.findByRole('alert')).toBeTruthy();
 vi.mocked(api.downloadTakeAsset).mockRejectedValue(new Error('failed'));fireEvent.click(within(row).getByText(messages.songDetail.downloadMp3));await screen.findByText(messages.songDetail.downloadError);
 fireEvent.click(within(row).getByText(messages.songDetail.downloadFlac));await waitFor(()=>expect(api.downloadTakeAsset).toHaveBeenLastCalledWith('T','master'));
});

test('maestro listo persiste, favorita conserva audio y letra muestra diferencias',async()=>{
 vi.mocked(api.listLyrics).mockResolvedValue({items:[{id:'L1',text:'antes',source:'manual',declaration:'own'},{id:'L2',text:'despues',source:'manual',declaration:'own'}]} as api.LyricsList);
 vi.mocked(api.getTakeAnalysis).mockResolvedValue({items:[{id:'B',kind:'audio.beats',data:{beats_s:[1,'bad',2],bpm:120}}]});
 vi.mocked(api.setSongMaster).mockResolvedValue({id:'S',title:'Cancion',status:'draft',master_take_id:'T'} as api.Song);
 const row=await mount();fireEvent.click(within(row).getByText(messages.songDetail.favoriteOff));await waitFor(()=>expect(api.patchTake).toHaveBeenCalledWith('T',{favorite:true}));
 fireEvent.click(within(row).getByText(messages.songDetail.masterAction));await waitFor(()=>expect((within(row).getByText(messages.songDetail.masterAction) as HTMLButtonElement).disabled).toBe(true));
 fireEvent.click(within(row).getByText(/^Primera /));expect(select).toHaveBeenCalled();
 fireEvent.click(screen.getByText(messages.songDetail.lyrics));expect(screen.getByText(messages.songDetail.difference)).toBeTruthy();expect(screen.getByText((_,node)=>node?.tagName === 'PRE' && node.textContent === '+ despues'+String.fromCharCode(10)+'- antes')).toBeTruthy();
});
test('carga fallida y peaks no disponibles se muestran sin inventar datos',async()=>{
 vi.mocked(api.getSong).mockRejectedValueOnce(new Error('failed'));render(<NextIntlClientProvider locale="es" messages={messages}><Page/></NextIntlClientProvider>);expect(await screen.findByRole('alert')).toHaveProperty('textContent',messages.songDetail.error);cleanup();
 vi.mocked(api.getTakePeaks).mockRejectedValue(new Error('failed'));await mount();await waitFor(()=>expect(screen.getByTestId('wave').textContent).toBe('[]'));
});

test('sin tomas no inventa onda ni maestro y error de favorita se anuncia',async()=>{
 vi.mocked(api.listSongTakes).mockResolvedValueOnce({items:[]});await mountEmpty();expect(screen.getByTestId('wave').textContent).toBe('[]');cleanup();
 const row=await mount();vi.mocked(api.patchTake).mockRejectedValue(new Error('failed'));fireEvent.click(within(row).getByText(messages.songDetail.favoriteOff));expect(await screen.findByRole('alert')).toBeTruthy();
});
async function mountEmpty(){render(<NextIntlClientProvider locale="es" messages={messages}><Page/></NextIntlClientProvider>);await screen.findByRole('heading',{level:1});}
test('pareja reproducible se encola y puede seleccionarse sin assets locales',async()=>{
 vi.mocked(api.listSongTakes).mockResolvedValue({items:[{...take,batch_id:'B',variant_index:0},{...take,id:'P',label:'Pareja',batch_id:'B',variant_index:1,assets:{listen:{...take.assets!.listen,url:'https://example.test/audio'}}}]});
 const row=await mount();fireEvent.click(within(row).getByText(/^Primera /));fireEvent.click(within(row).getByText(messages.songDetail.pairAction));expect(select).toHaveBeenLastCalledWith(expect.objectContaining({takeId:'P',url:'https://example.test/audio'}));
});

test('toma sin audio disponible se selecciona sin iniciar reproducción',async()=>{
 vi.mocked(api.listSongTakes).mockResolvedValue({items:[{...take,assets:{}}]});await mount();fireEvent.click(screen.getByText(/^Primera /));expect(select).not.toHaveBeenCalled();
});
