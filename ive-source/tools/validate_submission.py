"""Validate an IVE manifest and local trace hashes. No model calls or uploads."""
import argparse
import hashlib
import json
from pathlib import Path

ENGINES = {'cooksim': 150, 'vhhome': 75, 'screensim': 90}
FAMILIES = {'Frontier API', 'Streaming API', 'Open non-streaming', 'Open streaming'}


def load_catalog():
    here = Path(__file__).resolve()
    for path in [here.parents[1] / 'site/data/benchmark-catalog.json',
                 here.parents[2] / 'docs/data/benchmark-catalog.json']:
        if path.is_file():
            return json.loads(path.read_text())
    raise ValueError('The versioned benchmark catalog is missing')


def validate(data, root=None, full=False, catalog=None):
    if not isinstance(data, dict):
        return ['The manifest must be a JSON object']
    errors = []

    def require(condition, message):
        if not condition:
            errors.append(message)

    require(data.get('benchmark_version') == 'ive-v1', 'benchmark_version must be ive-v1')
    if full:
        require(data.get('demo_only') is not True, 'Demo manifests are not full benchmark submissions')
    model = data.get('model')
    if not isinstance(model, dict):
        errors.append('model must be an object')
    else:
        for key in ['name', 'revision']:
            value = model.get(key)
            require(isinstance(value, str) and bool(value.strip()), f'model.{key} is required')
        family = model.get('family')
        require(isinstance(family, str) and family in FAMILIES, 'Unknown model family')
    runs = data.get('runs')
    if not isinstance(runs, list) or not runs:
        errors.append('runs must be a nonempty array')
        return errors
    seen, cohorts = set(), {}
    for i, run in enumerate(runs):
        label = f'run {i + 1}'
        if not isinstance(run, dict):
            errors.append(f'{label}: must be an object')
            continue
        engine, rid = run.get('engine'), run.get('run_id')
        if not isinstance(engine, str) or engine not in ENGINES:
            errors.append(f'{label}: unknown engine')
            continue
        if type(rid) is not int or rid < 1:
            errors.append(f'{label}: run_id must be a positive integer')
            continue
        key = (engine, rid)
        require(key not in seen, f'{label}: duplicate engine/run')
        seen.add(key)
        episodes = run.get('episodes')
        if not isinstance(episodes, list) or not episodes:
            errors.append(f'{label}: episodes must be a nonempty array')
            continue
        if full:
            require(len(episodes) == ENGINES[engine],
                    f'{label}: expected {ENGINES[engine]} episodes, found {len(episodes)}')
        pairs = set()
        for j, ep in enumerate(episodes):
            el = f'{label}, episode {j + 1}'
            if not isinstance(ep, dict):
                errors.append(f'{el}: must be an object')
                continue
            fields = ['case_id', 'persona_id', 'trace_uri', 'trace_sha256']
            missing = [k for k in fields if not isinstance(ep.get(k), str) or not ep[k].strip()]
            if missing:
                errors.append(f'{el}: nonempty strings required for {", ".join(missing)}')
                continue
            pair = (ep['case_id'], ep['persona_id'])
            require(pair not in pairs, f'{el}: duplicate case/persona')
            pairs.add(pair)
            sha = ep['trace_sha256']
            require(len(sha) == 64 and all(c in '0123456789abcdef' for c in sha),
                    f'{el}: invalid SHA-256')
            uri = ep['trace_uri']
            relative = Path(uri)
            if relative.is_absolute() or '..' in relative.parts or '://' in uri or '\\' in uri:
                errors.append(f'{el}: trace_uri must be a relative path without parent traversal')
                continue
            if root is not None:
                try:
                    target = (root / relative).resolve()
                    if not target.is_relative_to(root.resolve()):
                        errors.append(f'{el}: trace path escapes submission directory')
                        continue
                    if not target.is_file():
                        errors.append(f'{el}: trace missing')
                        continue
                    with target.open('rb') as stream:
                        digest = hashlib.sha256()
                        for block in iter(lambda: stream.read(1024 * 1024), b''):
                            digest.update(block)
                        require(digest.hexdigest() == sha,
                                f'{el}: trace hash mismatch')
                    trace = json.loads(target.read_text())
                    require(isinstance(trace, dict), f'{el}: trace is not a JSON object')
                except (OSError, ValueError, UnicodeError):
                    errors.append(f'{el}: trace could not be read as a JSON object')
        if full and engine in cohorts:
            require(pairs == cohorts[engine], f'{label}: case/persona cohort differs between runs')
        if catalog is not None:
            expected = {(x['case_id'], x['persona_id']) for x in catalog['engines'][engine]}
            require(pairs <= expected, f'{label}: contains unknown case/persona pairs')
            if full:
                require(pairs == expected, f'{label}: case/persona membership differs from the benchmark catalog')
        cohorts.setdefault(engine, pairs)
    if full:
        require(seen == {(e, r) for e in ENGINES for r in [1, 2, 3]},
                'Full submissions require all three environments and runs 1, 2, 3')
    return errors


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--traces', type=Path)
    parser.add_argument('--full', action='store_true')
    args = parser.parse_args()
    try:
        errors = validate(json.loads(args.manifest.read_text()), args.traces, args.full, load_catalog())
    except (ValueError, OSError) as exc:
        errors = [str(exc)]
    if errors:
        print('\n'.join('ERROR: ' + e for e in errors))
        raise SystemExit(1)
    print('Manifest validation passed. Scores and trace authenticity still require benchmark verification.')
