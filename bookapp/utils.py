from functools import wraps
from flask import redirect, url_for
from flask_login import current_user
from models import UserRoleEnum

def roles_required(roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login_my_user'))
            if current_user.user_role not in roles:
                return redirect(url_for('index'))
            return func(*args, **kwargs)
        return wrapper
    return decorator
