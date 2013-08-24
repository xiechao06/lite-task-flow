#! /usr/bin/env python
# -*- coding: UTF-8 -*-

__version__ = "0.9.0"

class DelayedException(Exception):

    def __init__(self, task, message=""):
        super(DelayedException, self).__init__(message)
        self.task = task

class ApproveRefusedTaskFlow(Exception):
    pass

class TaskAlreadyApproved(Exception):
    pass

class TaskUnsubmitted(Exception):
    pass

class Task(object):

    UNSUBMITTED = 0
    WAIT_APPROVING = 1
    APPROVED = 2


    def __init__(self, name, annotation=""):
        self.__name = name
        self.__annotation = annotation
        self.status = Task.UNSUBMITTED

    @property
    def id(self):
        """
        id of the task, you must guarentee that a task has a unique id in the
        PERTAINNING TASK FLOW
        """
        return NotImplemented
    
    @property
    def name(self):
        return self.__name

    @property
    def annotation(self):
        return self.__annotation

    def __call__(self):
        """
        put the execution code here if necessary
        """
        pass

    @property
    def dependencies(self):
        """
        :return: a list of task depentent on
        """
        return []

    def before_executed(self):
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
        self.before_executed()
        self()

    def approve(self):
        self.status = Task.APPROVED

class TaskFlow(object):

    def __init__(self, root_task, annotation=""):
        self.root_task = root_task
        self.refused = False
        self.__annotation = annotation

    def on_delayed(self, unmet_task):
        """
        invoked when the task flow is delayed due to a task that hasn't been approved,
        it's a good place to put some logic like informing the handler of the task
        
        :param unmet_task: the task wait to be approved
        :type unmet_task: request_flow.Task
        """
        pass

    @property
    def annotation(self):
        return self.__annotation
    
    def start(self):
        """
        start the task flow, namely, approve the root task
        """
        self.root_task.status = Task.WAIT_APPROVING
        self.approve(self.root_task)

    def approve(self, task):
        """
        approve a task, if all the tasks are approved, then all tasks will be executed from 
        LEAF to ROOT

        :raise: ApproveRefusedTaskFlow when the task flow has been refused
        :raise: DelayedException when there exists task that hasn't been approved
        :raise: TaskAlreadyApproved when the task already approved
        :raise: TaskUnsubmitted when the task hasn't been submitted (fired) 
        """
        if self.refused:
            raise ApproveRefusedTaskFlow()
        if task.status == Task.APPROVED:
            raise TaskAlreadyApproved()
        elif task.status == Task.UNSUBMITTED:
            raise TaskUnsubmitted()
        # first, test if the task could be executed by me
        task.approve()
        self.serialize_task(task)

        # then we test if all the (indirect) depenecies of ROOT are met
        unmet_task = self._find_next_unmet_task(self.root_task)
        if unmet_task:
            unmet_task.status = Task.WAIT_APPROVING
            self.serialize_task(unmet_task)
            self.on_delayed(unmet_task)
            raise DelayedException(unmet_task, "task %s is not met" % unicode(unmet_task))

        # execute all the tasks
        self.root_task.execute()
        self.on_approved()

    def refuse(self, task):
        """
        refuse the task, this will incur the task flow refused
        
        :param task: the task refused
        :type task: request_flow.Task
        """
        self.refused = True
        self.on_refused(task)

    def on_refused(self, task):
        """
        invoked when a task is refused (which means, the task flow is refused)
        it's a good place to insert code like inform the applicant of root task
        """
        pass

    def on_approved(self):
        """
        invoked when the task flow is approved (after the root task is executed)
        it's a good place to insert code like marking the task flow is over
        """
        pass

    def _find_next_unmet_task(self, task):
        """
        find the next unapproved task (note, if the task is waiting for approvement, it will not be returned)
        
        :param task: search from it
        :type task: request_flow.Task
        """
        if task.status == Task.UNSUBMITTED:
            return task
        def _deserialize_task(task):
            try:
                return self.deserialize_task(task)
            except KeyError:
                return task
        for dep_task in [_deserialize_task(t) for t in task.dependencies]:
            unmet_task = self._find_next_unmet_task(dep_task)
            if unmet_task:
                return unmet_task
        
if __name__ == "__main__":
    class AddWeightExceed10000(Task):

        def __init__(self, name, weight, annotation=""):
            super(AddWeightExceed10000, self).__init__(name, annotation)
            self.weight = weight

        @property
        def id(self):
            return "add_weight_" + str(self.weight) 
        

        def __call__(self):
            print "add weight: " + str(self.weight)

        def on_approved(self):
            print "add weight %d approved by Loader" % self.weight

        @property
        def dependencies(self):
            return [PermitAddWeightExceed10000("permit weight exceeding 10000", self.weight)]

        def __unicode__(self):
            return u"<ADD WEIGHT(%d) TASK>" % self.weight

    class PermitAddWeightExceed10000(Task):

        @property
        def id(self):
            return "permit_add_weight_" + str(self.weight) 

        def __init__(self, name, weight, annotation=""):
            super(PermitAddWeightExceed10000, self).__init__(name, annotation)
            self.weight = weight

        def on_approved(self):
            print "add weight %d approved by Cargo Clerk" % self.weight

        def __call__(self):
            print "approve add weight " + str(self.weight)

        def __unicode__(self):
            return u"<PERMIT ADD WEIGHT(%d) TASK>" % self.weight

    storage = {}
    class AddWeightRequestFlow(TaskFlow):

        def __init__(self, id_, root_task):
            super(AddWeightRequestFlow, self).__init__(root_task)
            self.id = id_

        def serialize_task(self, task):
            storage.setdefault(self.id, {})[task.id] = task

        def deserialize_task(self, task):
            try:
                return storage[self.id][task.id]
            except KeyError:
                return task

        def on_delayed(self, task):
            if isinstance(task, PermitAddWeightExceed10000):
                print "send notification to Cargo Clerk"

    add_weight_exceed_10000 = AddWeightExceed10000("add weight exceeding 10000", 10000,
              "add weight exceeding 10000 should be approved by cargo clerk")
    task_flow = AddWeightRequestFlow("add_weight_task_flow_1", add_weight_exceed_10000)

    try:
        task_flow.start()
    except DelayedException, e:
        delayed_task = e.task
        print e

    # load the delayed task
    task = storage["add_weight_task_flow_1"][delayed_task.id]
    task_flow.approve(task)
    # now the tasks are all executed

    print "=================================================================="

    class RetrieveWorkCommand(Task):

        @property
        def id(self):
            return "retrieve_work_command_" + str(self.__work_command.id)

        def __init__(self, name, work_command, annotation=""):
            super(RetrieveWorkCommand, self).__init__(name, annotation)
            self.__work_command = work_command

        def __call__(self):
            print "retrieve " + unicode(self.__work_command)

        @property
        def dependencies(self):
            return [DeleteStoreBill("delete store bill", store_bill) for store_bill in self.__work_command.store_bill_list]

        def __unicode__(self):
            return "<Retrieve Work Command %d>" % self.__work_command.id

        def on_approved(self):
            print "retrieve work command %d approved by Scheduler" % self.__work_command.id

    class DeleteStoreBill(Task):

        @property
        def id(self):
            return "delete_store_bill_" + str(self.__store_bill.id)

        def __init__(self, name, store_bill, annotation=""):
            super(DeleteStoreBill, self).__init__(name, annotation)
            self.__store_bill = store_bill

        def __call__(self):
            print "delete store bill " + unicode(self.__store_bill)

        def __unicode__(self):
            return "<Retrieve Store Bill %d>" % self.__store_bill.id

        def on_approved(self):
            print "retrieve store bill %d approved by Cargo Clerk" % self.__store_bill.id

    class WorkCommand(object):
        
        def __init__(self, id_, store_bill_list):
            self.id = id_
            self.store_bill_list = store_bill_list

        def __unicode__(self):
            return unicode(self.id)

    class StoreBill(object):

        def __init__(self, id_):
            self.id = id_

        def __unicode__(self):
            return unicode(self.id)

    class RetrieveWorkCommandRequestFlow(TaskFlow):

        def __init__(self, id_, root_task):
            super(RetrieveWorkCommandRequestFlow, self).__init__(root_task)
            self.id = id_

        def serialize_task(self, task):
            storage.setdefault(self.id, {})[task.id] = task

        def deserialize_task(self, task):
            try:
                return storage[self.id][task.id]
            except KeyError:
                return task

        def on_delayed(self, task):
            if isinstance(task, DeleteStoreBill):
                print "send task %s to Cargo Clerk" % unicode(task)

    retrieve_work_command = RetrieveWorkCommand("retrieve work command", WorkCommand(100, [StoreBill(1), StoreBill(2)]))
    task_flow = RetrieveWorkCommandRequestFlow("retrieve_work_command_1", retrieve_work_command)
    try:
        task_flow.start()
    except DelayedException, e:
        delayed_task = e.task
        print e

    delayed_task = storage["retrieve_work_command_1"][delayed_task.id]
    try:
        task_flow.approve(delayed_task)
    except DelayedException, e:
        delayed_task = e.task
        print e

    delayed_task = storage["retrieve_work_command_1"][delayed_task.id]
    task_flow.approve(delayed_task)

