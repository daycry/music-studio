// CA-3 (M1/T-08): contraste WCAG AA del tema oscuro y ausencia de colores sueltos fuera de los tokens.
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {expect, test} from 'vitest';

const css = (name: string) => readFileSync(resolve(__dirname, '../styles', name), 'utf8');

function darkTokens(): Record<string, string> {
  const block = /:root,\s*:root\[data-theme="dark"\]\s*\{([^}]*)\}/.exec(css('tokens.css'));
  if (!block) throw new Error('bloque oscuro no encontrado en tokens.css');
  const tokens: Record<string, string> = {};
  for (const match of block[1]!.matchAll(/--([\w-]+)\s*:\s*([^;]+);/g)) tokens[match[1]!] = match[2]!.trim();
  return tokens;
}
function rgb(tokens: Record<string, string>, name: string): [number, number, number] {
  let value = tokens[name];
  if (!value) throw new Error(`token --${name} no definido`);
  const alias = /^var\(--([\w-]+)\)$/.exec(value);
  if (alias) return rgb(tokens, alias[1]!);
  value = value.replace('#', '');
  if (!/^[0-9a-f]{6}$/i.test(value)) throw new Error(`--${name} no es #rrggbb: ${value}`);
  return [0, 2, 4].map(i => parseInt(value.slice(i, i + 2), 16)) as [number, number, number];
}
function luminance([r, g, b]: [number, number, number]): number {
  const [lr, lg, lb] = [r, g, b].map(channel => {
    const c = channel / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  }) as [number, number, number];
  return 0.2126 * lr + 0.7152 * lg + 0.0722 * lb;
}
export function ratio(a: [number, number, number], b: [number, number, number]): number {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x) as [number, number];
  return (hi + 0.05) / (lo + 0.05);
}

const tokens = darkTokens();
const surfaces = ['bg-0', 'bg-1', 'bg-2', 'bg-3'];
// [primer plano, fondos, mínimo]: 4,5 texto normal; 3 texto grande y componentes de UI.
const pairs: Array<[string, string[], number]> = [
  ['text-primary', surfaces, 4.5],
  ['text-secondary', surfaces, 4.5],
  // ux.md: --text-muted nunca para texto informativo sobre --bg-2 o superior (bg-3 queda fuera a propósito).
  ['text-muted', ['bg-0', 'bg-1', 'bg-2'], 4.5],
  ['accent', surfaces, 4.5],
  ['accent-hover', surfaces, 4.5],
  ['danger', surfaces, 4.5],
  ['warning', surfaces, 4.5],
  ['info', surfaces, 4.5],
  ['on-accent', ['accent', 'accent-hover'], 4.5],
  ['border-strong', ['bg-0', 'bg-1'], 3],
  ['wave-idle', ['bg-0', 'bg-1'], 3],
  ['wave-generating', ['bg-0', 'bg-1'], 3],
  ['wave-played', ['bg-0', 'bg-1'], 3],
];

test.each(pairs.flatMap(([fg, backgrounds, minimum]) => backgrounds.map(bg => [fg, bg, minimum] as const)))('--%s sobre --%s alcanza AA (>= %s:1)', (fg, bg, minimum) => {
  expect(ratio(rgb(tokens, fg), rgb(tokens, bg))).toBeGreaterThanOrEqual(minimum);
});

test('el cálculo de contraste coincide con valores conocidos de WCAG', () => {
  expect(ratio([0, 0, 0], [255, 255, 255])).toBeCloseTo(21, 5);
  expect(ratio([255, 255, 255], [255, 255, 255])).toBeCloseTo(1, 5);
});

test('globals.css no define colores sueltos: todo sale de tokens.css', () => {
  expect(css('globals.css').match(/#[0-9a-fA-F]{3,8}\b/g) ?? []).toEqual([]);
});
