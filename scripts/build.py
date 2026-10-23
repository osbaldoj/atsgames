#!/usr/bin/env python3
"""Generate every locale from shared templates; refuse incomplete translations."""
import argparse
import html
import json
import re
import shutil
from string import Template
from urllib.parse import quote
from localization import ROOT, read_json, legal_ready, localized_legal, validate_locales, route, canonical_route, output_path

esc = html.escape


def link(url, label, classes='', attrs=''):
    return f'<a href="{esc(url, quote=True)}" class="{classes}" {attrs}>{esc(label)}</a>'


class SiteBuilder:
    def __init__(self, preview=False):
        self.config = read_json(ROOT / 'content/site.json')
        validate_locales(self.config)
        self.games = [game for game in self.config['games'] if game.get('published', True)]
        self.preview = preview
        self.output = ROOT / ('dist-preview' if preview else 'dist')
        self.template = Template((ROOT / 'templates/page.html').read_text())
        self.pages = []
        self.manifests = []

    def page(self, locale, text, path, title, description, body, app=None):
        ui = text['ui']
        home = route(locale)
        nav_items = [(home + '#apps', ui['apps']), (home + '#contact', ui['contact'])]
        if self.games:
            nav_items.insert(0, (home + '#games', ui['games']))
        if app:
            nav_items = [(home, 'ATS'), (route(locale, app['id'] + '/index.html'), app['name']),
                         (route(locale, app['id'] + '/support.html'), ui['help'])]
        navigation = ''.join(link(url, label) for url, label in nav_items)
        switches = []
        alternates = []
        for other in self.config['locales']:
            url = route(other, path)
            current = 'aria-current="true"' if other['code'] == locale['code'] else ''
            switches.append(link(url, other['label'], attrs=f'lang="{other["code"]}" hreflang="{other["code"]}" {current}'))
            alternates.append(f'<link rel="alternate" hreflang="{other["code"]}" href="{self.config["domain"]}{canonical_route(other, path)}" />')
        default = next(item for item in self.config['locales'] if item['code'] == self.config['defaultLocale'])
        canonical = self.config['domain'] + canonical_route(locale, path)
        seo = f'<link rel="canonical" href="{canonical}" />' + ''.join(alternates)
        seo += f'<link rel="alternate" hreflang="x-default" href="{self.config["domain"]}{canonical_route(default, path)}" />'
        relative = output_path(locale, path)
        target = self.output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.template.substitute(
            lang=locale['code'], title=esc(title), description=esc(description), seo=seo,
            robots='<meta name="robots" content="noindex,nofollow">' if self.preview or path == '404.html' else '',
            skip=esc(ui['skip']), home_url=home, brand_home=esc(ui['brandHome']),
            nav_label=esc(ui['navigation']), language_label=esc(ui['language']), languages=''.join(switches),
            navigation=navigation, body=body, company=esc(self.config['company']), location=esc(ui['location']),
            year=self.config['year'], email=esc(self.config['email'], quote=True)), encoding='utf-8')
        self.pages.append({'path': relative, 'logicalPath': path, 'locale': locale['code'], 'url': canonical})

    def game(self, game, copy, ui, index):
        name = esc(game['name'])
        image = f'<img src="{esc(game["image"], quote=True)}" alt="{name}" width="460" height="215" loading="lazy">'
        return f'''<article class="game"><a class="game-image" href="{esc(game['url'])}" rel="noreferrer" aria-label="{esc(ui['onSteam'].format(name=game['name']))}">{image}<span class="image-arrow" aria-hidden="true">↗</span></a><div class="game-body"><div class="project-meta"><span>{index:02d} / {esc(ui['game'])}</span><span class="badge">{esc(copy['status'])}</span></div><h3>{name}</h3><p>{esc(copy['description'])}</p><div class="tags">{' / '.join(map(esc, copy['tags']))}</div>{link(game['url'], ui['exploreSteam'] + ' ↗', 'text-link', 'rel="noreferrer"')}</div></article>'''

    def app(self, app, locale, text):
        slug, name = app['id'], app['name']
        if not re.fullmatch(r'[a-z0-9-]+', slug):
            raise ValueError('Invalid app identifier')
        copy, ui = text['apps'][slug], text['ui']
        data, digest = localized_legal(app, locale['code'])
        ready = legal_ready(data)
        self.manifests.append({'app': slug, 'locale': locale['code'], 'legalSourceSHA256': digest, 'legalComplete': ready})
        art = f'<div class="app-art" aria-hidden="true"><img src="{esc(app["icon"])}" alt="" width="256" height="256"></div>'
        support_url = route(locale, f'{slug}/support.html')
        features = ''.join(f'<article><p class="feature-number">{i+1:02d}</p><h2>{esc(f["title"])}</h2><p>{esc(f["text"])}</p></article>' for i, f in enumerate(copy['features']))
        policy_link = link(route(locale, f'{slug}/privacy.html'), ui['privacy'], 'button') if ready or self.preview else ''
        body = f'''<section class="app-hero"><div><p class="eyebrow">{esc(copy['status'])}</p><h1>{esc(copy['summary'])}</h1><p class="intro">{esc(copy['description'])}</p>{link(support_url, ui['helpSupport'], 'button')}</div>{art}</section><section><div class="features">{features}</div><div class="contact-strip"><div><h2>{esc(ui['needHelp'].format(name=name))}</h2><p>{esc(ui['helpIntro'])}</p></div>{policy_link}{link(support_url, ui['viewHelp'], 'button primary')}</div></section>'''
        self.page(locale, text, f'{slug}/index.html', name + ' · ATS', copy['description'], body, app)
        docs = [d for d in data['documents'] if d['id'] == 'support' or ready or self.preview]
        for doc in docs:
            navigation = ''.join(link(route(locale, f'{slug}/{d["id"]}.html'), d['title'], attrs='aria-current="page"' if d['id'] == doc['id'] else '') for d in docs)
            body = f'<p class="draft">{esc(ui["draft"])}</p>' if self.preview and not ready else ''
            body += f'<nav class="document-nav" aria-label="{esc(ui["documents"])}">{navigation}</nav><h1>{esc(doc["title"])}</h1><p class="meta">{esc(name)} · {esc(data["version"])}</p><p>{esc(ui["operator"])}: {esc(data["operatorName"])}</p><p>{link("mailto:" + quote(data["supportEmail"], safe="@"), data["supportEmail"])}</p>'
            for section in doc['sections']:
                body += f'<h2>{esc(section["title"])}</h2>'
                for paragraph in section['paragraphs']:
                    rendered = re.sub(r'{{(\w+)}}', lambda m: data.get(m[1]) or ui['pending'], paragraph)
                    if not self.preview and ui['pending'] in rendered:
                        raise ValueError('Unfinished document reached public build')
                    body += '<p>' + esc(rendered) + '</p>'
            if doc['id'] == 'support':
                body += '<p>' + link(data['refundURL'], ui['appleRefunds']) + '</p>'
            if doc['id'] == 'terms':
                body += '<p>' + link(data['eulaURL'], ui['appleEula']) + '</p>'
            self.page(locale, text, f'{slug}/{doc["id"]}.html', doc['title'] + ' · ' + name, doc['title'], '<article class="document">'+body+'</article>', app)
        return f'''<article class="app-feature"><div><p class="eyebrow">{esc(ui['app'])} / {esc(copy['status'])}</p><h3>{esc(name)}</h3><p>{esc(copy['description'])}</p>{link(route(locale, slug+'/index.html'), ui['learnApp'].format(name=name)+' ↗', 'button')}</div>{art}</article>'''

    def locale(self, locale):
        text = read_json(ROOT / 'content' / locale['catalog'])
        ui, home = text['ui'], text['home']
        games = ''.join(self.game(g, text['games'][g['id']], ui, i+1) for i, g in enumerate(self.games))
        apps = ''.join(self.app(a, locale, text) for a in self.config['apps'])
        games_section = f'<section id="games" class="work-section"><div class="games">{games}</div></section>' if self.games else ''
        headline = '<br>'.join('<span>'+esc(line)+'</span>' for line in home['headline'])
        body = f'''<section class="hero"><div class="hero-copy"><p class="eyebrow">{esc(home['eyebrow'])}</p><h1>{headline}</h1><div class="hero-bottom"><p class="intro">{esc(home['description'])}</p><a class="round-link" href="#work" aria-label="{esc(ui['explore'])}">↓</a></div></div><div class="studio-art" aria-hidden="true"><div class="orbit orbit-one"></div><div class="orbit orbit-two"></div><div class="orbit orbit-three"></div><div class="orbit-core">a<span>t</span>s</div><div class="art-label">AFTER THE SINGULARITY<br>{esc(ui['siteTitle'])}</div><div class="art-corner">↗</div></div></section><section class="work-intro" id="work"><p class="eyebrow">{esc(home['workLabel'])}</p><h2>{esc(home['workTitle'])}</h2><span class="section-index">01 — {len(self.games) + len(self.config['apps']):02d}</span></section>{games_section}<section id="apps">{apps}</section><section class="about-section"><div class="about"><p class="eyebrow">{esc(ui['studio'])}</p><h2>{esc(home['aboutTitle']).replace(chr(10), '<br>')}</h2><p>{esc(home['aboutText'])}</p></div></section><section id="contact"><div class="contact-strip"><div><p class="eyebrow">{esc(ui['conversation'])}</p><h2>{esc(home['contactTitle'])}</h2><p>{esc(home['contactText'])}</p></div>{link('mailto:'+self.config['email'], ui['getInTouch']+' ↗', 'button primary')}</div></section>'''
        self.page(locale, text, 'index.html', self.config['brand'] + ' · ' + ui['siteTitle'], text['intro'], body)
        body = f'<section class="not-found"><p class="eyebrow">404</p><h1>{esc(ui["notFoundHeading"])}</h1><p>{esc(ui["notFoundText"])}</p>{link(route(locale), ui["backHome"], "button primary")}</section>'
        self.page(locale, text, '404.html', ui['notFoundTitle']+' · ATS', ui['notFoundText'], body)

    def build(self):
        # Validate all legal translations before replacing the previous generated output.
        for locale in self.config['locales']:
            for app in self.config['apps']:
                localized_legal(app, locale['code'])
        if self.output.exists():
            shutil.rmtree(self.output)
        self.output.mkdir()
        shutil.copytree(ROOT / 'assets', self.output / 'assets')
        for locale in self.config['locales']:
            self.locale(locale)
        (self.output/'robots.txt').write_text('User-agent: *\nDisallow: /\n' if self.preview else 'User-agent: *\nAllow: /\nSitemap: '+self.config['domain']+'/sitemap.xml\n')
        urls = ''.join('<url><loc>'+esc(p['url'])+'</loc></url>' for p in self.pages if p['logicalPath'] != '404.html')
        (self.output/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+urls+'</urlset>')
        (self.output/'_headers').write_text("/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: no-referrer\n  X-Frame-Options: DENY\n  Content-Security-Policy: default-src 'self'; img-src 'self' https://shared.fastly.steamstatic.com; style-src 'self'; script-src 'none'; frame-src 'none'; connect-src 'none'; base-uri 'self'; form-action 'none'; frame-ancestors 'none'\n")
        (ROOT/('preview-manifest.json' if self.preview else 'build-manifest.json')).write_text(json.dumps({'mode':'preview' if self.preview else 'public','pages':[p['path'] for p in self.pages],'localizedPages':self.pages,'apps':self.manifests},indent=2)+'\n')
        print(f'{self.output}: {len(self.pages)} pages in {len(self.config["locales"])} languages')


def build(preview=False):
    SiteBuilder(preview).build()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preview', action='store_true')
    build(parser.parse_args().preview)
