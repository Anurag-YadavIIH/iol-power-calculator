"""Command line entry point.

Example:
    iol-calc --al 23.5 --k 44 --a 118.4
"""

import argparse
import sys

from .formulas import srk1_power, srkt_details
from .validation import BiometryError


def main(argv=None):
    p = argparse.ArgumentParser(
        description="IOL power calculator (learning tool, not for clinical use)"
    )
    p.add_argument("--al", type=float, required=True, help="axial length in mm")
    p.add_argument("--k", type=float, required=True, help="mean keratometry in D")
    p.add_argument("--a", type=float, required=True, help="IOL A-constant")
    p.add_argument("--target", type=float, default=0.0, help="target refraction in D (default 0)")
    args = p.parse_args(argv)

    try:
        d = srkt_details(args.al, args.k, args.a, args.target)
        s1 = srk1_power(args.al, args.k, args.a)
    except BiometryError as e:
        print(f"Input error: {e}", file=sys.stderr)
        return 2

    print(f"SRK/T power : {d['power']:.2f} D  (ELP {d['elp']:.2f} mm)")
    print(f"SRK I power : {s1:.2f} D  (emmetropia only)")
    print("Learning tool only. Not for clinical use.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
