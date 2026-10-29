"""Copy only this delivery into the established Git upload checkout."""
import shutil
import sys
from pathlib import Path

repo = Path(__file__).resolve().parents[5]
target = Path(sys.argv[1]).resolve()
assert (target/'.git').exists(), 'Use the managed Git upload checkout.'
files = [
    '从这里开始.md','docs/art/素材目录.md','docs/art/ROOM1_NEXT_SCHOOL_HANDOFF.md',
    'scripts/core/title_screen.gd','scripts/dev/verify_room1_title_flow.gd',
    'scripts/areas/military_facility/cryo_room_4f_01_3d.gd',
    'scenes/areas/military_facility/cryo_room_4f_01_3d.tscn',
    'scripts/dev/room1_complete_r19.gd','scripts/dev/room1_complete_surface_r19.gdshader',
    'scripts/props/cryopod_complete_screen_r19.gdshader',
    'scripts/dev/verify_room1_complete_r19.gd','scripts/dev/verify_room1_complete_title_r19.gd',
    'scripts/dev/capture_room1_complete_r19.gd','scripts/dev/capture_room1_playable_r19.gd',
    'scenes/dev/room1_complete_r19.tscn','scenes/dev/room1_complete_r19_verify.tscn',
    'scenes/dev/room1_complete_r19_capture.tscn','scenes/dev/room1_complete_r19_before_capture.tscn',
]
folders = ['assets/art/room1_complete_r19','docs/art/experiments/room1_complete_r19']
for folder in folders:
    files += [str(p.relative_to(repo)).replace('\\','/') for p in (repo/folder).rglob('*')
              if p.is_file() and p.suffix not in ['.log','.blend1','.import','.uid','.pyc'] and not p.name.endswith('_console.txt')
              and '__pycache__' not in p.parts
              and 'quality_probe_1024' not in p.parts]
assert len(files)==len(set(files))
total=0
for relative in files:
    source=repo/relative; dest=target/relative
    dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,dest); total+=source.stat().st_size
print(f'R19_PACKAGE files={len(files)} bytes={total}')
