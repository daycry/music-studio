'use client';
import {useTranslations} from 'next-intl';
import type {Take} from '../lib/api';

export function ProvenancePanel({take}: {take: Take | null}) {
  async function copy(value: string) {
    try { await navigator.clipboard?.writeText(value); } catch { /* clipboard may be unavailable in local preview */ }
  }
  const t = useTranslations('songDetail');
  if (!take) return <aside className="provenance-panel"><h2>{t('provenance')}</h2><p>{t('noTake')}</p></aside>;
  const payload = JSON.stringify(take, null, 2);
  return <aside className="provenance-panel"><h2>{t('provenance')}</h2><dl><div><dt>{t('takeId')}</dt><dd><code>{take.id}</code><button type="button" onClick={() => void copy(take.id)}>{t('copy')}</button></dd></div><div><dt>{t('model')}</dt><dd>{take.model_id}</dd></div><div><dt>{t('seed')}</dt><dd>{take.seed ?? '—'}</dd></div>{take.assets && Object.entries(take.assets).map(([role, asset]) => <div key={role}><dt>{role}</dt><dd><code>{asset.sha256}</code><button type="button" onClick={() => void copy(asset.sha256)}>{t('copy')}</button></dd></div>)}</dl><a download="take-provenance.json" href={`data:application/json;charset=utf-8,${encodeURIComponent(payload)}`}>{t('exportProvenance')}</a></aside>;
}
