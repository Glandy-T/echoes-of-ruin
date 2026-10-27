"""Bake the fixed open P12 Room 1 pose with the globally packed UV2 r2 layout.

This intentionally leaves the r1 bake untouched.  The called script rejects a
bad UV2 layout before it creates a Cycles bake, then this wrapper runs the
existing HDR denoise pass against the new output directory.
"""
import os
import runpy
from pathlib import Path

os.environ['ROOM1_BAKE_OUTPUT'] = 'assets/art/room1_open_hero_uv2_r2'
os.environ['ROOM1_OPEN_POD'] = 'P12'
runpy.run_path(str(Path(__file__).with_name('room1_lightmap_uv_tools.py')))
runpy.run_path(str(Path(__file__).with_name('denoise_room1_strip_r3.py')))
