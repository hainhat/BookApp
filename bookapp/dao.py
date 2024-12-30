import json
import hashlib

from flask_login import current_user
from sqlalchemy import extract, func, desc
from models import *
from bookapp import app, db


def load_categories():
    return Category.query.all()


def load_authors():
    return Author.query.all()


def load_book(q=None, cate_id=None, au_id=None, page=None):
    query = db.session.query(Book, BookInventory).outerjoin(BookInventory)
    if q:
        query = query.filter(Book.name.contains(q))
    if cate_id:
        query = query.filter(Book.category_id.__eq__(int(cate_id)))
    if au_id:
        query = query.filter(Book.author_id.__eq__(int(au_id)))

    if page:
        page_size = app.config["PAGE_SIZE"]
        start = (int(page) - 1) * page_size
        query = query.slice(start, start + page_size)
    return query.all()


def load_book_by_id(id):
    return Book.query.get(id)


def count_book():
    return Book.query.count()


def auth_user(username, password):
    if username and password:
        password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
        user = User.query.filter(
            User.username == username.strip(),
            User.password == password,
            User.active == True
        ).first()
        return user
    return None


def get_user_by_id(id):
    return User.query.get(id)


def add_user(name, username, password, avatar):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    u = User(name=name, username=username, password=password, avatar=avatar)
    db.session.add(u)
    db.session.commit()
    return u


# Thêm sách vào kho
def load_books_for_import():
    # Lấy sách và thông tin tồn kho
    return db.session.query(Book, BookInventory).outerjoin(BookInventory).all()


def get_store_rules():
    return StoreRules.query.first()


def create_import(manager_id, book_id, quantity):
    inventory = BookInventory.query.filter_by(book_id=book_id).first()
    if inventory:
        inventory.quantity += quantity
        inventory.imported_at = datetime.now()
    else:
        inventory = BookInventory(book_id=book_id, quantity=quantity)
        db.session.add(inventory)

    db.session.commit()
    return inventory


def get_book_inventory(book_id):
    return BookInventory.query.filter_by(book_id=int(book_id)).first()


def update_inventory(book_id, quantity_sold):
    inventory = get_book_inventory(book_id)
    if inventory:
        if inventory.quantity >= quantity_sold:
            inventory.quantity -= quantity_sold
            db.session.commit()
            return True
    return False


def restore_inventory(book_id, quantity):
    inventory = BookInventory.query.filter_by(book_id=book_id).first()
    if inventory:
        inventory.quantity += quantity
        db.session.commit()
        return True
    return False


def search_books(q=None):
    print("DAO search query:", q)  # Thêm log để debug

    query = db.session.query(Book, BookInventory).outerjoin(BookInventory)
    if q:
        query = query.filter(Book.name.ilike(f'%{q}%'))

    result = query.all()
    print("DAO search results:", result)  # Thêm log để debug
    return result


def create_receipt(staff_id, cart):
    """Tạo hóa đơn mới"""
    try:
        # Tạo receipt
        receipt = Receipt(
            staff_id=staff_id,
            total_amount=0,
            created_at=datetime.now()
        )
        db.session.add(receipt)
        db.session.flush()

        total_amount = 0
        # Thêm chi tiết hóa đơn
        for item in cart.values():
            detail = ReceiptDetail(
                receipt_id=receipt.id,
                book_id=item['id'],
                quantity=item['quantity'],
                unit_price=item['price']
            )
            total_amount += item['quantity'] * item['price']
            db.session.add(detail)

        receipt.total_amount = total_amount
        db.session.commit()
        return receipt

    except Exception as e:
        db.session.rollback()
        raise e


def stats_revenue_by_category(month=None, year=None):
    query = (db.session.query(Category.name, func.sum(OrderDetail.quantity * OrderDetail.unit_price).label('revenue'))
             .join(Book, Book.category_id == Category.id)
             .join(OrderDetail, OrderDetail.book_id == Book.id)
             .join(Order, Order.id == OrderDetail.order_id)
             .filter(Order.status == OrderStatusEnum.PAID))

    if month:
        query = query.filter(extract('month', Order.created_at) == month)
    if year:
        query = query.filter(extract('year', Order.created_at) == year)

    return query.group_by(Category.name).all()


def stats_book_frequency(month=None, year=None):
    query = (db.session.query(
        Book.name, func.sum(OrderDetail.quantity).label('total_quantity'))
             .join(OrderDetail, OrderDetail.book_id == Book.id)
             .join(Order, Order.id == OrderDetail.order_id)
             .filter(Order.status == OrderStatusEnum.PAID))

    if month:
        query = query.filter(extract('month', Order.created_at) == month)
    if year:
        query = query.filter(extract('year', Order.created_at) == year)

    return query.group_by(Book.name).order_by(func.sum(OrderDetail.quantity).desc()).limit(5).all()


def add_comment(content, book_id):
    c = Comment(content=content, book_id=book_id, user=current_user)
    db.session.add(c)
    db.session.commit()
    return c


def get_comments_by_book(book_id):
    return Comment.query.filter_by(book_id=book_id).order_by(desc(Comment.created_at)).all()


if __name__ == "__main__":
    print(load_book())
