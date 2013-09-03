# -*- coding: UTF-8 -*-
from CodernityDB.database import RecordNotFound
from lite_task_flow.task_flow_engine import TaskFlowEngine
from lite_task_flow import constants
from lite_task_flow.exceptions import TaskFlowRefused, TaskFlowDelayed, TaskFlowProcessing

class TaskFlow(object):

    def __init__(self, id_, annotation, status=constants.TASK_FLOW_PROCESSING, failed=False):
        """
        :param id_: id of the task flow
        :type id_: StringType
        :param annotation: annotaion to the task flow
        :type annotaion: StringType
        :param status: status of the task flow
        :param failed: if the task flow's execution failed
        """
        self.id_ = id_
        self.annotation = annotation
        self.status = status
        self.failed = failed
        self.root_task = None

    def set_root_task(self, root_task):
        """
        set the root task of the task flow
        """
        self.root_task = root_task

    def retry(self, last_operated_task):
        """
        test if all the tasks are approved, if they are, execute the tasks from
        LEAF to ROOT

        :raise: TaskFlowRefused when the task flow has been refused
        :raise: TaskFlowDelayed when there exists task that hasn't been approved
        """
        if self.status == constants.TASK_FLOW_REFUSED:
            raise TaskFlowRefused()
        # then we test if all the (indirect) depenecies of ROOT are met
        unmet_task = self._find_next_unmet_task(self.root_task)
        if unmet_task:
            unmet_task.save()
            last_operated_task.on_delayed(unmet_task)
            raise TaskFlowDelayed(unmet_task, "task %s is not met" % unicode(unmet_task))

        self.status = constants.TASK_FLOW_APPROVED
        self.update()

        # execute all the tasks
        try:
            self.root_task.execute()
            self.failed = False
            self.status = constants.TASK_FLOW_EXECUTED
            self.update()
        except:
            self.failed = True
            self.update()
            raise


    def execute(self):
        """
        execute the task flow
        you must guarantee each task is a transaction

        :raise TaskFlowRefused: if task flow is refused
        :raise TaskFlowProcessing: if task flow is processing
        :raise Exception: any exceptions raised when executing tasks
        """
        if self.status == constants.TASK_FLOW_REFUSED:
            raise TaskFlowRefused()
        elif self.status == constants.TASK_FLOW_PROCESSING:
            raise TaskFlowProcessing()
        try:
            self.root_task.execute()
            self.failed = False
            self.status == constants.TASK_FLOW_EXECUTED
            self.update()
        except:
            self.failed = True
            self.update()
            raise

    def approve(self, task):
        """
        approve the task
        """
        task.approve()
        self.retry(task)

    def update(self):
        """
        update task flow's status on disk
        """
        doc = TaskFlowEngine.instance.db.get('id', self.id_, with_doc=True)
        doc['status'] = self.status
        doc['failed'] = self.failed
        TaskFlowEngine.instance.db.update(doc)

    def _find_next_unmet_task(self, task):
        """
        find the next unapproved task (note, if the task is waiting for approvement, it will not be returned)

        :param task: search from it
        :type task: request_flow.Task
        """
        if not task.approved:
            return task

        for dep_task in task.dependencies:
            try:
                dep_task_data = TaskFlowEngine.instance.db.get('task', dict(task_flow_id=dep_task.task_flow.id_,
                                                                    tag=dep_task.tag), with_doc=True)
                dep_task.approved = dep_task_data['doc']['approved']
            except RecordNotFound:
                pass
            unmet_task = self._find_next_unmet_task(dep_task)
            if unmet_task:
                return unmet_task

    def start(self):
        """
        start this task flow
        """
        self.root_task.approve()
        self.retry(self.root_task)

    def refuse(self, task):
        """
        refuse the task flow
        :param task: the task refused DIRECTLY
        """
        doc = TaskFlowEngine.instance.db.get('id', self.id_)
        self.status = doc['status'] = constants.TASK_FLOW_REFUSED
        TaskFlowEngine.instance.db.update(doc)
        self._refuse_task_tree(self.root_task, task)

    def _refuse_task_tree(self, task, cause_task):
        """
        refuse the task tree roote by 'task'

        :param task: the task tree's root
        :param cause_task: the task refused directly
        """
        task.checkout()
        task.on_refused(task.tag == cause_task.tag)
        for t in task.dependencies:
            self._refuse_task_tree(t, cause_task)
