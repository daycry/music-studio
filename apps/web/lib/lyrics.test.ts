import { readFileSync, existsSync } from 'node:fs';
import { describe, expect, test } from 'vitest';

const cases = JSON.parse(readFileSync(new URL('../../../packages/contracts/lyrics-cases.json', import.meta.url), 'utf8')).cases as {id: string; input: string; expected: unknown}[];
describe('lyrics contrato compartido', () => {
  for (const fixture of cases) {
    test(fixture.id, async () => {
      const path = new URL('./lyrics.ts', import.meta.url);
      const parse = existsSync(path) ? (await import('./lyrics')).parseLyrics : (original: string) => ({ version: 1, original, sections: [], annotations: [], warnings: [] });
      expect(parse(fixture.input)).toEqual(fixture.expected);
    });
    test(fixture.id + ' slices literales', async () => {
      const result = (await import('./lyrics')).parseLyrics(fixture.input);
      for (const section of result.sections) {
        expect(result.original.slice(section.aliasRange.start, section.aliasRange.end)).toBe(section.alias);
        if (section.directions) expect(result.original.slice(section.directions.range.start, section.directions.range.end)).toBe(section.directions.text);
      }
      for (const annotation of result.annotations) expect(result.original.slice(annotation.range.start, annotation.range.end)).toBe(annotation.text);
    });
  }
});
