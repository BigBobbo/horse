import textwrap

from furlong.db import init_db
from furlong.sources.csv_import import import_results_csv

SAMPLE = textwrap.dedent("""\
    date,course,off,name,trainer,jockey,pos,draw,or,age,dist_m,going,type,class,country
    2024-03-01,Curragh,14:30,Harp Melody,W P Mullins,P Townend,1,4,95,5,1600,Good,Flat,3,IRE
    2024-03-01,Curragh,14:30,Liffey Runner,A P O'Brien,R Moore,2,1,88,4,1600,Good,Flat,3,IRE
    2024-03-01,Curragh,15:05,Shannon Mist,J Harrington,S Foley,1,2,84,6,2000,Good,Flat,4,IRE
    2024-03-02,Ascot,14:00,English Rose,J Gosden,F Dettori,1,3,101,4,1600,Good to Firm,Flat,2,GB
    ,,,Bad Row,,,,,,,,,,,
""")


def test_import_sample(settings, tmp_path):
    csv_file = tmp_path / "results.csv"
    csv_file.write_text(SAMPLE)
    result = import_results_csv(settings, csv_file)
    assert result.races == 3
    assert result.runners == 4
    assert result.skipped == 1
    assert result.errors

    conn = init_db(settings.database_path)
    races = conn.execute(
        "SELECT c.country, COUNT(*) n FROM races r JOIN courses c ON c.id=r.course_id "
        "GROUP BY c.country ORDER BY c.country"
    ).fetchall()
    assert {(r["country"], r["n"]) for r in races} == {("GB", 1), ("IRE", 2)}
    going = conn.execute(
        "SELECT going FROM races WHERE source_id LIKE '%Ascot%'"
    ).fetchone()
    assert going["going"] == "good_to_firm"
    fs = conn.execute(
        "SELECT field_size FROM races WHERE source_id LIKE '%14:30%'"
    ).fetchone()
    assert fs["field_size"] == 2
    conn.close()


def test_reimport_is_idempotent(settings, tmp_path):
    csv_file = tmp_path / "results.csv"
    csv_file.write_text(SAMPLE)
    import_results_csv(settings, csv_file)
    result2 = import_results_csv(settings, csv_file)
    conn = init_db(settings.database_path)
    assert conn.execute("SELECT COUNT(*) n FROM races").fetchone()["n"] == 3
    assert conn.execute("SELECT COUNT(*) n FROM runners").fetchone()["n"] == 4
    conn.close()
    assert result2.races == 3  # counted as (re)processed, not duplicated


def test_custom_mapping(settings, tmp_path):
    csv_file = tmp_path / "results.csv"
    csv_file.write_text(
        "race_date,track,race_time,runner,finish\n"
        "2024-05-01,Galway,17:00,Corrib Star,1\n"
    )
    mapping = tmp_path / "map.json"
    mapping.write_text(
        '{"date": "race_date", "course": "track", "off": "race_time", '
        '"horse": "runner", "position": "finish"}'
    )
    result = import_results_csv(settings, csv_file, mapping_path=mapping)
    assert result.races == 1
    assert result.runners == 1
    conn = init_db(settings.database_path)
    row = conn.execute(
        "SELECT c.country FROM races r JOIN courses c ON c.id=r.course_id"
    ).fetchone()
    assert row["country"] == "IRE"  # Galway inferred as Irish course
    conn.close()
