'use client';
import {useEffect, useRef, useState} from 'react';
import {useTranslations} from 'next-intl';

export type GenerativeVizProps = {
  progress: number | null;
  peaks?: number[] | null;
  reducedMotion?: boolean;
  columns?: number;
};

function clamp(value: number) { return Math.max(0, Math.min(1, Number.isFinite(value) ? value : 0)); }
function level(index: number) {
  const value = Math.sin((index + 1) * 12.9898) * 43758.5453;
  return .18 + (value - Math.floor(value)) * .64;
}

export function GenerativeViz({progress, peaks = null, reducedMotion = false, columns = 96}: GenerativeVizProps) {
  const t = useTranslations('generation');
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const frameRef = useRef<number | null>(null);
  const targetRef = useRef(clamp(progress ?? 0));
  const currentRef = useRef(clamp(progress ?? 0));
  const lastPaintRef = useRef(0);
  const [visible, setVisible] = useState(true);
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(() => {
    if (reducedMotion || typeof window === 'undefined' || typeof window.matchMedia !== 'function') return reducedMotion;
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  });

  useEffect(() => {
    if (reducedMotion || typeof window === 'undefined' || typeof window.matchMedia !== 'function') return;
    const media = window.matchMedia('(prefers-reduced-motion: reduce)');
    const update = () => setPrefersReducedMotion(media.matches);
    update();
    media.addEventListener?.('change', update);
    return () => media.removeEventListener?.('change', update);
  }, [reducedMotion]);

  useEffect(() => {
    targetRef.current = clamp(progress ?? 0);
    const canvas = canvasRef.current;
    if (!canvas) return;
    const context = canvas.getContext('2d');
    if (!context) return;
    const draw = (value: number) => {
      const width = canvas.width;
      const height = canvas.height;
      context.clearRect(0, 0, width, height);
      const values = peaks && peaks.length > 0 && value >= 1 ? peaks : Array.from({length: columns}, (_, index) => level(index));
      const barWidth = width / columns;
      const condensed = Math.floor(value * columns);
      for (let index = 0; index < columns; index += 1) {
        const sample = peaks && peaks.length > 0 && value >= 1 ? clamp(values[index % values.length] ?? 0) : (index < condensed ? level(index) : values[index]);
        const barHeight = Math.max(2, sample * height);
        context.fillStyle = index < condensed || value >= 1 ? '#34d399' : '#52605e';
        context.fillRect(index * barWidth, (height - barHeight) / 2, Math.max(1, barWidth - 1), barHeight);
      }
    };
    draw(currentRef.current);
    if (prefersReducedMotion || !visible || currentRef.current === targetRef.current) return;
    const tick = (time: number) => {
      frameRef.current = null;
      if (!visible) return;
      if (time - lastPaintRef.current < 1000 / 30) {
        frameRef.current = window.requestAnimationFrame(tick);
        return;
      }
      lastPaintRef.current = time;
      const target = targetRef.current;
      const current = currentRef.current;
      currentRef.current = Math.abs(target - current) < .01 ? target : current + (target - current) * .24;
      draw(currentRef.current);
      if (currentRef.current !== target) frameRef.current = window.requestAnimationFrame(tick);
    };
    frameRef.current = window.requestAnimationFrame(tick);
    return () => { if (frameRef.current !== null) window.cancelAnimationFrame(frameRef.current); frameRef.current = null; };
  }, [columns, peaks, progress, prefersReducedMotion, visible]);

  useEffect(() => {
    const element = canvasRef.current;
    if (!element || typeof IntersectionObserver === 'undefined') return;
    const observer = new IntersectionObserver(([entry]) => setVisible(entry.isIntersecting));
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  const value = Math.round(clamp(progress ?? 0) * 100);
  return <canvas ref={canvasRef} className="generative-viz" width={columns * 4} height={96} data-columns={columns} role="progressbar" aria-label={t('visualization')} aria-valuenow={value} aria-valuemin={0} aria-valuemax={100} />;
}
