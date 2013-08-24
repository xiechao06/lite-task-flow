#! /usr/bin/env python
# -*- coding: UTF-8 -*-

from task_flow import (Task, TaskFlow, DelayedException, ApproveRefusedTaskFlow, 
                       TaskAlreadyApproved, TaskUnsubmitted)
from mock import patch
from py.test import raises

def test_single_task():

    class FooTask(Task):

        @property
        def id(self):
            return "foo_task1"

    class FooTaskFlow(TaskFlow):

        def __init__(self, root_task):
            super(FooTaskFlow, self).__init__(root_task)
            self.storage = {}

        def serialize_task(self, task):
            self.storage[task.id] = task
        
        def deserialize_task(self, task_id):
            return self.storage[task_id]

    with patch.object(FooTask, "__call__") as mock_method1:
        with patch.object(FooTaskFlow, "on_approved") as mock_method2:
            with patch.object(FooTask, "before_executed") as mock_method3:
                foo_task1 = FooTask("foo task 1")
                foo_task_flow1 = FooTaskFlow(foo_task1)
                foo_task_flow1.start()
                mock_method1.assert_called_once_with() 
                mock_method2.assert_called_once_with()
                mock_method3.assert_called_once_with()
                assert foo_task1.status == Task.APPROVED

    with patch.object(FooTask, "__call__") as mock_method1:
        with patch.object(FooTaskFlow, "on_approved") as mock_method2:
            with patch.object(FooTask, "before_executed") as mock_method3:
                with patch.object(FooTaskFlow, "on_refused") as mock_method4:
                    foo_task2 = FooTask("foo task 2")
                    foo_task_flow2 = FooTaskFlow(foo_task2)
                    foo_task_flow2.refuse(foo_task2)
                    assert foo_task2.status == Task.UNSUBMITTED
                    assert foo_task_flow2.refused
                    assert mock_method1.call_count == 0
                    assert mock_method2.call_count == 0
                    assert mock_method3.call_count == 0
                    mock_method4.assert_called_once_with(foo_task2)

    foo_task3 = FooTask("foo task 3")
    foo_task_flow3 = FooTaskFlow(foo_task3)
    foo_task_flow3.start()
    raises(TaskAlreadyApproved, foo_task_flow3.approve, foo_task3)

def test_multiple_tasks():

    class A(Task):
        
        @property
        def id(self):
            return "a"
        
        @property
        def dependencies(self):
            return [B("b"), C("c")]

    class B(Task):

        @property
        def id(self):
            return "b"

    class C(Task):

        @property
        def id(self):
            return 'c'

        @property
        def dependencies(self):

            return [D("d")]

    class D(Task):

        @property
        def id(self):
            return "d"


    class ATaskFlow(TaskFlow):

        def __init__(self, root_task):
            super(ATaskFlow, self).__init__(root_task)
            self.storage = {}

        def serialize_task(self, task):
            self.storage[task.id] = task
        
        def deserialize_task(self, task):
            return self.storage[task.id]
        
    
    with patch.object(A, "__call__") as call_a:
        with patch.object(B, "__call__") as call_b:
            with patch.object(C, "__call__") as call_c:
                with patch.object(D, "__call__") as call_d:
                    a_task = A("a")
                    a_task_flow = ATaskFlow(a_task)
                    e_info = raises(DelayedException, a_task_flow.start)
                    assert a_task.status == Task.APPROVED
                    delayed_task = e_info.value.task
                    assert delayed_task.id == 'b'
                    assert delayed_task.status == Task.WAIT_APPROVING

                    e_info = raises(DelayedException, a_task_flow.approve, delayed_task)
                    assert delayed_task.status == Task.APPROVED
                    delayed_task = e_info.value.task
                    assert delayed_task.id == 'c'
                    assert delayed_task.status == Task.WAIT_APPROVING

                    e_info = raises(DelayedException, a_task_flow.approve, delayed_task)
                    assert delayed_task.status == Task.APPROVED
                    delayed_task = e_info.value.task
                    assert delayed_task.id == 'd'
                    assert delayed_task.status == Task.WAIT_APPROVING
        
                    a_task_flow.approve(delayed_task)
                    call_a.assert_called_once_with()
                    call_b.assert_called_once_with()
                    call_c.assert_called_once_with()
                    call_d.assert_called_once_with()

    # test refused
    with patch.object(ATaskFlow, "on_refused") as mock_method:
        a_task = A("a")
        a_task_flow = ATaskFlow(a_task)
        try:
            a_task_flow.start()
        except DelayedException, e:
            delayed_task = e.task
            pass
        a_task_flow.refuse(delayed_task)
        assert a_task_flow.refused
        mock_method.assert_called_once_with(delayed_task)
        raises(ApproveRefusedTaskFlow, a_task_flow.approve, C("c"))

    # test unsubmitted task
    a_task = A("a")
    a_task_flow = ATaskFlow(a_task)
    raises(TaskUnsubmitted, a_task_flow.approve, B("b"))

if __name__ == "__main__":
    test_single_task()
    test_multiple_tasks()
