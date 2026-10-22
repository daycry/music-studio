'use client';
import Link from 'next/link';
import {FormEvent, useEffect, useMemo, useRef, useState} from 'react';
import {useTranslations} from 'next-intl';
import {API_ORIGIN, ApiError, cancelJob, createGeneration, estimateGeneration, getSystemInfo, getTakePeaks, retryJob, type SystemInfo} from '../../lib/api';
import {LyricsEditor} from '../../components/LyricsEditor/LyricsEditor';
import {parseLyrics} from '../../lib/lyrics';
import {GenerationFeed, type FeedJob} from '../../components/GenerationFeed';
import {subscribeEvents, type JobState, type ServerEvent} from '../../lib/events';
import {createFeedJobs, normalizePeaks} from '../../lib/generation-feed';

type Declaration = 'own' | 'assistant' | 'public_domain' | 'licensed';
const FEED_STORAGE_KEY = 'music-studio:generation-feed';
const ACE_STEP_TURBO_PARAMS = new Set(['vocal_language', 'shift', 'time_signature', 'inference_steps']);

export default function CreatePage() {
  const t = useTranslations('create');
  const [lyrics, setLyrics] = useState('');
  const [stylePrompt, setStylePrompt] = useState('');
  const [declaration, setDeclaration] = useState<Declaration | ''>('');
  const [instrumental, setInstrumental] = useState(false);
  const [variants, setVariants] = useState('2');
  const [advanced, setAdvanced] = useState(false);
  const [duration, setDuration] = useState('180');
  const [language, setLanguage] = useState('es');
  const [bpm, setBpm] = useState('');
  const [key, setKey] = useState('');
  const [timeSignature, setTimeSignature] = useState('');
  const [negativePrompt, setNegativePrompt] = useState('');
  const [inferenceSteps, setInferenceSteps] = useState('');
  const [vocalLanguage, setVocalLanguage] = useState('es');
  const [shift, setShift] = useState('');
  const [guidanceScale, setGuidanceScale] = useState('');
  const [seed, setSeed] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [queuedJob, setQueuedJob] = useState<string | null>(null);
  const [estimate, setEstimate] = useState<number | null>(null);
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const [feedJobs, setFeedJobs] = useState<FeedJob[]>(() => {
    if (typeof window === 'undefined') return [];
    try {
      const stored = JSON.parse(window.localStorage.getItem(FEED_STORAGE_KEY) ?? '[]') as unknown;
      return Array.isArray(stored) ? stored as FeedJob[] : [];
    } catch { return []; }
  });
  const feedHydrated = useRef(true);
  const peakRequests = useRef(new Set<string>());
  const feedSubscriptionKey = useMemo(() => JSON.stringify(feedJobs
    .filter(job => /^[0-7][0-9A-HJKMNP-TV-Z]{25}$/.test(job.song_id))
    .map(job => [job.song_id, /^[0-7][0-9A-HJKMNP-TV-Z]{25}$/.test(job.job_id) ? job.job_id : null])
    .sort(([leftSong, leftJob], [rightSong, rightJob]) => `${leftSong}:${leftJob ?? ''}`.localeCompare(`${rightSong}:${rightJob ?? ''}`))), [feedJobs]);
  const feedSubscriptions = useMemo(() => {
    const bySong = new Map<string, Set<string>>();
    for (const [songId, jobId] of JSON.parse(feedSubscriptionKey) as Array<[string, string | null]>) {
      const known = bySong.get(songId) ?? new Set<string>();
      if (jobId) known.add(jobId);
      bySong.set(songId, known);
    }
    return [...bySong.entries()]
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([songId, known]) => ({songId, knownJobIds: [...known].sort()}));
  }, [feedSubscriptionKey]);
  const parsed = useMemo(() => parseLyrics(lyrics), [lyrics]);
  const task = instrumental ? 'music.instrumental' : 'music.song';
  const modelId = useMemo(() => systemInfo?.models?.find(model => model.tasks?.[task]?.verified && model.provider?.type === 'local' && model.commercial_use === true && Boolean(model.license))?.id, [systemInfo, task]);
  const selectedTask = useMemo(() => systemInfo?.models?.find(model => model.id === modelId)?.tasks?.[task], [modelId, systemInfo, task]);
  const fallbackSchema: Record<string, Record<string, unknown>> = {
    duration_s: {type: 'number', minimum: 10, maximum: 600},
    inference_steps: {type: 'integer', minimum: 1, maximum: 8},
    shift: {type: 'number', minimum: 1, maximum: 5},
    time_signature: {type: 'string', pattern: '^[1-9][0-9]?/(1|2|4|8|16|32)$'},
  };
  const paramRule = (name: string) => selectedTask?.params_schema?.properties?.[name] as Record<string, unknown> | undefined ?? fallbackSchema[name];
  const validParam = (name: string, value: string) => {
    if (!value) return true;
    const rule = paramRule(name);
    if (!rule) return true;
    if ((rule.type === 'number' || rule.type === 'integer') && !Number.isFinite(Number(value))) return false;
    if (typeof rule.minimum === 'number' && Number(value) < rule.minimum) return false;
    if (typeof rule.maximum === 'number' && Number(value) > rule.maximum) return false;
    if (typeof rule.pattern === 'string' && !(new RegExp(rule.pattern)).test(value)) return false;
    return true;
  };
  const supportsParam = (name: string) => {
    if (!selectedTask) return ACE_STEP_TURBO_PARAMS.has(name);
    const properties = selectedTask.params_schema?.properties;
    if (!properties || !(name in properties)) return false;
    const feature = selectedTask.features?.[name];
    return !feature || feature.verified === true;
  };
  const invalidLyrics = !instrumental && (lyrics.trim().length === 0 || parsed.warnings.length > 0);
  const invalidStyle = stylePrompt.trim().length === 0;
  const invalidAdvanced = !validParam('duration_s', duration)
    || !validParam('bpm', bpm)
    || !validParam('key', key)
    || !validParam('time_signature', timeSignature)
    || !validParam('inference_steps', inferenceSteps)
    || !validParam('shift', shift)
    || !validParam('guidance_scale', guidanceScale);
  const invalidLanguage = !instrumental && language.trim().length === 0;
  const canSubmit = !busy && !invalidLyrics && !invalidStyle && !invalidAdvanced && !invalidLanguage && (instrumental || declaration !== '');
  useEffect(() => {
    if (!feedHydrated.current) return;
    try { window.localStorage.setItem(FEED_STORAGE_KEY, JSON.stringify(feedJobs)); } catch { /* almacenamiento local no disponible */ }
  }, [feedJobs]);
  useEffect(() => {
    let active = true;
    let controller: AbortController | undefined;
    const refresh = () => {
      controller?.abort();
      controller = new AbortController();
      getSystemInfo(controller.signal).then(info => { if (active) setSystemInfo(info); }).catch(() => undefined);
    };
    refresh();
    const interval = window.setInterval(refresh, 5000);
    return () => { active = false; window.clearInterval(interval); controller?.abort(); };
  }, []);
  useEffect(() => {
    const update = (event: ServerEvent) => {
      const data = event.data;
      const jobId = typeof data.job_id === 'string' ? data.job_id : undefined;
      if (!jobId) return;
      setFeedJobs(current => current.map(job => job.job_id !== jobId ? job : {
        ...job,
        status: typeof data.status === 'string' ? data.status : event.type === 'job.done' ? 'succeeded' : event.type === 'job.failed' ? 'failed' : event.type === 'job.cancelled' ? 'cancelled' : job.status,
        stage: typeof data.stage === 'string' ? data.stage : job.stage,
        progress: typeof data.fraction === 'number' ? data.fraction : job.progress,
        error_code: typeof data.code === 'string' ? data.code : job.error_code,
      }));
    };
    const snapshot = (jobs: JobState[]) => setFeedJobs(current => {
      const states = new Map(jobs.map(job => [job.job_id, job]));
      // El snapshot del servidor incluye dependencias post.audio/audio.beats;
      // el feed sólo conserva los jobs de generación que ya conoce el navegador.
      return current.map(job => {
        const state = states.get(job.job_id);
        return state ? {...job, ...state, group_id: job.group_id} : job;
      });
    });
    const closes = feedSubscriptions.map(({songId, knownJobIds}) => {
      const suffix = knownJobIds.map(jobId => `&known_job_id=${encodeURIComponent(jobId)}`).join('');
      return subscribeEvents(`${API_ORIGIN}/api/events?song_id=${encodeURIComponent(songId)}${suffix}`, update, {snapshot});
    });
    return () => closes.forEach(close => close());
  }, [feedSubscriptions]);
  useEffect(() => {
    const ready = feedJobs.filter(job => job.take_id && job.status === 'succeeded' && !peakRequests.current.has(job.take_id));
    for (const job of ready) {
      const takeId = job.take_id as string;
      peakRequests.current.add(takeId);
      const poll = (attempt: number) => void getTakePeaks(takeId).then(value => {
        const peaks = normalizePeaks(value);
        if (peaks) setFeedJobs(current => current.map(item => item.take_id === takeId ? {...item, peaks} : item));
        else if (attempt < 15) window.setTimeout(() => poll(attempt + 1), 1000);
      }).catch(() => {
        // El audio puede estar listo antes que su análisis de peaks.
        if (attempt < 15) window.setTimeout(() => poll(attempt + 1), 1000);
      });
      poll(0);
    }
  }, [feedJobs]);

  const params: Record<string, unknown> = {
    style: stylePrompt,
    duration_s: Number(duration),
    ...(!instrumental ? {lyrics, language} : {}),
    ...(bpm && supportsParam('bpm') ? {bpm: Number(bpm)} : {}),
    ...(key && supportsParam('key') ? {key} : {}),
    ...(timeSignature && supportsParam('time_signature') ? {time_signature: timeSignature} : {}),
    ...(negativePrompt && supportsParam('negative_prompt') ? {negative_prompt: negativePrompt} : {}),
    ...(inferenceSteps && supportsParam('inference_steps') ? {inference_steps: Number(inferenceSteps)} : {}),
    ...(!instrumental && vocalLanguage && supportsParam('vocal_language') ? {vocal_language: vocalLanguage} : {}),
    ...(shift && supportsParam('shift') ? {shift: Number(shift)} : {}),
    ...(guidanceScale && supportsParam('guidance_scale') ? {guidance_scale: Number(guidanceScale)} : {}),
  };

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSubmit) return;
    setBusy(true); setError(null); setQueuedJob(null);
    try {
      try {
        const estimateParams = instrumental ? params : {...params, lyrics, language};
        const effectiveModelId = modelId ?? 'ace-step-1.5-turbo';
        const preview = await estimateGeneration({task, model_id: effectiveModelId, params: estimateParams, ...(seed ? {seed: Number(seed)} : {}), n_outputs: Number(variants)});
        setEstimate(typeof preview.eta_s === 'number' ? preview.eta_s : null);
      } catch { setEstimate(null); }
      const result = await createGeneration({
        task,
        model_id: modelId ?? 'ace-step-1.5-turbo',
        ...(instrumental ? {} : {lyrics, lyrics_declaration: declaration as Declaration}),
        style_prompt: stylePrompt, language, params,
        ...(seed ? {seed: Number(seed)} : {}), n_outputs: Number(variants),
      });
      setQueuedJob(result.generation_job_id);
      setFeedJobs(current => [...current, ...createFeedJobs(result)]);
    } catch (cause) {
      setError(cause instanceof ApiError && cause.code === 'LYRICS_DECLARATION_REQUIRED' ? t('declarationHelp') : t('reason'));
    } finally { setBusy(false); }
  }

  return <div className="page">
    <header className="page-heading"><p className="eyebrow">{t('eyebrow')}</p><h1>{t('title')}</h1><p>{t('description')}</p></header>
    <section className="composer" aria-labelledby="composer-title">
      <h2 id="composer-title">{t('composerTitle')}</h2>
      <form onSubmit={submit}>
        <div className="field"><label htmlFor="lyrics">{t('lyricsLabel')}</label><LyricsEditor id="lyrics" value={lyrics} onChange={setLyrics} />
          <p className="field-help">{t('lyricsPlaceholder')}</p>
          {!instrumental && parsed.warnings.length > 0 && <p className="field-warning" role="status">{t('invalidLyrics')}</p>}
          {instrumental && <p className="field-help">{t('instrumentalHelp')}</p>}
        </div>
        <div className="field"><label htmlFor="style-prompt">{t('styleLabel')}</label><input id="style-prompt" value={stylePrompt} onChange={event => setStylePrompt(event.target.value)} placeholder={t('stylePlaceholder')} />
          <div className="style-chips" aria-label={t('styleChipsLabel')}>
            {(['styleChipHipHop', 'styleChipOrchestral', 'styleChipBright', 'styleChipWarmVoices'] as const).map(key => <button type="button" key={key} onClick={() => setStylePrompt(current => current ? `${current}, ${t(key)}` : t(key))}>{t(key)}</button>)}
          </div>
          {invalidStyle && <p className="field-warning" role="status">{t('styleRequired')}</p>}
        </div>
        <fieldset className="field-group"><legend>{t('declarationLegend')}</legend><p className="field-help">{t('declarationHelp')}</p>
          {([['own', 'declarationOwn'], ['assistant', 'declarationAssistant'], ['public_domain', 'declarationPublicDomain'], ['licensed', 'declarationLicensed']] as const).map(([value, label]) => <label className="choice" key={value}><input type="radio" name="declaration" value={value} checked={declaration === value} onChange={() => setDeclaration(value)} />{t(label)}</label>)}
        </fieldset>
        <label className="choice checkbox"><input type="checkbox" checked={instrumental} onChange={event => setInstrumental(event.target.checked)} />{t('instrumentalLabel')}</label>
        <div className="field compact-field"><label htmlFor="variants">{t('variantsLabel')}</label><select id="variants" value={variants} onChange={event => setVariants(event.target.value)}>{[1, 2, 3, 4].map(value => <option key={value} value={value}>{value}</option>)}</select></div>
        <details open={advanced} onToggle={event => setAdvanced(event.currentTarget.open)} className="advanced">
          <summary>{t('advancedLabel')}</summary>
          <div className="advanced-grid">
            <label className="field"><span>{t('durationLabel')}</span><input type="number" min="10" max="600" value={duration} onChange={event => setDuration(event.target.value)} /></label>
            {!instrumental && <label className="field"><span>{t('languageLabel')}</span><input value={language} onChange={event => setLanguage(event.target.value)} /></label>}
            {supportsParam('bpm') && <label className="field"><span>{t('bpmLabel')}</span><input type="number" min="30" max="300" value={bpm} onChange={event => setBpm(event.target.value)} placeholder={t('bpmPlaceholder')} /></label>}
            {supportsParam('key') && <label className="field"><span>{t('keyLabel')}</span><input value={key} onChange={event => setKey(event.target.value)} placeholder={t('keyPlaceholder')} /></label>}
            {supportsParam('time_signature') && <label className="field"><span>{t('timeSignatureLabel')}</span><input value={timeSignature} onChange={event => setTimeSignature(event.target.value)} placeholder={t('timeSignaturePlaceholder')} /></label>}
            {supportsParam('negative_prompt') && <label className="field"><span>{t('negativePromptLabel')}</span><input value={negativePrompt} onChange={event => setNegativePrompt(event.target.value)} /></label>}
            {supportsParam('inference_steps') && <label className="field"><span>{t('stepsLabel')}</span><input type="number" min="1" value={inferenceSteps} onChange={event => setInferenceSteps(event.target.value)} /></label>}
            {!instrumental && supportsParam('vocal_language') && <label className="field"><span>{t('vocalLanguageLabel')}</span><input value={vocalLanguage} onChange={event => setVocalLanguage(event.target.value)} /></label>}
            {supportsParam('shift') && <label className="field"><span>{t('shiftLabel')}</span><input type="number" min="1" max="5" step="0.1" value={shift} onChange={event => setShift(event.target.value)} /></label>}
            {supportsParam('guidance_scale') && <label className="field"><span>{t('guidanceScaleLabel')}</span><input type="number" min="1" max="20" step="0.1" value={guidanceScale} onChange={event => setGuidanceScale(event.target.value)} /></label>}
            <label className="field"><span>{t('seedLabel')}</span><input type="number" min="0" value={seed} onChange={event => setSeed(event.target.value)} /></label>
          </div>
        </details>
        {error && <p role="alert">{error}</p>}
        {invalidAdvanced && <p className="field-warning" role="status">{t('advancedInvalid')}</p>}
        {estimate !== null && <p className="field-help">{t('estimateLabel', {seconds: Math.ceil(estimate)})}</p>}
        {systemInfo && <p className="field-help">{t('queueStatus', {queued: systemInfo.queue?.queued ? 1 : 0, running: systemInfo.queue?.running ? 1 : 0, gpu: systemInfo.gpu ? t('gpuAvailable') : t('gpuUnavailable')})}</p>}
        {queuedJob && <p role="status"><strong>{t('queued')}</strong> {t('queuedDetail', {jobId: queuedJob})}</p>}
        <button type="submit" className="primary" disabled={!canSubmit}>{busy ? t('submitting') : t('submit')}</button>
      </form>
    </section>
    <GenerationFeed jobs={feedJobs} onRetry={job => { void retryJob(job.job_id).then(result => setFeedJobs(current => [...current.filter(item => item.job_id !== job.job_id), ...createFeedJobs(result)])).catch(() => undefined); }} onCancel={job => { void cancelJob(job.job_id).then(() => setFeedJobs(current => current.map(item => item.job_id === job.job_id ? {...item, status: 'cancelled', stage: null} : item))).catch(() => undefined); }} />
    <p><Link href="/system">{t('system')}</Link></p>
  </div>;
}

