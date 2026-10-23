import type {components, operations, paths} from './generated/api';
type Schemas = components['schemas'];
type JsonOf<Response> = Response extends {content: {'application/json': infer Body}} ? Body : never;
type Ok<Op extends keyof operations, Status extends 200 | 202 = 200> = operations[Op]['responses'] extends Record<Status, infer Response> ? JsonOf<Response> : never;
export type Health = Schemas['HealthDTO'];
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

export type GenerationInput = Schemas['GenerationCreateDTO'];
export type GenerationResponse = Schemas['GenerationQueuedDTO'];
export type JobRetryResponse = Schemas['JobRetryDTO'];
export type JobCancelResponse = Schemas['JobCancelDTO'];
export type EstimateInput = Schemas['EstimateDTO'];
export type EstimateResponse = Schemas['EstimateResultDTO'];
export type SystemInfo = Schemas['SystemInfoDTO'];
export type SystemModel = Schemas['SystemModelDTO'];
export type SystemModelTask = Schemas['SystemTaskDTO'];
export type SystemEngine = Schemas['SystemEngineDTO'];
export type UnloadResult = Schemas['UnloadResultDTO'];
export type Peaks = Schemas['PeaksDTO'];
export type SessionCredential = Schemas['SessionCredentialDTO'];
export type Song = Ok<'get_song'>;
export type Collection = Ok<'list_collections'>['items'][number];
export type LyricsVersion = Ok<'list_song_lyrics'>['items'][number];
// El esquema OpenAPI de `params` es un objeto libre; openapi-typescript lo emite como Record<string, never>.
export type Take = Omit<Ok<'list_song_takes'>['items'][number], 'params'> & {params: Record<string, unknown>};
export type TakeAsset = NonNullable<Take['assets']>[string];
export type TakeList = {items: Take[]};
export type LyricsList = Ok<'list_song_lyrics'>;
export type TakeChanges = Schemas['TakePatchDTO'];
export type TakeAnalysis = {id:string; kind:string; analyzer_id?:string; analyzer_version?:string; data: Record<string, unknown>};
export type SongList = Ok<'list_songs'>;
// Contrato del cliente: los paths usados existen en el OpenAPI generado.
export const API_PATHS = {
  session: '/api/session/bootstrap', generations: '/api/generations', estimate: '/api/generations/estimate', system: '/api/system', unload: '/api/system/unload',
} as const satisfies Record<string, keyof paths>;
function isObject(value: unknown): value is Record<string, unknown> { return typeof value === 'object' && value !== null && !Array.isArray(value); }
/** Propiedades declaradas por el descriptor para los parámetros de una tarea (valida la forma; el esquema es libre en el contrato). */
export function taskParamProperties(task: SystemModelTask | undefined): Record<string, Record<string, unknown>> | undefined {
  const properties = task?.params_schema?.properties;
  if (!isObject(properties)) return undefined;
  return Object.fromEntries(Object.entries(properties).filter((entry): entry is [string, Record<string, unknown>] => isObject(entry[1])));
}
export function isFeatureVerified(task: SystemModelTask | undefined, name: string): boolean | undefined {
  const feature = task?.features?.[name];
  return isObject(feature) ? feature.verified === true : undefined;
}
function parseObject<T>(body: unknown, strings: readonly string[], error: string): T {
  if (!isObject(body) || strings.some(key => typeof body[key] !== 'string')) throw new Error(error);
  return body as T;
}
let sessionToken: string | undefined;
async function getSessionToken(): Promise<string> {
  if (sessionToken) return sessionToken;
  const response = await fetch(API_ORIGIN + '/api/session/bootstrap', {method:'POST', credentials:'omit', cache:'no-store', headers:{'X-Studio-Session-Bootstrap':'1'}});
  if (!response.ok) throw new ApiError(response.status);
  const body = parseObject<SessionCredential>(await response.json(), ['session_token'], 'invalidSession');
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
    const error: {code?:string} = await response.json().catch(() => ({}));
    throw new ApiError(response.status, error.code);
  }
  return parseObject<GenerationResponse>(await response.json(), ['song_id', 'generation_job_id', 'post_job_id'], 'invalidGeneration');
}
export async function estimateGeneration(input: Omit<EstimateInput, 'timeout_s' | 'n_outputs'> & {n_outputs?: number; timeout_s?: number}): Promise<EstimateResponse> {
  const token = await getSessionToken();
  const response = await fetch(API_ORIGIN + '/api/generations/estimate', {
    method:'POST', credentials:'omit', cache:'no-store',
    headers:{'Content-Type':'application/json', 'X-Studio-Session-Token':token},
    body:JSON.stringify(input),
  });
  if (response.status === 401) {sessionToken = undefined; throw new ApiError(response.status);}
  if (!response.ok) {
    const error: {code?:string} = await response.json().catch(() => ({}));
    throw new ApiError(response.status, error.code);
  }
  const body = await response.json();
  if (!isObject(body) || typeof body.eta_s !== 'number' || typeof body.vram_mb !== 'number') throw new Error('invalidEstimate');
  return body as EstimateResponse;
}
export async function getSystemInfo(signal?: AbortSignal): Promise<SystemInfo> {
  const token = await getSessionToken();
  const response = await fetch(API_ORIGIN + '/api/system', {signal, cache:'no-store', headers:{Accept:'application/json', 'X-Studio-Session-Token':token}});
  if (response.status === 401) {sessionToken = undefined; throw new ApiError(response.status);}
  if (!response.ok) throw new ApiError(response.status);
  const body: unknown = await response.json();
  if (!isObject(body) || !isObject(body.queue) || !Array.isArray(body.engines)) throw new Error('invalidSystemInfo');
  return body as SystemInfo;
}
export async function unloadSystem(): Promise<UnloadResult> {
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
async function jobAction<A extends 'cancel' | 'retry'>(jobId: string, action: A): Promise<A extends 'cancel' ? JobCancelResponse : JobRetryResponse> {
  const token = await getSessionToken();
  const response = await fetch(`${API_ORIGIN}/api/jobs/${encodeURIComponent(jobId)}/${action}`, {method:'POST', cache:'no-store', headers:{Accept:'application/json', 'X-Studio-Session-Token':token}});
  if (response.status === 401) {sessionToken = undefined; throw new ApiError(response.status);}
  if (!response.ok) throw new ApiError(response.status);
  const body: unknown = await response.json();
  const strings = (value: unknown) => Array.isArray(value) && value.every(item => typeof item === 'string');
  const valid = action === 'cancel'
    ? isObject(body) && typeof body.job_id === 'string' && typeof body.cancel_requested === 'boolean'
    : isObject(body) && typeof body.generation_job_id === 'string' && typeof body.post_job_id === 'string' && strings(body.take_ids) && strings(body.beat_job_ids);
  if (!valid) throw new Error('invalidJobAction');
  return body as A extends 'cancel' ? JobCancelResponse : JobRetryResponse;
}
export function cancelJob(jobId: string) { return jobAction(jobId, 'cancel'); }
export function retryJob(jobId: string) { return jobAction(jobId, 'retry'); }
export async function listSongs(options: {q?: string; cursor?: string; limit?: number; collection_id?: string; status?: string; model_id?: string; favorite?: boolean; tag?: string; updated_after?: string; updated_before?: string} = {}): Promise<SongList> {
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
  return await response.json();
}
export async function listSongTrash(options: {cursor?: string; limit?: number} = {}): Promise<SongList> {
  const token = await getSessionToken();
  const query = new URLSearchParams();
  if (options.cursor) query.set('cursor', options.cursor);
  query.set('limit', String(options.limit ?? 24));
  const response = await fetch(`${API_ORIGIN}/api/songs/trash?${query}`, {cache:'no-store', headers:{Accept:'application/json', 'X-Studio-Session-Token':token}});
  if (response.status === 401) {sessionToken = undefined; throw new ApiError(response.status);}
  if (!response.ok) throw new ApiError(response.status);
  return await response.json();
}
export async function listCollections(): Promise<{items: Collection[]}> { return await authedGet('/api/collections'); }
async function authedMutation(path: string, method: 'POST'|'PATCH', body: unknown) {
  const token = await getSessionToken();
  const response = await fetch(API_ORIGIN + path, {method, cache:'no-store', headers:{Accept:'application/json', 'Content-Type':'application/json', 'X-Studio-Session-Token':token}, body:JSON.stringify(body)});
  if (response.status === 401) { sessionToken = undefined; throw new ApiError(response.status); }
  if (!response.ok) throw new ApiError(response.status);
  return await response.json();
}
export async function createCollection(name: string): Promise<Collection> { return await authedMutation('/api/collections', 'POST', {name}); }
export async function renameCollection(collectionId: string, name: string): Promise<Collection> { return await authedMutation(`/api/collections/${encodeURIComponent(collectionId)}`, 'PATCH', {name}); }
export async function moveSong(songId: string, collection_id: string | null): Promise<Song> { return await authedMutation(`/api/songs/${encodeURIComponent(songId)}`, 'PATCH', {collection_id}); }
export async function patchTake(takeId: string, changes: TakeChanges): Promise<Take> { return await authedMutation(`/api/takes/${encodeURIComponent(takeId)}`, 'PATCH', changes); }
export async function setSongMaster(songId: string, take_id: string): Promise<Song> { return await authedMutation(`/api/songs/${encodeURIComponent(songId)}/master`, 'POST', {take_id}); }
export async function deleteSong(songId: string): Promise<void> {
  const token = await getSessionToken();
  const response = await fetch(`${API_ORIGIN}/api/songs/${encodeURIComponent(songId)}`, {method:'DELETE', cache:'no-store', headers:{'X-Studio-Session-Token':token}});
  if (response.status === 401) {sessionToken = undefined; throw new ApiError(response.status);}
  if (!response.ok) throw new ApiError(response.status);
}
export async function restoreSong(songId: string): Promise<Song> { return await authedMutation(`/api/songs/${encodeURIComponent(songId)}/restore`, 'POST', {}); }
export async function purgeSong(songId: string): Promise<void> {
  const token = await getSessionToken();
  const response = await fetch(`${API_ORIGIN}/api/songs/${encodeURIComponent(songId)}/purge`, {method:'POST', cache:'no-store', headers:{'X-Studio-Session-Token':token}});
  if (response.status === 401) {sessionToken = undefined; throw new ApiError(response.status);}
  if (!response.ok) {
    const error: {code?:string} = await response.json().catch(() => ({}));
    throw new ApiError(response.status, error.code);
  }
}
async function authedGet(path: string) {
  const token = await getSessionToken();
  const response = await fetch(API_ORIGIN + path, {cache:'no-store', headers:{Accept:'application/json', 'X-Studio-Session-Token':token}});
  if (response.status === 401) {sessionToken = undefined; throw new ApiError(response.status);}
  if (!response.ok) throw new ApiError(response.status);
  return await response.json();
}
export async function getSong(songId: string): Promise<Song> { return await authedGet(`/api/songs/${encodeURIComponent(songId)}`); }
export async function listSongTakes(songId: string): Promise<TakeList> { return await authedGet(`/api/songs/${encodeURIComponent(songId)}/takes`); }
export async function listLyrics(songId: string): Promise<LyricsList> { return await authedGet(`/api/songs/${encodeURIComponent(songId)}/lyrics`); }
export async function getTakePeaks(takeId: string): Promise<Peaks> { return await authedGet(`/api/takes/${encodeURIComponent(takeId)}/peaks`); }
// Sin esquema en el contrato (beats queda fuera del M1 recortado): tipo local explícito.
export async function getTakeAnalysis(takeId: string): Promise<{items: TakeAnalysis[]}> { return await authedGet(`/api/takes/${encodeURIComponent(takeId)}/analysis`); }
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
