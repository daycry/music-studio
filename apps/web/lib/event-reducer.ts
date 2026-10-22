import {parseCursor, type SSEFrame} from './event-parser';

export const eventTypes = ['job.created', 'job.stage', 'job.progress', 'job.delta', 'job.done', 'job.failed', 'job.cancelled', 'entity.updated', 'system.status'] as const;
export type ServerEvent = {id: number; type: typeof eventTypes[number]; ts: string; data: Record<string, unknown>};
export type JobState = {job_id: string; song_id: string; status: string; attempt_id: string | null; stage: string | null; progress: number | null; error_code: string | null};
const statuses = ['queued', 'blocked', 'running', 'interrupted', 'succeeded', 'failed', 'cancelled'];
const active = new Set(statuses.slice(0, 4));
const entities = ['song', 'take', 'lyrics', 'artwork', 'video_project', 'shot', 'shot_version', 'render', 'analysis', 'asset'];
const ulidPattern = /^[0-7][0-9A-HJKMNP-TV-Z]{25}$/;
const labelPattern = /^[A-Za-z0-9_-]{1,64}$/;
const snapshotPattern = /^[a-f0-9]{32}$/;
function invalid(): never {throw new Error('INVALID_EVENT');}
function object(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) invalid();
  return value as Record<string, unknown>;
}
function closed(value: Record<string, unknown>, allowed: string[], required = allowed) {
  if (Object.keys(value).some(key => !allowed.includes(key)) || required.some(key => !(key in value))) invalid();
}
function ulid(value: unknown): value is string {return typeof value === 'string' && ulidPattern.test(value);}
function label(value: unknown): value is string {return typeof value === 'string' && labelPattern.test(value);}
function integer(value: unknown, max: number): value is number {return Number.isSafeInteger(value) && (value as number) >= 0 && (value as number) <= max;}
function fraction(value: unknown): value is number {return typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= 1;}
function jobState(value: unknown): JobState {
  const job = object(value);
  closed(job, ['job_id', 'song_id', 'status', 'attempt_id', 'stage', 'progress', 'error_code']);
  if (!ulid(job.job_id) || !ulid(job.song_id) || !statuses.includes(job.status as string) ||
      job.attempt_id !== null && !ulid(job.attempt_id) || job.stage !== null && !label(job.stage) ||
      job.progress !== null && !fraction(job.progress) || job.error_code !== null && !label(job.error_code)) invalid();
  return {...job} as JobState;
}
function envelope(frame: SSEFrame): ServerEvent {
  const event = object(frame.data);
  closed(event, ['id', 'type', 'ts', 'data']);
  if (!integer(event.id, Number.MAX_SAFE_INTEGER) || event.id === 0 || !eventTypes.includes(event.type as ServerEvent['type']) ||
      typeof event.ts !== 'string' || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(event.ts)) invalid();
  const date = new Date(event.ts);
  if (!Number.isFinite(date.getTime()) || date.toISOString() !== event.ts || frame.event !== 'message' && frame.event !== event.type) invalid();
  object(event.data);
  return event as ServerEvent;
}
function publicData(event: ServerEvent) {
  const data = event.data;
  if (event.type === 'entity.updated') {
    closed(data, ['type', 'id']);
    if (!entities.includes(data.type as string) || !ulid(data.id)) invalid();
    return;
  }
  if (event.type === 'system.status') {
    closed(data, ['status']); if (!label(data.status)) invalid(); return;
  }
  const fields = { 'job.created': ['status'], 'job.stage': ['status', 'stage'], 'job.progress': ['status', 'fraction'], 'job.delta': ['status', 'text'], 'job.done': ['status'], 'job.failed': ['status', 'code', 'retryable'], 'job.cancelled': ['status']}[event.type];
  closed(data, ['job_id', 'attempt_id', 'song_id', 'entity_id', ...fields], ['job_id']);
  for (const key of ['job_id', 'attempt_id', 'song_id', 'entity_id']) if (key in data && !ulid(data[key])) invalid();
  for (const key of ['status', 'stage', 'code']) if (key in data && !label(data[key])) invalid();
  if ('fraction' in data && !fraction(data.fraction) || 'retryable' in data && typeof data.retryable !== 'boolean' || 'text' in data && typeof data.text !== 'string') invalid();
}
type Staging = {id: string; high: number; active: number; known: number; chunks: number; next: number; jobs: Map<string, JobState>};

/** Committed cursor and snapshot map never expose partially received state. */
export class EventReducer {
  cursor?: string;
  private staging?: Staging;
  private revision = 0;
  constructor(private receive: (event: ServerEvent) => void, private snapshot: (jobs: JobState[]) => void) {}
  discard() {this.revision++; this.staging = undefined;}
  clear() {this.discard(); this.cursor = undefined; this.snapshot([]);}

  accept(frame: SSEFrame) {
    const revision = this.revision;
    const event = envelope(frame);
    const data = event.data;
    if (event.type === 'system.status' && data.status === 'snapshot') {
      if (!snapshotPattern.test(String(data.snapshot_id))) invalid();
      if (data.phase === 'begin') {
        closed(data, ['status', 'phase', 'snapshot_id', 'reason', 'active_count', 'known_count', 'chunk_count']);
        if (frame.id !== undefined || this.staging || !['bootstrap', 'epoch', 'expired', 'ahead'].includes(data.reason as string) ||
            !integer(data.active_count, 1000) || !integer(data.known_count, 64) || !integer(data.chunk_count, 17) ||
            data.chunk_count !== Math.ceil((data.active_count + data.known_count) / 64)) invalid();
        this.staging = {id: data.snapshot_id as string, high: event.id, active: data.active_count, known: data.known_count, chunks: data.chunk_count, next: 0, jobs: new Map()};
        return;
      }
      const stage = this.staging;
      if (!stage || stage.id !== data.snapshot_id || stage.high !== event.id) invalid();
      if (data.phase === 'chunk') {
        closed(data, ['status', 'phase', 'snapshot_id', 'index', 'jobs']);
        if (frame.id !== undefined || data.index !== stage.next || stage.next >= stage.chunks || !Array.isArray(data.jobs) ||
            data.jobs.length < 1 || data.jobs.length > 64 || data.jobs.length !== Math.min(64, stage.active + stage.known - stage.jobs.size)) invalid();
        const validated = data.jobs.map(jobState);
        for (const job of validated) {
          if (stage.jobs.has(job.job_id) || stage.jobs.size >= 1064) invalid();
          stage.jobs.set(job.job_id, job);
        }
        stage.next++; return;
      }
      if (data.phase !== 'end') invalid();
      closed(data, ['status', 'phase', 'snapshot_id', 'chunk_count', 'cursor']);
      if (typeof data.cursor !== 'string' || frame.id !== data.cursor || parseCursor(data.cursor).seq !== stage.high ||
          data.chunk_count !== stage.chunks || stage.next !== stage.chunks || stage.jobs.size !== stage.active + stage.known) invalid();
      const jobs = [...stage.jobs.values()];
      if (jobs.filter(job => active.has(job.status)).length !== stage.active) invalid();
      this.snapshot(jobs);
      if (revision !== this.revision) return;
      this.cursor = data.cursor; this.staging = undefined; return;
    }
    if (this.staging || frame.id === undefined) invalid();
    const next = parseCursor(frame.id);
    if (next.seq !== event.id) invalid();
    if (this.cursor) {
      const previous = parseCursor(this.cursor);
      if (previous.epoch !== next.epoch || next.seq <= previous.seq) invalid();
    }
    publicData(event);
    this.receive(event);
    if (revision === this.revision) this.cursor = frame.id;
  }
}
