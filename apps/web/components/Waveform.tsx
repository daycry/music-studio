'use client';
import {useEffect, useRef, useState} from 'react';
import {useTranslations} from 'next-intl';
import type WaveSurfer from 'wavesurfer.js';

export function Waveform({peaks = [], beats = [], duration_s = 0, value = 0, onChange}: {peaks?: number[]; beats?: number[]; duration_s?: number; value?: number; onChange?: (value:number) => void}) {
  const t = useTranslations('songDetail');
  const [zoom, setZoom] = useState(1);
  const containerRef = useRef<HTMLDivElement>(null);
  const waveformRef = useRef<WaveSurfer | null>(null);
  const onChangeRef = useRef(onChange);
  const peaksKey = peaks.join(',');
  const beatsKey = beats.join(',');
  useEffect(() => { onChangeRef.current = onChange; }, [onChange]);
  useEffect(() => {
    let cancelled = false;
    void Promise.all([import('wavesurfer.js'), import('wavesurfer.js/dist/plugins/regions.esm.js')]).then(([waveModule, regionsModule]) => {
      if (cancelled || !containerRef.current) return;
      const WaveSurfer = waveModule.default;
      const RegionsPlugin = regionsModule.default;
      const regions = RegionsPlugin.create();
      const waveform = WaveSurfer.create({
        container: containerRef.current,
        height: 120,
        waveColor: '#34d399',
        progressColor: '#6ee7b7',
        cursorColor: '#fbbf24',
        minPxPerSec: 80 * zoom,
        peaks: peaks.length ? [peaks] : undefined,
        duration: duration_s || undefined,
        interact: true,
        plugins: [regions],
      });
      const markerLength = Math.max(0.01, Math.min(0.02, (duration_s || 1) / 1000));
      for (const beat of beats) {
        if (!Number.isFinite(beat) || beat < 0 || (duration_s > 0 && beat > duration_s)) continue;
        regions.addRegion({
          start: beat,
          end: Math.min(duration_s || beat + markerLength, beat + markerLength),
          color: 'rgba(251, 191, 36, 0.35)',
          drag: false,
          resize: false,
        });
      }
      waveform.on('interaction', () => {
        const total = duration_s || waveform.getDuration();
        if (total > 0) onChangeRef.current?.(waveform.getCurrentTime() / total);
      });
      waveformRef.current = waveform;
    }).catch(() => undefined);
    return () => {
      cancelled = true;
      waveformRef.current?.destroy();
      waveformRef.current = null;
    };
  // zoom is applied by the separate effect without recreating the waveform.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [beatsKey, duration_s, peaksKey]);
  useEffect(() => { waveformRef.current?.zoom(80 * zoom); }, [zoom]);
  return <div className="waveform" data-regions-ready="true">
    <div ref={containerRef} aria-label={t('waveform')}/>
    <label><span className="sr-only">{t('seek')}</span><input type="range" role="slider" min={0} max={1} step={.001} value={value} onChange={event => onChange?.(Number(event.target.value))}/></label>
    <label><span>{t('zoom')}</span><input type="range" min={1} max={4} step={.5} value={zoom} onChange={event => setZoom(Number(event.target.value))}/></label>
    {beats.length > 0 && <p className="sr-only">{t('beatsCount', {value: beats.length})}</p>}
  </div>;
}
