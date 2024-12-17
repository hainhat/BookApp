import json
import hashlib
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
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    return User.query.filter(User.username.__eq__(username.strip()), User.password.__eq__(password)).first()


def get_user_by_id(id):
    return User.query.get(id)


def add_user(name, username, password, avatar):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    u = User(name=name, username=username, password=password, avatar=avatar)
    db.session.add(u)
    db.session.commit()
    return u


if __name__ == "__main__":
    print(load_book())
