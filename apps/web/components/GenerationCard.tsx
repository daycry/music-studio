'use client';
import {useTranslations} from 'next-intl';
import type {FeedJob} from '../lib/generation-feed';
import {GenerativeViz} from './GenerativeViz';

export type GenerationCardProps = {
  job: FeedJob;
  variant: string;
  onRetry: () => void;
  onCancel: () => void;
  peaks?: number[] | null;
  modelLoading?: boolean;
};

const active = new Set(['queued', 'blocked', 'running', 'interrupted']);
const stages = ['queued', 'starting', 'generate', 'post'];

export function GenerationCard({job, variant, onRetry, onCancel, peaks = null, modelLoading = false}: GenerationCardProps) {
  const t = useTranslations('generation');
  const current = job.stage ?? job.status;
  const showModelStage = modelLoading || job.modelLoading === true || current === 'model';
  const stepStages = showModelStage ? ['model', ...stages] : stages;
  const currentIndex = job.status === 'succeeded' ? stepStages.length : Math.max(0, stepStages.indexOf(current));
  const resolvedPeaks = peaks ?? job.peaks ?? null;
  return <article className={`generation-card generation-${job.status}`} aria-label={t('cardLabel', {variant})} data-take-id={job.take_id} data-model-loading={showModelStage}>
    <header><strong>{variant}</strong><span>{t(`status.${job.status}` as never)}</span></header>
    <GenerativeViz progress={job.progress} peaks={resolvedPeaks} />
    <ol className="generation-stepper" aria-label={t('stepper')}>
      {stepStages.map((stage, index) => <li className={stage === current && job.status !== 'succeeded' ? 'current' : index < currentIndex ? 'done' : ''} key={stage}>{t(`stage.${stage}` as never)}</li>)}
    </ol>
    {job.status === 'failed' && <p className="generation-error" role="alert">{t('error', {code: job.error_code ?? 'UNKNOWN', jobId: job.job_id})}</p>}
    <footer>{active.has(job.status) && <button type="button" onClick={onCancel}>{t('cancel')}</button>}{job.status === 'failed' && <button type="button" onClick={onRetry}>{t('retry')}</button>}</footer>
  </article>;
}
