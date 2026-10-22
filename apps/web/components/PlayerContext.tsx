'use client';
import {createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode} from 'react';

const STORAGE_KEY = 'music-studio.player.queue';

export type PlayerTrack = {
  id: string;
  takeId?: string;
  title: string;
  url: string;
  duration_s: number | null;
  songId?: string;
  pairId?: string;
  variantIndex?: number;
};

type PlayerContextValue = {
  queue: PlayerTrack[];
  current: PlayerTrack | null;
  currentIndex: number;
  isPlaying: boolean;
  select: (track: PlayerTrack) => void;
  enqueue: (track: PlayerTrack) => void;
  remove: (trackId: string) => void;
  move: (from: number, to: number) => void;
  step: (delta: number) => void;
  advance: () => void;
  finish: () => void;
  canAdvance: boolean;
  toggleVariant: () => void;
  setPlaying: (playing: boolean) => void;
};

const PlayerContext = createContext<PlayerContextValue | null>(null);

function readQueue(): PlayerTrack[] {
  if (typeof window === 'undefined') return [];
  try {
    const value: unknown = JSON.parse(window.localStorage.getItem(STORAGE_KEY) ?? '[]');
    if (!Array.isArray(value)) return [];
    return value.filter((item): item is PlayerTrack => Boolean(item && typeof item === 'object' && typeof item.id === 'string' && typeof item.title === 'string' && typeof item.url === 'string' && (typeof item.duration_s === 'number' || item.duration_s === null)));
  } catch {
    return [];
  }
}

export function PlayerProvider({children}:{children:ReactNode}) {
  const [queue, setQueue] = useState<PlayerTrack[]>(readQueue);
  const [currentIndex, setCurrentIndex] = useState(() => readQueue().length ? 0 : -1);
  const [isPlaying, setPlaying] = useState(false);

  useEffect(() => {
    if (typeof window !== 'undefined') window.localStorage.setItem(STORAGE_KEY, JSON.stringify(queue));
  }, [queue]);

  const select = useCallback((track: PlayerTrack) => {
    setQueue(previous => {
      const index = previous.findIndex(item => item.id === track.id);
      if (index >= 0) { setCurrentIndex(index); return previous.map(item => item.id === track.id ? track : item); }
      setCurrentIndex(previous.length);
      return [...previous, track];
    });
    setPlaying(false);
  }, []);
  const enqueue = useCallback((track: PlayerTrack) => {
    setQueue(previous => previous.some(item => item.id === track.id) ? previous : [...previous, track]);
  }, []);
  const remove = useCallback((trackId: string) => {
    setQueue(previous => {
      const removed = previous.findIndex(item => item.id === trackId);
      if (removed < 0) return previous;
      setCurrentIndex(index => index > removed ? index - 1 : index === removed ? Math.min(index, previous.length - 2) : index);
      return previous.filter(item => item.id !== trackId);
    });
    setPlaying(false);
  }, []);
  const move = useCallback((from: number, to: number) => {
    setQueue(previous => {
      if (from < 0 || from >= previous.length || to < 0 || to >= previous.length || from === to) return previous;
      const next = [...previous];
      const [item] = next.splice(from, 1);
      next.splice(to, 0, item);
      setCurrentIndex(index => index === from ? to : index);
      return next;
    });
  }, []);
  const step = useCallback((delta: number) => {
    setCurrentIndex(index => queue.length ? Math.min(queue.length - 1, Math.max(0, index + delta)) : -1);
    setPlaying(false);
  }, [queue.length]);
  const advance = useCallback(() => {
    setCurrentIndex(index => {
      if (!queue.length) return -1;
      const current = queue[index];
      if (current?.pairId) {
        const sibling = queue.findIndex(item => item.id !== current.id && item.pairId === current.pairId && item.variantIndex !== current.variantIndex);
        if (sibling >= 0) return sibling;
      }
      return Math.min(queue.length - 1, Math.max(0, index + 1));
    });
    setPlaying(false);
  }, [queue]);
  const finish = useCallback(() => {
    setCurrentIndex(index => {
      if (!queue.length) return -1;
      const current = queue[index];
      if (current?.pairId) {
        const sibling = queue.findIndex(item => item.id !== current.id && item.pairId === current.pairId && item.variantIndex !== current.variantIndex);
        if (sibling > index) return sibling;
      }
      return Math.min(queue.length - 1, Math.max(0, index + 1));
    });
    setPlaying(false);
  }, [queue]);
  const canAdvance = useMemo(() => {
    const current = queue[currentIndex];
    if (!current) return false;
    if (current.pairId && queue.some(item => item.id !== current.id && item.pairId === current.pairId && item.variantIndex !== current.variantIndex)) return true;
    return currentIndex < queue.length - 1;
  }, [currentIndex, queue]);
  const toggleVariant = useCallback(() => {
    setCurrentIndex(index => {
      const current = queue[index];
      if (!current?.pairId) return index;
      const sibling = queue.findIndex(item => item.id !== current.id && item.pairId === current.pairId && item.variantIndex !== current.variantIndex);
      return sibling >= 0 ? sibling : index;
    });
    setPlaying(false);
  }, [queue]);
  const value = useMemo(() => ({queue, current: queue[currentIndex] ?? null, currentIndex, isPlaying, select, enqueue, remove, move, step, advance, finish, canAdvance, toggleVariant, setPlaying}), [advance, canAdvance, currentIndex, enqueue, finish, isPlaying, move, queue, remove, select, step, toggleVariant]);
  return <PlayerContext.Provider value={value}>{children}</PlayerContext.Provider>;
}

export function usePlayer() {
  const value = useContext(PlayerContext);
  if (!value) throw new Error('usePlayer must be used inside PlayerProvider');
  return value;
}
