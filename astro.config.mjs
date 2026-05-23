import { defineConfig } from 'astro/config';
import cloudflare from '@astrojs/cloudflare';

export default defineConfig({
  site: 'https://dianda.dpdns.org',
  output: 'static',
  i18n: {
    defaultLocale: 'zh',
    locales: ['zh', 'en'],
    routing: {
      prefixDefaultLocale: false,
    },
  },
  adapter: cloudflare({
    mode: 'directory',
    // 2026 新增：在适配器中显式尝试声明平台功能 (如果支持)
  }),
  vite: {
    ssr: {
      external: ['node:fs', 'node:path', 'node:process'],
    },
  },
});
