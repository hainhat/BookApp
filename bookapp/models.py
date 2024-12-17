from sqlalchemy import Column, String, Integer, Float, ForeignKey, Boolean
from bookapp import db, app
from sqlalchemy.orm import relationship
from flask_login import UserMixin


class Category(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=True)
    books = relationship('Book', backref="category", lazy=True)

    def __str__(self):
        return self.name


class Author(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=True)
    books = relationship('Book', backref="author", lazy=True)

    def __str__(self):
        return self.name


class Book(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    price = Column(Float, default=0)
    image = Column(String(300),
                   default='https://res.cloudinary.com/dcncfkvwv/image/upload/v1733224370/12_0cb5f1a2e9624a1f9490d8acc4caebaf_389a725001ed45ff873ab5a5ddbd79e7_72faca89566e4933a24302a36ba8c7d0_master_oqsanf.jpg')
    active = Column(Boolean, default=True)
    category_id = Column(Integer, ForeignKey(Category.id), nullable=True)
    author_id = Column(Integer, ForeignKey(Author.id), nullable=True)

    def __str__(self):
        return self.name


class User(db.Model, UserMixin):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50))
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(50), nullable=False)
    active = Column(Boolean, default=True)
    avatar = Column(String(300),
                    default='https://res.cloudinary.com/dcncfkvwv/image/upload/v1733225278/default-avatar-icon-of-social-media-user-vector_ootybr.jpg')

    def __str__(self):
        return self.name


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

        u = User(name='Nhat', username='user', password=password)
        db.session.add(u)
        db.session.commit()
