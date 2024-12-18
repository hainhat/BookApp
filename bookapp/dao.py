import json
import hashlib

from sqlalchemy import extract

from models import *
from bookapp import app, db


def load_categories():
    return Category.query.all()


def load_authors():
    return Author.query.all()


def load_book(q=None, cate_id=None, au_id=None, page=None):
    query = Book.query
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


def create_import(manager_id, book_id, quantity, import_price):
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
    return BookInventory.query.filter_by(book_id=book_id).first()


def update_inventory(book_id, quantity_sold):
    inventory = get_book_inventory(book_id)
    if inventory:
        if inventory.quantity >= quantity_sold:
            inventory.quantity -= quantity_sold
            db.session.commit()
            return True
    return False


def calculate_total_amount(receipt_id):
    receipt = Receipt.query.get(receipt_id)
    total = sum(detail.quantity * detail.unit_price for detail in receipt.receipt_details)
    receipt.total_amount = total
    db.session.commit()


def create_receipt(staff_id, payment_method):
    receipt = Receipt(
        staff_id=staff_id,
        payment_method=payment_method
    )
    db.session.add(receipt)
    db.session.commit()
    return receipt


def add_receipt_detail(receipt_id, book_id, quantity, unit_price):
    detail = ReceiptDetail(
        receipt_id=receipt_id,
        book_id=book_id,
        quantity=quantity,
        unit_price=unit_price
    )
    db.session.add(detail)
    db.session.commit()
    return detail


if __name__ == "__main__":
    print(load_book())
