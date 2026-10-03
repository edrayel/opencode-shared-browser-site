# opencode-shared-browser — site

Marketing and documentation site for
[opencode-shared-browser](https://github.com/edrayel/opencode-shared-browser),
the plugin that lets several opencode instances drive one signed-in Chrome.

## Stack

Astro 7 with Tailwind CSS v4. Static output, no client framework, no runtime
JavaScript unless a page earns it.

The design system is the **Vercel Geist** one — radius 0, no shadows, hairline
borders carrying all elevation, monochrome first, colour only where it carries
meaning. Two deliberate deviations, both documented in
`src/styles/global.css`: dark is the default surface rather than light, and
there are two semantic accents (`allow` / `deny`) rather than one brand accent,
because the product's whole vocabulary is allow versus deny.

Type is Geist Sans and Geist Mono, self-hosted via `@fontsource` (OFL-1.1).

## Commands

```bash
pnpm install
pnpm dev        # dev server
pnpm build      # static build to dist/
pnpm preview    # serve the built output
```

## Layout

```
src/
├─ styles/global.css     design tokens (@theme, OKLCH) + base styles
├─ layouts/
│  ├─ Base.astro         head, meta, header, footer
│  └─ Docs.astro        docs shell with side navigation
├─ components/           CodeBlock, GuardTable, Callout
├─ data/guards.ts        guard rules, single source for the table
└─ pages/
   ├─ index.astro        landing
   └─ docs/              install, guards, limitations
scripts/generate-assets.py
assets/source/logo.jpg   committed so assets stay reproducible
```

## Brand assets

Icons and the social card are generated, not hand-made:

```bash
python3 scripts/generate-assets.py
```

Requires Pillow, cairosvg and fontTools. Two things it does that are worth
knowing before changing it:

- **The mark's bounding box is found by luminance profiles**, not a fixed crop.
  The logo's field is a gradient, so thresholding on distance-from-corner finds
  nothing.
- **`favicon.svg` is a simplified two-ring silhouette**, not the detailed
  render, which is illegible below about 32px. The 16/32px PNGs and the `.ico`
  are rasterised from that simplified mark; 48px and the 180px touch icon keep
  the detailed version. Geometry was compared at 16/32/48px.

The matting thresholds for lifting the mark off its own navy are measured, not
guessed — background pixels sit at distance 4–60 from the fill while ring
surfaces start near 70. An earlier guess at 16/30 kept the background opaque and
left a visible tile.

## Site URL

`astro.config.mjs` reads `SITE_URL`, falling back to a placeholder. Override it
in the deploy environment so canonical URLs, the sitemap and `og:image` resolve
against the real domain.

## Content

Copy is drawn from the plugin's own `README.md` and `docs/`. The limitations
page is deliberately prominent: two of those limits are inherent to sharing one
browser process and cannot be guarded away, and a paying user should read that
before they find it themselves.

## License

Apache-2.0. The Geist typefaces are OFL-1.1, © Vercel.