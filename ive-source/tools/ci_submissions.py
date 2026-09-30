"""Read-only CI checks. Submitted files are data; never import submitted Python."""
import argparse,json
from pathlib import Path
from validate_submission import validate,load_catalog
p=argparse.ArgumentParser();p.add_argument('directory',type=Path);a=p.parse_args()
files=sorted(a.directory.glob('*.json'));failures=[];catalog=load_catalog()
for file in files:
 if file.is_symlink() or file.stat().st_size>10_000_000:failures.append(f'{file.name}: unsupported file');continue
 try:errors=validate(json.loads(file.read_text()),full=True,catalog=catalog)
 except Exception as ex:errors=[f'Invalid manifest: {type(ex).__name__}']
 failures.extend(f'{file.name}: {e}' for e in errors)
 print(file.name,': FAILED' if errors else ': manifest checks passed (scores unverified)')
if not files:print('No submitted manifests yet. Validator tests are run separately.')
if failures:print('\n'.join(failures));raise SystemExit(1)
