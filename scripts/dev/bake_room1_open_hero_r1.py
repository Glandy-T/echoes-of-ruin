"""Bake the fixed OPEN P12 pose; its shadow must not retain a closed lid."""
import os
import runpy
from pathlib import Path
os.environ['ROOM1_BAKE_OUTPUT'] = 'assets/art/room1_open_hero_bake_r1'
os.environ['ROOM1_OPEN_POD'] = 'P12'
runpy.run_path(str(Path(__file__).with_name('bake_room1_continuous_strip_r3.py')))
runpy.run_path(str(Path(__file__).with_name('denoise_room1_strip_r3.py')))
