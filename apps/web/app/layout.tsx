import type {ReactNode} from 'react';
import {NextIntlClientProvider} from 'next-intl';
import request from '../i18n/request';
import {ThemeProvider} from '../components/ThemeProvider';
import {StudioShell} from '../components/StudioShell';
import '@fontsource/inter/latin-400.css';
import '@fontsource/inter/latin-600.css';
import '@fontsource/bricolage-grotesque/latin-600.css';
import '@fontsource/jetbrains-mono/latin-400.css';
import '../styles/globals.css';

export default async function RootLayout({children}:{children:ReactNode}) {
  const {locale, messages} = await request({requestLocale:Promise.resolve('es')});
  return <html lang={locale} suppressHydrationWarning><body>
    <NextIntlClientProvider locale={locale} messages={messages}>
      <ThemeProvider><StudioShell>{children}</StudioShell></ThemeProvider>
    </NextIntlClientProvider>
  </body></html>;
}

