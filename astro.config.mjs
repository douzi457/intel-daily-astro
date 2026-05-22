import { defineConfig } from 'astro/config';
import cloudflare from '@astrojs/cloudflare';

export default defineConfig({
  site: 'https://dianda.dpdns.org',
  output: 'static',
  i18n: {
    defaultLocale: 'zh',
    locales: ['zh', 'en'],
    routing: {
      prefixDefaultLocale: false, // zh 路径不加前缀，/en 路径加前缀
    },
  },
  adapter: cloudflare({
    mode: 'directory',
  }),
});
