'use client';
import Link from 'next/link';
import {useParams} from 'next/navigation';
import {useEffect, useMemo, useState} from 'react';
import {useTranslations} from 'next-intl';
import {API_ORIGIN, downloadTakeAsset, getSong, getTakeAnalysis, getTakePeaks, listLyrics, listSongTakes, patchTake, setSongMaster, type LyricsVersion, type Song, type Take} from '../../../lib/api';
import {ProvenancePanel} from '../../../components/ProvenancePanel';
import {Waveform} from '../../../components/Waveform';
import {usePlayer} from '../../../components/PlayerContext';
import {findPairedTake} from '../../../lib/take-pairs';

function lyricDiff(previous: string, current: string): string {
  const before = new Set(previous.split(/\r?\n/));
  const after = new Set(current.split(/\r?\n/));
  return current.split(/\r?\n/).map(line => (before.has(line) ? '  ' : '+ ') + line).concat(previous.split(/\r?\n/).filter(line => !after.has(line)).map(line => '- ' + line)).join('\n');
}

export default function SongDetailPage() {
  const t = useTranslations('songDetail');
  const player = usePlayer();
  const params = useParams<{id:string}>();
  const [song, setSong] = useState<Song | null>(null);
  const [takes, setTakes] = useState<Take[]>([]);
  const [lyrics, setLyrics] = useState<LyricsVersion[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [peaks, setPeaks] = useState<number[]>([]);
  const [beats, setBeats] = useState<number[]>([]);
  const [bpm, setBpm] = useState<number | null>(null);
  const [tab, setTab] = useState<'audio'|'lyrics'>('audio');
  const [error, setError] = useState(false);
  const [position, setPosition] = useState(0);
  const [downloadError, setDownloadError] = useState(false);
  useEffect(() => {
    let active = true;
    Promise.all([getSong(params.id), listSongTakes(params.id), listLyrics(params.id)]).then(([nextSong, nextTakes, nextLyrics]) => {
      if (!active) return;
      setSong(nextSong); setTakes(nextTakes.items); setLyrics(nextLyrics.items); setSelected(nextTakes.items[0]?.id ?? null);
    }).catch(() => { if (active) setError(true); });
    return () => { active = false; };
  }, [params.id]);
  const take = useMemo(() => takes.find(item => item.id === selected) ?? null, [selected, takes]);
  function selectTake(item: Take) {
    setSelected(item.id);
    setPosition(0);
    const asset = item.assets?.listen;
    if (asset && song) {
      const pair = findPairedTake(takes, item);
      const pairId = item.batch_id ?? item.root_id ?? undefined;
      player.select({id: item.id, takeId: item.id, title: `${song.title} ${t('separator')} ${item.label ?? item.task}`, url: asset.url.startsWith('http') ? asset.url : API_ORIGIN + asset.url, duration_s: item.duration_s, songId: song.id, pairId, variantIndex: item.variant_index});
      if (pair?.assets?.listen) {
        const pairAsset = pair.assets.listen;
        player.enqueue({id: pair.id, takeId: pair.id, title: `${song.title} ${t('separator')} ${pair.label ?? pair.task}`, url: pairAsset.url.startsWith('http') ? pairAsset.url : API_ORIGIN + pairAsset.url, duration_s: pair.duration_s, songId: song.id, pairId: pair.batch_id ?? pair.root_id ?? pairId, variantIndex: pair.variant_index});
      }
    }
  }
  async function rateTake(item: Take, rating: number) {
    const updated = await patchTake(item.id, {rating});
    setTakes(current => current.map(value => value.id === updated.id ? updated : value));
  }
  async function toggleFavorite(item: Take) {
    const updated = await patchTake(item.id, {favorite: !item.favorite});
    setTakes(current => current.map(value => value.id === updated.id ? updated : value));
  }
  async function chooseMaster(item: Take) {
    if (!song) return;
    const updated = await setSongMaster(song.id, item.id);
    setSong(updated);
  }
  async function download(item: Take, role: 'listen'|'master') {
    setDownloadError(false);
    try { await downloadTakeAsset(item.id, role); } catch { setDownloadError(true); }
  }
  useEffect(() => {
    if (!take) return;
    let active = true;
    Promise.all([getTakePeaks(take.id), getTakeAnalysis(take.id)]).then(([peakResult, analysisResult]) => {
      if (!active) return;
      setPeaks(peakResult.data?.[0]?.[0] ?? []);
      const beat = analysisResult.items.find(item => item.kind === 'audio.beats');
      const times = beat?.data['beats_s'];
      setBeats(Array.isArray(times) ? times.filter((value): value is number => typeof value === 'number') : []);
      const value = beat?.data['bpm'];
      setBpm(typeof value === 'number' ? value : null);
    }).catch(() => { if (active) { setPeaks([]); setBeats([]); setBpm(null); } });
    return () => { active = false; };
  }, [take]);
  if (error) return <div className="page"><p role="alert">{t('error')}</p><Link href="/songs">{t('back')}</Link></div>;
  if (!song) return <div className="page"><p role="status">{t('loading')}</p></div>;
  const masterValue = song.master_take_id ? takes.find(item => item.id === song.master_take_id)?.label ?? song.master_take_id : t('noMaster');
  return <div className="page song-detail"><Link href="/songs">{t('back')}</Link><header className="page-heading"><p className="eyebrow">{t('eyebrow')}</p><h1>{song.title}</h1><p>{song.artist ?? song.style_prompt}</p><p className="song-meta"><span>{t('statusLabel')} {song.status}</span>{bpm !== null && <span>{t('bpm')} {bpm}</span>}</p><p>{t('masterValue', {value: masterValue})}</p></header><nav className="song-tabs" aria-label={t('tabs')}><button type="button" aria-pressed={tab === 'audio'} onClick={() => setTab('audio')}>{t('audio')}</button><button type="button" aria-pressed={tab === 'lyrics'} onClick={() => setTab('lyrics')}>{t('lyrics')}</button><button type="button" disabled>{t('videoSoon')}</button></nav>{tab === 'audio' ? <section className="song-audio"><Waveform peaks={take ? peaks : []} beats={beats} duration_s={take?.duration_s ?? 0} value={position} onChange={value => { setPosition(value); window.dispatchEvent(new CustomEvent('studio:seek', {detail: value * (take?.duration_s ?? 0)})); }}/><h2>{t('takes')}</h2><ul className="take-list">{takes.map(item => { const pair = findPairedTake(takes, item); return <li key={item.id} className={item.id === selected ? 'selected' : ''}><button type="button" onClick={() => selectTake(item)}>{item.label ?? item.task} {t('separator')} {item.status}</button><div className="take-actions"><button type="button" aria-label={`${t('rating')} ${item.label ?? item.task}`} onClick={() => void rateTake(item, item.rating === 5 ? 0 : 5)}>{item.rating ? t('ratingValue', {value: item.rating}) : t('unrated')}</button><button type="button" onClick={() => void toggleFavorite(item)} aria-pressed={item.favorite}>{item.favorite ? t('favoriteOn') : t('favoriteOff')}</button><button type="button" onClick={() => void chooseMaster(item)} disabled={song.master_take_id === item.id}>{t('masterAction')}</button>{pair && <button type="button" onClick={() => selectTake(pair)}>{t('pairAction')}</button>}<button type="button" onClick={() => void download(item, 'listen')}>{t('downloadMp3')}</button><button type="button" onClick={() => void download(item, 'master')}>{t('downloadFlac')}</button></div></li>; })}</ul>{downloadError && <p role="alert">{t('downloadError')}</p>}</section> : <section className="lyrics-panel"><h2>{t('lyrics')}</h2>{lyrics.map((version, index) => { const previous = lyrics[index - 1]; const usedBy = takes.filter(item => item.lyrics_version_id === version.id); return <article key={version.id}><h3>{version.source} {t('separator')} {version.declaration}</h3><p>{t('usedBy')} {t('separator')} {usedBy.length ? usedBy.map(item => item.label ?? item.id).join(t('separator')) : t('noTake')}</p><pre>{version.text}</pre>{previous && <><h4>{t('difference')}</h4><pre className="lyrics-diff">{lyricDiff(previous.text, version.text)}</pre></>}</article>; })}</section>}<ProvenancePanel take={take}/></div>;
}
