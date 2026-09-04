import os

import psycopg
from psycopg.rows import tuple_row

DB_DSN = os.environ.get(
    "DB_DSN",
    "postgresql://f1user:f1password@postgres:5432/f1data",
)

# OpenF1 returns this exact pair when a car has no live position
SENTINEL_X = -8325
SENTINEL_Y = -7058

def fetch_track(session_key: int, driver_number: int, step: int = 20) -> dict:
    params = {
        "session_key": session_key,
        "driver_number": driver_number,
        "sx": SENTINEL_X,
        "sy": SENTINEL_Y,
        "step": step,
    }

    points_sql = """
        SELECT x, y FROM (
            SELECT x, y, ROW_NUMBER() OVER (ORDER BY date) AS rn
            FROM location
            WHERE session_key = %(session_key)s
              AND driver_number = %(driver_number)s
              AND NOT (x = %(sx)s AND y = %(sy)s)
              AND NOT (x = 0 AND y = 0)
        ) sub
        WHERE rn %% %(step)s = 0
        ORDER BY rn
    """
    bounds_sql = """
        SELECT MIN(x), MAX(x), MIN(y), MAX(y)
        FROM location
        WHERE session_key = %(session_key)s
          AND driver_number = %(driver_number)s
          AND NOT (x = %(sx)s AND y = %(sy)s)
          AND NOT (x = 0 AND y = 0)
    """

    with psycopg.connect(DB_DSN) as conn:
        with conn.cursor(row_factory=tuple_row) as cur:
            cur.execute(points_sql, params)
            points = [[float(x), float(y)] for x, y in cur.fetchall()]
            cur.execute(bounds_sql, params)
            min_x, max_x, min_y, max_y = cur.fetchone()

    if min_x is None:
        return {"session_key": session_key, "driver_number": driver_number,
                "bounds": None, "points": []}

    return {
        "session_key": session_key,
        "driver_number": driver_number,
        "bounds": {
            "min_x": float(min_x), "max_x": float(max_x),
            "min_y": float(min_y), "max_y": float(max_y),
        },
        "points": points,
    }
