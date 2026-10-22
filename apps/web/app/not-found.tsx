'use client';
import Link from 'next/link';
import {useTranslations} from 'next-intl';
export default function NotFound() {
  const t = useTranslations('notFound');
  return <section className="page"><h1>{t('title')}</h1><p>{t('description')}</p><Link href="/create">{t('create')}</Link></section>;
}
