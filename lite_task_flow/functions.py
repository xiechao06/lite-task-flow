# -*- coding: UTF-8 -*-
from lite_task_flow.task_flow_engine import TaskFlowEngine
from lite_task_flow.task_flow import TaskFlow
from lite_task_flow.task import Task
from CodernityDB.database import RecordNotFound
from lite_task_flow import constants

def new_task_flow(task_cls, annotation="", **kwargs):
    """
    create a task flow, it's root task's class is 'task_cls', it's annotation is
    """

    d = dict(t=constants.TASK_FLOW_TYPE_CODE, status=constants.TASK_FLOW_PROCESSING, annotation=annotation,
             root_task_cls=task_cls.__name__, root_extra_params=kwargs, failed=False)
    id_ = TaskFlowEngine.instance.db.insert(d)['_id']
    task_flow = TaskFlow(id_, annotation)
    task_flow.set_root_task(task_cls(task_flow, **kwargs))
    task_flow.root_task.save()
    return task_flow

def get_task_flow(task_flow_id):
    """
    get task flow from disk

    :return: the task flow with given id, else None
    """
    try:
        doc = TaskFlowEngine.instance.db.get('id', task_flow_id)
    except RecordNotFound:
        return None
    ret = TaskFlow(task_flow_id, doc['annotation'], doc['status'], doc['failed'])
    ret.set_root_task(TaskFlowEngine.instance.registered_task_cls_map[doc['root_task_cls']](ret, **doc['root_extra_params']))
    ret.root_task.checkout()
    return ret

def register_task_cls(task_cls):
    """
    register the task class, all the root tasks' class should be registered
    """
    TaskFlowEngine.instance.registered_task_cls_map[task_cls.__name__] = task_cls

def get_task(task_id):
    try:
        doc = TaskFlowEngine.instance.db.get('id', task_id)
    except RecordNotFound:
        return None
    return get_task_from_doc(doc)

def get_task_from_doc(doc):
    task_flow = get_task_flow(doc['task_flow_id'])
    task_cls = TaskFlowEngine.instance.registered_task_cls_map[doc['cls']]
    ret = task_cls(task_flow, **doc['extra_params'])
    ret.approved = doc['approved']
    ret.failed = doc['failed']
    ret.create_time = doc['create_time']
    ret.approved_time = doc.get('approved_time')
    ret.id_ = doc['_id']
    return ret
