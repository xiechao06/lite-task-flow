# -*- coding: UTF-8 -*-

from lite_task_flow.indexes import TaskIndex

class TaskFlowEngine(object):

    instance = None

    def __init__(self, db):
        self.db = db
        self.registered_task_cls_map = {}
        TaskFlowEngine.instance = self

