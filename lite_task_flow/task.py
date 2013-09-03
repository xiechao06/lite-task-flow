# -*- coding: UTF-8 -*-
from datetime import datetime

from lite_task_flow.task_flow_engine import TaskFlowEngine
from lite_task_flow.exceptions import TaskUnsubmitted, TaskAlreadyApproved
from lite_task_flow.constants import TASK_TYPE_CODE, TASK_FLOW_EXECUTED
from CodernityDB.database import RecordNotFound

class Task(object):
    """
    represent a node in the flow
    """

    def __init__(self, task_flow, **kwargs):
        """
        :param task_flow: the task flow to attach
        """
        self.task_flow = task_flow
        self.extra_params = kwargs
        self.approved = False
        self.failed = False

    @property
    def tag(self):
        """
        tag of the task, you must guarentee that a task has a unique tag in the
        PERTAINNING TASK FLOW, you could utilize attribute "extra_params" here
        """
        return NotImplemented

    def checkout(self):
        """
        checkout the status from disk
        """
        try:
            task_doc = TaskFlowEngine.instance.db.get('task', {'task_flow_id': self.task_flow.id_,
                                                       'tag': self.tag},
                                              with_doc=True)['doc']
            self.approved = task_doc['approved']
            self.failed = task_doc['failed']
            self.extra_params = task_doc['extra_params']
        except RecordNotFound:
            pass
        return self


    def update(self, attr):
        '''
        the opposite operation of checkout
        '''
        task_doc = TaskFlowEngine.instance.db.get('task', {'task_flow_id': self.task_flow.id_,
                                                   'tag': self.tag},
                                          with_doc=True)['doc']
        task_doc[attr] = getattr(self, attr)
        TaskFlowEngine.instance.db.update(task_doc)

    def __call__(self):
        """
        put the execution code here if necessary
        """
        pass

    @property
    def dependencies(self):
        """
        :return: a list of tasks depentent on
        """
        return []

    def after_executed(self):
        """
        this method is invoked when the task is performed
        override this method to perform actions like informing somebody
        """
        pass

    def execute(self):
        """
        execute the task, all the dependent tasks will be executed at first
        """
        for task in self.dependencies:
            task.execute()
        if not self.task_flow.status == TASK_FLOW_EXECUTED or self.failed:
            try:
                self()
                self.failed = False
                self.update('failed')
                self.after_executed()
            except:
                self.failed = True
                self.update('failed')
                raise

    def approve(self):
        """
        approve the task, this method will save the task's status
        :raise TaskAlreadyApproved: if the task has been approved already
        :raise TaskUnsubmitted: if the task hasn't been submitted (because the task
            is NOT the NEXT task in task flow to be handled)
        """
        try:
            doc = TaskFlowEngine.instance.db.get('task', dict(task_flow_id=self.task_flow.id_, tag=self.tag), with_doc=True)['doc']
        except RecordNotFound:
            raise TaskUnsubmitted()
        if doc['approved']:
            raise TaskAlreadyApproved()

        doc['approved'] = True
        doc['approved_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        TaskFlowEngine.instance.db.update(doc)
        self.approved = True
        self.on_approved()
 
    def on_refused(self, caused_by_me):
        """
        invoked when the task flow is refused, and the task is submitted and wait for
        approving.

        :param caused_by_me: if the refused task is me
        :type caused_by_me: boolean
        """
        pass

    def save(self):
        """
        save the task on disk
        """
        d = dict(t=TASK_TYPE_CODE,
                 task_flow_id=self.task_flow.id_,
                 tag=self.tag,
                 approved=self.approved,
                 failed=self.failed,
                 extra_params=self.extra_params,
                 create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        return TaskFlowEngine.instance.db.insert(d)

    def on_delayed(self, unmet_task):
        """
        invoked when the task flow is delayed due to a task that hasn't been approved,
        it's a good place to put some logic like informing the handler of the task
 
        :param unmet_task: the task wait to be approved
        :type unmet_task: lite_task_flow.Task
        """
        pass

    def on_approved(self):
        """
        invoked when the task is approved
        """
        pass
