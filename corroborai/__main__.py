import argparse
import json
import sys
from pathlib import Path
from .demo import make_files, write_fixture
from .engine import reconcile
from .io import InputError, write_outputs


def main(argv=None):
    parser = argparse.ArgumentParser(description="Local, explainable HR reconciliation. No cloud calls.")
    parser.add_argument("--demo", action="store_true", help="Use entirely synthetic public demonstration data.")
    parser.add_argument("--write-demo", metavar="DIRECTORY", help="Write the five synthetic input workbooks.")
    for name in ("source", "destination", "positions", "reasons", "mapping"):
        parser.add_argument("--" + name, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--prefix", action="append", help="Allowed optional destination prefix; repeatable. Default: dev-08-v2_.")
    parser.add_argument("--reference-date", help="Justified ISO date to disambiguate historical unit periods.")
    parser.add_argument("--no-ai", action="store_true", help="Rules-only run for comparison.")
    args = parser.parse_args(argv)
    if args.write_demo:
        write_fixture(args.write_demo)
        print("Five synthetic workbooks written; no sponsor data included.")
        return 0
    if not args.output:
        parser.error("--output is required.")
    paths = {k: getattr(args, k) for k in ("source", "destination", "positions", "reasons", "mapping")}
    if not args.demo and not all(paths.values()):
        parser.error("Provide all five input paths or use --demo.")
    try:
        files = make_files() if args.demo else {k: (path.name, path.read_bytes()) for k, path in paths.items()}
        run = reconcile(files, prefixes=args.prefix if args.prefix is not None else ["dev-08-v2_"], as_of=args.reference_date, use_ai=not args.no_ai)
        write_outputs(run, args.output)
    except (InputError, OSError) as exc:
        print(f"Input/output error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"source_rows": run["metadata"]["source_rows"], "destination_rows": run["metadata"]["destination_rows"], "result_rows": run["metadata"]["result_rows"], "verdict_counts": run["metadata"]["verdict_counts"], "elapsed_seconds": run["metadata"]["elapsed_seconds"], "output": str(args.output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
