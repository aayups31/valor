"""Run frozen coherent-consequence comparison on fresh development checks."""
import argparse
from pathlib import Path

from aace.learning.structured_pilot import run_structured_pilot

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--continuation-index", type=Path, required=True)
parser.add_argument("--output", type=Path, default=Path("artifacts/structured-pilots"))
parser.add_argument("--smoke", action="store_true", help="Requires a separate engineering continuation index")
args = parser.parse_args()
run_structured_pilot(args.continuation_index, args.output, smoke=args.smoke)
