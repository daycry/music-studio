import {describe, expect, test} from 'vitest';
import {readTheme, resolveTheme, persistTheme} from './theme';
describe('preferencia de tema', () => {
 test('respeta una elección explícita y resuelve el sistema', () => {
  expect(resolveTheme('light', true)).toBe('light');
  expect(resolveTheme('dark', false)).toBe('dark');
  expect(resolveTheme('system', true)).toBe('dark');
  expect(resolveTheme('system', false)).toBe('light');
 });
 test('lee solo preferencias válidas y tolera almacenamiento bloqueado', () => {
  for (const value of ['light','dark','system']) expect(readTheme({getItem:()=>value})).toBe(value);
  for (const value of [null,'invalid']) expect(readTheme({getItem:()=>value})).toBe('system');
  expect(readTheme({getItem:()=>{throw Error('blocked');}})).toBe('system');
 });
 test('guarda la elección sin romper si el almacenamiento falla', () => {
  const stored: string[]=[];
  persistTheme({setItem:(key,value)=>stored.push(key,value)},'dark');
  expect(stored).toEqual(['studio.theme','dark']);
  expect(()=>persistTheme({setItem:()=>{throw Error('blocked');}},'light')).not.toThrow();
 });
});

