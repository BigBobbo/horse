"""FastAPI application: today's suggestions, race views, performance, method.

Web-first by design. Apple's guideline 5.3.4 and Google Play's real-money
gambling policy govern store-distributed apps; a responsive web app is
subject to neither, avoids the 15-30% store cut, and sidesteps the age-
rating friction that gambling-adjacent apps attract. See
docs/research/legal-regulatory-ireland.md.

Every page carries the responsible-gambling footer. This is a tips and
analytics product: it takes no bets and holds no money, which is what keeps
it outside the Gambling Regulation Act 2024's licensing categories.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from furlong.backtest.performance import compute_performance
from furlong.config import Settings
from furlong.db import init_db

TEMPLATE_DIR = Path(__file__).parent / "templates"

HELPLINE = "1800 936 725"
RG_LINKS = [
    ("GamblingCare.ie", "https://www.gamblingcare.ie/"),
    ("Gamblers Anonymous Ireland", "https://www.gamblersanonymous.ie/"),
]


def _connect(settings: Settings) -> sqlite3.Connection:
    return init_db(settings.database_path)


def load_suggestions(conn: sqlite3.Connection, date: str | None = None) -> list[dict]:
    """Suggestions for a date (defaults to the most recent published day)."""
    if date is None:
        row = conn.execute("SELECT MAX(date) AS d FROM suggestions").fetchone()
        date = row["d"] if row else None
    if date is None:
        return []
    rows = conn.execute(
        """SELECT s.*, h.name AS horse, c.name AS course, c.country AS country,
                  ra.start_time_utc AS off, ra.going AS going, ra.distance_m AS distance_m,
                  t.name AS trainer, j.name AS jockey,
                  st.result AS result, st.pl_units AS pl_units, st.clv AS clv
           FROM suggestions s
           JOIN runners r ON r.id = s.runner_id
           JOIN races ra ON ra.id = s.race_id
           JOIN courses c ON c.id = ra.course_id
           JOIN horses h ON h.id = r.horse_id
           LEFT JOIN trainers t ON t.id = r.trainer_id
           LEFT JOIN jockeys j ON j.id = r.jockey_id
           LEFT JOIN settlements st ON st.suggestion_id = s.id
           WHERE s.date = ?
           ORDER BY s.ev DESC""",
        (date,),
    ).fetchall()
    return [dict(row) for row in rows]


def load_run_status(settings: Settings, date: str | None) -> dict:
    """Why the last run for ``date`` advised what it did.

    An empty card has two very different causes, and conflating them would
    tell the reader the model is working and merely being selective when in
    fact it has been shown to know nothing. The daily run records which it
    was; this reads it back.

    The date is validated here rather than at the route, because it reaches a
    filesystem path: ``/`` takes it straight from the query string, and
    ``suggestions-../../etc/passwd.json`` would otherwise escape the data
    directory. Checking at the point of use survives a new caller forgetting.
    """
    if not date or not _valid_date(date):
        return {}
    path = Path(settings.data_dir) / "suggestions" / f"suggestions-{date}.json"
    try:
        payload = json.loads(path.read_text())
    except (OSError, ValueError):
        return {}
    return {
        "blend_adds_information": payload.get("blend_adds_information", True),
        "blend_lr_p": payload.get("blend_lr_p"),
        "races_considered": payload.get("races_considered"),
    }


def load_race(conn: sqlite3.Connection, race_id: int) -> dict | None:
    race = conn.execute(
        """SELECT ra.*, c.name AS course, c.country AS country FROM races ra
           JOIN courses c ON c.id = ra.course_id WHERE ra.id = ?""",
        (race_id,),
    ).fetchone()
    if race is None:
        return None
    runners = conn.execute(
        """SELECT r.id AS runner_id, h.name AS horse, t.name AS trainer,
                  j.name AS jockey, r.draw, r.status, r.finish_pos,
                  b.bsp AS bsp,
                  (SELECT MAX(o.odds_decimal) FROM odds_snapshots o
                   WHERE o.runner_id = r.id AND o.venue = 'book') AS best_book,
                  (SELECT o.odds_decimal FROM odds_snapshots o
                   WHERE o.runner_id = r.id AND o.venue = 'exchange'
                   ORDER BY o.ts_utc DESC LIMIT 1) AS exchange_odds,
                  s.blend_prob AS model_prob, s.market_prob AS market_prob,
                  s.fair_odds AS fair_odds, s.ev AS ev, s.price_floor AS price_floor,
                  s.status AS suggestion_status
           FROM runners r
           JOIN horses h ON h.id = r.horse_id
           LEFT JOIN trainers t ON t.id = r.trainer_id
           LEFT JOIN jockeys j ON j.id = r.jockey_id
           LEFT JOIN bsp_prices b ON b.runner_id = r.id AND b.market = 'win'
           LEFT JOIN suggestions s ON s.runner_id = r.id
           WHERE r.race_id = ?
           ORDER BY COALESCE(s.blend_prob, 0) DESC, r.id""",
        (race_id,),
    ).fetchall()
    return {"race": dict(race), "runners": [dict(r) for r in runners]}


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.load()
    app = FastAPI(title="Furlong", docs_url="/api/docs")
    templates = Jinja2Templates(directory=str(TEMPLATE_DIR))
    templates.env.globals.update(helpline=HELPLINE, rg_links=RG_LINKS)

    def render(request: Request, template: str, **kwargs):
        """Render a template with the shared context.

        Starlette's current signature takes the request first; passing the
        context dict positionally makes Jinja treat it as the template name.
        """
        return templates.TemplateResponse(
            request, template, {"settings": settings, **kwargs}
        )

    @app.get("/", response_class=HTMLResponse)
    def today(request: Request, date: str | None = Query(default=None)):
        conn = _connect(settings)
        suggestions = load_suggestions(conn, date)
        dates = [
            row["date"] for row in conn.execute(
                "SELECT DISTINCT date FROM suggestions ORDER BY date DESC LIMIT 30"
            )
        ]
        conn.close()
        shown_date = date or (dates[0] if dates else None)
        total_stake = sum(s["stake_units"] for s in suggestions if s["status"] != "withdrawn")
        return render(request, "today.html", suggestions=suggestions,
                      date=shown_date, dates=dates, total_stake=total_stake,
                      run=load_run_status(settings, shown_date))

    @app.get("/races/{race_id}", response_class=HTMLResponse)
    def race_view(request: Request, race_id: int):
        conn = _connect(settings)
        data = load_race(conn, race_id)
        conn.close()
        if data is None:
            raise HTTPException(status_code=404, detail="race not found")
        return render(request, "race.html", **data)

    @app.get("/performance", response_class=HTMLResponse)
    def performance(request: Request):
        conn = _connect(settings)
        metrics = compute_performance(conn)
        conn.close()
        return render(request, "performance.html", metrics=metrics)

    @app.get("/method", response_class=HTMLResponse)
    def method(request: Request):
        return render(request, "method.html")

    # -- JSON API ----------------------------------------------------------

    @app.get("/api/suggestions")
    def api_suggestions(date: str | None = Query(default=None)):
        if date is not None and not _valid_date(date):
            raise HTTPException(status_code=400, detail="date must be ISO format YYYY-MM-DD")
        conn = _connect(settings)
        suggestions = load_suggestions(conn, date)
        conn.close()
        return JSONResponse({
            "date": date or (suggestions[0]["date"] if suggestions else None),
            "count": len(suggestions),
            **load_run_status(settings, date or (suggestions[0]["date"] if suggestions else None)),
            "suggestions": suggestions,
        })

    @app.get("/api/races/{race_id}")
    def api_race(race_id: int):
        conn = _connect(settings)
        data = load_race(conn, race_id)
        conn.close()
        if data is None:
            raise HTTPException(status_code=404, detail="race not found")
        return JSONResponse(data)

    @app.get("/api/performance")
    def api_performance():
        conn = _connect(settings)
        metrics = compute_performance(conn)
        conn.close()
        return JSONResponse(metrics)

    return app


def _valid_date(value: str) -> bool:
    from datetime import date as date_cls

    try:
        date_cls.fromisoformat(value)
        return True
    except ValueError:
        return False
