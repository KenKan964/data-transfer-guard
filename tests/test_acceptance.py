import hashlib,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CASES=json.loads((ROOT/'tests/cases.json').read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
class Acceptance(unittest.TestCase):pass
def make(c):
 def test(self):
  with tempfile.TemporaryDirectory(prefix='dtg_accept_') as td:
   d=Path(td);paths={k:d/(k+('.json' if k=='policy' else '.csv')) for k in ('before','after','policy')}
   for k in ('before','after'):paths[k].write_bytes(bytes.fromhex(c[k+'_hex']) if k+'_hex' in c else c[k].encode('utf-8'))
   paths['policy'].write_text(c.get('policy_raw',json.dumps(c['policy'],ensure_ascii=False)),encoding='utf-8')
   if c.get('missing'):paths[c['missing']].unlink()
   out=paths.get(c.get('out_kind'),d/'report.json')
   if c.get('out_kind')=='existing':out.write_bytes(b'KEEP REPORT')
   hashes={k:sha(p) for k,p in paths.items()};old=out.read_bytes() if out.exists() else None
   cmd=[sys.executable,str(ROOT/'dtg.py'),'verify']
   for k,p in paths.items():cmd+=['--'+k,str(p)]
   cmd+=['--out',str(out)]
   if c.get('show_keys'):cmd+=['--show-keys']
   r=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8')
   rejected=c.get('out_kind') is not None
   report=json.loads(r.stderr) if rejected else json.loads(out.read_text(encoding='utf-8'))
   post={k:sha(p) for k,p in paths.items()}
   ev={'case':c['id'],'name':c['name'],'expected_status':c['status'],'actual_exit':r.returncode,'report':report,'input_sha256_before':hashes,'input_sha256_after':post,'input_unchanged':hashes==post}
   if os.environ.get('DTG_EVIDENCE_DIR'):
    target=Path(os.environ['DTG_EVIDENCE_DIR'])/(c['id']+'_'+c['name']);target.mkdir(parents=True,exist_ok=True)
    (target/'result.json').write_text(json.dumps(ev,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for k,p in paths.items():
     if p.exists():(target/p.name).write_bytes(p.read_bytes())
   self.assertEqual(r.returncode,{'PASS':0,'FAIL':1,'INVALID_INPUT':2}[c['status']],r.stderr)
   self.assertEqual(report['status'],c['status']);self.assertEqual(report['exit_code'],r.returncode)
   self.assertEqual(sorted({v['code'] for v in report['violations']}),sorted(c['codes']))
   self.assertEqual(hashes,post)
   if rejected:self.assertEqual(out.read_bytes(),old)
   else:
    self.assertEqual(report['sha256'],hashes)
    self.assertEqual(report['detection_count'],len(report['violations']))
    for v in report['violations']:
     self.assertNotIn('old_value',v);self.assertNotIn('new_value',v)
     if 'key' in v:self.assertEqual(v['key'] is not None,bool(c.get('show_keys')))
 return test
for c in CASES:setattr(Acceptance,'test_'+c['id'].replace('-','_')+'_'+c['name'],make(c))
