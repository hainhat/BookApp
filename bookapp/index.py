import math
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from flask import render_template, request, redirect, url_for, flash, jsonify, session, abort
import dao, utils
from bookapp import app, admin, login, db
from flask_login import login_user, logout_user, current_user, login_required
import cloudinary.uploader
from models import UserRoleEnum, Order, PaymentMethodEnum, OrderStatusEnum, OrderDetail
from utils import roles_required
from flask_apscheduler import APScheduler

scheduler = APScheduler()


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
        "UserRoleEnum": UserRoleEnum,
        "stats_cart": utils.count_cart(session.get("cart")),
        "get_book_inventory": dao.get_book_inventory
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
            if user.user_role == UserRoleEnum.MANAGER:
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

        flash("Nhập sách thành công", "import_success")

    except Exception as ex:
        flash(f"Lỗi: {str(ex)}", "import_error")

    return redirect(url_for('import_page'))


@app.route("/api/carts", methods=['post'])
def add_to_cart():
    print("Received request data:", request.json)  # Debug log
    cart = session.get("cart")
    if not cart:
        cart = {}

    id = str(request.json.get('id'))
    quantity = request.json.get('quantity', 1)

    # Kiểm tra tồn kho
    inventory = dao.get_book_inventory(id)
    if not inventory or inventory.quantity < quantity:
        return jsonify({"error": "Không đủ số lượng sách trong kho"}), 400

    # Cập nhật số lượng trong kho
    if dao.update_inventory(id, quantity):
        if id in cart:
            cart[id]["quantity"] += quantity
        else:
            cart[id] = {
                "id": id,
                "name": request.json.get('name'),
                "price": float(request.json.get('price')),
                "quantity": quantity
            }
        session['cart'] = cart
        result = utils.count_cart(cart)
        print("Sending response:", result)  # Debug log
        return jsonify(result)

    return jsonify({"error": "Không thể cập nhật số lượng"}), 400


@app.route("/cart")
def cart():
    return render_template("cart.html")


@app.route("/api/carts/<product_id>", methods=['DELETE'])
def delete_cart(product_id):
    cart = session.get('cart')
    if cart and product_id in cart:
        # Khôi phục số lượng sách trong kho
        quantity = cart[product_id]['quantity']
        dao.restore_inventory(product_id, quantity)

        del cart[product_id]
        session['cart'] = cart

    return jsonify(utils.count_cart(cart))


@app.route("/api/carts/<product_id>", methods=['PUT'])
def update_cart(product_id):
    try:
        cart = session.get('cart', {})
        data = request.json
        new_quantity = int(data.get('quantity'))
        current_quantity = cart[product_id]['quantity']

        if new_quantity > current_quantity:
            # Nếu tăng số lượng, kiểm tra và cập nhật inventory
            increase = new_quantity - current_quantity
            inventory = dao.get_book_inventory(product_id)
            if not inventory or inventory.quantity < increase:
                return jsonify({"error": "Không đủ số lượng sách trong kho"}), 400
            dao.update_inventory(product_id, increase)
        else:
            # Nếu giảm số lượng, khôi phục inventory
            decrease = current_quantity - new_quantity
            dao.restore_inventory(product_id, decrease)

        # Cập nhật số lượng trong giỏ hàng
        cart[product_id]['quantity'] = new_quantity
        session['cart'] = cart

        return jsonify({
            "cart_stats": utils.count_cart(cart),
            "product_total": cart[product_id]['price'] * new_quantity
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/order", methods=['GET', 'POST'])
@login_required
def order():
    rules = dao.get_store_rules()
    hours = rules.order_cancel_hours
    # if 'cart' not in session or not session['cart']:
    #     flash("Giỏ hàng trống!", "warning")
    #     return redirect(url_for('cart'))

    if request.method == 'POST':
        payment_method = request.form.get('payment_method')
        delivery_address = request.form.get('delivery_address') if payment_method == 'ONLINE' else None

        # Validate dữ liệu
        # if payment_method == 'ONLINE' and not delivery_address:
        #     flash("Vui lòng nhập địa chỉ giao hàng!", "error")
        #     return redirect(url_for('order'))

        try:
            # Tạo đơn hàng mới
            order = Order(
                user_id=current_user.id,
                payment_method=PaymentMethodEnum[payment_method],
                delivery_address=delivery_address,
                ordered_at=datetime.now()
            )

            # Set status và thời gian hết hạn dựa vào phương thức thanh toán
            if payment_method == 'CASH':
                order.status = OrderStatusEnum.PENDING
                rules = dao.get_store_rules()
                order.expires_at = datetime.now() + timedelta(hours=rules.order_cancel_hours)
            else:
                order.status = OrderStatusEnum.PAID

            db.session.add(order)
            db.session.flush()  # Để lấy order.id

            # Thêm chi tiết đơn hàng
            total_amount = 0
            for item in session['cart'].values():
                detail = OrderDetail(
                    order_id=order.id,
                    book_id=item['id'],
                    quantity=item['quantity'],
                    unit_price=item['price']
                )
                total_amount += item['quantity'] * item['price']
                db.session.add(detail)

            order.total_amount = total_amount
            db.session.commit()

            # Xóa giỏ hàng sau khi đặt hàng thành công
            session.pop('cart', None)

            # flash("Đặt hàng thành công!", "order_success")
            return redirect(url_for('order_details', order_id=order.id))

        except Exception as e:
            db.session.rollback()
            # flash(f"Lỗi khi đặt hàng: {str(e)}", "order_error")
            return redirect(url_for('cart'))

    return render_template('order.html', hours=hours)


# Route hiển thị trang thành công
@app.route('/order_details/<int:order_id>')
@login_required
def order_details(order_id):
    rules = dao.get_store_rules()
    hours = rules.order_cancel_hours
    order = Order.query.get(order_id)
    # Kiểm tra xem đơn hàng có phải của user hiện tại không
    # if order.user_id != current_user.id:
    #     abort(403)
    return render_template('order_details.html', order=order, hours=hours)


# Scheduled task để hủy đơn hàng quá hạn
def init_scheduler(app):
    scheduler = BackgroundScheduler()

    def check_expired_orders():
        with app.app_context():
            now = datetime.now()
            expired_orders = Order.query.filter(
                Order.status == OrderStatusEnum.PENDING,
                Order.payment_method == PaymentMethodEnum.CASH,
                Order.expires_at < now
            ).all()

            for order in expired_orders:
                order.status = OrderStatusEnum.CANCELLED

            if expired_orders:
                db.session.commit()
                print(f"Đã hủy {len(expired_orders)} đơn hàng quá hạn")

    # Sử dụng add_job thay vì task
    scheduler.add_job(
        func=check_expired_orders,
        trigger=IntervalTrigger(hours=1),
        id='check_expired_orders',
        name='Check and cancel expired orders',
        replace_existing=True
    )

    scheduler.start()
    return scheduler


@app.route("/list_orders")
@login_required
def list_orders():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.ordered_at.desc()).all()
    return render_template('list_orders.html', orders=orders)


if __name__ == '__main__':
    with app.app_context():
        init_scheduler(app)
        app.run(debug=True)
