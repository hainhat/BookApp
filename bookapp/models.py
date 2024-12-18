import enum

from sqlalchemy import Column, String, Integer, Float, ForeignKey, Boolean, Enum, DateTime, CheckConstraint, Index, \
    UniqueConstraint

from bookapp import db, app
from sqlalchemy.orm import relationship
from flask_login import UserMixin
from sqlalchemy_schemadisplay import create_schema_graph
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
    # import_history = relationship('ImportHistory', back_populates='book', lazy=True)
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
    COMPLETED = 4


# Nhà kho
class BookInventory(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey(Book.id), nullable=False)
    quantity = Column(Integer, default=0)
    imported_at = Column(DateTime, default=datetime.now())
    book = relationship('Book', backref='inventory', lazy=True)

    def __str__(self):
        return f"Inventory for {self.book.name}: {self.quantity}"


# Lịch sử nhập sách
# class ImportHistory(db.Model):
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     book_id = Column(Integer, ForeignKey(Book.id), nullable=False)
#     quantity = Column(Integer, nullable=False)
#     imported_at = Column(DateTime, default=datetime.now())
#     import_price = Column(Float, nullable=False)
#     manager_id = Column(Integer, ForeignKey(User.id), nullable=False)
#     book = relationship('Book', back_populates='import_history', lazy=True)
#     manager = relationship('User', lazy=True)
#
#     __table_args__ = (
#         Index('idx_book_import', 'book_id', 'imported_at'),
#     )
#
#     def __str__(self):
#         return f"Import {self.book.name} - Quantity: {self.quantity}"


# Đặt hàng (trực tuyến)
class Order(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    ordered_at = Column(DateTime, default=datetime.now())
    total_amount = Column(Float, default=0)
    payment_method = Column(Enum(PaymentMethodEnum))
    status = Column(Enum(OrderStatusEnum), default=OrderStatusEnum.PENDING)
    user = relationship('User', backref='orders', lazy=True)
    order_details = relationship('OrderDetail', backref='order', lazy='dynamic')
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now())
    deleted_at = Column(DateTime, nullable=True)
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
    payment_method = Column(Enum(PaymentMethodEnum))
    staff = relationship('User', lazy=True)
    receipt_details = relationship('ReceiptDetail', backref='receipt', lazy='dynamic')
    updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now())
    deleted_at = Column(DateTime, nullable=True)
    __table_args__ = (
        Index('idx_created_at', 'created_at'),
        Index('idx_payment_method', 'payment_method'),
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


# Thống kê
class MonthlyStatistics(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    category_id = Column(Integer, ForeignKey(Category.id), nullable=False)
    total_revenue = Column(Float, default=0)
    total_orders = Column(Integer, default=0)
    category = relationship('Category', lazy=True)
    __table_args__ = (
        UniqueConstraint('month', 'year', 'category_id', name='unique_monthly_stats'),
        CheckConstraint('month BETWEEN 1 AND 12', name='check_valid_month'),
        CheckConstraint('total_revenue >= 0', name='check_revenue'),
        CheckConstraint('total_orders >= 0', name='check_orders'),
    )

    def __str__(self):
        return f"Stats for {self.category.name} - {self.month}/{self.year}"


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


def create_db_diagram():
    # Create the directed graph
    graph = create_schema_graph(
        metadata=db.metadata,
        engine=db.engine,  # Add the engine parameter
        show_datatypes=True,
        show_indexes=True,
        rankdir='LR',
        concentrate=False
    )

    # Write graph to file
    graph.write_png('database_schema.png')


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        create_db_diagram()

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

        u1 = User(name='Nhat', username='user', password=password, user_role=UserRoleEnum.USER)
        u2 = User(name='Nhat', username='admin', password=password, user_role=UserRoleEnum.ADMIN)
        u3 = User(name='Nhat', username='staff', password=password, user_role=UserRoleEnum.STAFF)
        u4 = User(name='Nhat', username='manager', password=password, user_role=UserRoleEnum.MANAGER)
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

        db.session.commit()

