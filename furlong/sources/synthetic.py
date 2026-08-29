"""Deterministic synthetic racing world with known ground truth.

Purpose: validate the entire Furlong pipeline without paid data. The world
plants a *specific, learnable* inefficiency: the betting public (whose
opinion sets bookmaker prices, and partially sets exchange prices) under-
weights going suitability and trainer form cycles, and over-reacts to a
last-start win. A model that learns those factors from observable history
holds genuine edge; a naive strategy holds none.

Market structure generated per race (win market only):
- three bookmakers: prices from public probabilities, favourite-longshot
  distortion (rho < 1), ~116% overround, per-book noise;
- morning exchange: essentially the public's opinion, ~101% book;
- Betfair SP (BSP): the public's opinion plus a modest dose of truth (late
  money is sharper), margin-free (implied probabilities sum to 1).

Everything is generated from a single seeded ``numpy.random.Generator`` so
identical parameters give byte-identical databases.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date as date_cls
from datetime import datetime, timedelta, timezone

import numpy as np

from furlong.config import Settings
from furlong.db import init_db
from furlong import repo
from furlong.repo import RaceRecord, RunnerRecord

# -- world constants -------------------------------------------------------

IRE_COURSES = [
    "Leopardstown", "Curragh", "Galway", "Punchestown",
    "Dundalk", "Naas", "Cork", "Fairyhouse",
]
GB_COURSES = [
    "Ascot", "Cheltenham", "York", "Newmarket",
    "Aintree", "Sandown", "Doncaster", "Kempton",
]

GOINGS = ["heavy", "soft", "good", "good_to_firm", "firm"]
GOING_SCALE = {"heavy": -2.0, "soft": -1.0, "good": 0.0, "good_to_firm": 1.0, "firm": 2.0}

FLAT_DISTANCES = [1000, 1200, 1400, 1600, 2000, 2400, 2800]
NH_DISTANCES = [3200, 3600, 4000, 4400, 4800]

# Strength model coefficients (the data-generating process)
SHARPNESS = 0.92          # softmax temperature^-1 applied to strength
GOING_COEF = 0.85         # weight of going fit in true strength
TRAINER_FORM_COEF = 0.9   # weight of the trainer hot/cold cycle
DIST_COEF = 1.1           # distance-preference penalty weight

# Public (market) misperception parameters — the planted inefficiency
PUBLIC_GOING_DISCOUNT = 0.90     # public sees only 10% of going fit
PUBLIC_TRAINER_DISCOUNT = 0.95   # public sees only 5% of the trainer form cycle
PUBLIC_LAST_WIN_OVERREACTION = 0.40
PUBLIC_NOISE = 0.15

BOOK_OVERROUND = 1.16
BOOK_FLB_RHO = 0.93              # <1 -> longshots overbet (favourite-longshot bias)
BOOKMAKERS = ["GreenBook", "HarpBet", "ShamrockOdds"]

EXCH_MORNING_TRUTH_WEIGHT = 0.05
EXCH_MORNING_NOISE = 0.12
EXCH_MORNING_BOOK = 1.01

# Calibration target: an omniscient model blended with this market gains
# Delta R-squared of about +0.018 over the market alone -- the same edge
# Benter (1994) reported for his Hong Kong model. A realistic model that
# must infer the latent factors from form should capture a fraction of it.
BSP_TRUTH_WEIGHT = 0.20
BSP_NOISE = 0.05


@dataclass
class _Horse:
    idx: int
    ability: float
    going_slope: float
    pref_log_dist: float
    home_class: int
    form: float
    last_run_day: int = -999
    won_last: bool = False
    trainer_idx: int = 0


MIN_ODDS = 1.02  # bookmakers/exchanges never price below this


def _to_odds(prob: float) -> float:
    """Implied probability -> decimal odds, clamped to a realistic floor."""
    return max(1.0 / prob, MIN_ODDS)


def _softmax(x: np.ndarray) -> np.ndarray:
    z = x - x.max()
    e = np.exp(z)
    return e / e.sum()


def _plackett_luce_order(rng: np.random.Generator, probs: np.ndarray) -> np.ndarray:
    """Sample a full finishing order from win probabilities (Gumbel trick)."""
    gumbel = rng.gumbel(size=probs.shape)
    scores = np.log(np.clip(probs, 1e-12, None)) + gumbel
    return np.argsort(-scores)


def generate_world(settings: Settings, seasons: int = 3, seed: int = 42,
                   n_horses: int = 600, days: int | None = None) -> dict:
    """Generate racing into the configured database.

    ``days`` overrides ``seasons`` with an explicit number of calendar days
    (used by fast tests); the default is ``seasons * 364``.
    """
    conn = init_db(settings.database_path)
    rng = np.random.default_rng(seed)

    n_trainers = max(20, n_horses // 10)
    n_jockeys = max(24, n_horses // 8)

    trainer_skill = rng.normal(0.0, 0.35, size=n_trainers)
    trainer_amp = rng.uniform(0.05, 0.35, size=n_trainers)
    trainer_period = rng.uniform(60, 160, size=n_trainers)
    trainer_phase = rng.uniform(0, 1, size=n_trainers)
    jockey_skill = rng.normal(0.0, 0.20, size=n_jockeys)

    horses: list[_Horse] = []
    for i in range(n_horses):
        ability = float(rng.normal(0, 1))
        horses.append(_Horse(
            idx=i,
            ability=ability,
            going_slope=float(rng.normal(0, 1)),
            pref_log_dist=float(rng.normal(np.log(2200), 0.4)),
            home_class=int(np.clip(round(4 - 1.4 * ability + rng.normal(0, 0.9)), 1, 7)),
            form=float(rng.normal(0, 0.5)),
        ))
    for h in horses:
        h.trainer_idx = int(rng.integers(0, n_trainers))

    start = date_cls(2023, 1, 2)  # a Monday
    total_days = days if days is not None else seasons * 364
    races_written = 0
    runners_written = 0

    for day in range(total_days):
        current = start + timedelta(days=day)
        weekday = current.weekday()
        season_pos = (day % 364) / 364.0  # 0 = early January

        # Meetings per country: weekends busier; Ireland sparser midweek.
        if weekday == 5:      # Saturday
            n_gb, n_ire = 2, 1
        elif weekday == 6:    # Sunday
            n_gb, n_ire = 1, 1
        elif weekday in (1, 3):
            n_gb, n_ire = 1, 1 if rng.random() < 0.6 else 0
        else:
            n_gb, n_ire = 1, 1 if rng.random() < 0.35 else 0

        meetings: list[tuple[str, str]] = []
        gb_pick = rng.choice(len(GB_COURSES), size=n_gb, replace=False)
        meetings += [(GB_COURSES[int(i)], "GB") for i in gb_pick]
        if n_ire:
            ire_pick = rng.choice(len(IRE_COURSES), size=n_ire, replace=False)
            meetings += [(IRE_COURSES[int(i)], "IRE") for i in ire_pick]

        # winter -> softer ground, more NH racing
        winter = season_pos < 0.2 or season_pos > 0.85
        for course, country in meetings:
            going_probs = (
                np.array([0.28, 0.34, 0.28, 0.08, 0.02]) if winter
                else np.array([0.04, 0.16, 0.40, 0.28, 0.12])
            )
            going = GOINGS[int(rng.choice(5, p=going_probs))]
            g_num = GOING_SCALE[going]
            nh_meeting = rng.random() < (0.75 if winter else 0.30)

            for race_no in range(1, 7):
                race_type = "nh" if nh_meeting else "flat"
                distance = float(rng.choice(NH_DISTANCES if race_type == "nh" else FLAT_DISTANCES))
                race_class = int(rng.integers(1, 8))

                eligible = [
                    h for h in horses
                    if abs(h.home_class - race_class) <= 1 and (day - h.last_run_day) >= 6
                ]
                if len(eligible) < 5:
                    continue
                field_size = int(min(rng.integers(5, 17), len(eligible)))
                field_idx = rng.choice(len(eligible), size=field_size, replace=False)
                field = [eligible[int(i)] for i in field_idx]

                draw = rng.permutation(field_size) + 1
                jockeys_for_field = rng.integers(0, n_jockeys, size=field_size)

                # -- true strengths --------------------------------------
                strengths = np.empty(field_size)
                going_fit = np.empty(field_size)
                trainer_cycle = np.empty(field_size)
                dist_fit = np.empty(field_size)
                won_last = np.zeros(field_size)
                for k, h in enumerate(field):
                    going_fit[k] = h.going_slope * g_num * 0.5
                    t = h.trainer_idx
                    trainer_cycle[k] = trainer_amp[t] * np.sin(
                        2 * np.pi * (day / trainer_period[t] + trainer_phase[t])
                    )
                    dist_fit[k] = -DIST_COEF * (np.log(distance) - h.pref_log_dist) ** 2
                    won_last[k] = 1.0 if h.won_last else 0.0
                    strengths[k] = (
                        h.ability
                        + h.form
                        + trainer_skill[t]
                        + TRAINER_FORM_COEF * trainer_cycle[k]
                        + jockey_skill[jockeys_for_field[k]]
                        + GOING_COEF * going_fit[k]
                        + dist_fit[k]
                    )
                true_prob = _softmax(SHARPNESS * strengths)

                # -- public opinion (the planted misperception) ----------
                public_strength = (
                    strengths
                    - PUBLIC_GOING_DISCOUNT * GOING_COEF * going_fit
                    - PUBLIC_TRAINER_DISCOUNT * TRAINER_FORM_COEF * trainer_cycle
                    + PUBLIC_LAST_WIN_OVERREACTION * won_last
                    + rng.normal(0, PUBLIC_NOISE, size=field_size)
                )
                public_prob = _softmax(SHARPNESS * public_strength)

                # -- outcome ---------------------------------------------
                order = _plackett_luce_order(rng, true_prob)
                finish_pos = np.empty(field_size, dtype=int)
                finish_pos[order] = np.arange(1, field_size + 1)
                beaten = np.maximum(0.0, (finish_pos - 1) * 1.8 + rng.normal(0, 0.6, field_size))
                beaten[finish_pos == 1] = 0.0

                # -- prices ----------------------------------------------
                start_time = datetime(
                    current.year, current.month, current.day,
                    13 + (race_no - 1), (35 * race_no) % 60, tzinfo=timezone.utc,
                )
                morning_ts = datetime(
                    current.year, current.month, current.day, 9, 0, tzinfo=timezone.utc
                ).isoformat()

                book_probs = {}
                for b_i, book in enumerate(BOOKMAKERS):
                    noisy = public_prob * np.exp(rng.normal(0, 0.06, field_size))
                    flb = noisy ** BOOK_FLB_RHO
                    flb = flb / flb.sum() * BOOK_OVERROUND
                    book_probs[book] = flb

                mx_strength = (
                    EXCH_MORNING_TRUTH_WEIGHT * strengths
                    + (1 - EXCH_MORNING_TRUTH_WEIGHT) * public_strength
                    + rng.normal(0, EXCH_MORNING_NOISE, field_size)
                )
                mx_prob = _softmax(SHARPNESS * mx_strength) * EXCH_MORNING_BOOK

                bsp_strength = (
                    BSP_TRUTH_WEIGHT * strengths
                    + (1 - BSP_TRUTH_WEIGHT) * public_strength
                    + rng.normal(0, BSP_NOISE, field_size)
                )
                bsp_prob = _softmax(SHARPNESS * bsp_strength)  # margin-free

                # -- persist ---------------------------------------------
                source_id = f"SYN-{current.isoformat()}-{course}-{race_no}"
                race_id = repo.upsert_race(conn, RaceRecord(
                    source_id=source_id,
                    course=course,
                    country=country,
                    date=current.isoformat(),
                    start_time_utc=start_time.isoformat(),
                    race_type=race_type,
                    distance_m=distance,
                    going=going,
                    race_class=race_class,
                    field_size=field_size,
                    status="result",
                ))
                races_written += 1

                for k, h in enumerate(field):
                    runner_id = repo.upsert_runner(conn, race_id, RunnerRecord(
                        horse=f"Horse {h.idx:04d}",
                        trainer=f"Trainer {h.trainer_idx:03d}",
                        jockey=f"Jockey {int(jockeys_for_field[k]):03d}",
                        draw=int(draw[k]) if race_type == "flat" else None,
                        age=None,
                        status="ran",
                        finish_pos=int(finish_pos[k]),
                        beaten_lengths=float(beaten[k]),
                        win_flag=int(finish_pos[k] == 1),
                    ))
                    runners_written += 1
                    for book in BOOKMAKERS:
                        repo.add_odds_snapshot(
                            conn, runner_id, "book", morning_ts,
                            _to_odds(float(book_probs[book][k])), bookmaker=book,
                        )
                    repo.add_odds_snapshot(
                        conn, runner_id, "exchange", morning_ts,
                        _to_odds(float(mx_prob[k])),
                    )
                    repo.upsert_bsp(
                        conn, runner_id, "win",
                        bsp=_to_odds(float(bsp_prob[k])),
                        ppwap=_to_odds(float(bsp_prob[k])),
                        morning_wap=_to_odds(float(mx_prob[k])),
                    )
                    repo.set_synthetic_truth(conn, runner_id, float(true_prob[k]))

                # -- post-race state updates -----------------------------
                for k, h in enumerate(field):
                    h.form = 0.7 * h.form + float(rng.normal(0, 0.4))
                    h.last_run_day = day
                    h.won_last = finish_pos[k] == 1

        if day % 28 == 0:
            conn.commit()

    conn.commit()
    conn.close()
    return {"seasons": seasons, "races": races_written, "runners": runners_written}


class SyntheticSource:
    """Daily-pipeline source for the synthetic world: data is already local."""

    name = "synthetic"

    def sync_daily(self, settings: Settings, conn: sqlite3.Connection, date: str) -> None:
        # Nothing to fetch: `furlong generate` has already populated the DB.
        return None
