from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.db import get_conn
from models.utils import get_next_id

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def index():
    return render_template("login.html")


@auth_bp.route("/login", methods=["POST"])
def login():
    name = request.form.get("username")
    pwd = request.form.get("password")

    conn = get_conn()
    cursor = conn.cursor()
    sql = "SELECT * FROM users WHERE user_name=%s AND password=%s"
    cursor.execute(sql, (name, pwd))
    user = cursor.fetchone()
    conn.close()

    if user:
        session["username"] = name  # 保存用户名
        session["user_id"] = user[0]
        return redirect(url_for("home.home"))
    else:
        flash("用户名或密码错误，请重试")
        return redirect(url_for("auth.index"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    name = request.form.get("username")
    pwd = request.form.get("password")

    # 检查用户名是否已存在
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_name=%s", (name,))
    if cursor.fetchone():
        conn.close()
        flash("用户名已存在，请换一个")
        return redirect(url_for("auth.register"))

    # 插入新用户
    new_id = get_next_id("users", "user_id")
    sql = "INSERT INTO users (user_id, user_name, password) VALUES (%s, %s, %s)"
    cursor.execute(sql, (new_id, name, pwd))
    conn.commit()
    conn.close()

    flash("注册成功，请登录")
    return redirect(url_for("auth.index"))


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("您已成功退出登录")
    return redirect(url_for("auth.index"))
