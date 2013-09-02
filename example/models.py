# -*- coding: UTF-8 -*-

from flask.ext.login import UserMixin 
from database import sa_db

class User(UserMixin, sa_db.Model):

    __tablename__ = 'TB_USER'
    
    id = sa_db.Column(sa_db.Integer, primary_key=True)
    username = sa_db.Column(sa_db.String(32), nullable=False, unique=True)
    group_id = sa_db.Column(sa_db.Integer, sa_db.ForeignKey('TB_GROUP.id'))
    group = sa_db.relationship("Group")

    @property
    def is_clerk(self):
        return self.group.name == 'Clerks'

class Group(sa_db.Model):

    __tablename__ = 'TB_GROUP'
    id = sa_db.Column(sa_db.Integer, primary_key=True)
    name = sa_db.Column(sa_db.String(32), nullable=False, unique=True)

