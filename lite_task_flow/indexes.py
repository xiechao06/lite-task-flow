# -*- coding: UTF-8 -*-

from hashlib import md5

from CodernityDB.hash_index import HashIndex

from lite_task_flow import constants

class TaskIndex(HashIndex):
    """
    an index indexed by task flow id and task tag
    """
    custom_header = "from lite_task_flow import constants"

    def __init__(self, *args, **kwargs):
        kwargs['key_format'] = '16s'
        super(TaskIndex, self).__init__(*args, **kwargs)

    def make_key_value(self, data):
        if data['t'] == constants.TASK_TYPE_CODE:
            return md5(data.get('task_flow_id') + data.get('tag')).digest(), None

    def make_key(self, key):
        return md5(key['task_flow_id'] + key['tag']).digest()

def add_index(db):
    db.add_index(TaskIndex(db.path, 'task'))
