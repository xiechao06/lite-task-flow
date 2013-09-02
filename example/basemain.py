#! /usr/bin/env python
from datetime import datetime
from hashlib import md5


from flask import Flask, render_template, request, redirect, url_for, current_app, flash
from flask.ext.login import current_user, login_required, LoginManager, login_user, logout_user
from flask.ext.wtf import Form
from wtforms import TextField
from wtforms.validators import DataRequired
from CodernityDB.database import Database
from CodernityDB.hash_index import HashIndex
from sqlalchemy.orm.exc import NoResultFound

from lite_task_flow import TaskFlowEngine, Task, new_task_flow, exceptions, constants, get_task_flow, register_task_cls, get_task

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = "ieyaxuqu"
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///temp.db'

import models


login_manager = LoginManager()
login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):
    return models.User.query.get(user_id)
login_manager.login_view = "login"


db = Database('example/db')

TaskFlowEngine(db)


class Travel(Task):

    @property
    def tag(self):
        return "TRAVEL"
    
    @property
    def dependencies(self):
        return [(PermitTravel(self.task_flow, **self.extra_params))]

register_task_cls(Travel)

class PermitTravel(Task):

    @property
    def tag(self):
        return "PERMIT_TRAVEL"

@app.route("/")
def index():
    return redirect(url_for('task_list'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    class _Form(Form):
        username = TextField('username', validators=[DataRequired()])
    form = _Form()
    if form.validate_on_submit():
        try:
            user = models.User.query.filter(models.User.username==form.username.data).one()
        except NoResultFound:
            return render_template('login.html', form=form, error='no such user "%s"' % form.username.data )
        login_user(user) 
        return redirect(request.args.get('next'))
    return render_template('login.html', form=form)

@app.route("/logout")
@login_required
def logout():
    try:
        logout_user()
    except Exception: # in case sesson expire
        pass

    next_url = request.args.get("next", "/")
    return redirect(next_url)

@app.route("/task", methods=["GET", "POST"])
@login_required
def task():
    
    class _Form(Form):
        destination = TextField('destination', validators=[DataRequired()])
        contact = TextField('contact', validators=[DataRequired()])

    form = _Form()
    
    if form.validate_on_submit():
        task_flow = new_task_flow(Travel, annotation='travel application', 
                                  username=current_user.username, 
                                  destination=form.destination.data, 
                                  contact=form.contact.data)
        try:
            task_flow.start()
        except exceptions.TaskFlowDelayed:
            flash('You have just submitted an travel application')
            return redirect(url_for('task_list'))
    return render_template('/request.html', form=form)

@app.route("/task-list", methods=["GET", "POST"])
@login_required
def task_list():
    if current_user.group.name == 'Customers':
        task_list = (task for task in db.get_many('task_with_initiator', current_user, limit=-1, with_doc=True) if task['doc']['extra_params']['username'] == current_user.username)
    else:
        task_list = db.all('permit_travel', with_doc=True)
    def _to_dict(task):

        return {
            "id_": task['_id'],
            "create_time": datetime.strptime(task['create_time'], "%Y-%m-%d %H:%M:%S"),
            "approved": task['approved'],
            "approve_time": task.get('approve_time'),
            "username": task['extra_params']['username'],
            "destination": task['extra_params']['destination'],
            'contact': task['extra_params']['contact'],
            'task_flow': get_task_flow(task['task_flow_id']),
        }
    return render_template('/task-list.html', task_list=(_to_dict(task['doc']) for task in task_list), constants=constants)

@app.route('/process-task/<id_>', methods=['POST'])
@login_required
def process_task(id_):
    action = request.args['action'].lower()
    if action not in {'permit', 'refuse'}:
        return "", 403
    task = get_task(id_, PermitTravel)
    if action == 'permit':
        task.task_flow.approve(task)
    elif action == 'refuse':
        task.task_flow.refuse(task)
    return ''
