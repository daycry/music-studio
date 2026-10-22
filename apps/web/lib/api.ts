import type {paths} from './generated/api';
export type Health = paths['/health']['get']['responses'][200]['content']['application/json'];
export class ApiError extends Error { constructor(public status: number, public code?: string) { super(code ?? String(status)); } }
export const API_ORIGIN = process.env.NEXT_PUBLIC_API_ORIGIN ?? 'http://127.0.0.1:8000';
export async function getHealth(signal?: AbortSignal): Promise<Health> {
  const path: keyof paths = '/health';
  const response = await fetch(API_ORIGIN + path, {signal, cache:'no-store', headers:{Accept:'application/json'}});
  if (!response.ok) throw new ApiError(response.status);
  const body: unknown = await response.json();
  if (!body || typeof body !== 'object' || !('process' in body) || body.process !== 'server' || !('status' in body) || body.status !== 'running') {
    throw new Error('invalidHealth');
  }
  return {process:body.process, status:body.status};
}

export type GenerationInput = {
  task: 'music.song' | 'music.instrumental';
  lyrics?: string;
  lyrics_declaration?: 'own' | 'assistant' | 'public_domain' | 'licensed';
  style_prompt: string;
  language?: string;
  params?: Record<string, unknown>;
  seed?: number;
  model_id?: string;
  n_outputs: number;
};
export type GenerationResponse = {song_id:string; generation_job_id:string; post_job_id:string; take_ids:string[]; beat_job_ids:string[]};
export type EstimateResponse = {eta_s?: number; vram_mb?: number; cost_eur?: number | null};
export type SystemModelTask = {verified?:boolean; device?:string; params_schema?:{properties?:Record<string, unknown>}; features?:Record<string, {verified?:boolean}>};
export type SystemModel = {id:string; family?:string; version?:string; revision?:string; license?:string; commercial_use?:boolean; provider?:{type?:string}; weights?:Array<{path:string; sha256:string; bytes:number; format:string}>; tasks?:Record<string, SystemModelTask>};
export type SystemInfo = {gpu: {free_mb?: number; total_mb?: number; limit_mb?: number} | null; ram: {free_bytes?: number; total_bytes?: number} | null; queue: {queued?: boolean; blocked?: boolean; running?: boolean}; engines: Array<{state?: string; engine_id?: string; engine_version?: string}>; models?: SystemModel[]; disk?: {free_bytes?: number; total_bytes?: number}};
export type Song = {id:string; title:string; artist:string|null; status:string; style_prompt:string; collection_id?:string|null; master_take_id:string|null; updated_at:string; created_at:string; deleted_at?:string|null; purge_after?:string|null};
export type Collection = {id:string; name:string; cover_artwork_id?:string|null; created_at?:string; updated_at?:string};
export type Take = {id:string; song_id:string; batch_id?:string|null; root_id?:string|null; variant_index?:number; lyrics_version_id?:string|null; status:string; task:string; model_id:string; seed:number|null; params:Record<string, unknown>; duration_s:number|null; rating:number|null; favorite:boolean; label:string|null; error_code:string|null; assets?:Record<string, {url:string; media_type:string; sha256:string}>};
export type LyricsVersion = {id:string; song_id:string; text:string; declaration:string; source:string; sha256:string};
let sessionToken: string | undefined;
async function getSessionToken(): Promise<string> {
  if (sessionToken) return sessionToken;
  const response = await fetch(API_ORIGIN + '/api/session/bootstrap', {method:'POST', credentials:'omit', cache:'no-store', headers:{'X-Studio-Session-Bootstrap':'1'}});
  if (!response.ok) throw new ApiError(response.status);
  const body = await response.json() as {session_token?:unknown};
  if (typeof body.session_token !== 'string') throw new Error('invalidSession');
  sessionToken = body.session_token;
  return sessionToken;
}
export async function createGeneration(input: GenerationInput): Promise<GenerationResponse> {
  const token = await getSessionToken();
  const response = await fetch(API_ORIGIN + '/api/generations', {
    method:'POST', credentials:'omit', cache:'no-store',
    headers:{'Content-Type':'application/json', 'X-Studio-Session-Token':token},
    body:JSON.stringify(input),
  });
  if (response.status === 401) {sessionToken = undefined; throw new ApiError(response.status);}
  if (!response.ok) {
    const error = await response.json().catch(() => ({})) as {code?:string};
    throw new ApiError(response.status, error.code);
  }
  return await response.json() as GenerationResponse;
}
export async function estimateGeneration(input: {task: GenerationInput['task']; model_id: string; params?: Record<string, unknown>; seed?: number; n_outputs: number}): Promise<EstimateResponse> {
  const token = await getSessionToken();
  const response = await fetch(API_ORIGIN + '/api/generations/estimate', {
    method:'POST', credentials:'omit', cache:'no-store',
    headers:{'Content-Type':'application/json', 'X-Studio-Session-Token':token},
    body:JSON.stringify(input),
  });
  if (response.status === 401) {sessionToken = undefined; throw new ApiError(response.status);}
  if (!response.ok) {
    const error = await response.json().catch(() => ({})) as {code?:string};
    throw new ApiError(response.status, error.code);
  }
  return await response.json() as EstimateResponse;
}
export async function getSystemInfo(signal?: AbortSignal): Promise<SystemInfo> {
  const token = await getSessionToken();
  const response = await fetch(API_ORIGIN + '/api/system', {signal, cache:'no-store', headers:{Accept:'application/json', 'X-Studio-Session-Token':token}});
  if (response.status === 401) {sessionToken = undefined; throw new ApiError(response.status);}
  if (!response.ok) throw new ApiError(response.status);
  const body: unknown = await response.json();
  if (!body || typeof body !== 'object' || !('queue' in body) || !('engines' in body) || !Array.isArray(body.engines)) throw new Error('invalidSystemInfo');
  return body as SystemInfo;
}
export async function unloadSystem(): Promise<{freed_mb: number}> {
  const token = await getSessionToken();
  const response = await fetch(API_ORIGIN + '/api/system/unload', {
    method:'POST', cache:'no-store', headers:{Accept:'application/json', 'X-Studio-Session-Token':token},
  });
  if (response.status === 401) {sessionToken = undefined; throw new ApiError(response.status);}
  if (!response.ok) throw new ApiError(response.status);
  const body: unknown = await response.json();
  if (!body || typeof body !== 'object' || !('freed_mb' in body) || typeof body.freed_mb !== 'number') throw new Error('invalidUnload');
  return {freed_mb: body.freed_mb};
}
async function jobAction(jobId: string, action: 'cancel' | 'retry'): Promise<GenerationResponse> {
  const token = await getSessionToken();
  const response = await fetch(`${API_ORIGIN}/api/jobs/${encodeURIComponent(jobId)}/${action}`, {method:'POST', cache:'no-store', headers:{Accept:'application/json', 'X-Studio-Session-Token':token}});
  if (response.status === 401) {sessionToken = undefined; throw new ApiError(response.status);}
  if (!response.ok) throw new ApiError(response.status);
  return await response.json() as GenerationResponse;
}
export function cancelJob(jobId: string) { return jobAction(jobId, 'cancel'); }
export function retryJob(jobId: string) { return jobAction(jobId, 'retry'); }
export async function listSongs(options: {q?: string; cursor?: string; limit?: number; collection_id?: string; status?: string; model_id?: string; favorite?: boolean; tag?: string; updated_after?: string; updated_before?: string} = {}): Promise<{items: Song[]; next: string | null}> {
  const token = await getSessionToken();
  const query = new URLSearchParams();
  if (options.q) query.set('q', options.q);
  if (options.cursor) query.set('cursor', options.cursor);
  if (options.collection_id) query.set('collection_id', options.collection_id);
  if (options.status) query.set('status', options.status);
  if (options.model_id) query.set('model_id', options.model_id);
  if (options.favorite !== undefined) query.set('favorite', String(options.favorite));
  if (options.tag) query.set('tag', options.tag);
  if (options.updated_after) query.set('updated_after', options.updated_after);
  if (options.updated_before) query.set('updated_before', options.updated_before);
  query.set('limit', String(options.limit ?? 24));
  const response = await fetch(`${API_ORIGIN}/api/songs?${query}`, {cache:'no-store', headers:{Accept:'application/json', 'X-Studio-Session-Token':token}});
  if (response.status === 401) {sessionToken = undefined; throw new ApiError(response.status);}
  if (!response.ok) throw new ApiError(response.status);
  return await response.json() as {items: Song[]; next: string | null};
}
export async function listSongTrash(options: {cursor?: string; limit?: number} = {}): Promise<{items: Song[]; next: string | null}> {
  const token = await getSessionToken();
  const query = new URLSearchParams();
  if (options.cursor) query.set('cursor', options.cursor);
  query.set('limit', String(options.limit ?? 24));
  const response = await fetch(`${API_ORIGIN}/api/songs/trash?${query}`, {cache:'no-store', headers:{Accept:'application/json', 'X-Studio-Session-Token':token}});
  if (response.status === 401) {sessionToken = undefined; throw new ApiError(response.status);}
  if (!response.ok) throw new ApiError(response.status);
  return await response.json() as {items: Song[]; next: string | null};
}
export async function listCollections(): Promise<{items: Collection[]}> { return await authedGet('/api/collections') as {items: Collection[]}; }
async function authedMutation(path: string, method: 'POST'|'PATCH', body: unknown): Promise<unknown> {
  const token = await getSessionToken();
  const response = await fetch(API_ORIGIN + path, {method, cache:'no-store', headers:{Accept:'application/json', 'Content-Type':'application/json', 'X-Studio-Session-Token':token}, body:JSON.stringify(body)});
  if (response.status === 401) { sessionToken = undefined; throw new ApiError(response.status); }
  if (!response.ok) throw new ApiError(response.status);
  return response.json();
}
export async function createCollection(name: string) { return await authedMutation('/api/collections', 'POST', {name}) as Collection; }
export async function renameCollection(collectionId: string, name: string) { return await authedMutation(`/api/collections/${encodeURIComponent(collectionId)}`, 'PATCH', {name}) as Collection; }
export async function moveSong(songId: string, collection_id: string | null) { return await authedMutation(`/api/songs/${encodeURIComponent(songId)}`, 'PATCH', {collection_id}) as Song; }
export async function patchTake(takeId: string, changes: {rating?: number|null; favorite?: boolean; label?: string|null}) { return await authedMutation(`/api/takes/${encodeURIComponent(takeId)}`, 'PATCH', changes) as Take; }
export async function setSongMaster(songId: string, take_id: string) { return await authedMutation(`/api/songs/${encodeURIComponent(songId)}/master`, 'POST', {take_id}) as Song; }
export async function deleteSong(songId: string): Promise<void> {
  const token = await getSessionToken();
  const response = await fetch(`${API_ORIGIN}/api/songs/${encodeURIComponent(songId)}`, {method:'DELETE', cache:'no-store', headers:{'X-Studio-Session-Token':token}});
  if (response.status === 401) {sessionToken = undefined; throw new ApiError(response.status);}
  if (!response.ok) throw new ApiError(response.status);
}
export async function restoreSong(songId: string) { return await authedMutation(`/api/songs/${encodeURIComponent(songId)}/restore`, 'POST', {}) as Song; }
export async function purgeSong(songId: string): Promise<void> {
  const token = await getSessionToken();
  const response = await fetch(`${API_ORIGIN}/api/songs/${encodeURIComponent(songId)}/purge`, {method:'POST', cache:'no-store', headers:{'X-Studio-Session-Token':token}});
  if (response.status === 401) {sessionToken = undefined; throw new ApiError(response.status);}
  if (!response.ok) {
    const error = await response.json().catch(() => ({})) as {code?:string};
    throw new ApiError(response.status, error.code);
  }
}
async function authedGet(path: string): Promise<unknown> {
  const token = await getSessionToken();
  const response = await fetch(API_ORIGIN + path, {cache:'no-store', headers:{Accept:'application/json', 'X-Studio-Session-Token':token}});
  if (response.status === 401) {sessionToken = undefined; throw new ApiError(response.status);}
  if (!response.ok) throw new ApiError(response.status);
  return response.json();
}
export async function getSong(songId: string) { return await authedGet(`/api/songs/${encodeURIComponent(songId)}`) as Song; }
export async function listSongTakes(songId: string) { return await authedGet(`/api/songs/${encodeURIComponent(songId)}/takes`) as {items: Take[]}; }
export async function listLyrics(songId: string) { return await authedGet(`/api/songs/${encodeURIComponent(songId)}/lyrics`) as {items: LyricsVersion[]}; }
export async function getTakePeaks(takeId: string) { return await authedGet(`/api/takes/${encodeURIComponent(takeId)}/peaks`) as {data?: number[][][]}; }
export type TakeAnalysis = {id:string; kind:string; analyzer_id?:string; analyzer_version?:string; data: Record<string, unknown>};
export async function getTakeAnalysis(takeId: string) { return await authedGet(`/api/takes/${encodeURIComponent(takeId)}/analysis`) as {items: TakeAnalysis[]}; }
export async function getTakeAssetBlob(takeId: string, role: 'listen'|'master'): Promise<Blob> {
  const token = await getSessionToken();
  const path = role === 'master' ? 'master' : 'audio';
  const response = await fetch(`${API_ORIGIN}/api/takes/${encodeURIComponent(takeId)}/${path}`, {cache:'no-store', headers:{Accept:role === 'master' ? 'audio/flac' : 'audio/mpeg', 'X-Studio-Session-Token':token}});
  if (response.status === 401) { sessionToken = undefined; throw new ApiError(response.status); }
  if (!response.ok) throw new ApiError(response.status);
  return response.blob();
}
export async function getTakeAudioBlob(takeId: string): Promise<Blob> { return getTakeAssetBlob(takeId, 'listen'); }
export async function getTakeMasterBlob(takeId: string): Promise<Blob> { return getTakeAssetBlob(takeId, 'master'); }
export async function downloadTakeAsset(takeId: string, role: 'listen'|'master'): Promise<void> {
  const blob = await getTakeAssetBlob(takeId, role);
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = `${takeId}-${role}.${role === 'master' ? 'flac' : 'mp3'}`;
  anchor.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 0);
}
