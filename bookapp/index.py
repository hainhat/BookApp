import math

from flask import render_template, request, redirect, url_for, flash
import dao
from bookapp import app, admin, login
from flask_login import login_user, logout_user, current_user, login_required
import cloudinary.uploader

from models import UserRoleEnum
from utils import roles_required


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
        "authors": dao.load_authors(),
        "UserRoleEnum": UserRoleEnum
    }


@login.user_loader
def load_user(user_id):
    return dao.get_user_by_id(user_id)


@app.route("/login", methods=['get', 'post'])
def login_my_user():
    # Nếu đã đăng nhập thì chuyển về trang chủ
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    err_msg = ""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = dao.auth_user(username=username, password=password)
        if user:
            login_user(user=user)

            # Chuyển hướng về trang chủ theo role
            if user.user_role == UserRoleEnum.ADMIN:
                return redirect(url_for('admin_dashboard'))
            elif user.user_role == UserRoleEnum.MANAGER:
                return redirect(url_for('import_page'))
            elif user.user_role == UserRoleEnum.STAFF:
                return redirect(url_for('sale_page'))
            else:
                return redirect(url_for('index'))
        else:
            err_msg = "Tài khoản hoặc mật khẩu không đúng!"

    return render_template('login.html', err_msg=err_msg)


@app.route("/logout")
def logout_my_user():
    logout_user()
    return redirect(url_for('login_my_user'))


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


@app.route("/import", methods=['GET'])
@login_required
@roles_required([UserRoleEnum.MANAGER])
def import_page():
    if current_user.user_role != UserRoleEnum.MANAGER:
        return redirect("/")

    books = dao.load_books_for_import()
    rules = dao.get_store_rules()
    return render_template('manager/import.html', books=books, rules=rules)


@app.route("/import/<int:book_id>", methods=['POST'])
@login_required
@roles_required([UserRoleEnum.MANAGER])
def import_book(book_id):
    # Đặt return statement mặc định ở đầu
    if request.method != 'POST':
        return redirect(url_for('import_page'))

    try:
        quantity = int(request.form.get('quantity', 0))
        import_price = float(request.form.get('import_price', 0))

        # Kiểm tra quy định
        rules = dao.get_store_rules()
        if quantity < rules.min_import_quantity:
            flash(f"Số lượng nhập tối thiểu là {rules.min_import_quantity}", "error")
            return redirect(url_for('import_page'))

        # Kiểm tra tồn kho
        inventory = dao.get_book_inventory(book_id)
        if inventory and inventory.quantity > rules.min_stock_before_import:
            flash(f"Số lượng tồn kho vẫn còn trên {rules.min_stock_before_import}", "error")
            return redirect(url_for('import_page'))

        # Thực hiện nhập sách
        dao.create_import(
            manager_id=current_user.id,
            book_id=book_id,
            quantity=quantity,
            import_price=import_price
        )

        flash("Nhập sách thành công", "success")

    except Exception as ex:
        flash(f"Lỗi: {str(ex)}", "error")

    return redirect(url_for('import_page'))


if __name__ == '__main__':
    with app.app_context():
        app.run(debug=True)
