'use client';
import {useCallback, useEffect, useRef, useState} from 'react';
import {useTranslations} from 'next-intl';
import {getTakeAudioBlob, listSongTakes, type Song} from '../lib/api';

type PreviewState = 'idle' | 'loading' | 'playing';

export function MasterPreview({song, enabled}: {song: Pick<Song, 'id'|'title'|'master_take_id'>; enabled: boolean}) {
  const t = useTranslations('songs');
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const stopRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const objectUrlRef = useRef<string | null>(null);
  const activeRef = useRef(true);
  const requestRef = useRef(0);
  const [state, setState] = useState<PreviewState>('idle');

  const stop = useCallback(() => {
    requestRef.current += 1;
    if (timerRef.current) clearTimeout(timerRef.current);
    if (stopRef.current) clearTimeout(stopRef.current);
    timerRef.current = null;
    stopRef.current = null;
    audioRef.current?.pause();
    if (audioRef.current) audioRef.current.removeAttribute('src');
    if (objectUrlRef.current) URL.revokeObjectURL(objectUrlRef.current);
    objectUrlRef.current = null;
    if (activeRef.current) setState('idle');
  }, []);

  const play = useCallback(async () => {
    if (!enabled || !song.master_take_id || !activeRef.current) return;
    const request = ++requestRef.current;
    setState('loading');
    try {
      const result = await listSongTakes(song.id);
      if (!activeRef.current || request !== requestRef.current) return;
      const take = result.items.find(item => item.id === song.master_take_id && item.status === 'ready');
      if (!take || !activeRef.current || request !== requestRef.current) { setState('idle'); return; }
      const blob = await getTakeAudioBlob(take.id);
      if (!activeRef.current || request !== requestRef.current) return;
      const url = URL.createObjectURL(blob);
      objectUrlRef.current = url;
      const audio = audioRef.current;
      if (!audio) return;
      audio.src = url;
      await audio.play();
      if (!activeRef.current || request !== requestRef.current) { stop(); return; }
      setState('playing');
      stopRef.current = setTimeout(stop, 10000);
    } catch {
      if (activeRef.current) stop();
    }
  }, [enabled, song.id, song.master_take_id, stop]);

  const schedule = useCallback(() => {
    if (!enabled || !song.master_take_id) return;
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => { timerRef.current = null; void play(); }, 400);
  }, [enabled, play, song.master_take_id]);

  useEffect(() => {
    activeRef.current = true;
    const audio = audioRef.current;
    return () => {
      activeRef.current = false;
      if (timerRef.current) clearTimeout(timerRef.current);
      if (stopRef.current) clearTimeout(stopRef.current);
      audio?.pause();
      if (objectUrlRef.current) URL.revokeObjectURL(objectUrlRef.current);
    };
  }, []);

  useEffect(() => { if (!enabled) stop(); }, [enabled, stop]);

  return <>
    <button type="button" aria-label={t('preview')} disabled={!enabled || !song.master_take_id} data-state={state} onMouseEnter={schedule} onFocus={schedule} onMouseLeave={stop} onBlur={stop} onClick={() => { if (state === 'playing') stop(); else void play(); }}>
      {state === 'loading' ? t('previewLoading') : state === 'playing' ? t('previewStop') : t('preview')}
    </button>
    <audio ref={audioRef} preload="none" aria-hidden="true" onEnded={stop} />
  </>;
}
