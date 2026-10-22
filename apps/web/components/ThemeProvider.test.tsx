// @vitest-environment jsdom
import React from 'react';
import {cleanup, render, screen, fireEvent, act} from '@testing-library/react';
import {afterEach, beforeEach, expect, test, vi} from 'vitest';
import {NextIntlClientProvider} from 'next-intl';
import messages from '../messages/es.json';
import {ThemeProvider} from './ThemeProvider';
let listener: ((event:MediaQueryListEvent)=>void)|undefined;
let remove: ReturnType<typeof vi.fn>;
let media: {matches:boolean;addEventListener:(_type:string,fn:typeof listener)=>void;removeEventListener:ReturnType<typeof vi.fn>};
function emit(matches:boolean){media.matches=matches;listener?.({matches} as MediaQueryListEvent);}
beforeEach(()=>{
 localStorage.clear(); listener=undefined; remove=vi.fn();
 media={matches:true,addEventListener:(_type:string,fn:typeof listener)=>{listener=fn;},removeEventListener:remove};
 vi.stubGlobal('matchMedia',vi.fn(()=>media));
});
afterEach(()=>{cleanup();vi.unstubAllGlobals();vi.restoreAllMocks();document.documentElement.removeAttribute('data-theme');});
function mount(){return render(<NextIntlClientProvider locale="es" messages={messages}><ThemeProvider><div data-testid="child"/></ThemeProvider></NextIntlClientProvider>);}
test('sigue el sistema, guarda elección explícita y limpia listeners',()=>{
 const view=mount();
 expect(document.documentElement.dataset.theme).toBe('dark');
 expect(screen.getByTestId('child')).toBeTruthy();
 const select=screen.getByRole('combobox',{name:messages.theme.label});
 fireEvent.change(select,{target:{value:'light'}});
 expect(document.documentElement.dataset.theme).toBe('light');
 expect(localStorage.getItem('studio.theme')).toBe('light');
 act(()=>emit(true));
 expect(document.documentElement.dataset.theme).toBe('light');
 fireEvent.change(select,{target:{value:'system'}});
 act(()=>emit(false));
 expect(document.documentElement.dataset.theme).toBe('light');
 act(()=>emit(true));
 expect(document.documentElement.dataset.theme).toBe('dark');
 fireEvent.change(select,{target:{value:'dark'}});
 expect(document.documentElement.dataset.theme).toBe('dark');
 view.unmount();expect(remove).toHaveBeenCalled();
});
test('restaura preferencia y funciona con almacenamiento inaccesible',()=>{
 localStorage.setItem('studio.theme','light');
 const view=mount();
 expect((screen.getByRole('combobox') as HTMLSelectElement).value).toBe('light');
 expect(document.documentElement.dataset.theme).toBe('light');
 view.unmount();
 vi.spyOn(Storage.prototype,'getItem').mockImplementation(()=>{throw Error('blocked');});
 vi.spyOn(Storage.prototype,'setItem').mockImplementation(()=>{throw Error('blocked');});
 mount();
 fireEvent.change(screen.getByRole('combobox'),{target:{value:'dark'}});
 expect(document.documentElement.dataset.theme).toBe('dark');
});
test('tolera un navegador que deniega incluso el acceso a localStorage',()=>{
 vi.spyOn(window,'localStorage','get').mockImplementation(()=>{throw Error('blocked');});
 mount();
 expect(document.documentElement.dataset.theme).toBe('dark');
 fireEvent.change(screen.getByRole('combobox'),{target:{value:'light'}});
 expect(document.documentElement.dataset.theme).toBe('light');
});
