from datetime import datetime
from flask import redirect, request, url_for, jsonify, render_template, flash
from flask_admin import Admin, BaseView, expose, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user, logout_user, login_required
from sqlalchemy.exc import SQLAlchemyError
from bookapp import app, db, dao
from bookapp.utils import roles_required
from models import Book, Author, Category, UserRoleEnum, StoreRules


class MyModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRoleEnum.ADMIN


class MyBaseView(BaseView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRoleEnum.ADMIN


class MyCategoryView(MyModelView):
    column_list = ['name', 'books']
    column_searchable_list = ['name']


class MyAuthorView(MyModelView):
    column_list = ['name', 'books']
    column_searchable_list = ['name']


class MyBookView(MyModelView):
    column_list = ['id', 'name', 'price', 'category_id', 'author_id', 'image']
    form_excluded_columns = ['receipt_details', 'order_details', 'inventory']
    column_searchable_list = ['name']
    column_filters = ['price']
    can_export = True


class StatsView(MyBaseView):
    @expose('/')
    def index(self):
        month = request.args.get('month', datetime.now().month, type=int)
        year = request.args.get('year', datetime.now().year, type=int)
        revenue_stats = dao.stats_revenue_by_category(month=month, year=year)
        frequency_stats = dao.stats_book_frequency(month=month, year=year)
        return self.render('admin/stats.html', revenue_stats=revenue_stats, frequency_stats=frequency_stats,
                           current_month=month, current_year=year)


class LogoutView(MyBaseView):
    def is_accessible(self):
        return current_user.is_authenticated

    @expose('/')
    def index(self):
        logout_user()
        return redirect('/admin')


class RulesView(MyModelView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        rules = StoreRules.query.first()
        if request.method == 'POST':
            try:
                # Thay đổi các quy định
                rules.min_import_quantity = int(request.form.get('min_import_quantity', rules.min_import_quantity))
                rules.min_stock_before_import = int(
                    request.form.get('min_stock_before_import', rules.min_stock_before_import))
                rules.order_cancel_hours = int(request.form.get('order_cancel_hours', rules.order_cancel_hours))
                db.session.commit()
                flash("Cập nhật quy định thành công!", "success")
            except SQLAlchemyError as e:
                db.session.rollback()
                flash(f"Lỗi khi cập nhật quy định: {str(e)}", "error")
            return redirect(url_for('.index'))

        return self.render('admin/rules.html', rules=rules)


class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        return self.render('admin/index.html', UserRoleEnum=UserRoleEnum)


admin = Admin(app=app, name="Book Store Administrator", template_mode="bootstrap4", index_view=MyAdminIndexView())
admin.add_view(MyCategoryView(Category, db.session))
admin.add_view(MyAuthorView(Author, db.session))
admin.add_view(MyBookView(Book, db.session))
admin.add_view(StatsView(name="Thống kê"))
admin.add_view(RulesView(StoreRules, db.session, name="Quy định"))
admin.add_view(LogoutView(name="Đăng xuất"))
