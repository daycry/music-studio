'use client';
import {FormEvent, useEffect, useState} from 'react';
import {useTranslations} from 'next-intl';
import {createCollection, listCollections, renameCollection, type Collection} from '../lib/api';

export function CollectionsPanel({selected, onSelect, onLoaded}:{selected:string|null; onSelect:(id:string|null)=>void; onLoaded?:(items:Collection[])=>void}) {
  const t = useTranslations('collections');
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<Collection[]>([]);
  const [name, setName] = useState('');
  const [creating, setCreating] = useState(false);
  const [renaming, setRenaming] = useState<string|null>(null);
  const [error, setError] = useState(false);
  useEffect(() => {
    if (!open) return;
    void listCollections().then(result => { setItems(result.items); onLoaded?.(result.items); setError(false); }).catch(() => setError(true));
  }, [onLoaded, open]);
  async function submit(event: FormEvent) {
    event.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) return;
    try {
      if (renaming) {
        const updated = await renameCollection(renaming, trimmed);
        setItems(current => current.map(item => item.id === updated.id ? updated : item));
      } else {
        const created = await createCollection(trimmed);
        setItems(current => [...current, created]);
        onSelect(created.id);
      }
      setName(''); setCreating(false); setRenaming(null); setError(false);
    } catch { setError(true); }
  }
  return <section className="collections-panel" aria-label={t('title')}>
    <button type="button" onClick={() => setOpen(value => !value)} aria-expanded={open}>{t('open')}</button>
    {open && <div className="collections-popover">
      <button type="button" onClick={() => onSelect(null)} aria-pressed={selected === null}>{t('all')}</button>
      {error && <p role="alert">{t('error')}</p>}
      <ul>{items.map(item => <li key={item.id}><button type="button" aria-pressed={selected === item.id} onClick={() => onSelect(item.id)}>{item.name}</button><button type="button" aria-label={`${t('rename')} ${item.name}`} onClick={() => { setRenaming(item.id); setName(item.name); setCreating(true); }}>{t('rename')}</button></li>)}</ul>
      {!creating && <button type="button" onClick={() => { setCreating(true); setRenaming(null); setName(''); }}>{t('new')}</button>}
      {creating && <form onSubmit={submit}><label htmlFor="collection-name">{t('name')}</label><input id="collection-name" value={name} onChange={event => setName(event.target.value)} required autoFocus/><button type="submit">{renaming ? t('save') : t('create')}</button><button type="button" onClick={() => { setCreating(false); setRenaming(null); }}>{t('cancel')}</button></form>}
    </div>}
  </section>;
}
