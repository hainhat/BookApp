import enum

from sqlalchemy import Column, String, Integer, Float, ForeignKey, Boolean, Enum, DateTime, CheckConstraint, Index, \
    UniqueConstraint
from bookapp import db, app
from sqlalchemy.orm import relationship
from flask_login import UserMixin
from datetime import datetime


# Thể loại
class Category(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=True)
    books = relationship('Book', backref="category", lazy=True)

    def __str__(self):
        return self.name


# Tác giả
class Author(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=True)
    books = relationship('Book', backref="author", lazy=True)

    def __str__(self):
        return self.name


# Sách
class Book(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    price = Column(Float, default=0)
    image = Column(String(300),
                   default='https://res.cloudinary.com/dcncfkvwv/image/upload/v1733224370/12_0cb5f1a2e9624a1f9490d8acc4caebaf_389a725001ed45ff873ab5a5ddbd79e7_72faca89566e4933a24302a36ba8c7d0_master_oqsanf.jpg')
    active = Column(Boolean, default=True)
    category_id = Column(Integer, ForeignKey(Category.id), nullable=True)
    author_id = Column(Integer, ForeignKey(Author.id), nullable=True)
    order_details = relationship('OrderDetail', back_populates='book', lazy=True)
    receipt_details = relationship('ReceiptDetail', back_populates='book', lazy=True)
    comments = relationship('Comment', backref='book', lazy=True)
    __table_args__ = (
        CheckConstraint('price >= 0', name='check_book_price'),
        Index('idx_category_author', 'category_id', 'author_id'),
    )

    def __str__(self):
        return self.name


# Enum vai trò
class UserRoleEnum(enum.Enum):
    USER = 1
    ADMIN = 2
    STAFF = 3
    MANAGER = 4


# Người dùng
class User(db.Model, UserMixin):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50))
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(128), nullable=False)
    active = Column(Boolean, default=True)
    avatar = Column(String(300),
                    default='https://res.cloudinary.com/dcncfkvwv/image/upload/v1733225278/default-avatar-icon-of-social-media-user-vector_ootybr.jpg')
    user_role = Column(Enum(UserRoleEnum), default=UserRoleEnum.USER)
    comments = relationship('Comment', backref='user', lazy=True)
    google_id = Column(String(100), unique=True, nullable=True)
    email = Column(String(100), unique=True, nullable=True)
    refresh_token = Column(String(255), nullable=True)

    def __str__(self):
        return self.name


# Enum phương thức tính tiền
class PaymentMethodEnum(enum.Enum):
    CASH = 1
    ONLINE = 2


# Enum trạng thái đơn hàng
class OrderStatusEnum(enum.Enum):
    PENDING = 1
    PAID = 2
    CANCELLED = 3


# Nhà kho
class BookInventory(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey(Book.id), nullable=False)
    quantity = Column(Integer, default=0)
    imported_at = Column(DateTime, default=datetime.now())
    book = relationship('Book', backref='inventory', lazy=True)

    def __str__(self):
        return f"Inventory for {self.book.name}: {self.quantity}"


# Đặt hàng (trực tuyến)
class Order(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    ordered_at = Column(DateTime, default=datetime.now())
    total_amount = Column(Float, default=0)
    payment_method = Column(Enum(PaymentMethodEnum))
    delivery_address = Column(String(500), nullable=True)
    status = Column(Enum(OrderStatusEnum), default=OrderStatusEnum.PENDING)
    user = relationship('User', backref='orders', lazy=True)
    order_details = relationship('OrderDetail', backref='order', lazy='dynamic')
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now())
    deleted_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    __table_args__ = (
        Index('idx_ordered_at', 'ordered_at'),
        Index('idx_status', 'status'),
    )

    def __str__(self):
        return f"Order #{self.id} by {self.user.name}"


class OrderDetail(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey(Order.id), nullable=False)
    book_id = Column(Integer, ForeignKey(Book.id), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    book = relationship('Book', back_populates='order_details', lazy=True)
    __table_args__ = (
        CheckConstraint('quantity > 0', name='check_order_quantity'),
        CheckConstraint('unit_price >= 0', name='check_order_unit_price'),
    )

    def __str__(self):
        return f"{self.book.name} x {self.quantity}"


# Hoá đơn (trực tiếp)
class Receipt(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    staff_id = Column(Integer, ForeignKey(User.id), nullable=False)
    created_at = Column(DateTime, default=datetime.now())
    total_amount = Column(Float, default=0)
    staff = relationship('User', lazy=True)
    receipt_details = relationship('ReceiptDetail', backref='receipt', lazy='dynamic')
    updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now())
    deleted_at = Column(DateTime, nullable=True)
    __table_args__ = (
        Index('idx_created_at', 'created_at'),
    )

    def __str__(self):
        return f"Receipt #{self.id} by {self.staff.name}"


class ReceiptDetail(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    receipt_id = Column(Integer, ForeignKey(Receipt.id), nullable=False)
    book_id = Column(Integer, ForeignKey(Book.id), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    book = relationship('Book', back_populates='receipt_details', lazy=True)
    __table_args__ = (
        CheckConstraint('quantity > 0', name='check_receipt_quantity'),
        CheckConstraint('unit_price >= 0', name='check_receipt_unit_price'),
    )

    def __str__(self):
        return f"{self.book.name} x {self.quantity}"


# Quy định
class StoreRules(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    min_import_quantity = Column(Integer, default=150)  # Số lượng sách nhập tối thiểu
    min_stock_before_import = Column(Integer, default=300)  # Số lượng tồn tối thiểu trước khi nhập
    order_cancel_hours = Column(Integer, default=48)  # Thời gian huỷ đơn nếu người dùng không nhận
    updated_at = Column(DateTime, default=datetime.now())
    updated_by = Column(Integer, ForeignKey(User.id))
    admin = relationship('User', lazy=True)
    __table_args__ = (
        CheckConstraint('min_import_quantity > 0', name='check_min_import_quantity'),
        CheckConstraint('min_stock_before_import > 0', name='check_min_stock'),
        CheckConstraint('order_cancel_hours > 0', name='check_cancel_hours'),
    )

    def __str__(self):
        return f"Store Rules (Last updated: {self.updated_at})"


class Comment(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now())
    content = Column(String(255), nullable=False)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    book_id = Column(Integer, ForeignKey(Book.id), nullable=False)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        c1 = Category(name="Truyện tranh")
        c2 = Category(name="Tiểu thuyết")
        c3 = Category(name="Truyện kinh dị")
        db.session.add_all([c1, c2, c3])

        a1 = Author(name="Fujiko Fujio")
        a2 = Author(name="Nguyễn Nhật Ánh")
        a3 = Author(name="Lê Hữu Nam")
        db.session.add_all([a1, a2, a3])

        import json

        with open('data/books.json', encoding='utf-8') as f:
            books = json.load(f)
            for b in books:
                book = Book(**b)
                db.session.add(book)

        import hashlib

        password = str(hashlib.md5("123".encode('utf-8')).hexdigest())

        u1 = User(name='Nhat User', username='user', password=password, user_role=UserRoleEnum.USER)
        u2 = User(name='Nhat Admin', username='admin', password=password, user_role=UserRoleEnum.ADMIN)
        u3 = User(name='Nhat Staff', username='staff', password=password, user_role=UserRoleEnum.STAFF)
        u4 = User(name='Nhat Manager', username='manager', password=password, user_role=UserRoleEnum.MANAGER)
        db.session.add_all([u1, u2, u3, u4])
        db.session.commit()

        if not StoreRules.query.first():
            rules = StoreRules(
                min_import_quantity=150,  # Số lượng nhập tối thiểu
                min_stock_before_import=300,  # Số lượng tồn tối thiểu trước khi nhập
                order_cancel_hours=48,  # Thời gian huỷ đơn
                updated_by=2  # ID của admin
            )
            db.session.add(rules)

        books = Book.query.all()
        for book in books:
            # Kiểm tra xem sách đã có inventory chưa
            if not BookInventory.query.filter_by(book_id=book.id).first():
                # Tạo inventory mới với số lượng mặc định là 100
                inventory = BookInventory(
                    book_id=book.id,
                    quantity=100,
                    imported_at=datetime.now()
                )
                db.session.add(inventory)
        db.session.commit()
