from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify
import pymysql
from models.db import get_conn
from datetime import datetime, timedelta
from collections import defaultdict

home_bp = Blueprint("home", __name__)


@home_bp.route("/home")
def home():
    username = session.get("username")
    user_id = session.get("user_id")
    if not username:
        flash("请先登录")
        return redirect(url_for("auth.index"))

    conn = get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # 随机书籍
    cursor.execute("SELECT book_id, title, cover_path FROM Book ORDER BY RAND() LIMIT 3")
    books = cursor.fetchall()

    # 朋友列表
    cursor.execute("""
        SELECT u.user_id, u.user_name, l.create_time AS latest_note_time
        FROM Friend f
        JOIN Users u ON f.friend_id = u.user_id
        LEFT JOIN UserLatestNote l ON u.user_id = l.user_id
        WHERE f.user_id = %s
    """, (user_id,))
    friends = cursor.fetchall()

    conn.close()

    return render_template("home.html", username=username, books=books, friends=friends)


@home_bp.route("/add_friend", methods=["POST"])
def add_friend():
    user_id = session.get("user_id")
    if not user_id:
        flash("请先登录")
        return redirect(url_for("auth.index"))

    friend_name = request.form.get("friend_name").strip()

    conn = get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # 查找该用户名是否存在
    cursor.execute("SELECT user_id, user_name FROM Users WHERE user_name = %s", (friend_name,))
    friend = cursor.fetchone()

    if not friend:
        search_error = "用户不存在"
    elif friend["user_id"] == user_id:
        search_error = "不能添加自己为好友"
    else:
        friend_id = friend["user_id"]
        # 查是否已经是好友
        cursor.execute("SELECT * FROM Friend WHERE user_id = %s AND friend_id = %s", (user_id, friend_id))
        if cursor.fetchone():
            search_error = "已经是好友了"
        else:
            # 插入双向好友
            cursor.execute("INSERT INTO Friend (user_id, friend_id) VALUES (%s, %s)", (user_id, friend_id))
            cursor.execute("INSERT INTO Friend (user_id, friend_id) VALUES (%s, %s)", (friend_id, user_id))
            conn.commit()
            conn.close()
            return redirect(url_for("home.home", success=True))

    # 回显错误
    # 获取原始数据重新渲染 home 页
    cursor.execute("SELECT book_id, title, cover_path FROM Book ORDER BY RAND() LIMIT 3")
    books = cursor.fetchall()
    cursor.execute("""
        SELECT u.user_id, u.user_name
        FROM Friend f JOIN Users u ON f.friend_id = u.user_id
        WHERE f.user_id = %s
    """, (user_id,))
    friends = cursor.fetchall()
    conn.close()

    return render_template("home.html", username=session["username"],
                           books=books, friends=friends, search_error=search_error)


@home_bp.route("/search")
def search():
    user_id = session.get("user_id")
    if not user_id:
        flash("请先登录")
        return redirect(url_for("auth.index"))

    keyword = request.args.get("q", "").strip()
    search_type = request.args.get("type")

    if not keyword:
        flash("请输入关键词")
        return redirect(url_for("home"))

    conn = get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    book_results = []
    note_results = []

    if search_type == "book":
        # 搜索书籍：书名、作者、标签
        cursor.execute("SELECT * FROM Book WHERE title LIKE %s or author LIKE %s", (f"%{keyword}%", f"%{keyword}%"))
        results = cursor.fetchall()
        book_results.extend(results)

        cursor.execute(
            '''
            SELECT b.*
            FROM Tag t
            JOIN BookTagLink bt ON bt.tag_id = t.tag_id
            JOIN Book b ON b.book_id = bt.book_id
            WHERE t.tag_name LIKE %s
            ''',
            (f"%{keyword}%", )
        )
        results = cursor.fetchall()
        book_results.extend(results)
        conn.close()
        book_results = list({book["book_id"]: book for book in book_results}.values())
        return render_template("search_results.html", books=book_results, keyword=keyword, type="book")

    elif search_type == "note":
        # 搜索普通笔记：引文、内容
        cursor.execute("SELECT * FROM Note WHERE (owner_id = %s) AND (content LIKE %s OR quote LIKE %s)",
                       (user_id, f"%{keyword}%", f"%{keyword}%"))
        results = cursor.fetchall()
        note_results.extend(results)

        cursor.execute(
            '''
            SELECT n.*
            FROM Tag t
            JOIN NoteTagLink nt ON nt.tag_id = t.tag_id
            JOIN Note n ON n.note_id = nt.note_id
            WHERE t.tag_name LIKE %s
            ''',
            (f"%{keyword}%", )
        )
        results = cursor.fetchall()
        note_results.extend(results)
        note_results = list({note["note_id"]: note for note in note_results}.values())

        # 笔记标签
        note_tags = {}
        for note in note_results:
            note_id = note["note_id"]
            cursor.execute("""
                    SELECT t.tag_name FROM Tag t
                    JOIN NoteTagLink ntl ON t.tag_id = ntl.tag_id
                    WHERE ntl.note_id = %s
                """, (note_id,))
            tags = [row["tag_name"] for row in cursor.fetchall()]
            note_tags[note_id] = tags

        # 获取好友列表
        cursor.execute("""
            SELECT u.user_id, u.user_name
            FROM Friend f JOIN Users u ON f.friend_id = u.user_id
            WHERE f.user_id = %s
        """, (user_id,))
        friends = cursor.fetchall()

        conn.close()
        return render_template("search_results.html", notes=note_results,
                               note_tags=note_tags, keyword=keyword, friends=friends, type="note")

    else:
        flash("无效的搜索类型")
        conn.close()
        return redirect(url_for("home"))


@home_bp.route("/contribution_data")
def contribution_data():
    user_id = session.get("user_id")  # 或从数据库获取当前用户
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=29)

    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DATE(create_time), COUNT(*)
        FROM Note
        WHERE owner_id = %s AND DATE(create_time) BETWEEN %s AND %s
        GROUP BY DATE(create_time)
    """, (user_id, start_date, end_date))

    result = cursor.fetchall()
    conn.close()

    # 组装成完整30天数据，空天为0
    date_count_map = defaultdict(int, {str(row[0]): row[1] for row in result})
    contribution = [
        {"date": (start_date + timedelta(days=i)).isoformat(),
         "count": date_count_map[(start_date + timedelta(days=i)).isoformat()]}
        for i in range(30)
    ]

    return jsonify(contribution)