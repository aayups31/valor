"""Create three fresh disposable databases for the read-only shadow pilot."""

import argparse
import sqlite3
from contextlib import closing
from pathlib import Path

from aace.shadow import TABLE


def create(directory):
    directory.mkdir(parents=True, exist_ok=False)
    for name in ("bounded", "overbroad", "drift"):
        with closing(sqlite3.connect(directory/f"{name}.sqlite3")) as database:
            database.execute(TABLE)
            database.executemany("INSERT INTO items VALUES (?, ?, ?)",
                                 [(1, "pending", 0), (2, "pending", 0), (3, "protected", 0), (4, "protected", 1)])
            database.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    create(parser.parse_args().directory)
