'use client';
import {useEffect, useRef, type ReactNode} from 'react';
import {useTranslations} from 'next-intl';
import {readTheme, persistTheme, resolveTheme, type ThemeChoice} from '../lib/theme';

export function ThemeProvider({children}:{children:ReactNode}) {
  const t = useTranslations('theme');
  const select = useRef<HTMLSelectElement>(null);
  const choice = useRef<ThemeChoice>('system');
  useEffect(() => {
    const media = window.matchMedia('(prefers-color-scheme: dark)');
    try { choice.current = readTheme(window.localStorage); } catch { choice.current = 'system'; }
    // El selector siempre se monta antes de ejecutar el efecto.
    select.current!.value = choice.current;
    const apply = () => { document.documentElement.dataset.theme = resolveTheme(choice.current, media.matches); };
    apply();
    media.addEventListener('change', apply);
    return () => media.removeEventListener('change', apply);
  }, []);
  return <>
    <div className="theme-control">
      <label htmlFor="theme-choice">{t('label')}</label>
      <select id="theme-choice" ref={select} defaultValue="system" onChange={event => {
        choice.current = event.target.value as ThemeChoice;
        try { persistTheme(window.localStorage, choice.current); } catch { /* Almacenamiento no disponible. */ }
        document.documentElement.dataset.theme = resolveTheme(choice.current, window.matchMedia('(prefers-color-scheme: dark)').matches);
      }}>
        <option value="system">{t('system')}</option>
        <option value="dark">{t('dark')}</option>
        <option value="light">{t('light')}</option>
      </select>
    </div>
    {children}
  </>;
}
