/** Parser puro: los offsets nativos de JS son unidades UTF-16. */
export interface LyricsRange { start: number; end: number }
export type LyricsKind = 'intro' | 'verse' | 'pre-chorus' | 'chorus' | 'post-chorus' | 'bridge' | 'hook' | 'break' | 'instrumental' | 'solo' | 'outro';
export type LyricsWarningCode = 'EMPTY_SECTION' | 'UNKNOWN_TAG' | 'MALFORMED_TAG';
export interface LyricsSection {
  kind: LyricsKind; alias: string; aliasRange: LyricsRange; number: number | null;
  qualifier: 'final' | null; headerRange: LyricsRange; bodyRange: LyricsRange;
  directions: { text: string; range: LyricsRange } | null; empty: boolean;
}
export interface LyricsWarning { code: LyricsWarningCode; range: LyricsRange }
export interface LyricsAnnotation extends LyricsWarning { text: string }
export interface ParsedLyrics { version: 1; original: string; sections: LyricsSection[]; annotations: LyricsAnnotation[]; warnings: LyricsWarning[] }

const aliases: Record<LyricsKind, string[]> = {
  intro: ['intro', 'introducción'], verse: ['verse', 'verses', 'verso', 'versos', 'estrofa', 'estrofas'],
  'pre-chorus': ['pre-chorus', 'pre chorus', 'precoro', 'pre-coro', 'preestribillo'],
  chorus: ['chorus', 'choruses', 'coro', 'coros', 'estribillo', 'estribillos'],
  'post-chorus': ['post-chorus', 'post chorus', 'postcoro', 'post-coro', 'postestribillo'],
  bridge: ['bridge', 'puente'], hook: ['hook', 'gancho'], break: ['break', 'pausa'],
  instrumental: ['instrumental'], solo: ['solo'], outro: ['outro', 'salida'],
};
const trimHorizontal = (text: string) => text.replace(/^[ \t]+|[ \t]+$/g, '');
const range = (start: number, end: number): LyricsRange => ({ start, end });

export function parseLyrics(original: string): ParsedLyrics {
  const result: ParsedLyrics = { version: 1, original, sections: [], annotations: [], warnings: [] };
  let cursor = 0;
  while (cursor < original.length) {
    const start = cursor;
    while (cursor < original.length && original[cursor] !== '\r' && original[cursor] !== '\n') cursor++;
    const contentEnd = cursor;
    if (original[cursor] === '\r') cursor++;
    if (original[cursor] === '\n') cursor++;
    let left = start;
    if (left === 0 && original[left] === '\uFEFF') left++;
    while (original[left] === ' ' || original[left] === '\t') left++;
    const candidate = original.slice(left, contentEnd).replace(/[ \t]+$/g, '');
    if (!/^\**\[/.test(candidate)) continue;
    const headerRange = range(start, cursor);
    let code: LyricsWarningCode = 'MALFORMED_TAG';
    const wrapped = candidate.startsWith('**[') && candidate.endsWith(']**');
    const bare = candidate.startsWith('[') && candidate.endsWith(']');
    const inner = wrapped ? candidate.slice(3, -3) : bare ? candidate.slice(1, -1) : null;
    if (inner !== null && !/[\[\]]/.test(inner)) {
      const innerStart = left + (wrapped ? 3 : 1);
      const divider = inner.indexOf(' - ');
      const structure = divider === -1 ? inner : inner.slice(0, divider);
      const clean = trimHorizontal(structure);
      const tokens = clean.split(/[ \t]+/);
      const tail = tokens[tokens.length - 1];
      let alias = clean;
      let number: number | null = null;
      let qualifier: 'final' | null = null;
      let invalidNumber = false;
      if (tokens.length > 1 && (tail.toLowerCase() === 'final' || /^[0-9]+$/.test(tail))) {
        alias = clean.slice(0, clean.length - tail.length).replace(/[ \t]+$/g, '');
        if (tail.toLowerCase() === 'final') qualifier = 'final';
        else if (/^[1-9][0-9]*$/.test(tail) && Number.isSafeInteger(Number(tail))) number = Number(tail);
        else invalidNumber = true;
      }
      const normalized = alias.toLowerCase().replace(/[ \t]+/g, ' ');
      const kind = (Object.keys(aliases) as LyricsKind[]).find(key => aliases[key].includes(normalized));
      if (kind && !invalidNumber) {
        const previous = result.sections.at(-1);
        if (previous) previous.bodyRange.end = start;
        const aliasStart = innerStart + structure.length - structure.replace(/^[ \t]+/, '').length;
        result.sections.push({ kind, alias, aliasRange: range(aliasStart, aliasStart + alias.length), number, qualifier,
          headerRange, bodyRange: range(cursor, original.length),
          directions: divider === -1 ? null : { text: inner.slice(divider + 3), range: range(innerStart + divider + 3, innerStart + inner.length) }, empty: false });
        continue;
      }
      if (!invalidNumber && /^\p{L}+(?:[ \t-]+\p{L}+)*$/u.test(alias)) code = 'UNKNOWN_TAG';
    }
    result.annotations.push({ code, range: headerRange, text: original.slice(start, cursor) });
    result.warnings.push({ code, range: headerRange });
  }
  for (const section of result.sections) {
    section.empty = /^[ \t\r\n]*$/.test(original.slice(section.bodyRange.start, section.bodyRange.end));
    if (section.empty) result.warnings.push({ code: 'EMPTY_SECTION', range: section.headerRange });
  }
  result.warnings.sort((a, b) => a.range.start - b.range.start || (a.code < b.code ? -1 : a.code > b.code ? 1 : 0));
  return result;
}
