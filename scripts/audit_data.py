from pathlib import Path
import csv, hashlib, json
root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'data/provided/manifest.json').read_text())
for name, expected in manifest['files'].items():
    path=root/'data/provided'/name
    actual=hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected['sha256']: raise SystemExit(f'Checksum mismatch: {name}')
    if path.suffix == '.csv':
        with path.open() as f: rows=list(csv.DictReader(f))
    elif path.suffix == '.jsonl': rows=[json.loads(x) for x in path.read_text().splitlines() if x.strip()]
    else: rows=[]
    print(name, 'records=',len(rows),'checksum=OK')
