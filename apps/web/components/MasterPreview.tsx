'use client';
import {useCallback, useEffect, useId, useRef, useState} from 'react';
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
  const [notice, setNotice] = useState<'previewLatestReady' | 'previewNoReady' | 'previewUnavailable' | null>(null);
  const noticeId = useId();

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
    if (!enabled || !activeRef.current) return;
    if (timerRef.current) clearTimeout(timerRef.current);
    const request = ++requestRef.current;
    setState('loading');
    setNotice(null);
    try {
      const result = await listSongTakes(song.id);
      if (!activeRef.current || request !== requestRef.current) return;
      const ready = result.items.filter(item => item.status === 'ready');
      const take = song.master_take_id
        ? ready.find(item => item.id === song.master_take_id)
        : ready.sort((a, b) => b.created_at.localeCompare(a.created_at) || b.id.localeCompare(a.id))[0];
      if (!take) { setNotice('previewNoReady'); setState('idle'); return; }
      if (!song.master_take_id) setNotice('previewLatestReady');
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
      if (activeRef.current && request === requestRef.current) { stop(); setNotice('previewUnavailable'); }
    }
  }, [enabled, song.id, song.master_take_id, stop]);

  const schedule = useCallback(() => {
    if (!enabled) return;
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => { timerRef.current = null; void play(); }, 400);
  }, [enabled, play]);

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
    <button type="button" aria-label={t('preview')} aria-describedby={notice ? noticeId : undefined} disabled={!enabled} data-state={state} onMouseEnter={schedule} onFocus={schedule} onMouseLeave={stop} onBlur={stop} onClick={() => { if (state === 'playing') stop(); else void play(); }}>
      {state === 'loading' ? t('previewLoading') : state === 'playing' ? t('previewStop') : t('preview')}
    </button>
    {notice && <small id={noticeId} role="status">{t(notice)}</small>}
    <audio ref={audioRef} preload="none" aria-hidden="true" onEnded={stop} />
  </>;
}
