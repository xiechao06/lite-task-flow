#! /usr/bin/env python
import types

from basemain import app
from database import sa_db, init_db
from models import Group, User

def do_commit(obj):

    if isinstance(obj, types.ListType) or isinstance(obj, types.TupleType):
        sa_db.session.add_all(obj)
    else:
        sa_db.session.add(obj)
    sa_db.session.commit()
    return obj

sa_db.drop_all()
init_db()

customers = do_commit(Group(name='Customers'))
clerks = do_commit(Group(name='Clerks'))
do_commit(User(username='Tom', group=customers))
do_commit(User(username='Jerry', group=clerks))


from CodernityDB.database import Database 
from CodernityDB.hash_index import HashIndex

class TaskWithIntiator(HashIndex):

    def __init__(self, *args, **kwargs):
        kwargs['key_format'] = '16s'
        super(TaskWithIntiator, self).__init__(*args, **kwargs)

    def make_key_value(self, data):
        if data['t'] == constants.TASK_TYPE_CODE and data['tag'] == 'TRAVEL':
            return md5(data['extra_params']['username']).digest(), None

    def make_key(self, key):
        return md5(key.username).digest()

class PermitTravelIndex(HashIndex):

    def __init__(self, *args, **kwargs):
        kwargs['key_format'] = 'I'
        super(PermitTravelIndex, self).__init__(*args, **kwargs)
    
    def make_key_value(self, data):
        if data['t'] == constants.TASK_TYPE_CODE and data['tag'] == 'PERMIT_TRAVEL':
            return 0, None
   
    def make_key(self, key):
        return 0

codernity_db = Database('db')
codernity_db.create()
codernity_db.add_index(TaskWithIntiator(codernity_db.path, 'task_with_initiator'))
codernity_db.add_index(PermitTravelIndex(codernity_db.path, 'permit_travel'))
from lite_task_flow.indexes import add_index
add_index(codernity_db)


