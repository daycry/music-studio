// Claves de messages/es.json (namespace `enums`) para los valores de estado y tarea que llegan de la API.
const SONG_STATUS = ['draft', 'in_progress', 'final', 'archived'];
const TAKE_STATUS = ['queued', 'running', 'ready', 'failed', 'cancelled'];
const TASKS = ['music.song', 'music.instrumental'];
export const songStatusKey = (value: string) => SONG_STATUS.includes(value) ? `songStatus.${value}` : 'unknown';
export const takeStatusKey = (value: string) => TAKE_STATUS.includes(value) ? `takeStatus.${value}` : 'unknown';
export const taskKey = (value: string) => TASKS.includes(value) ? `task.${value.replace('.', '_')}` : 'unknown';
