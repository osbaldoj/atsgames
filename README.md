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

5. Validate the returned `workers.dev` URL, then add `atsgames.com` and `www.atsgames.com` as custom domains in the Cloudflare dashboard. Both verified custom domains are declared in `wrangler.jsonc` so future deployments retain them. Redirect www to the primary domain if desired.
6. Verify public HTTPS, navigation, images, support, missing-policy 404 and mobile layout. Add actual privacy URL only after its content is complete.

No account IDs or credentials belong in Git. No paid plan, database, server script or mail service is required for these static pages. Static asset requests are free; optional dynamic services have separate limits/pricing. The public build has been deployed through the dashboard; custom-domain setup is tracked below. A dry run by itself is not a deployment.

## Migration state

Updated 2026-10-23 on `codex/cloudflare-fotoswipe`:

- Live at https://atsgames.com/ and https://www.atsgames.com/ on Cloudflare Workers Static Assets. The dashboard confirms the zone is active and both domains route to production. GoDaddy remains the registrar; Cloudflare is the DNS/hosting provider on Free.
- GoDaddy accepted the assigned nameservers `kia.ns.cloudflare.com` and `wells.ns.cloudflare.com`. Resolver caches can retain the prior delegation temporarily.
- With the owner's explicit confirmation, the two imported parking A records and `www` CNAME were replaced by Worker custom domains. `_domainconnect` remains DNS-only and `_dmarc` is preserved. No mail service was configured.
- Public HTTPS checks for both homepages, FotoSwipe, support and CSS match the local build. The platform canonicalizes `/fotoswipe/support.html` to `/fotoswipe/support` (307, then 200). Unfinished privacy and unknown paths return 404. Always Use HTTPS is enabled on the zone.
- The fallback https://atsgames.jorgere-1.workers.dev/ remains available (dashboard asset version `9cb1dc80`). No paid plan, dynamic worker code or analytics script was enabled.
- PR #1 records the replacement design. The old GitHub Pages deployment has not been removed; DNS now serves Cloudflare. Builds validate/package in GitHub Actions; publishing is currently manual through Cloudflare or Wrangler.
- Privacy and terms remain unpublished until the owner's deferred retention decision and canonical legal fields are complete.

Official references: [static assets setup](https://developers.cloudflare.com/workers/static-assets/get-started/), [pricing](https://developers.cloudflare.com/workers/static-assets/billing-and-limitations/), [custom domains](https://developers.cloudflare.com/workers/configuration/routing/custom-domains/).
