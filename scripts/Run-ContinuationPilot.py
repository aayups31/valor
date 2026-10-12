"""Run frozen public-history action-conditioned consequence experiment."""
import argparse
from pathlib import Path

from aace.learning.continuation_pilot import run_continuation_pilot

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, default=Path("artifacts/continuation-pilots"))
parser.add_argument("--smoke", action="store_true", help="Separate small engineering cohort, not the research pilot")
args = parser.parse_args()
run_continuation_pilot(args.output, smoke=args.smoke)
