import {expect, test} from 'vitest';
import messages from '../messages/es.json';
import {songStatusKey, takeStatusKey, taskKey} from './enum-labels';
const lookup = (key: string) => key.split('.').reduce<unknown>((node, part) => (node as Record<string, unknown> | undefined)?.[part], messages.enums);
test('cada valor conocido y el desconocido resuelven a una cadena de es.json', () => {
  for (const key of [...['draft', 'in_progress', 'final', 'archived', 'x'].map(songStatusKey), ...['queued', 'running', 'ready', 'failed', 'cancelled', 'x'].map(takeStatusKey), ...['music.song', 'music.instrumental', 'x.y'].map(taskKey)]) {
    expect(typeof lookup(key), key).toBe('string');
  }
  expect(taskKey('music.song')).toBe('task.music_song');
});
