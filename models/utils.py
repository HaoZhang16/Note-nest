from .db import get_conn
from datetime import timedelta


def get_next_id(table, id_column):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(f"SELECT MAX({id_column}) FROM {table}")
    result = cursor.fetchone()
    conn.close()
    return (result[0] or 0) + 1


def compute_next_review_time(last_time, score):
    if score == 5:
        return last_time + timedelta(days=14)
    elif score == 4:
        return last_time + timedelta(days=7)
    elif score == 3:
        return last_time + timedelta(days=3)
    elif score == 2:
        return last_time + timedelta(days=1)
    else:
        return last_time + timedelta(hours=12)