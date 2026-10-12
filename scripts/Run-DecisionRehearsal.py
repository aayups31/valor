"""Replay frozen v2 proposals under a separately qualified simulator guard."""
import argparse
from pathlib import Path

from aace.learning.rehearsal import run_rehearsal

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("--pilot-index",type=Path,required=True)
parser.add_argument("--output",type=Path,default=Path("artifacts/decision-rehearsals"))
parser.add_argument("--smoke",action="store_true",help="Two engineering subjects on disjoint seeds, not the frozen pilot")
args=parser.parse_args()
run_rehearsal(args.pilot_index,args.output,smoke=args.smoke)
