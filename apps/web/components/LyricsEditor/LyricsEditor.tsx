'use client';
import {ChangeEvent, KeyboardEvent, useRef} from 'react';
import {useTranslations} from 'next-intl';
import {parseLyrics} from '../../lib/lyrics';

function syllables(text: string): number {
  const words = text.toLocaleLowerCase().match(/[\p{L}]+/gu) ?? [];
  return words.reduce((total, word) => total + Math.max(1, (word.match(/[aeiou\u00e1\u00e9\u00ed\u00f3\u00fa\u00fc]+/giu) ?? []).length), 0);
}

export function LyricsEditor({value, onChange, disabled = false, id}:{value:string; onChange:(value:string)=>void; disabled?:boolean; id?:string}) {
  const t = useTranslations('create');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const parsed = parseLyrics(value);
  const ranges = [...parsed.sections.map(section => ({...section.headerRange, invalid: false})),
    ...parsed.annotations.map(annotation => ({...annotation.range, invalid: true}))].sort((left, right) => left.start - right.start);
  const highlighted = ranges.flatMap((range, index) => {
    const prefix = value.slice(ranges[index - 1]?.end ?? 0, range.start);
    return [<span key={`text-${index}`}>{prefix}</span>, <mark className={range.invalid ? 'invalid-tag' : undefined} key={`tag-${index}`}>{value.slice(range.start, range.end)}</mark>];
  });
  highlighted.push(<span key="tail">{value.slice(ranges.at(-1)?.end ?? 0)}</span>);
  const sections = parsed.sections.map(section => ({
    name: section.alias,
    lines: value.slice(section.bodyRange.start, section.bodyRange.end).split(/\r?\n/).filter(Boolean).length,
    syllables: syllables(value.slice(section.bodyRange.start, section.bodyRange.end)),
  }));
  function keyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
      event.preventDefault();
      event.currentTarget.form?.requestSubmit();
    }
  }
  function insertSection(section: string) {
    const textarea = textareaRef.current;
    const start = textarea?.selectionStart ?? value.length;
    const end = textarea?.selectionEnd ?? start;
    const prefix = start > 0 && !value.slice(0, start).endsWith('\n') ? '\n' : '';
    const next = `${value.slice(0, start)}${prefix}[${section}]\n${value.slice(end)}`;
    onChange(next);
    requestAnimationFrame(() => {
      const position = start + prefix.length + section.length + 3;
      textarea?.focus();
      textarea?.setSelectionRange(position, position);
    });
  }
  return <div className="lyrics-editor">
    <div className="lyrics-mirror" aria-hidden="true">{highlighted}</div>
    <textarea ref={textareaRef} id={id} aria-label={t('editorAriaLabel')} value={value} disabled={disabled} onChange={(event:ChangeEvent<HTMLTextAreaElement>) => onChange(event.target.value)} onKeyDown={keyDown} rows={14} />
    <div className="section-inserter" aria-label={t('sectionButtonsLabel')}>
      {(['Verse', 'Chorus', 'Bridge', 'Intro', 'Outro'] as const).map(section => <button type="button" key={section} disabled={disabled} onClick={() => insertSection(section)}>{`[${section}]`}</button>)}
    </div>
    {sections.length > 0 && <ul className="lyrics-stats" aria-label={t('statsAriaLabel')}>{sections.map(section => <li key={`${section.name}-${section.lines}`}>{t('sectionStats', section)}</li>)}</ul>}
  </div>;
}
