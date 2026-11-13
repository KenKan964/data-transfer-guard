"""Independent csv + unittest baseline. No DTG imports; core safety classifications."""
import csv,io,json,sys
from pathlib import Path
class Bad(Exception):pass
def pairs(items):
 d={}
 for k,v in items:
  if k in d:raise Bad('DUPLICATE_POLICY_FIELD')
  d[k]=v
 return d
def inspect(before,after,policy):
 try:
  raws=[Path(p).read_bytes() for p in (before,after,policy)]
 except OSError:return {'status':'INVALID_INPUT','codes':['READ_ERROR']}
 try:
  try:p=json.loads(raws[2].decode('utf-8-sig'),object_pairs_hook=pairs)
  except (ValueError,UnicodeError):raise Bad('INVALID_POLICY')
  if type(p)!=dict or set(p)!={'schema_version','key_column','allowed_update_columns','allow_added_rows','allow_removed_rows'}:raise Bad('INVALID_POLICY_FIELDS')
  if p['schema_version']!='dtg-policy-v1':raise Bad('INVALID_POLICY_VERSION')
  key=p['key_column'];allowed=p['allowed_update_columns']
  if type(key)!=str or not key.strip():raise Bad('INVALID_KEY_COLUMN')
  if type(allowed)!=list or any(type(x)!=str or not x.strip() for x in allowed) or len(allowed)!=len(set(allowed)) or key in allowed:raise Bad('INVALID_ALLOWED_COLUMNS')
  if type(p['allow_added_rows'])!=bool or type(p['allow_removed_rows'])!=bool:raise Bad('INVALID_ROW_POLICY')
  tables=[]
  for raw in raws[:2]:
   try:rows=list(csv.reader(io.StringIO(raw.decode('utf-8-sig'),newline=''),strict=True))
   except UnicodeError:raise Bad('INVALID_UTF8')
   except csv.Error:raise Bad('CSV_PARSE_ERROR')
   if not rows:raise Bad('MISSING_HEADER')
   h=rows.pop(0)
   if not h or any(not x.strip() for x in h):raise Bad('EMPTY_HEADER')
   if len(set(h))!=len(h):raise Bad('DUPLICATE_HEADER')
   if key not in h:raise Bad('MISSING_KEY_COLUMN')
   if any(x not in h for x in allowed):raise Bad('UNKNOWN_ALLOWED_COLUMN')
   d={}
   for row in rows:
    if len(row)!=len(h):raise Bad('COLUMN_COUNT_MISMATCH')
    row=dict(zip(h,row));k=row[key]
    if not k.strip():raise Bad('EMPTY_KEY')
    if k in d:raise Bad('DUPLICATE_KEY')
    d[k]=row
   tables.append((h,d))
  (bh,b),(ah,a)=tables;codes=[]
  if set(bh)!=set(ah):codes=['SCHEMA_MISMATCH']
  else:
   if not p['allow_removed_rows'] and b.keys()-a.keys():codes.append('MISSING_ROW')
   if not p['allow_added_rows'] and a.keys()-b.keys():codes.append('UNEXPECTED_ROW')
   if any(b[k][c]!=a[k][c] for k in b.keys()&a.keys() for c in bh if c not in allowed):codes.append('UNAUTHORIZED_CHANGE')
  return {'status':'FAIL' if codes else 'PASS','codes':sorted(codes)}
 except Bad as e:return {'status':'INVALID_INPUT','codes':[str(e)]}
if __name__=='__main__':
 r=inspect(*sys.argv[1:]);print(json.dumps(r));sys.exit({'PASS':0,'FAIL':1,'INVALID_INPUT':2}[r['status']])
