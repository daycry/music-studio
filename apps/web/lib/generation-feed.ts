import type {GenerationResponse} from './api';
import type {JobState} from './event-reducer';

export type FeedJob = JobState & {
  /** Take represented by this card. A generation job can own several takes. */
  take_id?: string;
  group_id?: string;
  variant_index?: number;
  peaks?: number[] | null;
  modelLoading?: boolean;
};

/**
 * The generation endpoint returns one GPU job and one take id per variant.
 * Keep the parent job id on every card so SSE updates and actions still target
 * the same job, while the take id gives each card a stable identity for audio
 * analysis and React rendering.
 */
export function createFeedJobs(result: GenerationResponse): FeedJob[] {
  const takeIds = result.take_ids.length ? result.take_ids : [undefined];
  return takeIds.map((take_id, variant_index) => ({
    job_id: result.generation_job_id,
    song_id: result.song_id,
    status: 'queued',
    attempt_id: null,
    stage: 'queued',
    progress: 0,
    error_code: null,
    group_id: result.generation_job_id,
    variant_index,
    ...(take_id ? {take_id} : {}),
    peaks: null,
  }));
}

function numbers(value: unknown): number[] {
  if (Array.isArray(value)) return value.flatMap(numbers);
  return typeof value === 'number' && Number.isFinite(value) ? [Math.max(0, Math.min(1, value))] : [];
}

/** Accepts the published peaks envelope, including the legacy nested shape. */
export function normalizePeaks(value: unknown): number[] | null {
  const data = value && typeof value === 'object' && 'data' in value ? value.data : value;
  const result = numbers(data);
  return result.length ? result : null;
}
