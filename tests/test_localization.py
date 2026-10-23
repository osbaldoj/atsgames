from html.parser import HTMLParser
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import localization
from localization import ROOT, read_json, route, localized_legal, validate_locales, canonical_route


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.language = None
        self.links = []
        self.feed(path.read_text())

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'html':
            self.language = attrs['lang']
        if tag in ('a', 'link'):
            self.links.append((tag, attrs))


class LocalizationTests(unittest.TestCase):
    def setUp(self):
        self.config = read_json(ROOT/'content/site.json')

    def test_default_language_and_existing_routes(self):
        en, es = self.config['locales']
        self.assertEqual(self.config['defaultLocale'], 'en')
        self.assertEqual(route(en), '/')
        self.assertEqual(route(es), '/es/')
        self.assertEqual(route(en, 'fotoswipe/index.html'), '/fotoswipe/')
        self.assertEqual(route(es, 'fotoswipe/index.html'), '/es/fotoswipe/')
        self.assertEqual(route(en, 'fotoswipe/privacy.html'), '/fotoswipe/privacy.html')
        self.assertEqual(canonical_route(es, 'fotoswipe/privacy.html'), '/es/fotoswipe/privacy')

    def test_changed_source_blocks_outdated_legal_translation(self):
        app = self.config['apps'][0]
        actual = localization.read_json
        def stale(path):
            data = actual(path)
            if path.name == 'fotoswipe-legal.en.json':
                data['sourceSHA256'] = 'old-revision'
            return data
        with patch.object(localization, 'read_json', side_effect=stale):
            with self.assertRaisesRegex(ValueError, 'source changed'):
                localized_legal(app, 'en')

    def test_missing_paragraph_blocks_legal_translation(self):
        app = self.config['apps'][0]
        actual = localization.read_json
        def incomplete(path):
            data = actual(path)
            if path.name == 'fotoswipe-legal.en.json':
                data['documents'][0]['sections'][0]['paragraphs'] = []
            return data
        with patch.object(localization, 'read_json', side_effect=incomplete):
            with self.assertRaisesRegex(ValueError, 'missing sections'):
                localized_legal(app, 'en')

    def test_missing_ui_copy_has_no_silent_language_fallback(self):
        actual = localization.read_json
        def incomplete(path):
            data = actual(path)
            if path.name == 'es.json':
                del data['ui']['help']
            return data
        with patch.object(localization, 'read_json', side_effect=incomplete):
            with self.assertRaisesRegex(ValueError, 'Incomplete catalog'):
                validate_locales(self.config)

    def test_language_switch_preserves_every_page_and_navigation_stays_local(self):
        manifest = read_json(ROOT/'build-manifest.json')
        locales = {l['code']: l for l in self.config['locales']}
        expected_per_locale = 2 + sum(1 + len(read_json(ROOT/'content'/app['legalFile'])['documents']) for app in self.config['apps'])
        self.assertEqual(len(manifest['localizedPages']), expected_per_locale * len(locales))
        for entry in manifest['localizedPages']:
            with self.subTest(path=entry['path']):
                page = Page(ROOT/'dist'/entry['path'])
                self.assertEqual(page.language, entry['locale'])
                switches = [a for t,a in page.links if t == 'a' and 'hreflang' in a]
                self.assertEqual({a['hreflang'] for a in switches}, set(locales))
                for a in switches:
                    self.assertEqual(a['href'], route(locales[a['hreflang']], entry['logicalPath']))
                canonicals = [a['href'] for t,a in page.links if t == 'link' and a.get('rel') == 'canonical']
                self.assertEqual(canonicals, [entry['url']])
                alternates = [a for t,a in page.links if t == 'link' and a.get('rel') == 'alternate']
                self.assertEqual({a['hreflang'] for a in alternates}, {*locales, 'x-default'})
                for tag,a in page.links:
                    url = urlsplit(a.get('href', ''))
                    if tag != 'a' or url.scheme or 'hreflang' in a or not url.path:
                        continue
                    self.assertEqual(url.path.startswith('/es/'), entry['locale'] == 'es', a)

    def test_legal_identity_and_retention_meaning_are_preserved(self):
        app = self.config['apps'][0]
        en, digest_en = localized_legal(app, 'en')
        es, digest_es = localized_legal(app, 'es')
        self.assertEqual(digest_en, digest_es)
        for field in ('operatorName', 'supportEmail', 'version', 'privacyURL', 'supportURL', 'eulaURL'):
            self.assertEqual(en[field], es[field])
        self.assertIn('12 months after the request is closed', en['supportRetention'])
        self.assertIn('12 meses desde el cierre', es['supportRetention'])


if __name__ == '__main__':
    unittest.main()
