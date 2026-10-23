#!/usr/bin/env python3
"""Build the static ATS catalogue. Public builds never contain unfinished policies."""
import argparse
import hashlib
import html
import json
import re
import shutil
from pathlib import Path
from string import Template
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
esc = html.escape

def read_json(path):
    return json.loads(path.read_text())

def legal_ready(data):
    fields = ('operatorName', 'supportEmail', 'hostingProvider', 'supportRetention', 'privacyURL', 'supportURL')
    return all(str(data.get(key, '')).strip() for key in fields) and all(
        data[key].startswith('https://') for key in ('privacyURL', 'supportURL'))

def build(preview=False):
    config = read_json(ROOT / 'content/site.json')
    output = ROOT / ('dist-preview' if preview else 'dist')
    if output.exists():
        shutil.rmtree(output)
    output.mkdir()
    shutil.copytree(ROOT / 'assets', output / 'assets')
    template = Template((ROOT / 'templates/page.html').read_text())
    paths = []
    manifests = []

    def page(path, title, description, body, lang='en', app=None):
        spanish = lang == 'es'
        navigation = '<a href="/#games">Games</a><a href="/#apps">Apps</a><a href="/#contact">Contact</a>'
        if spanish and app:
            navigation = f'<a href="/">ATS</a><a href="/{app["id"]}/">{esc(app["name"])}</a><a href="/{app["id"]}/support.html">Ayuda</a>'
        target = output / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(template.substitute(
            lang=esc(lang), title=esc(title), description=esc(description),
            robots='<meta name="robots" content="noindex,nofollow">' if preview else '',
            skip='Saltar al contenido' if spanish else 'Skip to content',
            nav_label='Navegación principal' if spanish else 'Main navigation',
            navigation=navigation, body=body, company=esc(config['company']),
            year=config['year'], email=esc(config['email'], quote=True)), encoding='utf-8')
        paths.append(path)

    games = ''
    for index, game in enumerate(config['games']):
        games += f'''<article class="game"><a class="game-image" href="{esc(game['url'], quote=True)}" rel="noreferrer" aria-label="{esc(game['name'])} on Steam"><img src="{esc(game['image'], quote=True)}" alt="{esc(game['name'])}" width="460" height="215" loading="lazy"><span class="image-arrow" aria-hidden="true">↗</span></a><div class="game-body"><div class="project-meta"><span>0{index+1} / GAME</span><span class="badge">{esc(game['status'])}</span></div><h3>{esc(game['name'])}</h3><p>{esc(game['description'])}</p><div class="tags">{' / '.join(map(esc,game['tags']))}</div><a class="text-link" href="{esc(game['url'], quote=True)}" rel="noreferrer">Explore on Steam <span aria-hidden="true">↗</span></a></div></article>'''
    apps = ''
    for app in config['apps']:
        slug = app['id']
        if not re.fullmatch(r'[a-z0-9-]+', slug):
            raise ValueError('Invalid app identifier')
        art = f'<div class="app-art" aria-hidden="true"><img src="{esc(app["icon"], quote=True)}" alt="" width="256" height="256"></div>'
        apps += f'''<article class="app-feature" lang="{esc(app['language'])}"><div><p class="eyebrow">APP / {esc(app['status'])}</p><h3>{esc(app['name'])}</h3><p>{esc(app['description'])}</p><a class="button" href="/{slug}/">Conoce {esc(app['name'])} <span aria-hidden="true">↗</span></a></div>{art}</article>'''
        legal_path = ROOT / 'content' / app['legalFile']
        data = read_json(legal_path)
        ready = legal_ready(data)
        manifests.append({'app': slug, 'legalSourceSHA256': hashlib.sha256(legal_path.read_bytes()).hexdigest(), 'legalComplete': ready})
        features = ''.join(f'<article><p class="feature-number">0{i+1}</p><h2>{esc(f["title"])}</h2><p>{esc(f["text"])}</p></article>' for i,f in enumerate(app['features']))
        policy_link = f'<a class="button" href="/{slug}/privacy.html">Privacidad</a>' if ready or preview else ''
        page(f'{slug}/index.html', app['name'] + ' · ATS', app['description'], f'''<section class="app-hero"><div><p class="eyebrow">{esc(app['status'])}</p><h1>{esc(app['summary'])}</h1><p class="intro">{esc(app['description'])}</p><a class="button" href="/{slug}/support.html">Ayuda y soporte</a></div>{art}</section><section><div class="features">{features}</div><div class="contact-strip"><div><h2>¿Necesitas ayuda con {esc(app['name'])}?</h2><p>Encuentra respuestas o escríbenos directamente.</p></div>{policy_link}<a class="button primary" href="/{slug}/support.html">Consultar ayuda</a></div></section>''', app['language'], app)
        docs = [d for d in data['documents'] if d['id'] == 'support' or ready or preview]
        links = ''.join(f'<a href="/{slug}/{d["id"]}.html">{esc(d["title"])}</a>' for d in docs)
        for doc in docs:
            draft = preview and not ready
            body = '<p class="draft">BORRADOR LOCAL · Los documentos de privacidad y términos aún no están aprobados para publicación.</p>' if draft else ''
            body += f'<nav class="document-nav" aria-label="Documentos">{links}</nav><h1>{esc(doc["title"])}</h1><p class="meta">{esc(app["name"])} · {esc(data["version"])}</p><p>Responsable: {esc(data["operatorName"])}</p>'
            body += f'<p><a href="mailto:{quote(data["supportEmail"], safe="@")}">{esc(data["supportEmail"])}</a></p>'
            for section in doc['sections']:
                body += f'<h2>{esc(section["title"])}</h2>'
                for paragraph in section['paragraphs']:
                    text = re.sub(r'\{\{(\w+)\}\}', lambda m: data.get(m[1]) or 'PENDIENTE DE DEFINIR', paragraph)
                    if not preview and 'PENDIENTE DE DEFINIR' in text:
                        raise ValueError('Unfinished document reached public build')
                    body += '<p>' + esc(text) + '</p>'
            if doc['id'] == 'support':
                body += f'<p><a href="{esc(data["refundURL"], quote=True)}">Ayuda de Apple sobre reembolsos</a></p>'
            if doc['id'] == 'terms':
                body += f'<p><a href="{esc(data["eulaURL"], quote=True)}">EULA estándar de Apple</a></p>'
            page(f'{slug}/{doc["id"]}.html', doc['title'] + ' · ' + app['name'], doc['title'], '<article class="document">'+body+'</article>', app['language'], app)
    home = config['home']
    hero_lines = '<br>'.join(f'<span>{esc(line)}</span>' for line in home['headline'])
    page('index.html', config['brand'] + ' · Games & Apps', config['intro'], f'''<section class="hero"><div class="hero-copy"><p class="eyebrow">{esc(home['eyebrow'])}</p><h1>{hero_lines}</h1><div class="hero-bottom"><p class="intro">{esc(home['description'])}</p><a class="round-link" href="#games" aria-label="Explore our work">↓</a></div></div><div class="studio-art" aria-hidden="true"><div class="orbit orbit-one"></div><div class="orbit orbit-two"></div><div class="orbit orbit-three"></div><div class="orbit-core">a<span>t</span>s</div><div class="art-label">AFTER THE SINGULARITY<br>GAMES & APPS</div><div class="art-corner">↗</div></div></section><section class="work-intro" id="games"><p class="eyebrow">{esc(home['workLabel'])}</p><h2>{esc(home['workTitle'])}</h2><span class="section-index">01 — {len(config['games']) + len(config['apps']):02d}</span></section><section class="work-section"><div class="games">{games}</div></section><section id="apps">{apps}</section><section class="about-section"><div class="about"><p class="eyebrow">The studio</p><h2>{esc(home['aboutTitle']).replace(chr(10), '<br>')}</h2><p>{esc(home['aboutText'])}</p></div></section><section id="contact"><div class="contact-strip"><div><p class="eyebrow">Start a conversation</p><h2>{esc(home['contactTitle'])}</h2><p>{esc(home['contactText'])}</p></div><a class="button primary" href="mailto:{esc(config['email'],quote=True)}">Get in touch <span aria-hidden="true">↗</span></a></div></section>''')
    page('404.html', 'Page not found · ATS', 'Return to ATS Games.', '<section class="not-found"><p class="eyebrow">404</p><h1>Nothing here yet.</h1><p>The page may have moved or is not available.</p><a class="button primary" href="/">Back to ATS</a></section>')
    (output/'robots.txt').write_text('User-agent: *\nDisallow: /\n' if preview else 'User-agent: *\nAllow: /\nSitemap: '+config['domain']+'/sitemap.xml\n')
    sitemap = ''.join('<url><loc>'+esc(config['domain'] + '/' + (p[:-10] if p.endswith('index.html') else p))+'</loc></url>' for p in paths if p != '404.html')
    (output/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+sitemap+'</urlset>')
    (output/'_headers').write_text("/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: no-referrer\n  X-Frame-Options: DENY\n  Content-Security-Policy: default-src 'self'; img-src 'self' https://shared.fastly.steamstatic.com; style-src 'self'; script-src 'none'; frame-src 'none'; connect-src 'none'; base-uri 'self'; form-action 'none'; frame-ancestors 'none'\n")
    (ROOT/('preview-manifest.json' if preview else 'build-manifest.json')).write_text(json.dumps({'mode':'preview' if preview else 'public','pages':paths,'apps':manifests},indent=2)+'\n')
    print(f'{output}: {len(paths)} pages; unfinished legal documents '+('included as local drafts' if preview else 'excluded'))

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preview',action='store_true')
    build(parser.parse_args().preview)
