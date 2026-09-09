"""Is the market beatable in any corner of it, by anyone, without a model?

`calibration` asks whether the market has priced *our features*. This asks a
blunter question with no model in it at all: split the market by country,
code, field size, odds band and class, and in each slice measure

* the return to backing every runner at Betfair SP less commission, with its
  standard error, and
* the market's own self-calibration -- actual win rate minus the mean
  de-vigged probability it quoted -- wherever the slice cuts across races
  rather than taking whole ones. (Proportional de-vigging forces a complete
  book to sum to 1, so a country or a race code would report perfect
  calibration on any market at all; only slices like an odds band, which
  split a race, can say anything.)

A segment where the market is loose shows up here before any model is built,
and cannot be explained away as a feature the model happened to lack. It is
the cheapest possible test of "is there a soft corner", and it is the test
that decides whether building a better model is worth anyone's time.

Measured on 253,784 Betfair-priced UK and Irish runners the answer was no in
every slice: no segment's return was positive at even one standard error, and
across odds bands -- where calibration is a real test -- the market was
accurate to within 0.6 of a percentage point. The two significant results
were both negative: short-priced favourites, the favourite-longshot bias
running the wrong way to bet on.

Second markets get the same treatment via ``place_efficiency``. The place
pool is the classic place to look, because Hausch, Ziemba and Rubinstein's
system beat it in the 1980s by pricing place from the win market. It is not
loose now.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from furlong.config import Settings
from furlong.db import init_db

COMMISSION_DEFAULT = 0.02

ODDS_EDGES = [1.0, 3.0, 6.0, 11.0, 21.0, np.inf]
ODDS_LABELS = ["1-3", "3-6", "6-11", "11-21", "21+"]
FIELD_EDGES = [0, 7, 11, 15, 99]
FIELD_LABELS = ["<=7", "8-11", "12-15", "16+"]

# Segments smaller than this are not reported: the standard error on a few
# hundred bets at racing odds is wider than any edge worth chasing, so a
# small slice can only produce a number that looks like a finding.
MIN_SEGMENT = 3000

RUNS_SQL = """
SELECT r.race_id, r.win_flag, r.finish_pos, ra.date, ra.race_type,
       ra.race_class, ra.field_size, c.country, c.name AS course,
       w.bsp AS win_bsp, p.bsp AS place_bsp
FROM runners r
JOIN races ra ON ra.id = r.race_id
JOIN courses c ON c.id = ra.course_id
JOIN bsp_prices w ON w.runner_id = r.id AND w.market = 'win'
LEFT JOIN bsp_prices p ON p.runner_id = r.id AND p.market = 'place'
WHERE r.status = 'ran' AND w.bsp > 1.0
"""


def load(settings: Settings) -> pd.DataFrame:
    conn = init_db(settings.database_path)
    frame = pd.read_sql(RUNS_SQL, conn)
    conn.close()
    return frame


def prepare(frame: pd.DataFrame, commission: float = COMMISSION_DEFAULT) -> pd.DataFrame:
    """Add the de-vigged win probability, P/L at BSP, and segment labels."""
    if frame.empty:
        return frame.assign(q=[], pl=[], odds_band=[], field_band=[])
    frame = frame.copy()
    book = frame.groupby("race_id")["win_bsp"].transform(lambda s: (1.0 / s).sum())
    frame["q"] = (1.0 / frame["win_bsp"]) / book
    won = frame["win_flag"].fillna(0) == 1
    frame["pl"] = np.where(won, (frame["win_bsp"] - 1.0) * (1 - commission), -1.0)
    frame["odds_band"] = pd.cut(frame["win_bsp"], ODDS_EDGES, labels=ODDS_LABELS)
    frame["field_band"] = pd.cut(frame["field_size"], FIELD_EDGES, labels=FIELD_LABELS)
    return frame


def _slice(name: str, group: pd.DataFrame, whole_races: bool) -> dict:
    n = len(group)
    roi = float(group["pl"].mean())
    # Standard error of the mean return. At racing odds the spread is wide --
    # a 21+ segment carries several points of it -- so a return is never
    # reported without it.
    se = float(group["pl"].std(ddof=1) / np.sqrt(n)) if n > 1 else float("nan")
    # Self-calibration is only meaningful when the slice cuts *across* races.
    # Proportional de-vigging forces each race's book to sum to 1, so a slice
    # made of whole races has a mean quoted probability equal to its win rate
    # by construction -- it would report 0.00 on any market however wrong,
    # which is an artefact, not a finding.
    calib = None
    if not whole_races:
        calib = float(
            (group["win_flag"].fillna(0) == 1).mean() - group["q"].mean()) * 100
    return {
        "segment": name,
        "n": n,
        "roi_pp": roi * 100,
        "se_pp": se * 100,
        "z": roi / se if se else None,
        "calibration_pp": calib,
        "whole_races": whole_races,
    }


def sweep(frame: pd.DataFrame, by: list[str] | str,
          min_segment: int = MIN_SEGMENT) -> list[dict]:
    """Return and self-calibration for each slice of ``by``."""
    if frame.empty:
        return []
    keys = [by] if isinstance(by, str) else list(by)
    if any(k not in frame for k in keys):
        return []
    # Does this grouping keep every race intact? If so its calibration column
    # is uninformative; see _slice.
    per_race = frame.groupby("race_id", observed=True)[keys].nunique()
    whole_races = bool((per_race <= 1).all().all())

    rows = []
    for key, group in frame.groupby(keys, observed=True, dropna=True):
        if len(group) < min_segment:
            continue
        label = key if isinstance(key, str) else " / ".join(str(k) for k in key)
        rows.append(_slice(label, group, whole_races))
    return sorted(rows, key=lambda r: -(r["z"] or 0))


def place_efficiency(frame: pd.DataFrame, bins: int = 10,
                     commission: float = COMMISSION_DEFAULT) -> list[dict]:
    """Is the place market loose relative to the win market?

    Runners are binned by their *win*-market probability and, within each
    bin, the actual place rate is compared with the place market's own
    de-vigged probability. That is the Hausch-Ziemba-Rubinstein test without
    its Harville approximation: no formula relating win to place is assumed,
    the relationship is simply measured.

    The number of places is read from the results rather than from field-size
    rules, so varying place terms need no special handling.
    """
    if frame.empty or "place_bsp" not in frame:
        return []
    df = frame.dropna(subset=["place_bsp"])
    df = df[df["place_bsp"] > 1.0].copy()
    if df.empty:
        return []
    df["placed"] = (df["finish_pos"].fillna(99) <= 2).astype(int)
    grouped = df.groupby("race_id")
    df["places"] = grouped["placed"].transform("sum")
    place_book = grouped["place_bsp"].transform(lambda s: (1.0 / s).sum())
    df = df[(df["places"].between(2, 4)) & (place_book > 0)]
    if df.empty:
        return []
    df["place_prob"] = (1.0 / df["place_bsp"]) / place_book * df["places"]
    df["place_pl"] = np.where(df["placed"] == 1,
                              (df["place_bsp"] - 1.0) * (1 - commission), -1.0)

    rows = []
    for places, sub in df.groupby("places", observed=True):
        if len(sub) < MIN_SEGMENT:
            continue
        try:
            labels = pd.qcut(sub["q"], bins, labels=False, duplicates="drop")
        except ValueError:
            continue
        for label, group in sub.groupby(labels, observed=True):
            n = len(group)
            actual = float(group["placed"].mean())
            implied = float(group["place_prob"].mean())
            se = np.sqrt(actual * (1 - actual) / n) if 0 < actual < 1 else None
            roi = float(group["place_pl"].mean())
            roi_se = float(group["place_pl"].std(ddof=1) / np.sqrt(n)) if n > 1 else None
            rows.append({
                "places": int(places), "bin": int(label), "n": n,
                "win_prob": float(group["q"].mean()),
                "actual": actual, "implied": implied,
                "diff_pp": (actual - implied) * 100,
                "z": (actual - implied) / se if se else None,
                "roi_pp": roi * 100,
                "roi_se_pp": roi_se * 100 if roi_se else None,
            })
    return rows


# Earlier prices, best first, as stored by the Betfair SP archive ingester.
# MORNINGWAP is a genuine morning price; PPWAP is volume-weighted over the
# whole pre-off window and so sits much closer to the close.
EARLY_PRICES = [("morning_wap", "morning WAP"), ("ppwap", "pre-off WAP")]


def drift(settings: Settings, commission: float = COMMISSION_DEFAULT) -> list[dict]:
    """Does the price move predictably between an early price and the close?

    This is the one question the Betfair hub files cannot answer, because they
    carry BSP alone. The free daily SP archives at promo.betfair.com do carry
    earlier prices -- MORNINGWAP and PPWAP -- and ``furlong ingest-bsp`` already
    stores them, so this runs as soon as those files are ingested.

    For each odds band it reports closing line value (the early price divided
    by BSP) alongside the return to actually backing at each price. Both are
    needed, and they answer different questions: CLV says whether the early
    price was better, the return says whether better was enough.

    On 192,564 Australian and New Zealand runners the two answers diverged.
    Favourites drifted from a pre-off average of 1.022 times BSP -- shortening
    into the close, z = -47 -- while runners above 21.0 went the other way at
    z = +166. Genuine, enormous, and worth almost exactly the commission: at
    the pre-off price, favourites returned -0.34% +/- 1.20. A market can be
    predictably wrong and still not pay.
    """
    conn = init_db(settings.database_path)
    frame = pd.read_sql("""
        SELECT r.win_flag, b.bsp, b.ppwap, b.morning_wap
        FROM runners r JOIN bsp_prices b ON b.runner_id = r.id AND b.market = 'win'
        WHERE r.status = 'ran' AND b.bsp > 1.0""", conn)
    conn.close()
    if frame.empty:
        return []

    frame["band"] = pd.cut(frame["bsp"], ODDS_EDGES, labels=ODDS_LABELS)
    won = frame["win_flag"].fillna(0) == 1
    rows = []
    for band, group in frame.groupby("band", observed=True):
        if len(group) < MIN_SEGMENT:
            continue
        entry = {"band": str(band), "n": len(group)}
        for column, label in [("bsp", "BSP")] + EARLY_PRICES:
            prices = pd.to_numeric(group[column], errors="coerce")
            usable = prices.notna() & (prices > 1.0)
            if usable.sum() < MIN_SEGMENT:
                continue
            price = prices[usable]
            win = won.loc[price.index]
            pl = np.where(win, (price - 1.0) * (1 - commission), -1.0)
            entry[label] = {
                "n": int(len(price)),
                "roi_pp": float(pl.mean()) * 100,
                "se_pp": float(pl.std(ddof=1) / np.sqrt(len(pl))) * 100,
                # CLV: what the early price was worth against the close.
                "clv": float((price / group.loc[price.index, "bsp"]).mean()),
            }
        rows.append(entry)
    return rows


def run_efficiency(settings: Settings,
                   commission: float = COMMISSION_DEFAULT) -> dict:
    frame = prepare(load(settings), commission=commission)
    sweeps = {
        "country": sweep(frame, "country"),
        "code": sweep(frame, "race_type"),
        "field size": sweep(frame, "field_band"),
        "odds band": sweep(frame, "odds_band"),
        "country x code": sweep(frame, ["country", "race_type"]),
        "country x odds band": sweep(frame, ["country", "odds_band"]),
    }
    return {
        "runners": int(len(frame)),
        "races": int(frame["race_id"].nunique()) if len(frame) else 0,
        "commission": commission,
        "sweeps": sweeps,
        "place": place_efficiency(frame, commission=commission),
        "drift": drift(settings, commission=commission),
    }


def best_segment(report: dict) -> dict | None:
    """The most profitable slice found anywhere, whatever its significance."""
    rows = [r for group in report["sweeps"].values() for r in group]
    return max(rows, key=lambda r: r["roi_pp"]) if rows else None


def render(report: dict) -> str:
    lines = [
        f"Market efficiency over {report['runners']:,} runners in "
        f"{report['races']:,} races",
        f"  Backing every runner at Betfair SP less {report['commission']:.0%} "
        "commission, by segment.",
    ]
    for name, rows in report["sweeps"].items():
        if not rows:
            continue
        lines += ["", f"  {name}",
                  f"    {'segment':<22}{'n':>9}{'return':>10}{'1 SE':>9}"
                  f"{'z':>8}{'calib pp':>10}"]
        for row in rows:
            calib = ("       n/a" if row["calibration_pp"] is None
                     else f"{row['calibration_pp']:>10.2f}")
            lines.append(
                f"    {row['segment']:<22}{row['n']:>9,}{row['roi_pp']:>9.2f}%"
                f"{row['se_pp']:>9.2f}{row['z'] or 0:>8.2f}{calib}"
            )
    place = report.get("place") or []
    if place:
        worst = max(place, key=lambda r: abs(r["z"] or 0))
        lines += [
            "",
            f"  place market: {len(place)} bins, largest |z| {abs(worst['z'] or 0):.2f} "
            f"({worst['places']} places, bin {worst['bin']}, "
            f"{worst['diff_pp']:+.2f}pp)",
        ]
    for row in report.get("drift") or []:
        if row is report["drift"][0]:
            lines += ["", "  early price vs the close (CLV, and the return to "
                      "backing at each)",
                      f"    {'band':<10}{'n':>9}" +
                      "".join(f"{label:>26}" for label in
                              ["BSP"] + [name for _, name in EARLY_PRICES])]
        cells = ""
        for label in ["BSP"] + [name for _, name in EARLY_PRICES]:
            cell = row.get(label)
            cells += ("%25s " % "-") if not cell else (
                f"{cell['roi_pp']:>10.2f}% CLV {cell['clv']:>6.3f} ")
        lines.append(f"    {row['band']:<10}{row['n']:>9,}{cells}")

    best = best_segment(report)
    if best:
        lines += [
            "",
            f"  Best segment found: {best['segment']} at {best['roi_pp']:+.2f}% "
            f"+/- {best['se_pp']:.2f} (1 SE) over {best['n']:,} runners.",
            "  'calib pp' is the actual win rate minus the mean probability the "
            "market quoted -- the",
            "  market's own accuracy, before any model is involved. It reads "
            "n/a where a slice is",
            "  made of whole races, because de-vigging forces those to agree "
            "whatever the prices.",
        ]
    return "\n".join(lines)
