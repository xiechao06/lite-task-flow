#! /usr/bin/env python
# -*- coding: UTF-8 -*-
import tempfile
import shutil
import types

from py.test import raises
from mock import patch
from CodernityDB.database import Database

from lite_task_flow import (TaskFlowEngine, Task,  new_task_flow, 
                                constants, register_task_cls, get_task_flow)

from lite_task_flow.exceptions import (TaskFlowDelayed, ApproveRefusedTaskFlow, 
                                TaskAlreadyApproved, TaskUnsubmitted)

from lite_task_flow.indexes import add_index


class BaseTest(object):

    def setup(self):
        self.db = Database(tempfile.mkdtemp()) 
        self.db.create()
        add_index(self.db)
        self.task_flow_engine = TaskFlowEngine(self.db) 

    def teardown(self):
        shutil.rmtree(self.db.path)

    def run_plainly(self, tests=None):
        self.setup()
        for k, v in self.__class__.__dict__.items():
            if k.startswith("test") and isinstance(v, types.FunctionType):
                if not tests or (k in tests):
                    v(self)
        self.teardown()

class TestSingleTask(BaseTest):
    def test(self):

        class FooTask(Task):

            @property
            def tag(self):
                return "foo_task1"

            def serialize(self, task_flow):
                task_flow.storage[self.id] = self

            def deserialize(self, task_flow):
                return self.storage[self.id]

        register_task_cls(FooTask)

        with patch.object(FooTask, "__call__") as mock_method1:
            with patch.object(FooTask, "on_approved") as mock_method2:
                with patch.object(FooTask, "after_executed") as mock_method3:
                    task_flow = new_task_flow(FooTask, annotation="foo task flow", a=1, b=2) 
                    task_flow.start()
                    mock_method1.assert_called_once_with() 
                    mock_method2.assert_called_once_with()
                    mock_method3.assert_called_once_with()
                    foo_task = task_flow.root_task.checkout()
                    assert foo_task.approved
                    assert task_flow.status == constants.TASK_FLOW_APPROVED

        with patch.object(FooTask, "__call__") as mock_method1:
            with patch.object(FooTask, "on_approved") as mock_method2:
                with patch.object(FooTask, "after_executed") as mock_method3:
                    with patch.object(FooTask, "on_refused") as mock_method4:
                        task_flow = new_task_flow(FooTask, annotation='foo task flow', a=1, b=2)
                        foo_task = task_flow.root_task.checkout()
                        task_flow.refuse(foo_task)
                        assert mock_method1.call_count == 0
                        assert mock_method2.call_count == 0
                        assert mock_method3.call_count == 0
                        mock_method4.assert_called_once_with(True)

        task_flow = new_task_flow(FooTask, annotation='foo task flow')
        task_flow.start()
        foo_task = task_flow.root_task.checkout()
        raises(TaskAlreadyApproved, task_flow.approve, foo_task)

class TestMultipleTasks(BaseTest):

    def test(self):

        class A(Task):
            
            @property
            def tag(self):
                return self.extra_params['name']
            
            @property
            def dependencies(self):
                return [B(self.task_flow, name="b"), C(self.task_flow, name="c")]
        register_task_cls(A)

        class B(Task):

            @property
            def tag(self):
                return self.extra_params['name']

        class C(Task):

            @property
            def tag(self):
                return self.extra_params['name']

            @property
            def dependencies(self):
                return [D(self.task_flow, name="d")]

        class D(Task):

            @property
            def tag(self):
                return self.extra_params['name']

        with patch.object(A, "__call__") as call_a:
            with patch.object(B, "__call__") as call_b:
                with patch.object(C, "__call__") as call_c:
                    with patch.object(D, "__call__") as call_d:
                        task_flow = new_task_flow(A, annotation="foo task flow", name='a')
                        e_info = raises(TaskFlowDelayed, task_flow.start)
                        a_task = task_flow.root_task.checkout()
                        assert a_task.approved
                        delayed_task = e_info.value.task
                        assert delayed_task.tag == 'b'
                        delayed_task.checkout()
                        assert not delayed_task.approved

                        e_info = raises(TaskFlowDelayed, task_flow.approve, delayed_task)
                        delayed_task.checkout()
                        assert delayed_task.approved
                        delayed_task = e_info.value.task
                        assert delayed_task.tag == 'c'
                        delayed_task.checkout()
                        assert not delayed_task.approved

                        e_info = raises(TaskFlowDelayed, task_flow.approve, delayed_task)
                        delayed_task.checkout()
                        assert delayed_task.approved
                        delayed_task = e_info.value.task
                        assert delayed_task.tag == 'd'
                        delayed_task.checkout()
                        assert not delayed_task.approved
            
                        task_flow.approve(delayed_task)
                        call_a.assert_called_once_with()
                        call_b.assert_called_once_with()
                        call_c.assert_called_once_with()
                        call_d.assert_called_once_with()

        ## test refused
        with patch.object(B, "on_refused") as mock_method:
            task_flow = new_task_flow(A, annotation="foo task flow", name='a')
            try:
                task_flow.start()
            except TaskFlowDelayed, e:
                delayed_task = e.task
                pass
            task_flow.refuse(delayed_task)
            task_flow = get_task_flow(task_flow.id_)
            assert task_flow.status == constants.TASK_FLOW_REFUSED
            mock_method.assert_called_once_with(True)
            raises(ApproveRefusedTaskFlow, task_flow.approve, delayed_task)

        # test unsubmitted task
        task_flow = new_task_flow(A, annotation='foo task flow', name='a')
        raises(TaskUnsubmitted, task_flow.approve, B(task_flow, name="b"))

        # test approve twice
        task_flow = new_task_flow(A, annotation='foo task flow', name='a')
        try: 
            task_flow.start()
        except TaskFlowDelayed:
            pass
        raises(TaskAlreadyApproved, task_flow.approve, A(task_flow, name="a"))

if __name__ == "__main__":
    TestSingleTask().run_plainly()
    TestMultipleTasks().run_plainly()
