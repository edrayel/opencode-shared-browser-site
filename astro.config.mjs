// @ts-check
import { defineConfig } from 'astro/config'

import tailwindcss from '@tailwindcss/vite'
import sitemap from '@astrojs/sitemap'

// Set SITE_URL in the deploy environment (or here) so canonical URLs, the
// sitemap and og:image resolve against the real domain. The fallback is a
// placeholder — override it rather than shipping this.
const site = process.env.SITE_URL ?? 'https://opencode-shared-browser.dev'

// https://astro.build/config
export default defineConfig({
  site,
  trailingSlash: 'always',
  integrations: [sitemap()],
  vite: {
    plugins: [tailwindcss()],
  },
})