// CA-4 (M1/T-08): toda clave de next-intl usada estáticamente existe en messages/es.json y los
// estados/tareas que la UI muestra tienen traducción.
import {readdirSync, readFileSync, statSync} from 'node:fs';
import {join, relative, resolve} from 'node:path';
import {expect, test} from 'vitest';
import messages from '../messages/es.json';

const root = resolve(__dirname, '..');
function sources(dir: string): string[] {
  return readdirSync(dir).flatMap(name => {
    const path = join(dir, name);
    if (name === 'node_modules' || name === '.next') return [];
    if (statSync(path).isDirectory()) return sources(path);
    return /\.tsx$/.test(name) && !/\.test\.tsx$/.test(name) ? [path] : [];
  });
}
/** Primer argumento (hasta la coma de nivel superior) de cada llamada `t(`. */
function firstArguments(code: string, name: string): string[] {
  const found: string[] = [];
  for (const match of code.matchAll(new RegExp('(?<![\\w.])' + name + '\\(', 'g'))) {
    let depth = 0;
    let index = match.index! + match[0].length;
    const start = index;
    for (; index < code.length; index++) {
      const char = code[index]!;
      if (char === '(' || char === '[' || char === '{') depth++;
      else if (char === ')' || char === ']' || char === '}') { if (depth === 0) break; depth--; }
      else if (char === ',' && depth === 0) break;
    }
    found.push(code.slice(start, index));
  }
  return found;
}
function lookup(path: string): unknown {
  return path.split('.').reduce<unknown>((node, part) => (node && typeof node === 'object' ? (node as Record<string, unknown>)[part] : undefined), messages);
}

test('toda clave estática t(...) existe en es.json bajo su namespace', () => {
  const missing: string[] = [];
  let checked = 0;
  for (const file of [...sources(join(root, 'app')), ...sources(join(root, 'components'))]) {
    const code = readFileSync(file, 'utf8');
    for (const declaration of code.matchAll(/const (\w+) = useTranslations\((?:'([^']+)')?\)/g)) {
      const prefix = declaration[2] ? declaration[2] + '.' : '';
      for (const argument of firstArguments(code, declaration[1]!)) {
        if (argument.includes('${') || argument.includes('+') || argument.includes('(')) continue;
        for (const key of argument.matchAll(/'([A-Za-z][\w.]*)'/g)) {
          checked++;
          if (typeof lookup(prefix + key[1]) !== 'string') missing.push(`${relative(root, file)}: ${prefix}${key[1]}`);
        }
      }
    }
  }
  expect(checked).toBeGreaterThan(100);
  expect(missing).toEqual([]);
});

test('estados de canción, toma, tarea y unidades se traducen desde es.json', () => {
  const wanted = [
    ...['draft', 'in_progress', 'final', 'archived'].map(v => `enums.songStatus.${v}`),
    ...['queued', 'running', 'ready', 'failed', 'cancelled'].map(v => `enums.takeStatus.${v}`),
    ...['music_song', 'music_instrumental'].map(v => `enums.task.${v}`),
    'enums.unknown', 'units.mib', 'units.none',
  ];
  expect(wanted.filter(key => typeof lookup(key) !== 'string')).toEqual([]);
});
