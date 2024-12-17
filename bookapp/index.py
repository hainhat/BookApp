import math

from flask import render_template, request, redirect
import dao
from bookapp import app, admin, login
from flask_login import login_user, logout_user, current_user
import cloudinary.uploader


@app.route("/")
def index():
    q = request.args.get("q")
    cate_id = request.args.get("category_id")
    au_id = request.args.get("author_id")
    page = request.args.get("page", 1, type=int)
    pages = dao.count_book()
    books = dao.load_book(q=q, cate_id=cate_id, au_id=au_id, page=page)
    return render_template("index.html", books=books, pages=math.ceil(pages / app.config["PAGE_SIZE"]),
                           current_page=page)


@app.route("/books/<int:id>")
def book_details(id):
    book = dao.load_book_by_id(id)
    return render_template("book_details.html", book=book)


@app.context_processor
def common_attribute():
    return {
        "categories": dao.load_categories(),
        "authors": dao.load_authors()
    }


@login.user_loader
def load_user(user_id):
    return dao.get_user_by_id(user_id)


@app.route("/login", methods=['get', 'post'])
def login_my_user():
    if current_user.is_authenticated:
        return redirect("/")
    err_msg = None
    if request.method.__eq__('POST'):
        print(request.form)
        username = request.form.get('username')
        password = request.form.get('password')
        user = dao.auth_user(username=username, password=password)
        if user:
            login_user(user)
            return redirect("/")
        else:
            err_msg = "Tài khoản hoặc mật khẩu không đúng"
    return render_template("login.html", err_msg=err_msg)


@app.route("/logout")
def logout_my_user():
    logout_user()
    return redirect("/login")


@app.route("/register", methods=['get', 'post'])
def register_user():
    ava_path = None
    err_msg = None
    if request.method.__eq__('POST'):
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        if password == confirm:
            name = request.form.get("name")
            username = request.form.get("username")
            avatar = request.files.get("avatar")
            if avatar:
                result = cloudinary.uploader.upload(avatar)
                ava_path = result['secure_url']
            dao.add_user(name=name, username=username, password=password, avatar=ava_path)
            return redirect("/login")
        else:
            err_msg = "Mật khẩu không khớp."
    return render_template("register.html", err_msg=err_msg)


if __name__ == '__main__':
    with app.app_context():
        app.run(debug=True)
