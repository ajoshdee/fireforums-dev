from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.bootstrap import Bootstrap
from flask.ext.moment import Moment
from instance.config import APP_ID, APP_SECRET
from .momentjs import momentjs

app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('config.py')
app.config['OAUTH_CREDENTIALS'] = {
    'facebook': {
        'id': APP_ID,
        'secret': APP_SECRET
    }
}
app.jinja_env.globals['momentjs'] = momentjs
db = SQLAlchemy(app)
lm = LoginManager(app)
lm.login_view = 'login'
bootstrap = Bootstrap(app)
moment = Moment(app)
from app import views, models