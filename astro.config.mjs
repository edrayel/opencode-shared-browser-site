// @ts-check
import { defineConfig } from 'astro/config'

import tailwindcss from '@tailwindcss/vite'
import sitemap from '@astrojs/sitemap'

// Set SITE_URL in the deploy environment (or here) so canonical URLs, the
// sitemap and og:image resolve against the real domain. Defaults to the
// live domain, osb.edwardrajah.com; override via SITE_URL if needed.
const site = process.env.SITE_URL ?? 'https://osb.edwardrajah.com'

// https://astro.build/config
export default defineConfig({
  site,
  trailingSlash: 'always',
  integrations: [sitemap()],
  vite: {
    plugins: [tailwindcss()],
  },
})