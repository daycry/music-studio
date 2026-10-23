// CA-1 (M1/T-08): api.d.ts debe ser exactamente lo que genera `pnpm gen` sobre openapi.json.
import {execFileSync} from 'node:child_process';
import {mkdtempSync, readFileSync, rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join, resolve} from 'node:path';
import {expect, test} from 'vitest';

const root = resolve(__dirname, '..');
const normalize = (text: string) => text.replace(/\r\n/g, '\n');

test('lib/generated/api.d.ts coincide con la generación sobre packages/contracts/openapi.json', () => {
  const dir = mkdtempSync(join(tmpdir(), 'studio-gen-'));
  try {
    const out = join(dir, 'api.d.ts');
    const cli = join(root, 'node_modules', 'openapi-typescript', 'bin', 'cli.js');
    execFileSync(process.execPath, [cli, resolve(root, '../../packages/contracts/openapi.json'), '-o', out], {stdio: 'pipe'});
    expect(normalize(readFileSync(out, 'utf8'))).toBe(normalize(readFileSync(join(root, 'lib/generated/api.d.ts'), 'utf8')));
  } finally {
    rmSync(dir, {recursive: true, force: true});
  }
}, 60_000);
