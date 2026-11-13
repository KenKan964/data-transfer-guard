import os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import dtg
class Edges(unittest.TestCase):
 def test_escaped_quotes(self):
  p=dtg.load_policy(Path('examples/policy.json').read_bytes())
  _,rows=dtg.load_csv('ID,状態\n001,"a""b"\n'.encode(),p)
  self.assertEqual(rows['001'][1]['状態'],'a"b')
 def test_missing_output_parent(self):
  with tempfile.TemporaryDirectory() as td,patch('sys.stderr'):
   code=dtg.main(['verify','--before','x','--after','y','--policy','z','--out',str(Path(td)/'missing/o.json')])
  self.assertEqual(code,2)
 def test_hardlink_input(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'input';p.write_bytes(b'KEEP');link=Path(td)/'alias';os.link(p,link)
   with patch('sys.stderr'):code=dtg.main(['verify','--before',str(p),'--after','y','--policy','z','--out',str(link)])
   self.assertEqual(code,2);self.assertEqual(p.read_bytes(),b'KEEP')
 def test_quoted_cell_privacy(self):
  with tempfile.TemporaryDirectory() as td:
   d=Path(td);b=d/'b';a=d/'a';p=d/'p'
   p.write_text('{"schema_version":"dtg-policy-v1","key_column":"ID","allowed_update_columns":[],"allow_added_rows":false,"allow_removed_rows":false}')
   b.write_text('ID,x\nSECRETKEY,SECRETVALUE\n');a.write_text('ID,x\nSECRETKEY,NEWSECRET\n')
   import json
   text=json.dumps(dtg.verify(b,a,p));self.assertNotIn('SECRET',text)
