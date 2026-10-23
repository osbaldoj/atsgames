"""Locale routing and reviewed legal translations, shared by build and checks."""
import copy
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_json(path):
    return json.loads(path.read_text())


def shape(value):
    """Require the same fields and list lengths; never fall back to another language."""
    if isinstance(value, dict):
        return {key: shape(item) for key, item in value.items()}
    if isinstance(value, list):
        return [shape(item) for item in value]
    return type(value).__name__


def validate_locales(config):
    locales = config['locales']
    codes = [item['code'] for item in locales]
    prefixes = [item['prefix'] for item in locales]
    if len(set(codes)) != len(codes) or len(set(prefixes)) != len(prefixes):
        raise ValueError('Locale codes and prefixes must be unique')
    default = next(item for item in locales if item['code'] == config['defaultLocale'])
    if default['prefix'] != '' or prefixes.count('') != 1:
        raise ValueError('Only the default locale must use the root path')
    reference = read_json(ROOT / 'content' / default['catalog'])
    for locale in locales:
        if not re.fullmatch(r'[a-z]{2}(?:-[A-Z]{2})?', locale['code']):
            raise ValueError('Invalid locale code')
        if locale['prefix'] and not re.fullmatch(r'[a-zA-Z-]+', locale['prefix']):
            raise ValueError('Invalid locale prefix')
        if shape(read_json(ROOT / 'content' / locale['catalog'])) != shape(reference):
            raise ValueError(f"Incomplete catalog: {locale['code']}")


def route(locale, path='index.html'):
    """Output links retain .html compatibility with both static preview and hosting."""
    directory = path.endswith('index.html')
    path = path[:-10] if directory else path
    joined = '/'.join(part.strip('/') for part in (locale['prefix'], path) if part.strip('/'))
    return '/' + joined + ('/' if directory and joined else '')


def canonical_route(locale, path):
    url = route(locale, path)
    return url[:-5] if url.endswith('.html') else url


def output_path(locale, path):
    return '/'.join(part for part in (locale['prefix'], path) if part)


def legal_ready(data):
    fields = ('operatorName', 'supportEmail', 'hostingProvider', 'supportRetention', 'privacyURL', 'supportURL')
    return all(str(data.get(key, '')).strip() for key in fields) and all(
        data[key].startswith('https://') for key in ('privacyURL', 'supportURL'))


def localized_legal(app, code):
    source_path = ROOT / 'content' / app['legalFile']
    data = read_json(source_path)
    digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
    if code == app['legalSourceLocale']:
        return data, digest
    translation = read_json(ROOT / 'content' / app['legalTranslations'][code])
    if translation['sourceSHA256'] != digest:
        raise ValueError(f"Review {app['id']} legal translation ({code}): source changed")
    if shape(translation['documents']) != shape(data['documents']):
        raise ValueError('Legal translation has missing sections or paragraphs')
    if [d['id'] for d in translation['documents']] != [d['id'] for d in data['documents']]:
        raise ValueError('Legal document identities differ')
    for original, translated in zip(data['documents'], translation['documents']):
        for source_section, translated_section in zip(original['sections'], translated['sections']):
            for source_text, translated_text in zip(source_section['paragraphs'], translated_section['paragraphs']):
                if sorted(re.findall(r'{{\w+}}', source_text)) != sorted(re.findall(r'{{\w+}}', translated_text)):
                    raise ValueError('Legal translation placeholders differ')
    result = copy.deepcopy(data)
    for key in ('hostingProvider', 'supportRetention', 'documents'):
        result[key] = translation[key]
    return result, digest
