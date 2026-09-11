# -*- coding: utf-8 -*-
"""Migrate the cleaned dataset from the development SQLite database into MySQL.

This reuses the already-extracted, cleaned and normalised data in
``data/app.db`` instead of re-parsing the raw CSVs, applying the production
``schema.sql`` (3NF, indexes, foreign keys, FULLTEXT) and bulk-copying every
table.  Run from the ``backend`` directory:

    python -m etl.migrate_to_mysql
"""
import os
import sqlite3
import sys
import time

import pymysql

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
SQLITE = os.path.join(HERE, "..", "data", "app.db")
SCHEMA = os.path.join(HERE, "..", "schema.sql")
MYSQL = dict(host="127.0.0.1", port=3306, user="root", password="111111", charset="utf8mb4")

TABLES = ["companies", "skills", "postings", "job_skills", "company_specialities", "users"]
BATCH = {"postings": 500, "companies": 1000, "company_specialities": 2000,
         "job_skills": 2000, "skills": 1000, "users": 1000}


def apply_schema(conn):
    with open(SCHEMA, encoding="utf-8") as f:
        raw = f.read()
    lines = [ln for ln in raw.splitlines() if not ln.strip().startswith("--")]
    statements = [s.strip() for s in "\n".join(lines).split(";") if s.strip()]
    cur = conn.cursor()
    for st in statements:
        cur.execute(st)
    conn.commit()


def main():
    t0 = time.time()
    # 1) raise packet limit globally, then reconnect so the new limit applies
    admin = pymysql.connect(**MYSQL)
    admin.cursor().execute("SET GLOBAL max_allowed_packet=268435456")
    admin.close()

    conn = pymysql.connect(**MYSQL, autocommit=False)
    cur = conn.cursor()
    cur.execute("SET SESSION sql_mode=''")
    print("Applying schema.sql ...")
    apply_schema(conn)
    cur.execute("USE linkedin_jobs")
    cur.execute("SET FOREIGN_KEY_CHECKS=0")
    cur.execute("SET UNIQUE_CHECKS=0")
    # start clean in case of re-run
    for tbl in reversed(TABLES):
        cur.execute(f"DELETE FROM {tbl}")
    conn.commit()

    lite = sqlite3.connect(f"file:{os.path.abspath(SQLITE)}?mode=ro", uri=True)
    for tbl in TABLES:
        cols = [r[1] for r in lite.execute(f"PRAGMA table_info(`{tbl}`)").fetchall()]
        collist = ",".join("`" + c + "`" for c in cols)
        placeholders = ",".join(["%s"] * len(cols))
        insert = f"INSERT INTO {tbl} ({collist}) VALUES ({placeholders})"
        total = lite.execute(f"SELECT COUNT(*) FROM `{tbl}`").fetchone()[0]
        bsize = BATCH.get(tbl, 1000)
        src = lite.execute(f"SELECT {collist} FROM `{tbl}`")
        done, batch = 0, []
        for row in src:
            batch.append(tuple(row))
            if len(batch) >= bsize:
                cur.executemany(insert, batch); conn.commit(); done += len(batch); batch = []
        if batch:
            cur.executemany(insert, batch); conn.commit(); done += len(batch)
        print(f"  {tbl}: {done}/{total}")

    cur.execute("SET FOREIGN_KEY_CHECKS=1")
    cur.execute("SET UNIQUE_CHECKS=1")
    conn.commit()

    print("Verify row counts in MySQL:")
    for tbl in TABLES:
        cur.execute(f"SELECT COUNT(*) FROM {tbl}")
        print(f"  {tbl} = {cur.fetchone()[0]:,}")
    lite.close(); conn.close()
    print(f"Migration complete in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
