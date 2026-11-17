"""Package existing artwork only; does not call PixelLab or paint pixels."""
from pathlib import Path
import argparse
import subprocess

root = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser()
parser.add_argument('--aseprite', default='C:/文件类/Aseprite/Aseprite/aseprite.exe')
args = parser.parse_args()
subprocess.run([args.aseprite, '-b', '--script-param', 'root=' + root.as_posix(),
                '--script', str(root / 'source/package.lua')], check=True)
assert (root / 'editable/front_candidate.aseprite').is_file()
assert (root / 'evidence/aseprite_readback.png').is_file()
