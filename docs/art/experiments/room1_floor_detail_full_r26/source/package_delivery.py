from pathlib import Path
import shutil,json,hashlib,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4];target=Path(sys.argv[1]);files=[]
for folder in ['assets/art/room1_floor_detail_full_r26','docs/art/experiments/room1_floor_detail_full_r26']:
    files += [p.relative_to(ROOT).as_posix() for p in (ROOT/folder).rglob('*') if p.is_file() and p.suffix not in ['.log','.err','.import','.uid','.pyc','.blend1'] and '.log.' not in p.name and '__pycache__' not in p.parts and p.name!='delivery_manifest.json' and not p.name.startswith('balance_')]
files += [p.relative_to(ROOT).as_posix() for p in (ROOT/'scripts/dev').glob('*floor_detail_full_r26*') if p.suffix in ['.gd','.gdshader']]
files += [p.relative_to(ROOT).as_posix() for p in (ROOT/'scenes/dev').glob('*floor_detail_full_r26*.tscn')]
files += ['从这里开始.md','docs/art/素材目录.md','docs/art/ROOM1_FLOOR_TEXTURE_BRIEF.md','docs/art/PIXEL_TEXTURE_WORKFLOW.md','docs/art/ROOM1_LIGHTMAP_QA.md']
assert len(files)==len(set(files))
for name in files:
    dst=target/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dst)
manifest={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}
(HERE/'delivery_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8');shutil.copy2(HERE/'delivery_manifest.json',target/'docs/art/experiments/room1_floor_detail_full_r26/source/delivery_manifest.json')
print('R26_PACKAGE',len(files),'files; credentials/billing/logs/cache excluded')
