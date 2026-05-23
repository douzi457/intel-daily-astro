import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://dianda.dpdns.org',
  output: 'static', // 纯静态模式
  i18n: {
    defaultLocale: 'zh',
    locales: ['zh', 'en'],
    routing: {
      prefixDefaultLocale: false,
    },
  },
  // 删掉了 cloudflare 适配器，回归 Pages 默认的极速静态托管
  vite: {
    ssr: {
      external: ['node:fs', 'node:path', 'node:process'],
    },
  },
});
