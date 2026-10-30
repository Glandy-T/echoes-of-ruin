"""Copy this isolated candidate only; never sync the dirty primary checkout."""
from pathlib import Path
import shutil,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
target=Path(sys.argv[1]).resolve();assert (target/'.git').exists()
files=['从这里开始.md']
for folder in ['assets/art/room1_pixel_cluster_r20','docs/art/experiments/room1_pixel_cluster_r20']:
    files += [str(p.relative_to(ROOT)).replace('\\','/') for p in (ROOT/folder).rglob('*')
              if p.is_file() and p.suffix not in ['.log','.uid','.import','.pyc','.blend1']
              and '__pycache__' not in p.parts]
files += [str(p.relative_to(ROOT)).replace('\\','/') for p in (ROOT/'scripts/dev').glob('*r20*') if p.suffix in ['.gd','.gdshader']]
files += [str(p.relative_to(ROOT)).replace('\\','/') for p in (ROOT/'scenes/dev').glob('*r20.tscn')]
files += ['scenes/dev/room1_pixel_cluster_r20_capture.tscn','scenes/dev/room1_pixel_cluster_r20_verify.tscn']
assert len(files)==len(set(files))
for name in files:
    destination=target/name;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,destination)
print('R20_PACKAGE',len(files),'files')
