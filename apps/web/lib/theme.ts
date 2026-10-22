export type ThemeChoice = 'system' | 'dark' | 'light';
export function resolveTheme(choice: ThemeChoice, dark: boolean): 'dark' | 'light' {
  return choice === 'system' ? (dark ? 'dark' : 'light') : choice;
}
export function readTheme(storage: Pick<Storage, 'getItem'>): ThemeChoice {
  try {
    const value = storage.getItem('studio.theme');
    if (value === 'light' || value === 'dark' || value === 'system') return value;
  } catch { /* La preferencia del sistema funciona sin almacenamiento. */ }
  return 'system';
}
export function persistTheme(storage: Pick<Storage, 'setItem'>, choice: ThemeChoice): void {
  try { storage.setItem('studio.theme', choice); } catch { /* Sigue disponible durante esta sesión. */ }
}
