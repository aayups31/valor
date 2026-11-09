"""Verify the published wheel contents and exercise a separate installed copy."""

import argparse
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
CHECK = """
import importlib.metadata as metadata
import json
import sqlite3
import sys
from contextlib import closing
from pathlib import Path
target, root = map(Path, sys.argv[1:])
sys.path.insert(0, str(target))
import aace
from aace.demo.reserve import reserve_replay
from aace.shadow import TABLE, observe
assert Path(aace.__file__).is_relative_to(target)
assert aace.__version__ == metadata.version('valor-aace') == '0.2.0'
case = json.loads((root/'reports/examples/shared-reserve-damaged-v1.json').read_text())
replay = json.loads(json.dumps(reserve_replay('damaged')))
assert replay['guarded'] == case['selected'] and replay['baseline'] == case['baseline']
path = target/'wheel-test.sqlite3'
with closing(sqlite3.connect(path)) as conn:
    conn.execute(TABLE)
    conn.execute("INSERT INTO items VALUES (1, 'protected', 0)")
    conn.commit()
before = path.read_bytes()
assert observe(path, 'archive_all')['shadow_advisory'] == 'protected_changes'
assert before == path.read_bytes()
print('Installed wheel: version, frozen replay and read-only observation verified.')
"""


def verify(wheel, target):
    if target.exists():
        raise ValueError("Installation target must be new")
    package = ROOT/"src/aace"
    with ZipFile(wheel) as archive:
        for path in [*package.rglob("*.py"), *(package/"demo/static").glob("*"), (package/"learning/dataset_splits.json")]:
            if path.is_file() and archive.read(f"aace/{path.relative_to(package).as_posix()}") != path.read_bytes():
                raise ValueError(f"Wheel differs from source: {path}")
        for name in ("LICENSE", "NOTICE"):
            item, = [p for p in archive.namelist() if p.endswith(f".dist-info/licenses/{name}")]
            if archive.read(item) != (ROOT/name).read_bytes():
                raise ValueError(f"Wheel license differs: {name}")
    subprocess.run([sys.executable, "-m", "pip", "install", "--no-index", "--no-deps",
                    "--target", str(target), str(wheel)], check=True)
    subprocess.run([sys.executable, "-I", "-c", CHECK, str(target.resolve()), str(ROOT)], check=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheel", type=Path)
    parser.add_argument("target", type=Path)
    args = parser.parse_args()
    verify(args.wheel, args.target)
