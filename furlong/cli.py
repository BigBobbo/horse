"""Furlong command-line interface.

Subcommand handlers import their modules lazily so `furlong --help` stays
fast and the CLI remains usable while parts of the system are unconfigured.
"""

from __future__ import annotations

import argparse
import sys

from furlong import __version__
from furlong.config import Settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="furlong",
        description=(
            "Irish-first UK+IRE horse-racing value engine: daily bet suggestions "
            "from a predictive model blended with market odds."
        ),
    )
    parser.add_argument("--version", action="version", version=f"furlong {__version__}")
    sub = parser.add_subparsers(dest="command", metavar="command")

    p = sub.add_parser("init-db", help="Create the SQLite schema (idempotent)")

    p = sub.add_parser("generate", help="Generate the deterministic synthetic racing world")
    p.add_argument("--seasons", type=int, default=3, help="number of seasons (default 3)")
    p.add_argument("--seed", type=int, default=42, help="RNG seed (default 42)")
    p.add_argument("--horses", type=int, default=600, help="horse population (default 600)")

    p = sub.add_parser("ingest-bsp", help="Ingest Betfair SP CSV files (free daily archives)")
    p.add_argument("paths", nargs="*", help="local CSV files to ingest")
    p.add_argument("--download-date", help="download files for ISO date (requires network)")

    p = sub.add_parser("import-csv", help="Import historic results from a mapped CSV file")
    p.add_argument("path", help="CSV file")
    p.add_argument("--mapping", help="JSON column-mapping file (see docs/OPERATIONS.md)")

    p = sub.add_parser("import-kaggle",
                       help="Import the Kaggle UK+IRE dataset (races_YYYY/horses_YYYY)")
    p.add_argument("directory", help="directory containing the extracted CSV files")
    p.add_argument("--inspect", action="store_true",
                   help="report detected files and columns without importing")
    p.add_argument("--years", nargs="*", help="only these years (e.g. 2015 2016)")

    p = sub.add_parser("import-betfair-hub",
                       help="Import Betfair's free UK+IRE model files (BSP for every runner)")
    p.add_argument("target", nargs="?", default=None,
                   help="CSV file or directory (default: <data-dir>/betfair-hub)")
    p.add_argument("--inspect", action="store_true",
                   help="report the files' shape without importing")
    p.add_argument("--download", action="store_true",
                   help="fetch the published files first (no login required)")
    p.add_argument("--since", help="only races on or after this ISO date")
    p.add_argument("--until", help="only races on or before this ISO date")
    p.add_argument("--with-benchmark", action="store_true",
                   help="also store Betfair's own RATED_PRICE for comparison")

    p = sub.add_parser("import-raceform",
                       help="Import an rpscrape-schema SQLite database (raceform.db)")
    p.add_argument("path", help="path to raceform.db")
    p.add_argument("--inspect", action="store_true",
                   help="report the database's shape without importing")
    p.add_argument("--since", help="only races on or after this ISO date")
    p.add_argument("--until", help="only races on or before this ISO date")

    p = sub.add_parser("train", help="Train models and fit the market blend")
    p.add_argument("--model", choices=["gbm", "logit"], default="gbm")

    p = sub.add_parser("backtest", help="Walk-forward backtest at BSP minus commission")
    p.add_argument("--model", choices=["gbm", "logit"], default="gbm")
    p.add_argument("--out", help="directory for the report (default data/reports)")

    p = sub.add_parser("daily", help="Produce today's suggestions")
    p.add_argument("--date", help="ISO date (default: today's racing)")
    p.add_argument("--dry-run", action="store_true", help="compute but write nothing")
    p.add_argument("--out", help="directory for JSON/HTML output (default data/suggestions)")

    p = sub.add_parser("rescore", help="Re-score a date after non-runners")
    p.add_argument("--date", required=True, help="ISO date")

    p = sub.add_parser("settle", help="Settle suggestions against results and BSP")
    p.add_argument("--date", help="ISO date (default: all unsettled)")

    p = sub.add_parser("report", help="Performance report (P/L, ROI, CLV)")
    p.add_argument("--out", help="directory for the report (default data/reports)")

    p = sub.add_parser("web", help="Run the web UI")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)

    p = sub.add_parser("demo", help="End-to-end demo: generate, train, backtest, daily, settle")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--seasons", type=int, default=3)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 0

    settings = Settings.load()

    if args.command == "init-db":
        from furlong.db import init_db

        init_db(settings.database_path)
        print(f"Initialised database at {settings.database_path}")
        return 0

    if args.command == "generate":
        from furlong.sources.synthetic import generate_world

        stats = generate_world(
            settings, seasons=args.seasons, seed=args.seed, n_horses=args.horses
        )
        print(
            f"Synthetic world: {stats['races']} races, {stats['runners']} runners, "
            f"{stats['seasons']} seasons (seed {args.seed}) -> {settings.database_path}"
        )
        return 0

    if args.command == "ingest-bsp":
        from furlong.sources.betfair_bsp import ingest_files, download_for_date

        paths = list(args.paths)
        if args.download_date:
            paths += download_for_date(settings, args.download_date)
        if not paths:
            print("Nothing to ingest: pass CSV paths or --download-date. ", file=sys.stderr)
            return 1
        result = ingest_files(settings, paths)
        print(
            f"BSP ingest: {result.rows_ingested} rows ingested, "
            f"{result.rows_unmatched} unmatched, {result.files} file(s)"
        )
        return 0

    if args.command == "import-csv":
        from furlong.sources.csv_import import import_results_csv

        result = import_results_csv(settings, args.path, mapping_path=args.mapping)
        print(
            f"CSV import: {result.races} races, {result.runners} runners, "
            f"{result.skipped} rows skipped"
        )
        return 0

    if args.command == "import-kaggle":
        from furlong.sources.kaggle_import import import_kaggle_dataset, inspect

        if args.inspect:
            report = inspect(args.directory)
            if not report["pairs"]:
                print(f"No races_YYYY/horses_YYYY pairs found under {args.directory}",
                      file=sys.stderr)
                return 1
            print(f"Found {report['pairs']} file pair(s): "
                  f"{', '.join(report['years'][:6])}"
                  f"{' ...' if len(report['years']) > 6 else ''}")
            for section in ("races", "runners"):
                info = report[section]
                print(f"\n{section} ({info['file']})")
                print(f"  columns found: {', '.join(info['columns'][:20])}")
                print("  mapped:")
                for field_name, column in sorted(info["mapped"].items()):
                    print(f"    {field_name:18} <- {column}")
                missing = set(
                    {"races": ("race_id", "course", "date"),
                     "runners": ("race_id", "horse", "position")}[section]
                ) - set(info["mapped"])
                if missing:
                    print(f"  MISSING (import will fail): {', '.join(sorted(missing))}")
            return 0

        result = import_kaggle_dataset(settings, args.directory,
                                       years=tuple(args.years) if args.years else None)
        print(result.summary())
        return 0 if result.races else 1

    if args.command == "import-betfair-hub":
        from furlong.sources.betfair_hub import (
            import_betfair_hub, inspect, download_files, DEFAULT_DIR_NAME,
        )

        target = args.target or str(settings.data_dir / DEFAULT_DIR_NAME)
        if args.download:
            paths, failures = download_files(target)
            print(f"Downloaded {len(paths)} file(s) to {target}")
            for name, reason in failures:
                print(f"  could not fetch {name}: {reason}", file=sys.stderr)
            if not paths:
                return 1

        if args.inspect:
            report = inspect(target)
            if not report["rows"]:
                print(f"No usable CSV files found at {target}", file=sys.stderr)
                for message in report["errors"]:
                    print(f"  {message}", file=sys.stderr)
                return 1
            print(f"{report['rows']:,} runner rows across {report['races']:,} races "
                  f"in {report['files']} file(s), {report['first']} to {report['last']}")
            print("  by country: " + ", ".join(
                f"{name} {count:,}" for name, count in report["countries"]))
            print("  busiest tracks:")
            for name, count in report["tracks"]:
                print(f"    {name:<24}{count:>8,} runners")
            for message in report["errors"]:
                print(f"  WARNING {message}")
            return 0

        result = import_betfair_hub(settings, target, since=args.since,
                                    until=args.until,
                                    with_benchmark=args.with_benchmark)
        print(result.summary())
        return 0 if result.races else 1

    if args.command == "import-raceform":
        from furlong.sources.raceform_db import import_raceform_db, inspect

        if args.inspect:
            report = inspect(args.path)
            if not report.get("columns"):
                print(f"No 'data' table found in {args.path}", file=sys.stderr)
                return 1
            print(f"{report['rows']:,} runner rows across {report['races']:,} races, "
                  f"{report['first']} to {report['last']}")
            print(f"columns: {', '.join(report['columns'])}")
            print("busiest courses:")
            for row in report["countries"]:
                print(f"    {row['course']:<28} {row['races']:>7,} races")
            return 0

        result = import_raceform_db(settings, args.path,
                                    since=args.since, until=args.until)
        print(result.summary())
        return 0 if result.races else 1

    if args.command == "train":
        from furlong.modeling.train import train_and_evaluate

        metrics = train_and_evaluate(settings, model_kind=args.model)
        print(metrics.summary())
        return 0

    if args.command == "backtest":
        from furlong.backtest.engine import run_backtest
        from furlong.backtest.report import write_report

        result = run_backtest(settings, model_kind=args.model)
        out_dir = args.out or str(settings.data_dir / "reports")
        paths = write_report(result, out_dir)
        print(result.summary())
        print(f"Report written: {paths['json']} and {paths['html']}")
        return 0

    if args.command == "daily":
        from furlong.pipeline.daily import run_daily

        outcome = run_daily(settings, date=args.date, dry_run=args.dry_run, out_dir=args.out)
        print(outcome.render_terminal())
        return 0

    if args.command == "rescore":
        from furlong.pipeline.rescore import run_rescore

        outcome = run_rescore(settings, date=args.date)
        print(outcome.render_terminal())
        return 0

    if args.command == "settle":
        from furlong.value.settlement import settle_suggestions

        result = settle_suggestions(settings, date=args.date)
        print(result.summary())
        return 0

    if args.command == "report":
        from furlong.backtest.performance import write_performance_report

        paths = write_performance_report(settings, out_dir=args.out)
        print(f"Performance report written: {paths['json']}")
        return 0

    if args.command == "web":
        import uvicorn

        from furlong.web.app import create_app

        uvicorn.run(create_app(settings), host=args.host, port=args.port)
        return 0

    if args.command == "demo":
        from furlong.pipeline.demo import run_demo

        run_demo(settings, seed=args.seed, seasons=args.seasons)
        return 0

    parser.error(f"unknown command {args.command!r}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
