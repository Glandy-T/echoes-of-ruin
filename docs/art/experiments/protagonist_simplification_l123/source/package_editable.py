"""Wrap this authorized geometric study into editable Aseprite layers."""
from pathlib import Path
import argparse,subprocess
root=Path(__file__).resolve().parent.parent
p=argparse.ArgumentParser()
p.add_argument('--aseprite',default='C:/文件类/Aseprite/Aseprite/aseprite.exe')
a=p.parse_args()
subprocess.run([a.aseprite,'-b','--script-param','root='+root.as_posix(),'--script',str(root/'source/package.lua')],check=True)
assert (root/'editable/L123_comparison.aseprite').is_file()
assert (root/'evidence/aseprite_readback.png').is_file()
