# ATS Games & Apps

New static website for **After The Singularity Games Ltd**, built for Cloudflare Workers Static Assets. Game listings are retained in the catalogue but hidden from the published site; the former layout, tracking counter, embeds and placeholder biography are replaced. FotoSwipe is labelled as preparing for launch.

## Content and generation

- `content/site.json`: company identity, product catalogue and locale configuration. Set a game’s `published` flag to control whether its listing and navigation appear.
- `content/apps/*-legal.json`: imported snapshots of each app's canonical legal content. Do not maintain a separate policy by hand.
- `templates/page.html`: shared HTML shell.
- `assets/site.css`: responsive design and shared tokens; local assets contain the approved FotoSwipe mark.
- `scripts/build.py`: generates complete static HTML, sitemap, robots and Cloudflare headers. No browser JavaScript or application server.
- `scripts/check.py`: verifies local links, absence of scripts/placeholders and the unfinished-policy publication boundary.

```sh
python3 scripts/build.py
python3 scripts/check.py dist
python3 -m unittest discover -s tests -v
python3 -m http.server 4177 --bind 127.0.0.1 --directory dist
```

The public output is `dist/`, never the repository root. GitHub Actions validates and packages only this folder; it no longer deploys via GitHub Pages. The previous Pages deployment is not deleted by this change.

For a **local-only** view of unfinished documents:

```sh
python3 scripts/build.py --preview
python3 -m http.server 4178 --bind 127.0.0.1 --directory dist-preview
```

Never upload `dist-preview`. It contains draft notices and `noindex`, which is not an access-control mechanism. Wrangler points exclusively at `dist`.

## Languages

English is the default at `/`; Spanish is available at `/es/`. Every page includes a language selector that preserves the current page. Language choices are ordinary links, without JavaScript, cookies or automatic redirects.

- Shared product identities live in `content/site.json`; translated marketing and interface copy lives in `content/locales/`.
- Add a locale by adding its unique code, path prefix and catalog to `locales`, translating all catalog fields and adding each app’s legal translation file. The default locale alone uses the root path.
- Legal content is authored in Spanish in the native app. Reviewed translations in `content/apps/` record the SHA-256 of that imported source. After syncing changes, review the full translation before updating its checksum; do not merely refresh the checksum to bypass review.
- Builds reject incomplete catalogs, missing legal paragraphs, changed placeholders and translations tied to an old source. The native app’s language is unaffected.
- Canonical links, reciprocal `hreflang`, English `x-default` and the sitemap are generated from locale configuration.

## FotoSwipe legal source

Sync from the native application's `FotoSwipe/Resources/LegalContent.json`:

```sh
python3 scripts/sync_legal.py fotoswipe /absolute/path/to/LegalContent.json
```

`build-manifest.json` records the source checksum and which pages were generated. Privacy, support and terms are now complete and publicly available. The owner selected up to 12 months after case closure for support email retention, with early deletion of unnecessary attachments and limited exceptions. Public URLs and provider details match the native canonical JSON. Future changes must still be imported from that source.

The published website uses only local assets. Hidden game listings do not emit images or links into the output. Re-enabling those Steam-hosted images requires reviewing the website privacy disclosure first. There are no third-party fonts, counters, analytics scripts, forms or Steam iframes. Outbound links open the relevant external service only when selected.

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

5. Validate the returned `workers.dev` URL, then add `atsgames.com` and `www.atsgames.com` as custom domains in the Cloudflare dashboard. Both verified custom domains are declared in `wrangler.jsonc` so future deployments retain them. Redirect www to the primary domain if desired.
6. Verify public HTTPS, navigation, images, support, missing-policy 404 and mobile layout. Add actual privacy URL only after its content is complete.

No account IDs or credentials belong in Git. No paid plan, database, server script or mail service is required for these static pages. Static asset requests are free; optional dynamic services have separate limits/pricing. The public build has been deployed through the dashboard; custom-domain setup is tracked below. A dry run by itself is not a deployment.

## Migration state

Updated 2026-10-23 on `codex/cloudflare-fotoswipe`:

- Live at https://atsgames.com/ and https://www.atsgames.com/ on Cloudflare Workers Static Assets. The dashboard confirms the zone is active and both domains route to production. GoDaddy remains the registrar; Cloudflare is the DNS/hosting provider on Free.
- GoDaddy accepted the assigned nameservers `kia.ns.cloudflare.com` and `wells.ns.cloudflare.com`. Resolver caches can retain the prior delegation temporarily.
- With the owner's explicit confirmation, the two imported parking A records and `www` CNAME were replaced by Worker custom domains. `_domainconnect` remains DNS-only and `_dmarc` is preserved. No mail service was configured.
- Public HTTPS checks for both homepages, FotoSwipe, support and CSS match the local build. The platform canonicalizes `/fotoswipe/support.html` to `/fotoswipe/support` (307, then 200). Unknown paths return 404. Always Use HTTPS is enabled on the zone.
- The fallback https://atsgames.jorgere-1.workers.dev/ remains available (dashboard asset version `2493c531`). No paid plan, dynamic worker code or analytics script was enabled.
- PR #1 records the replacement design. The old GitHub Pages deployment has not been removed; DNS now serves Cloudflare. Builds validate/package in GitHub Actions; publishing is currently manual through Cloudflare or Wrangler.
- Privacy, support and terms are published at `/fotoswipe/privacy`, `/fotoswipe/support` and `/fotoswipe/terms`. Public responses match the generated files. This does not mean the app is submitted or approved by Apple.

Official references: [static assets setup](https://developers.cloudflare.com/workers/static-assets/get-started/), [pricing](https://developers.cloudflare.com/workers/static-assets/billing-and-limitations/), [custom domains](https://developers.cloudflare.com/workers/configuration/routing/custom-domains/).
