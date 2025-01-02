import math
from datetime import datetime, timedelta
from io import BytesIO

import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from flask import render_template, request, redirect, url_for, flash, jsonify, session, abort, send_file
import dao, utils
from bookapp import app, admin, login, db
from flask_login import login_user, logout_user, current_user, login_required
import cloudinary.uploader
from models import UserRoleEnum, Order, PaymentMethodEnum, OrderStatusEnum, OrderDetail, User, Book, ReceiptDetail, \
    Receipt
from utils import roles_required
from flask_apscheduler import APScheduler
from vnpay import VNPay

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
    comments = dao.get_comments_by_book(id)
    return render_template("book_details.html", book=book, comments=comments)


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
            next = request.args.get("next")
            return redirect(next if next else "/")
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


@app.route('/login-admin', methods=['post'])
def process_login_admin():
    username = request.form.get('username')
    password = request.form.get('password')
    user = dao.auth_user(username=username, password=password)

    if user:
        login_user(user)
        return redirect("/admin")  # Cho phép tất cả user đăng nhập vào /admin
    else:
        flash("Tài khoản hoặc mật khẩu không đúng", "error")
        return redirect("/admin")


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

    quantity = int(request.form.get('quantity', 0))

    # Kiểm tra quy định
    rules = dao.get_store_rules()
    if quantity < rules.min_import_quantity:
        return redirect(url_for('import_page'))

        # Kiểm tra tồn kho
    inventory = dao.get_book_inventory(book_id)
    if inventory and inventory.quantity > rules.min_stock_before_import:
        return redirect(url_for('import_page'))

        # Thực hiện nhập sách
    dao.create_import(manager_id=current_user.id, book_id=book_id, quantity=quantity)

    return redirect(url_for('import_page'))


@app.route("/api/carts", methods=['post'])
def add_to_cart():
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

        # Lấy số lượng tồn kho mới
        inventory = dao.get_book_inventory(id)

        return jsonify({
            **utils.count_cart(cart),
            "inventory_quantity": inventory.quantity if inventory else 0
        })
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

        # Lấy số lượng tồn kho mới
        inventory = dao.get_book_inventory(product_id)
        inventory_quantity = inventory.quantity if inventory else 0

        return jsonify({
            "cart_stats": utils.count_cart(cart),
            "product_total": cart[product_id]['price'] * new_quantity,
            "inventory_quantity": inventory_quantity
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# Đặt hàng online
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

        try:
            # Tạo đơn hàng
            order = Order(
                user_id=current_user.id,
                payment_method=PaymentMethodEnum[payment_method],
                delivery_address=delivery_address,
                ordered_at=datetime.now()
            )

            if payment_method == 'CASH':
                order.status = OrderStatusEnum.PENDING
                rules = dao.get_store_rules()
                order.expires_at = datetime.now() + timedelta(hours=rules.order_cancel_hours)
            else:
                order.status = OrderStatusEnum.PENDING

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

            # Nếu thanh toán online, tạo URL thanh toán VNPay
            if payment_method == 'ONLINE':
                # Khởi tạo VNPay với config
                vnpay = VNPay()

                # Tạo URL thanh toán
                vnpay_url = vnpay.get_payment_url(
                    order_id=order.id,
                    total_amount=order.total_amount,
                    order_desc=f"Thanh toan don hang #{order.id}"
                )

                # Chuyển hướng đến trang thanh toán VNPay
                return redirect(vnpay_url)

            # Thanh toán tiền mặt
            session.pop('cart', None)  # Xóa giỏ hàng
            return redirect(url_for('order_details', order_id=order.id))

        except Exception as e:
            db.session.rollback()
            return redirect(url_for('cart'))

    return render_template('order.html', hours=hours)


# Chi tiết đơn hàng
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


# Schedule tự động hủy đơn hàng quá hạn
def init_scheduler(app):
    scheduler = BackgroundScheduler()

    def check_expired_orders():
        with app.app_context():
            now = datetime.now()
            expired_orders = Order.query.filter(
                Order.status == OrderStatusEnum.PENDING,
                Order.payment_method == PaymentMethodEnum.CASH,
                Order.expires_at < now).all()

            for order in expired_orders:
                order.status = OrderStatusEnum.CANCELLED

            if expired_orders:
                db.session.commit()

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


@app.route('/payment_return', methods=['GET'])
def payment_return():
    vnpay = VNPay()
    vnp_response = request.args.to_dict()

    if vnpay.verify_response(vnp_response):
        vnp_ResponseCode = vnp_response.get('vnp_ResponseCode')
        order_id = vnp_response.get('vnp_TxnRef')
        amount = int(vnp_response.get('vnp_Amount', 0)) / 100
        order_desc = vnp_response.get('vnp_OrderInfo')
        vnp_TransactionNo = vnp_response.get('vnp_TransactionNo')
        vnp_PayDate = vnp_response.get('vnp_PayDate')

        order = Order.query.get(order_id)

        if order:
            # Đăng nhập lại user trước khi redirect
            user = User.query.get(order.user_id)
            if user:
                login_user(user)
            if vnp_ResponseCode == "00":
                # Thanh toán thành công
                order.status = OrderStatusEnum.PAID
                db.session.commit()
                session.pop('cart', None)
            else:
                # Thanh toán thất bại
                order.status = OrderStatusEnum.CANCELLED
                db.session.commit()

            return redirect(url_for('order_details', order_id=order_id))

    return redirect(url_for('cart'))


@app.route("/online_order", methods=['GET', 'POST'])
@login_required
@roles_required([UserRoleEnum.STAFF])
def online_order_page():
    order = None
    if request.method == 'POST':
        order_id = request.form.get('order_id')
        action = request.form.get('action')

        if order_id:
            order = Order.query.get(order_id)

            if action == 'complete':
                try:
                    # Cập nhật trạng thái đơn hàng
                    order.status = OrderStatusEnum.PAID
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()

    return render_template('staff/online_order.html', order=order)


@app.route('/api/books/<int:id>/comments', methods=['post'])
@login_required
def add_comment(id):
    data = request.json
    c = dao.add_comment(content=data.get('content'), book_id=id)

    return jsonify({'id': c.id, 'content': c.content, 'book_id': c.book_id,
                    'user': {
                        'name': c.user.name,
                        'avatar': c.user.avatar
                    },
                    'created_at': c.created_at.isoformat()
                    })


@app.route('/export_excel')
def export_excel():
    month = request.args.get('month', type=int, default=1)  # Thêm giá trị mặc định nếu không có
    year = request.args.get('year', type=int, default=2024)  # Thêm giá trị mặc định nếu không có

    revenue_stats = dao.stats_revenue_by_category(month, year)
    frequency_stats = dao.stats_book_frequency(month, year)

    revenue_df = pd.DataFrame(revenue_stats, columns=['Thể loại', 'Doanh thu'])
    frequency_df = pd.DataFrame(frequency_stats, columns=['Tên sách', 'Số lượng bán'])

    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        revenue_df.to_excel(writer, sheet_name='Doanh thu', index=False)
        frequency_df.to_excel(writer, sheet_name='Sách bán chạy', index=False)

    output.seek(0)
    return send_file(output, as_attachment=True, download_name=f"thong_ke_{month}_{year}.xlsx",
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


if __name__ == '__main__':
    with app.app_context():
        init_scheduler(app)
        app.run(debug=True)
