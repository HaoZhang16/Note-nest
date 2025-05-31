from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.db import get_conn
from datetime import datetime
import pymysql
import json
import markdown

note_bp = Blueprint("note", __name__)  # 蓝图名为 note


@note_bp.route("/add_note", methods=["GET", "POST"])
def add_note():
    username = session.get("username")
    if not username:
        flash("请先登录")
        return redirect(url_for("auth.index"))

    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM Users WHERE user_name=%s", (username,))
    result = cursor.fetchone()
    if not result:
        conn.close()
        flash("用户不存在")
        return redirect(url_for("auth.index"))
    user_id = result[0]

    if request.method == "GET":
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT book_id, title FROM Book")
        books = cursor.fetchall()
        cursor.execute("SELECT note_id, content FROM Note WHERE owner_id=%s", (user_id,))
        notes = cursor.fetchall()
        conn.close()
        return render_template("add_note.html", books=books, notes=notes)

    # POST 提交笔记
    content = request.form.get("content")
    quote = request.form.get("quote") or None
    create_time = datetime.now()
    is_summary = request.form.get("is_summary")
    related_book_id = request.form.get("related_book")
    summary_topic = request.form.get("summary_topic") or None
    related_notes = request.form.getlist("related_notes")
    raw_tags = request.form.get("tags")  # 是一个 JSON 字符串
    tags = json.loads(raw_tags) if raw_tags else []

    if not content:
        flash("笔记内容不能为空")
        conn.close()
        return redirect(url_for("note.add_note"))

    cursor = conn.cursor()
    cursor.execute("SELECT MAX(note_id) FROM Note")
    result = cursor.fetchone()
    new_note_id = (result[0] or 0) + 1

    cursor.execute("SELECT MAX(note_id) FROM SummaryNote")
    result = cursor.fetchone()
    new_summary_note_id = (result[0] or 0) + 1

    if is_summary:
        if not summary_topic:
            flash("总结笔记必须填写总结主题")
            conn.rollback()
            conn.close()
            return redirect(url_for("note.add_note"))

        cursor.execute("""
            INSERT INTO SummaryNote (note_id, quote, content, create_time, owner_id, summary_topic)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (new_summary_note_id, quote, content, create_time, user_id, summary_topic))

        for nid in related_notes:
            cursor.execute("INSERT INTO summary (summary_note_id, note_id) VALUES (%s, %s)",
                           (new_summary_note_id, nid))
    else:
        # 调用存储过程：插入 Note 并标记在读书籍
        if related_book_id:
            cursor.execute("CALL AddNoteAndMarkInRead(%s, %s, %s, %s, %s, %s)", (
                new_note_id,
                quote,
                content,
                user_id,
                create_time,
                related_book_id
            ))

            # 绑定笔记与书籍
            cursor.execute("INSERT INTO BookNoteLink (book_id, note_id) VALUES (%s, %s)",
                           (related_book_id, new_note_id))
        else:
            # 没有关联书籍，手动插入 Note
            cursor.execute("""
                INSERT INTO Note (note_id, quote, content, create_time, owner_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (new_note_id, quote, content, create_time, user_id))

        # 插入 Tag 和 NoteTagLink 表
        for tag_name in tags:
            # 查是否已存在该标签
            cursor.execute("SELECT tag_id FROM Tag WHERE tag_name=%s", (tag_name,))
            row = cursor.fetchone()
            if row:
                tag_id = row[0]
            else:
                # 新建标签
                cursor.execute("SELECT MAX(tag_id) FROM Tag")
                result = cursor.fetchone()
                tag_id = (result[0] or 0) + 1
                cursor.execute("INSERT INTO Tag (tag_id, tag_name, use_count) VALUES (%s, %s, 0)", (tag_id, tag_name))

            cursor.execute("INSERT INTO NoteTagLink (note_id, tag_id) VALUES (%s, %s)", (new_note_id, tag_id))

    conn.commit()
    conn.close()
    flash("笔记添加成功")
    return redirect(url_for("home.home"))


@note_bp.route("/notes")
def notes():
    user_id = session.get("user_id")
    conn = get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # 普通笔记
    cursor.execute("SELECT * FROM Note WHERE owner_id = %s", (user_id,))
    plain_notes = cursor.fetchall()

    # 总结笔记
    cursor.execute("SELECT * FROM SummaryNote WHERE owner_id = %s", (user_id,))
    summary_notes = cursor.fetchall()

    # 分享笔记
    cursor.execute(
        '''
        SELECT s.share_id, s.permission, s.share_time,
               u.user_name AS sender_name,
               n.note_id, n.content, n.create_time, n.quote
        FROM NoteShare s
        JOIN Note n ON s.note_id = n.note_id
        JOIN Users u ON s.sender_id = u.user_id
        WHERE s.receiver_id = %s
        ''',
        (user_id,)
    )
    share_notes = cursor.fetchall()

    # 获取标签
    note_tags = {}
    for note in plain_notes:
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
    return render_template("notes.html", notes=plain_notes, snotes=summary_notes,
                           note_tags=note_tags, share_notes=share_notes, friends=friends, flag=0)


@note_bp.route("/note/<int:note_id>")
def note_detail(note_id):
    conn = get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    # 检查权限
    user_id = session.get("user_id")

    # 查询普通笔记
    cursor.execute("SELECT * FROM Note WHERE note_id = %s AND owner_id = %s", (note_id, user_id))
    note = cursor.fetchone()
    if not note:
        # 检查分享
        cursor.execute("""
            SELECT n.*
            FROM NoteShare s JOIN Note n ON s.note_id = n.note_id
            WHERE s.note_id = %s AND s.receiver_id = %s
        """, (note_id, user_id))
        note = cursor.fetchone()

        if not note:
            return "笔记不存在或无权限", 404

    # 查询该笔记的标签
    cursor.execute("""
        SELECT t.tag_name FROM Tag t
        JOIN NoteTagLink ntl ON t.tag_id = ntl.tag_id
        WHERE ntl.note_id = %s
    """, (note_id,))
    tags = [row["tag_name"] for row in cursor.fetchall()]
    note["content"] = markdown.markdown(note["content"])

    conn.close()
    return render_template("note_details.html", note=note, tags=tags, flag=0)


@note_bp.route("/snote/<int:note_id>")
def snote_detail(note_id):
    conn = get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # 查询总结笔记
    cursor.execute("SELECT * FROM SummaryNote WHERE note_id = %s", (note_id,))
    note = cursor.fetchone()
    if not note:
        conn.close()
        return "笔记不存在或无权限", 404

    # 查询相关联的笔记
    cursor.execute("SELECT note_id FROM Summary WHERE Summary_note_id = %s", (note_id,))
    links = cursor.fetchall()

    conn.close()
    return render_template("note_details.html", note=note, links=links, flag=1)


@note_bp.route("/note/<int:note_id>/edit", methods=["GET", "POST"])
def edit_note(note_id):
    user_id = session.get("user_id")
    if not user_id:
        flash("请先登录")
        return redirect(url_for("auth.index"))

    conn = get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    if request.method == "GET":
        # 笔记拥有者
        cursor.execute("SELECT * FROM Note WHERE note_id = %s AND owner_id = %s", (note_id, user_id))
        note = cursor.fetchone()

        # 如果不是拥有者，再检查是否为分享用户且权限不为 read
        if not note:
            cursor.execute("""
                SELECT n.*
                FROM NoteShare s JOIN Note n ON s.note_id = n.note_id
                WHERE s.note_id = %s AND s.receiver_id = %s AND s.permission != 'read'
            """, (note_id, user_id))
            note = cursor.fetchone()

        conn.close()
        if not note:
            return "笔记不存在或无权限", 404
        return render_template("edit_note.html", note=note)

    # 更新引文
    new_quote = request.form.get("quote")

    # 更新内容
    new_content = request.form.get("content")
    if not new_content.strip():
        flash("笔记内容不能为空")
        return redirect(url_for("note.edit_note", note_id=note_id))

    cursor = conn.cursor()
    cursor.execute("UPDATE Note SET content = %s WHERE note_id = %s",
                   (new_content, note_id))
    cursor.execute("UPDATE Note SET quote = %s WHERE note_id = %s",
                   (new_quote, note_id))
    conn.commit()
    conn.close()

    flash("笔记修改成功")
    return redirect(url_for("note.note_detail", note_id=note_id))


@note_bp.route("/delete_note", methods=["POST"])
def delete_note():
    user_id = session.get("user_id")
    if not user_id:
        flash("请先登录")
        return redirect(url_for("auth.index"))

    note_id = int(request.form["note_id"])

    conn = get_conn()

    try:
        conn.begin()
        cursor = conn.cursor()
        # 删除 Note 相关联记录
        cursor.execute("DELETE FROM BookNoteLink WHERE note_id = %s", (note_id,))
        cursor.execute("DELETE FROM ReviewLog WHERE note_id = %s", (note_id,))
        cursor.execute("DELETE FROM summary WHERE note_id = %s", (note_id,))
        cursor.execute("DELETE FROM NoteShare WHERE note_id = %s", (note_id,))
        cursor.execute("DELETE FROM NoteTagLink WHERE note_id = %s", (note_id, ))

        # 删除 Note 本身
        cursor.execute("DELETE FROM Note WHERE note_id = %s AND owner_id = %s", (note_id, user_id))

        conn.commit()
        flash("笔记已删除")
    except Exception as e:
        conn.rollback()
        flash(f"删除失败：{e}")
    finally:
        conn.close()

    return redirect(url_for("note.notes"))


# 删除总结笔记
@note_bp.route("/delete_snote", methods=["POST"])
def delete_snote():
    user_id = session.get("user_id")
    if not user_id:
        flash("请先登录")
        return redirect(url_for("auth.index"))

    note_id = int(request.form["note_id"])

    conn = get_conn()

    try:
        conn.begin()
        cursor = conn.cursor()
        # 删除 summaryNote 相关联记录
        cursor.execute("DELETE FROM summary WHERE summary_note_id = %s", (note_id, ))

        # 删除 summaryNote 本身
        cursor.execute("DELETE FROM summaryNote WHERE note_id = %s", (note_id,))

        conn.commit()
        flash("笔记已删除")
    except Exception as e:
        conn.rollback()
        flash(f"删除失败：{e}")
    finally:
        conn.close()

    return redirect(url_for("note.notes"))


@note_bp.route("/share_note", methods=["POST"])
def share_note():
    sender_id = session.get("user_id")
    if not sender_id:
        flash("请先登录")
        return redirect(url_for("auth.index"))

    note_id = int(request.form.get("note_id"))
    receiver_id = int(request.form.get("receiver_id"))
    permission = request.form.get("permission")
    share_time = datetime.now()

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("SELECT MAX(share_id) FROM NoteShare")
    result = cursor.fetchone()
    share_id = (result[0] or 0) + 1

    # 防止重复分享
    cursor.execute("""
        SELECT * FROM NoteShare
        WHERE sender_id = %s AND receiver_id = %s AND note_id = %s
    """, (sender_id, receiver_id, note_id))
    if cursor.fetchone():
        flash("你已经分享过这条笔记给该好友")
        conn.close()
        return redirect(url_for("note.notes"))

    # 插入记录
    cursor.execute("""
        INSERT INTO NoteShare (share_id, sender_id, receiver_id, note_id, permission, share_time)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (share_id, sender_id, receiver_id, note_id, permission, share_time))
    conn.commit()
    conn.close()

    flash("分享成功！")
    return redirect(url_for("note.notes"))
