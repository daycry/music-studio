// @vitest-environment jsdom
import React from 'react';
import {cleanup, render, screen} from '@testing-library/react';
import {afterEach, expect, test, vi} from 'vitest';
vi.mock('next/navigation',()=>({usePathname:()=>'/create',useRouter:()=>({push:vi.fn()})}));
vi.mock('next-intl/server',async()=>({getRequestConfig:(factory:unknown)=>factory}));
import request from '../i18n/request';
import RootLayout from './layout';
import messages from '../messages/es.json';
afterEach(()=>{cleanup();vi.unstubAllGlobals();});
test('el layout establece castellano, traducciones y reproductor fuera de la ruta',async()=>{
 vi.stubGlobal('matchMedia',()=>({matches:false,addEventListener:()=>{},removeEventListener:()=>{}}));
 const config=await request({requestLocale:Promise.resolve(undefined)});
 expect(config.locale).toBe('es');expect(config.messages).toEqual(messages);
 const tree=await RootLayout({children:<section data-testid="route"/>});
 expect(tree.type).toBe('html');expect(tree.props.lang).toBe('es');
 // Renderiza el body de la estructura real: evita html anidado en el document de jsdom.
 render(tree.props.children.props.children);
 expect(screen.getByRole('navigation',{name:messages.shell.navigation})).toBeTruthy();
 const dock=screen.getByRole('region',{name:messages.player.title});
 expect(screen.getByRole('main').contains(dock)).toBe(false);
 expect(screen.getByTestId('route')).toBeTruthy();
});

