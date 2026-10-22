'use client';
import type {ReactNode} from 'react';
import Link from 'next/link';
import {usePathname} from 'next/navigation';
import {useTranslations} from 'next-intl';
import {PlayerDock} from './PlayerDock';
import {PlayerProvider} from './PlayerContext';

export function StudioShell({children}:{children:ReactNode}) {
  const t = useTranslations();
  const pathname = usePathname();
  return <PlayerProvider><div className="studio-shell">
    <a className="skip-link" href="#content">{t('shell.skip')}</a>
    <header className="studio-header">
      <span className="brand">{t('shell.brand')}</span>
      <span className="tagline">{t('shell.tagline')}</span>
    </header>
    <nav className="studio-nav" aria-label={t('shell.navigation')}>
      {(['create','songs','system'] as const).map(route =>
        <Link key={route} href={'/' + route} aria-current={pathname === '/' + route ? 'page' : undefined}>
          {t('nav.' + route)}
        </Link>
      )}
    </nav>
    <main id="content" tabIndex={-1}>{children}</main>
    <PlayerDock/>
  </div></PlayerProvider>;
}

