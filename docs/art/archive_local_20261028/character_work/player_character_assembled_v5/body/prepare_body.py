"""Stable entry point for the body UV preparation pipeline.

Run with Blender 5.0+:
  blender --background --factory-startup --disable-autoexec \
    --python-exit-code 1 --python prepare_body.py

The implementation lives in prepare_body_anatomy.py so the investigation and
the accepted pipeline remain reviewable in one file.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from prepare_body_anatomy import main


if __name__ == "__main__":
    main()
