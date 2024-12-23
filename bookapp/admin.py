from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from models import Book, Author, Category
from bookapp import app, db

admin = Admin(app=app, name="Book Store Administrator", template_mode="bootstrap4")


class MyCategoryView(ModelView):
    column_list = ['name', 'books']
    column_searchable_list = ['name']


class MyAuthorView(ModelView):
    column_list = ['name', 'books']
    column_searchable_list = ['name']


class MyBookView(ModelView):
    column_list = ['id', 'name', 'price', 'category_id', 'author_id', 'image']
    form_excluded_columns = ['receipt_details', 'order_details', 'inventory']
    column_searchable_list = ['name']
    column_filters = ['price']
    can_export = True


admin.add_view(MyCategoryView(Category, db.session))
admin.add_view(MyAuthorView(Author, db.session))
admin.add_view(MyBookView(Book, db.session))
