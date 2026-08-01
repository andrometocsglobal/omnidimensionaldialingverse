"""Tiny CLI: `omnidimensional verify power --n 100 --p 2`."""

import argparse
import json
import sys

from . import omnidimensional_midpoint, power_mean_spectrum, verify
from .engine import ComputeError, compute


def main(argv=None):
    ap = argparse.ArgumentParser(prog="omnidimensional")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("sum", help="evaluate a progression sum in closed form")
    c.add_argument("family", choices=["arithmetic", "geometric", "power", "harmonic"])
    c.add_argument("--n", type=int, default=100)
    c.add_argument("--a", type=float, default=1.0)
    c.add_argument("--d", type=float, default=1.0)
    c.add_argument("--r", type=float, default=2.0)
    c.add_argument("--p", type=int, default=2)

    v = sub.add_parser("verify", help="verify a closed form vs brute force")
    v.add_argument("family", choices=["arithmetic", "geometric", "power", "harmonic"])
    v.add_argument("--n", type=int, default=100)
    v.add_argument("--a", type=float, default=1.0)
    v.add_argument("--d", type=float, default=1.0)
    v.add_argument("--r", type=float, default=2.0)
    v.add_argument("--p", type=int, default=2)

    m = sub.add_parser("midpoint", help="harmonic/arithmetic/geometric/quadratic midpoint")
    m.add_argument("a", type=float)
    m.add_argument("b", type=float)
    m.add_argument("--family", default="harmonic")

    s = sub.add_parser("spectrum", help="power-mean spectrum of values")
    s.add_argument("values", nargs="+", type=float)

    args = ap.parse_args(argv)
    if args.cmd in ("sum", "verify"):
        kw = {k: getattr(args, k) for k in ("a", "d", "r", "p")}
        try:
            result = (compute(args.family, args.n, **kw) if args.cmd == "sum"
                      else verify(args.family, args.n, **kw))
        except (ComputeError, ValueError, ZeroDivisionError) as exc:
            print("error: %s" % exc, file=sys.stderr)
            return 2
        print(json.dumps(result, indent=2))
    elif args.cmd == "midpoint":
        try:
            print(omnidimensional_midpoint(args.a, args.b, args.family))
        except (ValueError, ZeroDivisionError) as exc:
            print("error: %s" % exc, file=sys.stderr)
            return 2
    elif args.cmd == "spectrum":
        print(json.dumps(power_mean_spectrum(args.values), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
