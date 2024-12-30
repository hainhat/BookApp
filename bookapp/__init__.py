from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from urllib.parse import quote
from flask_login import LoginManager
import cloudinary
from flask_babel import Babel

app = Flask(__name__)
app.secret_key = "hnsahfiuh43q8"
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:%s@localhost/bookdb?charset=utf8mb4" % quote('Admin@123')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["PAGE_SIZE"] = 4
db = SQLAlchemy(app)
login = LoginManager(app=app)
cloudinary.config(cloud_name='dcncfkvwv',
                  api_key='429919544328797',
                  api_secret='8ceqNUyck4BnLwqIaMDG5ap_hBk')
babel = Babel(app)
