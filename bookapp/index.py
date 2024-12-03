import math

from flask import render_template, request, redirect
import dao

from bookapp import app


@app.route("/")
def index():
    q = request.args.get("q")
    cate_id = request.args.get("category_id")
    au_id= request.args.get("author_id")
    page = request.args.get("page", 1, type=int)
    pages = dao.count_book()
    books = dao.load_book(q=q, cate_id=cate_id, au_id=au_id, page=page)
    return render_template("index.html", books=books, pages=math.ceil(pages / app.config["PAGE_SIZE"]), current_page = page)


@app.route("/books/<int:id>")
def book_details(id):
    book = dao.load_book_by_id(id)
    return render_template("book_details.html", book=book)


@app.context_processor
def common_attribute():
    return {
        "categories": dao.load_categories(),
        "authors" : dao.load_authors()
    }


@app.route("/login", methods=['get', 'post'])
def login():
    err_msg = None
    if request.method.__eq__('POST'):
        print(request.form)
        username = request.form.get('username')
        password = request.form.get('password')
        user = dao.auth_user(username=username, password=password)
        if user:
            return redirect("/")
        else:
            err_msg = "Tài khoản hoặc mật khẩu không đúng"

    return render_template("login.html",err_msg=err_msg)


if __name__ == '__main__':
    with app.app_context():
        app.run(debug=True)
