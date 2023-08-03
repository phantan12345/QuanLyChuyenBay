from urllib.parse import quote
from flask import Flask
from flask_babelex import Babel
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager


app = Flask(__name__)

app.secret_key = '$%^*&())(*&%^%4678675446&#%$%^&&*^$&%&*^&^'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:%s@localhost/project_btl?charset=utf8mb4' % quote('phantan0106')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
babel = Babel(app)

db = SQLAlchemy(app=app)

login = LoginManager(app=app)


@babel.localeselector
def get_locale():
    return 'vi'