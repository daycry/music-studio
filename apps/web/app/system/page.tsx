'use client';
import {useEffect, useState} from 'react';
import {useTranslations} from 'next-intl';
import {getHealth, getSystemInfo, unloadSystem, type Health, type SystemInfo} from '../../lib/api';

function bytes(value?: number) { return typeof value === 'number' ? `${Math.round(value / 1024 / 1024)} MiB` : '—'; }

type Connection = {state:'loading'} | {state:'ready'; health:Health} | {state:'error'};
export default function SystemPage() {
  const t = useTranslations('system');
  const [connection, setConnection] = useState<Connection>({state:'loading'});
  const [info, setInfo] = useState<SystemInfo | null>(null);
  const [request, setRequest] = useState(0);
  const [unloading, setUnloading] = useState(false);
  const [unloadMessage, setUnloadMessage] = useState<string | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    getHealth(controller.signal).then(health => {
      if (!controller.signal.aborted) {
        setConnection({state:'ready', health});
        getSystemInfo(controller.signal).then(value => { if (!controller.signal.aborted) setInfo(value); }).catch(() => undefined);
      }
    }).catch(() => {
      if (!controller.signal.aborted) setConnection({state:'error'});
    });
    return () => controller.abort();
  }, [request]);
  return <div className="page">
    <header className="page-heading"><p className="eyebrow">{t('eyebrow')}</p><h1>{t('title')}</h1><p>{t('description')}</p></header>
    <section className="system-card" aria-labelledby="connection-title">
      <h2 id="connection-title">{t('connection')}</h2>
      {connection.state === 'error'
        ? <p role="alert">{t('error')}</p>
        : <p role="status">{t(connection.state === 'ready' ? 'ready' : 'loading')}</p>}
      <button type="button" disabled={connection.state === 'loading'} onClick={() => {
        setConnection({state:'loading'});
        setRequest(value => value + 1);
      }}>{t('refresh')}</button>
      <button type="button" disabled={unloading || connection.state !== 'ready'} onClick={() => {
        setUnloading(true);
        setUnloadMessage(null);
        unloadSystem().then(result => {
          setUnloadMessage(t('unloaded', {freed: Math.round(result.freed_mb)}));
          setRequest(value => value + 1);
        }).catch(() => setUnloadMessage(t('unloadError'))).finally(() => setUnloading(false));
      }}>{t(unloading ? 'unloading' : 'unload')}</button>
      {unloadMessage ? <p role="status">{unloadMessage}</p> : null}
    </section>
    <section className="system-card" aria-labelledby="resources-title">
      <h2 id="resources-title">{t('measurements')}</h2>
      {info ? <><dl className="system-measurements"><div><dt>{t('queue')}</dt><dd>{info.queue?.running ? t('running') : info.queue?.queued ? t('queued') : t('idle')}</dd></div><div><dt>{t('engines')}</dt><dd>{info.engines?.length ?? 0}</dd></div><div><dt>{t('gpu')}</dt><dd>{info.gpu ? `${t('free')}: ${bytes((info.gpu.free_mb ?? 0) * 1024 * 1024)} · ${t('total')}: ${bytes((info.gpu.total_mb ?? 0) * 1024 * 1024)} · ${t('limit')}: ${info.gpu.limit_mb == null ? '?' : bytes(info.gpu.limit_mb * 1024 * 1024)}` : t('unavailableTelemetry')}</dd></div><div><dt>{t('ram')}</dt><dd>{info.ram ? `${bytes(info.ram.free_bytes)} / ${bytes(info.ram.total_bytes)}` : '—'}</dd></div><div><dt>{t('disk')}</dt><dd>{info.disk ? `${bytes(info.disk.free_bytes)} / ${bytes(info.disk.total_bytes)}` : '—'}</dd></div></dl><section className="system-engines" aria-labelledby="engines-title"><h3 id="engines-title">{t('engines')}</h3>{info.engines?.length ? <ul>{info.engines.map(engine => <li key={engine.engine_id ?? engine.engine_version}><strong>{engine.engine_id ?? '—'}</strong><span>{engine.engine_version ?? '—'}</span><span>{engine.state ?? '—'}</span></li>)}</ul> : <p>{t('noEngines')}</p>}</section><section className="system-models" aria-labelledby="models-title"><h3 id="models-title">{t('models')}</h3>{info.models?.length ? <ul>{info.models.map(model => <li key={`${model.id}-${model.revision}`}><strong>{model.id}</strong><span>{model.license ?? '—'}</span><span>{Object.entries(model.tasks ?? {}).filter(([, task]) => task.verified).map(([task]) => task).join(t('separator')) || t('unverified')}</span>{model.weights?.map(weight => <small key={`${weight.path}-${weight.sha256}`}><code>{weight.path}</code> {t('separator')} {t('hash')} <code>{weight.sha256}</code> {t('separator')} {bytes(weight.bytes)}</small>)}</li>)}</ul> : <p>{t('noModels')}</p>}</section></> : <p>{t('noTelemetry')}</p>}
    </section>
  </div>;
}

