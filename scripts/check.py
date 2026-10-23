#!/usr/bin/env python3
"""Check public artifacts: local links, privacy boundary and no tracking/scripts."""
import json
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
from localization import ROOT, legal_ready, localized_legal, output_path, validate_locales

class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.urls=[]; self.scripts=0
    def handle_starttag(self, tag, attrs):
        if tag == 'script': self.scripts += 1
        for key,value in attrs:
            if key in ('href','src') and value: self.urls.append(value)

def check(directory):
    errors=[]; pages=list(directory.rglob('*.html'))
    if not pages: errors.append('No HTML output')
    for page in pages:
        text=page.read_text(); parser=Links(); parser.feed(text)
        if parser.scripts: errors.append(f'{page}: unexpected scripts')
        if any(word in text for word in ('BORRADOR','PENDIENTE DE DEFINIR','[Your Name]','freevisitorcounters')):
            errors.append(f'{page}: unfinished or disallowed content')
        for url in parser.urls:
            parts=urlsplit(url)
            if parts.scheme or parts.netloc or not parts.path: continue
            target=(directory/unquote(parts.path).lstrip('/')) if parts.path.startswith('/') else page.parent/unquote(parts.path)
            if target.is_dir(): target=target/'index.html'
            if not target.exists(): errors.append(f'{page}: broken local link {url}')
    config=json.loads((ROOT/'content/site.json').read_text())
    validate_locales(config)
    for locale in config['locales']:
        for app in config['apps']:
            legal, _ = localized_legal(app, locale['code'])
            if not legal_ready(legal):
                for name in ('privacy.html','terms.html'):
                    if (directory/output_path(locale, app['id']+'/'+name)).exists():
                        errors.append('Unfinished legal document published: '+name)
    if errors: raise SystemExit('\n'.join(errors))
    print(f'Checked {len(pages)} HTML pages: links, no scripts, no unfinished policies.')

if __name__ == '__main__': check(ROOT/(sys.argv[1] if len(sys.argv)>1 else 'dist'))
