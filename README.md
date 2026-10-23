# ATS Games & Apps

New static website for **After The Singularity Games Ltd**, built for Cloudflare Workers Static Assets. Existing game listings are retained; the former layout, tracking counter, embeds and placeholder biography are replaced. FotoSwipe is labelled as preparing for launch.

## Content and generation

- `content/site.json`: company identity, games, app catalogue, home-page copy. Add products here.
- `content/apps/*-legal.json`: imported snapshots of each app's canonical legal content. Do not maintain a separate policy by hand.
- `templates/page.html`: shared HTML shell.
- `assets/site.css`: responsive design and shared tokens; local assets contain the approved FotoSwipe mark.
- `scripts/build.py`: generates complete static HTML, sitemap, robots and Cloudflare headers. No browser JavaScript or application server.
- `scripts/check.py`: verifies local links, absence of scripts/placeholders and the unfinished-policy publication boundary.

```sh
python3 scripts/build.py
python3 scripts/check.py dist
python3 -m http.server 4177 --bind 127.0.0.1 --directory dist
```

The public output is `dist/`, never the repository root. GitHub Actions validates and packages only this folder; it no longer deploys via GitHub Pages. The previous Pages deployment is not deleted by this change.

For a **local-only** view of unfinished documents:

```sh
python3 scripts/build.py --preview
python3 -m http.server 4178 --bind 127.0.0.1 --directory dist-preview
```

Never upload `dist-preview`. It contains draft notices and `noindex`, which is not an access-control mechanism. Wrangler points exclusively at `dist`.

## FotoSwipe legal source

Sync from the native application's `FotoSwipe/Resources/LegalContent.json`:

```sh
python3 scripts/sync_legal.py fotoswipe /absolute/path/to/LegalContent.json
```

`build-manifest.json` records the source checksum and which pages were generated. Currently support is public-build eligible; privacy and terms remain excluded until operator, email, host, retention and public HTTPS URLs are complete. The user deferred the support-retention decision. Do not invent it. After publishing and verifying the final URLs, update the app's canonical JSON and import it again.

The corporate homepage uses the existing game header images hosted by Steam, which causes browser requests to that provider. FotoSwipe and its help pages use only local assets. There are no third-party fonts, counters, analytics scripts, forms or Steam iframes. Outbound links open the relevant external service only when selected.

## Cloudflare (Free)

1. Create/sign into the ATS owner's Cloudflare account and verify the email.
2. Add `atsgames.com` to Cloudflare's Free zone; review imported DNS records before changing nameservers at GoDaddy. Preserve mail, verification and DNSSEC settings as appropriate.
3. In Workers & Pages create a Worker from this repository. Build command: `python3 scripts/build.py && python3 scripts/check.py dist`. Deploy command: `npx wrangler deploy`. Install dependencies with the checked-in lockfile (`npm ci`). Configure the intended branch explicitly; default production is `main`.
4. Or deploy from a trusted local session:

```sh
npm ci --ignore-scripts
npx wrangler login
npm run deploy
```

5. Validate the returned `workers.dev` URL, then add `atsgames.com` and `www.atsgames.com` as custom domains in the Cloudflare dashboard. No custom domain routes are configured locally until the zone is owned/active. Redirect www to the primary domain if desired.
6. Verify public HTTPS, navigation, images, support, missing-policy 404 and mobile layout. Add actual privacy URL only after its content is complete.

No account IDs or credentials belong in Git. No paid plan, database, server script or mail service is required for these static pages. Static asset requests are free; optional dynamic services have separate limits/pricing. Cloudflare and GoDaddy login/DNS setup remain required; a dry run is not a deployment.

## Migration state

Prepared on 2026-10-23 in `codex/cloudflare-fotoswipe`. The user requested a completely new design. The domain purchase at GoDaddy is user-confirmed; public DNS still pointed to GoDaddy at preparation time. Deployment awaits Cloudflare account access. Existing GitHub Pages configuration has not been removed, and production DNS has not been changed.

Official references: [static assets setup](https://developers.cloudflare.com/workers/static-assets/get-started/), [pricing](https://developers.cloudflare.com/workers/static-assets/billing-and-limitations/), [custom domains](https://developers.cloudflare.com/workers/configuration/routing/custom-domains/).
