'use client';
import Link from 'next/link';
import {useCallback, useEffect, useRef, useState} from 'react';
import {useTranslations} from 'next-intl';
import {deleteSong, listSongTrash, listSongs, moveSong, purgeSong, restoreSong, type Collection, type Song} from '../../lib/api';
import {CollectionsPanel} from '../../components/CollectionsPanel';
import {GenerativeViz} from '../../components/GenerativeViz';
import {MasterPreview} from '../../components/MasterPreview';

export default function SongsPage() {
  const t = useTranslations('songs');
  const [songs, setSongs] = useState<Song[]>([]);
  const [query, setQuery] = useState('');
  const [next, setNext] = useState<string | null>(null);
  const [view, setView] = useState<'grid'|'list'>('grid');
  const [collection, setCollection] = useState<string|null>(null);
  const [collections, setCollections] = useState<Collection[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [bulkCollection, setBulkCollection] = useState('');
  const [trashMode, setTrashMode] = useState(false);
  const [previewEnabled, setPreviewEnabled] = useState(true);
  const [filterStatus, setFilterStatus] = useState('');
  const [filterModel, setFilterModel] = useState('');
  const [filterTag, setFilterTag] = useState('');
  const [filterAfter, setFilterAfter] = useState('');
  const [filterBefore, setFilterBefore] = useState('');
  const [favoriteOnly, setFavoriteOnly] = useState(false);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const loadingMoreRef = useRef(false);
  const loadRequestRef = useRef(0);
  const sentinelRef = useRef<HTMLDivElement | null>(null);
  const [actionError, setActionError] = useState<string|null>(null);
  const [state, setState] = useState<'loading'|'ready'|'error'>('loading');
  const load = useCallback(async (search: string, cursor?: string, append = false, collection_id?: string|null) => {
    if (append && loadingMoreRef.current) return;
    const requestId = ++loadRequestRef.current;
    if (!append) setNext(null);
    if (append) { loadingMoreRef.current = true; setIsLoadingMore(true); }
    setState('loading');
    try {
      const result = trashMode
        ? await listSongTrash({cursor})
        : await listSongs({q: search || undefined, cursor, collection_id: collection_id ?? collection ?? undefined, status: filterStatus || undefined, model_id: filterModel || undefined, tag: filterTag || undefined, favorite: favoriteOnly || undefined, updated_after: filterAfter ? `${filterAfter}T00:00:00Z` : undefined, updated_before: filterBefore ? `${filterBefore}T23:59:59Z` : undefined});
      if (requestId !== loadRequestRef.current) return;
      setSongs(current => append ? [...current, ...result.items] : result.items);
      setNext(result.next);
      setState('ready');
    } catch { if (requestId === loadRequestRef.current) setState('error'); }
    finally { if (append && requestId === loadRequestRef.current) { loadingMoreRef.current = false; setIsLoadingMore(false); } }
  }, [collection, favoriteOnly, filterAfter, filterBefore, filterModel, filterStatus, filterTag, trashMode]);
  useEffect(() => { void Promise.resolve().then(() => load('')); }, [load]);
  useEffect(() => {
    const element = sentinelRef.current;
    if (!element || !next || trashMode || typeof IntersectionObserver === 'undefined') return;
    const observer = new IntersectionObserver(entries => { if (entries[0]?.isIntersecting) void load(query, next, true); });
    observer.observe(element);
    return () => observer.disconnect();
  }, [load, next, query, trashMode]);
  function submit() { void load(query, undefined, false, collection); }
  async function remove(song: Song) {
    try { await deleteSong(song.id); setSongs(current => current.filter(item => item.id !== song.id)); }
    catch { setActionError(t('actionError')); }
  }
  async function restore(song: Song) {
    try { await restoreSong(song.id); setSongs(current => current.filter(item => item.id !== song.id)); }
    catch { setActionError(t('actionError')); }
  }
  async function purge(song: Song) {
    try { await purgeSong(song.id); setSongs(current => current.filter(item => item.id !== song.id)); }
    catch { setActionError(t('purgeBlocked')); }
  }
  async function moveSelected() {
    if (!bulkCollection || selectedIds.length === 0) return;
    try {
      await Promise.all(selectedIds.map(id => moveSong(id, bulkCollection)));
      setSongs(current => current.map(item => selectedIds.includes(item.id) ? {...item, collection_id: bulkCollection} : item));
      setSelectedIds([]);
      setActionError(null);
    } catch { setActionError(t('actionError')); }
  }
  return <div className="page">
    <header className="page-heading"><p className="eyebrow">{t('eyebrow')}</p><h1>{t('title')}</h1><p>{t('description')}</p></header>
    <div className="library-toolbar" role="search"><label htmlFor="song-search">{t('searchLabel')}</label><input id="song-search" value={query} onChange={event => setQuery(event.target.value)} placeholder={t('searchPlaceholder')} disabled={trashMode}/><button type="button" onClick={submit} disabled={trashMode}>{t('search')}</button>{!trashMode && <><label htmlFor="song-status-filter">{t('filterStatus')}</label><select id="song-status-filter" value={filterStatus} onChange={event => setFilterStatus(event.target.value)}><option value="">{t('allStatuses')}</option><option value="draft">{t('statusDraft')}</option><option value="in_progress">{t('statusInProgress')}</option><option value="final">{t('statusFinal')}</option><option value="archived">{t('statusArchived')}</option></select><label htmlFor="song-model-filter">{t('filterModel')}</label><input id="song-model-filter" value={filterModel} onChange={event => setFilterModel(event.target.value)} placeholder={t('modelPlaceholder')}/><label htmlFor="song-tag-filter">{t('filterTag')}</label><input id="song-tag-filter" value={filterTag} onChange={event => setFilterTag(event.target.value)} placeholder={t('tagPlaceholder')}/><label htmlFor="song-date-after">{t('filterAfter')}</label><input id="song-date-after" type="date" value={filterAfter} onChange={event => setFilterAfter(event.target.value)}/><label htmlFor="song-date-before">{t('filterBefore')}</label><input id="song-date-before" type="date" value={filterBefore} onChange={event => setFilterBefore(event.target.value)}/><label><input type="checkbox" checked={favoriteOnly} onChange={event => setFavoriteOnly(event.target.checked)}/>{t('favoriteOnly')}</label><button type="button" onClick={submit}>{t('applyFilters')}</button></>}<button type="button" aria-pressed={trashMode} onClick={() => { setTrashMode(mode => !mode); setActionError(null); }}>{trashMode ? t('backToLibrary') : t('openTrash')}</button>{!trashMode && <button type="button" aria-pressed={previewEnabled} onClick={() => setPreviewEnabled(value => !value)}>{previewEnabled ? t('disablePreview') : t('enablePreview')}</button>}<CollectionsPanel selected={collection} onSelect={id => { setCollection(id); void load(query, undefined, false, id); }} onLoaded={setCollections}/>{!trashMode && selectedIds.length > 0 && <div className="bulk-actions"><label htmlFor="bulk-collection">{t('bulkDestination')}</label><select id="bulk-collection" value={bulkCollection} onChange={event => setBulkCollection(event.target.value)}><option value="">{t('uncategorized')}</option>{collections.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select><button type="button" disabled={!bulkCollection} onClick={() => void moveSelected()}>{t('bulkMove', {count: selectedIds.length})}</button></div>}<div className="view-toggle" aria-label={t('viewLabel')}><button type="button" aria-pressed={view === 'grid'} onClick={() => setView('grid')}>{t('grid')}</button><button type="button" aria-pressed={view === 'list'} onClick={() => setView('list')}>{t('list')}</button></div></div>
    {actionError && <p role="alert">{actionError}</p>}
    {state === 'loading' && <div className="song-skeletons" aria-label={t('loading')}><span/><span/><span/></div>}
    {state === 'error' && <section className="empty-state" role="alert"><h2>{t('unavailable')}</h2><p>{t('retry')}</p><button type="button" onClick={() => void load(query)}>{t('retryAction')}</button></section>}
    {state === 'ready' && songs.length === 0 && <section className="empty-state" aria-labelledby="songs-empty"><h2 id="songs-empty">{trashMode ? t('trashEmpty') : t('empty')}</h2><p>{trashMode ? t('trashDetail') : t('detail')}</p>{!trashMode && <Link href="/create">{t('create')}</Link>}</section>}
    {songs.length > 0 && <section className={`song-library ${view}`} aria-label={t('results')}>
      {songs.map(song => <article className={`song-card ${song.status === 'in_progress' ? 'song-generating' : ''}`} key={song.id}>{!trashMode && <label className="song-select"><input type="checkbox" aria-label={`${t('selectSong')} ${song.title}`} checked={selectedIds.includes(song.id)} onChange={event => setSelectedIds(current => event.target.checked ? [...current, song.id] : current.filter(id => id !== song.id))}/>{t('selectSong')}</label>}{trashMode ? <div className="song-art" aria-label={t('artwork')}>{t('artwork')}</div> : <Link className="song-art-link" href={`/songs/${song.id}`} aria-label={t('artwork')}><div className="song-art" aria-label={song.status === 'in_progress' ? t('generatingArtwork') : t('artwork')}>{song.status === 'in_progress' ? <GenerativeViz progress={null} columns={24} reducedMotion /> : t('artwork')}</div></Link>}<div className="song-card-body"><h2>{trashMode ? song.title : <Link href={`/songs/${song.id}`}>{song.title}</Link>}</h2><p>{song.artist ?? song.style_prompt}</p><small>{trashMode ? `${t('deletedAt')}: ${song.deleted_at ?? ''}` : song.status}</small>{!trashMode && <label>{t('collection')}<select value={song.collection_id ?? ''} onChange={event => { const id = event.target.value || null; void moveSong(song.id, id).then(() => setSongs(current => current.map(item => item.id === song.id ? {...item, collection_id:id} : item))); }}><option value="">{t('uncategorized')}</option>{collections.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>}</div>{trashMode ? <div><button type="button" onClick={() => void restore(song)}>{t('restore')}</button><button type="button" onClick={() => void purge(song)}>{t('purge')}</button></div> : <div><MasterPreview song={song} enabled={previewEnabled}/><button type="button" onClick={() => void remove(song)}>{t('trash')}</button></div>}</article>)}
    </section>}
    <div ref={sentinelRef} aria-hidden="true" />
    {next && <button type="button" disabled={isLoadingMore} onClick={() => void load(query, next, true)}>{t('loadMore')}</button>}
  </div>;
}

