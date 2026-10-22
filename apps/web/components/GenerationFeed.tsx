'use client';
import {useTranslations} from 'next-intl';
import type {FeedJob} from '../lib/generation-feed';
import {GenerationCard} from './GenerationCard';

export type {FeedJob} from '../lib/generation-feed';
export function GenerationFeed({jobs, onRetry, onCancel, modelLoading = false}: {jobs: FeedJob[]; onRetry: (job: FeedJob) => void; onCancel: (job: FeedJob) => void; modelLoading?: boolean}) {
  const t = useTranslations('generation');
  const groups = new Map<string, FeedJob[]>();
  for (const job of jobs) { const key = job.group_id ?? job.song_id; groups.set(key, [...(groups.get(key) ?? []), job]); }
  if (!groups.size) return null;
  return <section className="generation-feed" aria-label={t('feed')}>
    {[...groups.entries()].map(([key, members]) => <div className="generation-group" key={key}>
      <h2>{t('groupTitle')}</h2>
      <div className="generation-cards">{[...members].sort((a, b) => (a.variant_index ?? 0) - (b.variant_index ?? 0)).map((job, index) => <GenerationCard key={job.take_id ?? `${job.job_id}:${job.variant_index ?? index}`} job={job} variant={String.fromCharCode(65 + (job.variant_index ?? index))} peaks={job.peaks} modelLoading={modelLoading || job.modelLoading === true || job.stage === 'model'} onRetry={() => onRetry(job)} onCancel={() => onCancel(job)} />)}</div>
    </div>)}
  </section>;
}
