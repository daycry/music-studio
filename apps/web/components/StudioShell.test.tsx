// @vitest-environment jsdom
import React from 'react';
import {cleanup, render, screen} from '@testing-library/react';
import {afterEach, expect, test, vi} from 'vitest';
import {NextIntlClientProvider} from 'next-intl';
import messages from '../messages/es.json';
import {StudioShell} from './StudioShell';
vi.mock('next/navigation',()=>({usePathname:vi.fn(()=>'/create'),useRouter:vi.fn(()=>({push:vi.fn()}))}));
import {usePathname} from 'next/navigation';
afterEach(cleanup);
test('ofrece navegación accesible y conserva el dock al cambiar la página',()=>{
 const view=render(<NextIntlClientProvider locale="es" messages={messages}><StudioShell><section data-testid="route"/></StudioShell></NextIntlClientProvider>);
 expect(screen.getByRole('navigation',{name:messages.shell.navigation})).toBeTruthy();
 for(const [name,url] of [[messages.nav.create,'/create'],[messages.nav.songs,'/songs'],[messages.nav.system,'/system']]) expect(screen.getByRole('link',{name}).getAttribute('href')).toBe(url);
 expect(screen.getByRole('link',{name:messages.nav.create}).getAttribute('aria-current')).toBe('page');
 expect(screen.getByRole('link',{name:messages.shell.skip}).getAttribute('href')).toBe('#content');
 const dock=screen.getByRole('region',{name:messages.player.title});
 vi.mocked(usePathname).mockReturnValue('/songs');
 view.rerender(<NextIntlClientProvider locale="es" messages={messages}><StudioShell><section data-testid="new-route"/></StudioShell></NextIntlClientProvider>);
 expect(screen.getByRole('region',{name:messages.player.title})).toBe(dock);
 expect(screen.getByRole('link',{name:messages.nav.songs}).getAttribute('aria-current')).toBe('page');
 expect(screen.getByRole('link',{name:messages.nav.create}).hasAttribute('aria-current')).toBe(false);
 expect(screen.getByRole('main').contains(dock)).toBe(false);
});

