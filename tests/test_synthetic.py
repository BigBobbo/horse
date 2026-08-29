import pandas as pd

from furlong.config import Settings
from furlong.db import init_db
from furlong.sources.synthetic import generate_world


def _world_checksums(db_path):
    conn = init_db(db_path)
    races = conn.execute("SELECT COUNT(*) n, COALESCE(SUM(field_size),0) fs FROM races").fetchone()
    runners = conn.execute(
        "SELECT COUNT(*) n, COALESCE(SUM(finish_pos),0) fp FROM runners"
    ).fetchone()
    odds = conn.execute(
        "SELECT COUNT(*) n, ROUND(SUM(odds_decimal), 4) s FROM odds_snapshots"
    ).fetchone()
    conn.close()
    return (races["n"], races["fs"], runners["n"], runners["fp"], odds["n"], odds["s"])


def test_determinism_same_seed(tmp_path):
    s1 = Settings(data_dir=tmp_path / "a")
    s2 = Settings(data_dir=tmp_path / "b")
    r1 = generate_world(s1, seed=99, n_horses=150, days=40)
    r2 = generate_world(s2, seed=99, n_horses=150, days=40)
    assert r1 == r2
    assert _world_checksums(s1.database_path) == _world_checksums(s2.database_path)


def test_different_seed_differs(tmp_path):
    s1 = Settings(data_dir=tmp_path / "a")
    s2 = Settings(data_dir=tmp_path / "b")
    generate_world(s1, seed=1, n_horses=150, days=40)
    generate_world(s2, seed=2, n_horses=150, days=40)
    assert _world_checksums(s1.database_path) != _world_checksums(s2.database_path)


def test_world_statistical_properties(world_conn):
    # exactly one winner per race
    winners = pd.read_sql_query(
        "SELECT race_id, SUM(win_flag) w FROM runners GROUP BY race_id", world_conn
    )
    assert (winners["w"] == 1).all()

    odds = pd.read_sql_query(
        """SELECT o.runner_id, o.venue, o.bookmaker, o.odds_decimal, r.race_id, r.win_flag
           FROM odds_snapshots o JOIN runners r ON r.id = o.runner_id""",
        world_conn,
    )
    odds["imp"] = 1.0 / odds["odds_decimal"]

    book_sums = odds[odds.venue == "book"].groupby(["race_id", "bookmaker"])["imp"].sum()
    assert 1.12 <= book_sums.mean() <= 1.24

    exch_sums = odds[odds.venue == "exchange"].groupby("race_id")["imp"].sum()
    assert 1.00 <= exch_sums.mean() <= 1.03

    bsp = pd.read_sql_query(
        """SELECT b.runner_id, b.bsp, r.race_id, r.win_flag FROM bsp_prices b
           JOIN runners r ON r.id = b.runner_id WHERE b.market='win'""",
        world_conn,
    )
    bsp["imp"] = 1.0 / bsp["bsp"]
    bsp_sums = bsp.groupby("race_id")["imp"].sum()
    assert 0.99 <= bsp_sums.mean() <= 1.02

    # favourite strike rate in the realistic band
    favs = bsp.loc[bsp.groupby("race_id")["imp"].idxmax()]
    assert 0.26 <= favs["win_flag"].mean() <= 0.40

    # favourite-longshot bias at the bookmaker: implied > true for longshots
    truth = pd.read_sql_query("SELECT runner_id, true_prob FROM synthetic_truth", world_conn)
    book = odds[(odds.venue == "book")].merge(truth, on="runner_id")
    longshots = book[book["imp"] < 0.05]
    assert longshots["imp"].mean() > longshots["true_prob"].mean() * 1.1


def test_truth_never_in_analytical_tables(world_conn):
    # ground truth lives only in synthetic_truth
    cols = [r["name"] for r in world_conn.execute("PRAGMA table_info(runners)")]
    assert "true_prob" not in cols
