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
const stages = ['queued', 'starting', 'loading_model', 'generating', 'decoding', 'post'];
const aliases: Record<string, string> = {model: 'loading_model', generate: 'generating'};

export function GenerationCard({job, variant, onRetry, onCancel, peaks = null, modelLoading = false}: GenerationCardProps) {
  const t = useTranslations('generation');
  const ready = job.take_status === 'ready';
  const status = ready ? 'succeeded' : job.take_status === 'failed' || job.take_status === 'cancelled' ? job.take_status : job.status === 'succeeded' ? 'running' : job.status;
  const rawStage = job.status === 'succeeded' && !ready ? 'post' : job.stage ?? job.status;
  const mapped = aliases[rawStage] ?? rawStage;
  const current = stages.includes(mapped) ? mapped : 'unknown';
  const showModelStage = modelLoading || job.modelLoading === true || current === 'loading_model';
  const stepStages = current === 'unknown' ? [...stages, 'unknown'] : stages;
  const currentIndex = ready ? stepStages.length : Math.max(0, stepStages.indexOf(current));
  const resolvedPeaks = peaks ?? job.peaks ?? null;
  return <article className={`generation-card generation-${status}`} aria-label={t('cardLabel', {variant})} data-take-id={job.take_id} data-model-loading={showModelStage}>
    <header><strong>{variant}</strong><span>{t(`status.${status}` as never)}</span></header>
    <GenerativeViz progress={ready ? 1 : job.progress} peaks={resolvedPeaks} />
    <ol className="generation-stepper" aria-label={t('stepper')}>
      {stepStages.map((stage, index) => <li data-stage={stage} className={stage === current && !ready ? 'current' : index < currentIndex ? 'done' : ''} key={stage}>{t(`stage.${stage}` as never)}</li>)}
    </ol>
    {(status === 'failed' || job.action_error) && <p className="generation-error" role="alert">{t('error', {code: job.action_error ?? job.take_error_code ?? job.error_code ?? 'UNKNOWN', jobId: job.job_id})}</p>}
    <footer>{active.has(status) && <button type="button" onClick={onCancel}>{t('cancel')}</button>}{status === 'failed' && <button type="button" onClick={onRetry}>{t('retry')}</button>}</footer>
  </article>;
}
