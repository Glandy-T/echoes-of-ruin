"""Copy this review only; preserve unrelated files and remote-only handoff text."""
import shutil
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[5]
target = Path(sys.argv[1]).resolve()
experiment = Path(__file__).resolve().parents[1].relative_to(root)
files = [
    "scripts/dev/door_inner_phosphor_r17.gdshader",
    "scripts/dev/room1_door_inner_light_r17.gd",
    "scripts/dev/capture_room1_door_inner_light_r17.gd",
    "scripts/dev/verify_room1_door_inner_light_r17.gd",
    "scenes/dev/room1_door_inner_light_r17.tscn",
    "scenes/dev/room1_door_inner_light_r17_capture.tscn",
    "scenes/dev/room1_door_inner_light_r17_verify.tscn",
]
files += [str(path.relative_to(root)) for path in root.joinpath(experiment).rglob("*")
          if path.is_file() and path.suffix in {".md", ".html", ".png", ".json", ".py", ".gd"}]
for relative in files:
    source = root / relative
    destination = target / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)

for relative, prefix, marker in [
    ("从这里开始.md", "- [门洞内侧灯 r17", "## 最新材质审查（2026-10-29）\n\n"),
    ("docs/art/素材目录.md", "| 门洞内侧灯候选 r17", "|---|---|---|\n"),
    ("docs/art/ROOM1_NEXT_SCHOOL_HANDOFF.md", "> 2026-10-29门灯补充", None),
]:
    local = (root / relative).read_text(encoding="utf-8")
    line = next(line for line in local.splitlines() if line.startswith(prefix))
    path = target / relative
    original = path.read_bytes()
    remote = original.decode("utf-8")
    assert prefix not in remote, "Already packaged; inspect rather than duplicate."
    rows = remote.splitlines(keepends=True)
    if marker is None:
        index = 2
    else:
        heading = marker.splitlines()[0]
        index = next(i for i, row in enumerate(rows) if row.rstrip("\r\n") == heading)
        index += 2 if marker.endswith("\n\n") else 1
    newline = "\r\n" if rows[index - 1].endswith("\r\n") else "\n"
    rows.insert(index, line + newline + (newline if marker is None else ""))
    updated = "".join(rows)
    path.write_bytes(updated.encode("utf-8"))
print(f"Copied {len(files)} task files and inserted three handoff entries.")
