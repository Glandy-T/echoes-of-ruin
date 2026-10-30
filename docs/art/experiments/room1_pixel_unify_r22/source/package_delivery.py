"""Copy only this task's public assets and reproducibility evidence to upload checkout."""
from pathlib import Path
import shutil,sys,json,hashlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
target=Path(sys.argv[1]);files=[]
for folder in ['assets/art/room1_pixel_unify_r22','docs/art/experiments/room1_pixel_unify_r22']:
    for p in (ROOT/folder).rglob('*'):
        if not p.is_file() or p.suffix in ['.log','.uid','.import','.pyc','.blend1'] or '__pycache__' in p.parts:continue
        if p.name in ['balance_before.json','balance_after.json','upload_validation.json','delivery_manifest.json']:continue
        files.append(str(p.relative_to(ROOT)).replace('\\','/'))
for p in (ROOT/'scripts/dev').glob('*pixel_unify_r22*'):
    if p.suffix in ['.gd','.gdshader']:files.append(str(p.relative_to(ROOT)).replace('\\','/'))
files += [str(p.relative_to(ROOT)).replace('\\','/') for p in (ROOT/'scenes/dev').glob('*pixel_unify_r22*.tscn')]
files+=['从这里开始.md','docs/art/素材目录.md','docs/art/ROOM1_LIGHTMAP_QA.md']
assert len(files)==len(set(files))
for name in files:
    destination=target/name;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,destination)
manifest={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in files}
(HERE/'delivery_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
destination=target/'docs/art/experiments/room1_pixel_unify_r22/source/delivery_manifest.json'
shutil.copy2(HERE/'delivery_manifest.json',destination)
print('R22_PACKAGE',len(files),'files; no credentials or personal billing records')
