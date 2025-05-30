from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.db import get_conn
from models.utils import compute_next_review_time
from datetime import datetime
import pymysql
import json
import markdown

review_bp = Blueprint("review", __name__)  # 蓝图名


@review_bp.route("/review")
def review():
    user_id = session.get("user_id")
    if not user_id:
        flash("请先登录")
        return redirect(url_for("auth.index"))

    conn = get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # 找出该用户的所有普通笔记
    cursor.execute("SELECT * FROM Note WHERE owner_id = %s", (user_id,))
    notes = cursor.fetchall()

    review_candidates = []
    last_time_list = []

    now = datetime.now()
    nearest_time = datetime.max
    for note in notes:
        nid = note["note_id"]
        cursor.execute("""
            SELECT review_time, score FROM ReviewLog
            WHERE note_id = %s
            ORDER BY review_time DESC LIMIT 1
        """, (nid,))
        row = cursor.fetchone()

        if not row:
            review_candidates.append(note)  # 从未复习，立即复习
            continue

        last_time, score = row["review_time"], row["score"]
        next_time = compute_next_review_time(last_time, score)
        nearest_time = min(nearest_time, next_time)
        if now >= next_time:
            review_candidates.append(note)
            last_time_list.append(last_time)

    conn.close()

    if review_candidates:
        # 展示第一条笔记
        review_candidates[0]["content"] = markdown.markdown(review_candidates[0]["content"])
        return render_template("note_details.html", note=review_candidates[0],
                               remaining=len(review_candidates)-1, ltime = last_time_list[0] if last_time_list else None, flag=2)
    else:
        return render_template("note_details.html", flag=3, note=None, nearest_time=nearest_time)  # 无需复习


@review_bp.route("/submit_review", methods=["POST"])
def submit_review():
    note_id = int(request.form["note_id"])
    score = int(request.form["score"])

    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(log_id) FROM ReviewLog")
    result = cursor.fetchone()
    log_id = (result[0] or 0) + 1

    now = datetime.now()
    cursor.execute("""
        INSERT INTO ReviewLog (log_id, review_time, score, note_id)
        VALUES (%s, %s, %s, %s)
    """, (log_id, now, score, note_id))
    conn.commit()
    conn.close()

    return redirect(url_for("review.review"))