#!/usr/bin/env python3
"""Import the app's canonical LegalContent.json; never edit a second policy by hand."""
import argparse
import json
from pathlib import Path
from build import ROOT
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('app_id'); p.add_argument('source',type=Path)
a=p.parse_args()
config=json.loads((ROOT/'content/site.json').read_text())
app=next(item for item in config['apps'] if item['id']==a.app_id)
data=json.loads(a.source.read_text())
required={'version','operatorName','supportEmail','documents'}
if not required.issubset(data): raise SystemExit('Not a legal-content document')
(ROOT/'content'/app['legalFile']).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print('Imported legal snapshot for '+a.app_id+'. Rebuild and review before deployment.')
