from pathlib import Path
import hashlib,json,sys
here=Path(__file__).resolve().parent
root=here.parent.parent
before=json.loads((here/'existing-files-before.json').read_text())
bad=[]
for name,digest in before.items():
 p=root/name
 if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:bad.append(name)
print(f"Checked {len(before)} pre-existing project files; changes: {len(bad)}")
for name in bad:print(name)
sys.exit(bool(bad))
