# -*- coding: UTF-8 -*-

from flask.ext.sqlalchemy import SQLAlchemy
from basemain import app

sa_db = SQLAlchemy(app)

def init_db():
    # 必须要import models, 否则不会建立表
    import models
    sa_db.create_all()
