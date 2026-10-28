import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://daily.dianda.dpdns.org',
  output: 'static',
  integrations: [sitemap({
    filter: (page) => !page.includes('/daily/'),
    i18n: {
      defaultLocale: 'zh',
      locales: {
        zh: 'zh-CN',
        en: 'en-US',
      },
    },
  })],
  i18n: {
    defaultLocale: 'zh',
    locales: ['zh', 'en'],
    routing: {
      prefixDefaultLocale: false,
    },
  },
});
