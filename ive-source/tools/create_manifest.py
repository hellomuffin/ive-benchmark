"""Build a manifest from existing traces; no simulation, uploads, or score claims."""
import argparse,hashlib,json
from pathlib import Path
from validate_submission import load_catalog,validate,FAMILIES

def build(root,name,family,revision,catalog):
    root=Path(root).resolve()
    data={'benchmark_version':'ive-v1','model':{'name':name,'family':family,'revision':revision},'runs':[]}
    missing=[]
    for engine,cells in catalog['engines'].items():
        for run_id in [1,2,3]:
            episodes=[]
            for cell in cells:
                relative=Path(engine)/f'run-{run_id}'/f'{cell["case_id"]}__{cell["persona_id"]}.json'
                path=(root/relative).resolve()
                if not path.is_relative_to(root):raise ValueError('Trace path escapes the trace directory')
                if not path.is_file():
                    missing.append(str(relative));continue
                digest=hashlib.sha256()
                with path.open('rb') as stream:
                    for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
                episodes.append({**cell,'trace_uri':relative.as_posix(),'trace_sha256':digest.hexdigest()})
            data['runs'].append({'engine':engine,'run_id':run_id,'episodes':episodes})
    if missing:raise ValueError(f'{len(missing)} missing traces. First missing paths:\n'+'\n'.join(missing[:10]))
    errors=validate(data,root=root,full=True,catalog=catalog)
    if errors:raise ValueError('\n'.join(errors[:20]))
    return data

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--traces',required=True,type=Path)
    p.add_argument('--name',required=True);p.add_argument('--family',required=True,choices=sorted(FAMILIES))
    p.add_argument('--revision',required=True);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args()
    if a.output.exists():p.error('Output already exists; choose a new path to avoid overwriting it.')
    try:result=build(a.traces,a.name,a.family,a.revision,load_catalog())
    except (ValueError,OSError) as e:p.exit(1,str(e)+'\n')
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(f'Wrote {a.output}: 9 engine/run entries, 945 episode records. Scores remain unverified.')
