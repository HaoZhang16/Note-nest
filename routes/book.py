import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.utils import secure_filename
from models.db import get_conn
from models.utils import get_next_id
import pymysql

book_bp = Blueprint("book", __name__)  # 蓝图名称为 "book"

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg'}


@book_bp.route("/add_book", methods=["GET", "POST"])
def add_book():
    if request.method == "GET":
        return render_template("add_book.html")

    title = request.form.get("title")
    author = request.form.get("author") or None
    total_page = request.form.get("total_page") or None
    file = request.files.get("cover")

    if not title:
        flash("书名不能为空")
        return redirect(url_for("book.add_book"))  # 注意：url_for 要带上蓝图名

    book_id = get_next_id("Book", "book_id")
    cover_path = None

    if file and allowed_file(file.filename):
        filename = secure_filename(f"book{book_id}_{file.filename}")
        save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)
        cover_path = f"covers/{filename}"

    conn = get_conn()
    cursor = conn.cursor()
    sql = "INSERT INTO Book (book_id, title, author, total_page, cover_path) VALUES (%s, %s, %s, %s, %s)"
    cursor.execute(sql, (book_id, title, author, total_page, cover_path))
    conn.commit()
    conn.close()

    flash("书籍添加成功！")
    return redirect(url_for("book.library"))


@book_bp.route("/library")
def library():
    user_id = session.get("user_id")
    conn = get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute("SELECT * FROM Book")
    books = cursor.fetchall()

    if user_id:
        cursor.execute("SELECT book_id FROM inRead WHERE user_id = %s", (user_id,))
        in_read_books = {row["book_id"] for row in cursor.fetchall()}
    else:
        in_read_books = set()

    conn.close()
    return render_template("library.html", books=books, in_read_books=in_read_books)


@book_bp.route("/mark_in_read", methods=["POST"])
def mark_in_read():
    book_id = request.form.get("book_id")
    user_id = session.get("user_id")

    if not user_id:
        return "未登录，无法标记", 403

    conn = get_conn()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT IGNORE INTO inRead (user_id, book_id)
            VALUES (%s, %s)
        """, (user_id, book_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        return f"数据库错误：{e}", 500
    finally:
        conn.close()

    return redirect(url_for("book.library"))


@book_bp.route("/book/<int:book_id>/notes")
def related_notes(book_id):
    conn = get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    user_id = session.get("user_id")

    # 查询相关联的笔记
    cursor.execute("SELECT * FROM Note WHERE owner_id = %s AND note_id IN (SELECT note_id FROM BookNoteLink WHERE "
                   "book_id = %s)", (user_id, book_id,))
    notes = cursor.fetchall()

    # 获取标签
    note_tags = {}
    for note in notes:
        note_id = note["note_id"]
        cursor.execute("""
            SELECT t.tag_name FROM Tag t
            JOIN NoteTagLink ntl ON t.tag_id = ntl.tag_id
            WHERE ntl.note_id = %s
        """, (note_id,))
        tags = [row["tag_name"] for row in cursor.fetchall()]
        note_tags[note_id] = tags

    conn.close()
    return render_template("notes.html", notes=notes, note_tags=note_tags, flag=1)