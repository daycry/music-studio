import createNextIntlPlugin from 'next-intl/plugin';
import type {NextConfig} from 'next';
const withNextIntl = createNextIntlPlugin('./i18n/request.ts');
const config: NextConfig = {reactStrictMode:true, poweredByHeader:false};
export default withNextIntl(config);

