"""End-to-end demonstration on the synthetic world.

Takes a fresh checkout to a browsable app with no external keys: generate a
racing world, train the model, backtest it walk-forward, publish today's
suggestions, run the races, settle them, and report.
"""

from __future__ import annotations

import time

from furlong.backtest.engine import run_backtest
from furlong.backtest.performance import compute_performance, write_performance_report
from furlong.backtest.report import write_report
from furlong.config import Settings
from furlong.db import init_db
from furlong.modeling.train import train_and_evaluate
from furlong.pipeline.daily import run_daily
from furlong.sources.synthetic import generate_world, resolve_open_card
from furlong.value.settlement import settle_suggestions

RULE = "=" * 72


def _step(number: int, total: int, title: str) -> float:
    print(f"\n{RULE}\n[{number}/{total}] {title}\n{RULE}")
    return time.monotonic()


def run_demo(settings: Settings, seed: int = 42, seasons: int = 2) -> dict:
    total = 6
    summary: dict = {}

    started = _step(1, total, "Generating a synthetic racing world")
    stats = generate_world(settings, seasons=seasons, seed=seed, n_horses=450,
                           open_last_day=True)
    print(f"  {stats['races']:,} races, {stats['runners']:,} runners over "
          f"{seasons} season(s), seed {seed}")
    print("  The final day is left as an open card: declared runners, morning")
    print("  prices, no result and no Betfair SP -- the state a real morning is in.")
    print(f"  ({time.monotonic() - started:.1f}s)")

    started = _step(2, total, "Training the model and fitting the market blend")
    metrics = train_and_evaluate(settings, model_kind="gbm")
    print(metrics.summary())
    print(f"  ({time.monotonic() - started:.1f}s)")
    summary["delta_r2"] = metrics.delta_r2

    started = _step(3, total, "Walk-forward backtest at Betfair SP minus commission")
    result = run_backtest(settings, model_kind="gbm")
    print(result.summary())
    paths = write_report(result, settings.data_dir / "reports")
    print(f"  Report: {paths['html']}")
    print(f"  ({time.monotonic() - started:.1f}s)")
    summary["backtest_roi"] = result.roi()
    summary["backtest_bets"] = result.n_bets

    started = _step(4, total, "Publishing suggestions for the open card")
    outcome = run_daily(settings)
    print(outcome.render_terminal())
    print(f"  ({time.monotonic() - started:.1f}s)")
    summary["date"] = outcome.date
    summary["n_suggestions"] = len(outcome.suggestions)

    _step(5, total, "Running the races and settling")
    resolve_open_card(settings, seed=seed + 1)
    settlement = settle_suggestions(settings, date=outcome.date)
    print(f"  {settlement.summary()}")
    summary["mean_clv"] = settlement.mean_clv

    _step(6, total, "Performance")
    conn = init_db(settings.database_path)
    performance = compute_performance(conn)
    conn.close()
    write_performance_report(settings)

    print(f"\n{RULE}\nSUMMARY\n{RULE}")
    print(f"  Model information gain over the market (delta R2): "
          f"{summary['delta_r2']:+.4f}")
    print(f"  Backtest: {summary['backtest_bets']:,} bets, "
          f"ROI {summary['backtest_roi']:+.2%} "
          f"(naive back-everything {result.naive_roi():+.2%})")
    print(f"  Today ({summary['date']}): {summary['n_suggestions']} suggestion(s)")
    if performance.get("n_settled"):
        clv = performance.get("mean_clv")
        print(f"  Settled: {performance['n_settled']} bet(s), "
              f"P/L {performance['profit_units']:+.2f}u"
              + (f", mean CLV {clv:.3f}" if clv else ""))
        print("  Note: a handful of settled bets proves nothing about edge. That is")
        print("  why closing line value, not profit, is the headline metric.")

    print(f"\n  Next: furlong web   (browse the suggestions, races and performance)")
    print(f"        furlong daily --help   (the daily run)")
    print(f"        docs/OPERATIONS.md     (real data, and the daily schedule)")
    return summary
