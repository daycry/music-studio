'use client';
import {useTranslations} from 'next-intl';
import {useEffect, useRef, useState} from 'react';
import {useRouter} from 'next/navigation';
import {usePlayer} from './PlayerContext';
import {getTakeAudioBlob} from '../lib/api';

export function PlayerDock() {
  const t = useTranslations('player');
  const player = usePlayer();
  const router = useRouter();
  const audio = useRef<HTMLAudioElement>(null);
  const [position, setPosition] = useState(0);
  const [help, setHelp] = useState(false);
  const [queueOpen, setQueueOpen] = useState(false);
  const [resolved, setResolved] = useState<{id:string; url:string} | null>(null);
  const current = player.current;
  useEffect(() => {
    let active = true;
    let objectUrl: string | undefined;
    if (current) {
      void getTakeAudioBlob(current.takeId ?? current.id).then(blob => {
        if (!active || typeof URL.createObjectURL !== 'function') return;
        objectUrl = URL.createObjectURL(blob);
        setResolved({id: current.id, url: objectUrl});
      }).catch(() => undefined);
    }
    return () => { active = false; if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [current]);
  useEffect(() => {
    const onSeek = (event: Event) => {
      const seconds = (event as CustomEvent<number>).detail;
      if (audio.current && Number.isFinite(seconds)) audio.current.currentTime = seconds;
    };
    window.addEventListener('studio:seek', onSeek);
    return () => window.removeEventListener('studio:seek', onSeek);
  }, []);
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      if (target && (target.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName))) return;
      if (event.key === '?') { event.preventDefault(); setHelp(value => !value); return; }
      if ((event.key === 'c' || event.key === 'C') && !event.ctrlKey && !event.metaKey) { event.preventDefault(); router.push('/create'); return; }
      if ((event.key === 'b' || event.key === 'B') && !event.ctrlKey && !event.metaKey) { event.preventDefault(); router.push('/songs'); return; }
      if (!current) return;
      if (event.key === ' ') { event.preventDefault(); player.setPlaying(!player.isPlaying); return; }
      if (event.key === 'v' || event.key === 'V') { event.preventDefault(); player.toggleVariant(); return; }
      if (event.key === 'l' || event.key === 'L') { event.preventDefault(); if (audio.current) audio.current.loop = !audio.current.loop; return; }
      if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
        event.preventDefault();
        if (event.shiftKey) { player.step(event.key === 'ArrowLeft' ? -1 : 1); return; }
        if (audio.current) audio.current.currentTime = Math.max(0, Math.min(audio.current.duration || Infinity, audio.current.currentTime + (event.key === 'ArrowLeft' ? -5 : 5)));
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [current, player, router]);
  useEffect(() => {
    if (audio.current) {
      if (player.isPlaying) void audio.current.play().catch(() => player.setPlaying(false));
      else audio.current.pause();
    }
  }, [player, player.isPlaying, current]);
  const setPlay = () => player.setPlaying(!player.isPlaying);
  return <section className="player-dock" aria-label={t('title')}>
    <div className="player-selection">
      <strong>{current?.title ?? t('empty')}</strong>
      <p id="player-reason">{current ? t('nowPlaying') : t('reason')}</p>
    </div>
    <div className="player-transport">
      <button type="button" disabled={!current || player.currentIndex <= 0} onClick={() => player.step(-1)} aria-describedby="player-reason">{t('previous')}</button>
      <button type="button" disabled={!current} onClick={setPlay} aria-describedby="player-reason">{player.isPlaying ? t('pause') : t('play')}</button>
      <button type="button" disabled={!current || !player.canAdvance} onClick={player.advance} aria-describedby="player-reason">{t('next')}</button>
    </div>
    <label className="player-seek">
      <span className="sr-only">{t('seek')}</span>
      <input type="range" min={0} max={current?.duration_s ?? 1} value={position} disabled={!current} aria-describedby="player-reason" onChange={event => { const next = Number(event.target.value); setPosition(next); if (audio.current) audio.current.currentTime = next; }}/>
    </label>
    <div className="player-extras">
      <button type="button" disabled={!current} aria-describedby="player-reason">{t('volume')}</button>
      <button type="button" disabled={!player.queue.length} onClick={() => setQueueOpen(value => !value)} aria-describedby="player-reason">{t('queue')}</button>
      <button type="button" onClick={() => setHelp(value => !value)} aria-expanded={help}>{t('help')}</button>
    </div>
    {current && <audio ref={audio} src={resolved?.id === current.id ? resolved.url : current.url} onTimeUpdate={event => setPosition(event.currentTarget.currentTime)} onEnded={player.finish} preload="metadata"/>}
    {queueOpen && <aside className="player-queue" aria-label={t('queue')}><ol>{player.queue.map((item, index) => <li key={item.id}><span>{item.title}</span><button type="button" onClick={() => player.move(index, index - 1)} disabled={index === 0}>{t('moveUp')}</button><button type="button" onClick={() => player.move(index, index + 1)} disabled={index === player.queue.length - 1}>{t('moveDown')}</button><button type="button" onClick={() => player.remove(item.id)}>{t('remove')}</button></li>)}</ol></aside>}
    {help && <aside className="player-help" role="dialog" aria-label={t('help')}><strong>{t('help')}</strong><p>{t('shortcuts')}</p></aside>}
  </section>;
}

