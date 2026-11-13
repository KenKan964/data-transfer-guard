"""Core comparison: API timings, same synthetic bytes, independent expected results."""
import difflib,hashlib,json,platform,random,statistics,sys,tempfile,time,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import dtg
from oss_check import inspect
ROOT=Path(__file__).resolve().parents[1]
def run(out):
 out.mkdir(exist_ok=False)
 cases=[c for c in json.loads((ROOT/'tests/cases.json').read_text(encoding='utf-8')) if c['id'].startswith('DTG-') and not c.get('out_kind')]
 checks=unittest.TestCase();records=[];rng=random.Random(1001)
 with tempfile.TemporaryDirectory() as td:
  paths=[Path(td)/n for n in ['before','after','policy']]
  for c in cases:
   for n,p in zip(['before','after','policy'],paths):
    if n=='policy':raw=c.get('policy_raw',json.dumps(c['policy'],ensure_ascii=False)).encode()
    else:raw=bytes.fromhex(c[n+'_hex']) if n+'_hex' in c else c[n].encode()
    p.write_bytes(raw)
   if c.get('missing'):paths[['before','after','policy'].index(c['missing'])].unlink()
   hashes=lambda:[hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None for p in paths]
   initial=hashes()
   for i in range(30):
    modes=['oss','dtg'];rng.shuffle(modes)
    for mode in modes:
     t=time.perf_counter_ns();r=inspect(*paths) if mode=='oss' else dtg.verify(*paths)
     elapsed=(time.perf_counter_ns()-t)/1e6
     codes=r.get('codes',sorted({v['code'] for v in r.get('violations',[])}))
     checks.assertEqual(r['status'],c['status']);checks.assertEqual(sorted(codes),sorted(c['codes']));checks.assertEqual(hashes(),initial)
     records.append({'case':c['id']+'_'+c['name'],'iteration':i,'mode':mode,'runtime_ms':elapsed,'status':r['status'],'codes':codes,'input_unchanged':True})
 baseline=json.loads((ROOT/'examples/policy.json').read_text(encoding='utf-8'))
 changed={**baseline,'allowed_update_columns':baseline['allowed_update_columns']+['所属']}
 diff=''.join(difflib.unified_diff((json.dumps(baseline,ensure_ascii=False,indent=2)+'\n').splitlines(True),(json.dumps(changed,ensure_ascii=False,indent=2)+'\n').splitlines(True),fromfile='policy.json',tofile='policy.json'))
 (out/'allowed_column.patch').write_text(diff,encoding='utf-8')
 summary={'environment':{'python':platform.python_version(),'platform':platform.platform()},'cases':len(cases),'repeats':30,'executions':len(records),'all_expected':True,'human_effort':None,'seed':1001,
 'median_ms':{mode:statistics.median(r['runtime_ms'] for r in records if r['mode']==mode) for mode in ['oss','dtg']},
 'source_physical_lines':{n:len((ROOT/n).read_text().splitlines()) for n in ['dtg.py','benchmarks/oss_check.py']},
 'scripted_artifact_operations':{task:{'oss':counts,'dtg':counts} for task,counts in {'initial_setup':{'config_files_created':1,'cli_invocations':1},'allowed_column_addition':{'config_files_edited':1,'production_code_lines_changed':0},'sample_change':{'csv_files_edited':1,'production_code_lines_changed':0},'result_judgment':{'cli_invocations':1,'production_code_lines_changed':0}}.items()},
 'limits':['API wall time includes reading and validation, excludes process startup/report persistence','baseline core classification only; lacks DTG strict quote extension, provenance JSON and exclusive output handling','operation counts describe this scripted workflow, not observed human actions']}
 (out/'raw.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':run(Path(sys.argv[1]))
