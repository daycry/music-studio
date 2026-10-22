// @vitest-environment jsdom
import React from 'react';
import {cleanup, render, screen} from '@testing-library/react';
import {afterEach, expect, test} from 'vitest';
import {NextIntlClientProvider} from 'next-intl';
import messages from '../messages/es.json';
import NotFound from './not-found';
afterEach(cleanup);
test('la página no encontrada muestra un título accesible en castellano y vuelve a Crear',()=>{
 render(<NextIntlClientProvider locale="es" messages={messages}><NotFound/></NextIntlClientProvider>);
 expect(screen.getByRole('heading',{level:1}).textContent).toBe('Página no encontrada');
 expect(screen.getByRole('link',{name:'Volver a Crear'}).getAttribute('href')).toBe('/create');
 expect(screen.getByText('No encontramos la página que buscas.')).toBeTruthy();
});
