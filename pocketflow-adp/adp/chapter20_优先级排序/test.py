#!/usr/bin/env python3
"""
Chapter 20: 优先级排序 - 测试用例
"""

import unittest
import uuid
from task_manager import TaskManager, Task
from flow import PrioritizationFlow, InteractiveTaskManager


class TestTaskManager(unittest.TestCase):
    """测试任务管理器"""
    
    def setUp(self):
        """设置测试环境"""
        self.task_manager = TaskManager()
    
    def test_create_task(self):
        """测试创建任务"""
        description = "测试任务"
        task_id = self.task_manager.create_task(description)
        
        self.assertIsNotNone(task_id)
        self.assertEqual(len(task_id), 36)  # UUID长度
        
        task = self.task_manager.get_task(task_id)
        self.assertIsNotNone(task)
        self.assertEqual(task.description, description)
        self.assertEqual(task.status, "pending")
    
    def test_assign_priority(self):
        """测试分配优先级"""
        task_id = self.task_manager.create_task("测试任务")
        
        # 分配优先级
        result = self.task_manager.assign_priority(task_id, "P0")
        self.assertTrue(result)
        
        task = self.task_manager.get_task(task_id)
        self.assertEqual(task.priority, "P0")
        
        # 测试无效优先级
        result = self.task_manager.assign_priority(task_id, "P3")
        self.assertFalse(result)
    
    def test_assign_task(self):
        """测试分配任务"""
        task_id = self.task_manager.create_task("测试任务")
        
        # 分配任务
        result = self.task_manager.assign_task(task_id, "Worker A")
        self.assertTrue(result)
        
        task = self.task_manager.get_task(task_id)
        self.assertEqual(task.assigned_to, "Worker A")
    
    def test_update_task_status(self):
        """测试更新任务状态"""
        task_id = self.task_manager.create_task("测试任务")
        
        # 更新状态
        result = self.task_manager.update_task_status(task_id, "in_progress")
        self.assertTrue(result)
        
        task = self.task_manager.get_task(task_id)
        self.assertEqual(task.status, "in_progress")
    
    def test_delete_task(self):
        """测试删除任务"""
        task_id = self.task_manager.create_task("测试任务")
        
        # 确认任务存在
        task = self.task_manager.get_task(task_id)
        self.assertIsNotNone(task)
        
        # 删除任务
        result = self.task_manager.delete_task(task_id)
        self.assertTrue(result)
        
        # 确认任务已删除
        task = self.task_manager.get_task(task_id)
        self.assertIsNone(task)
    
    def test_get_tasks_by_priority(self):
        """测试按优先级获取任务"""
        # 创建不同优先级的任务
        task_id1 = self.task_manager.create_task("P0任务")
        task_id2 = self.task_manager.create_task("P1任务")
        task_id3 = self.task_manager.create_task("P2任务")
        
        self.task_manager.assign_priority(task_id1, "P0")
        self.task_manager.assign_priority(task_id2, "P1")
        self.task_manager.assign_priority(task_id3, "P2")
        
        # 获取P0任务
        p0_tasks = self.task_manager.get_tasks_by_priority("P0")
        self.assertEqual(len(p0_tasks), 1)
        self.assertEqual(p0_tasks[0].id, task_id1)
        
        # 获取P1任务
        p1_tasks = self.task_manager.get_tasks_by_priority("P1")
        self.assertEqual(len(p1_tasks), 1)
        self.assertEqual(p1_tasks[0].id, task_id2)
    
    def test_get_tasks_by_assignee(self):
        """测试按分配对象获取任务"""
        # 创建分配给不同人员的任务
        task_id1 = self.task_manager.create_task("Worker A任务")
        task_id2 = self.task_manager.create_task("Worker B任务")
        
        self.task_manager.assign_task(task_id1, "Worker A")
        self.task_manager.assign_task(task_id2, "Worker B")
        
        # 获取Worker A的任务
        worker_a_tasks = self.task_manager.get_tasks_by_assignee("Worker A")
        self.assertEqual(len(worker_a_tasks), 1)
        self.assertEqual(worker_a_tasks[0].id, task_id1)
        
        # 获取Worker B的任务
        worker_b_tasks = self.task_manager.get_tasks_by_assignee("Worker B")
        self.assertEqual(len(worker_b_tasks), 1)
        self.assertEqual(worker_b_tasks[0].id, task_id2)
    
    def test_get_all_tasks_sorted(self):
        """测试获取排序后的所有任务"""
        # 创建不同优先级的任务
        task_id1 = self.task_manager.create_task("P1任务")
        task_id2 = self.task_manager.create_task("P0任务")
        task_id3 = self.task_manager.create_task("P2任务")
        
        self.task_manager.assign_priority(task_id1, "P1")
        self.task_manager.assign_priority(task_id2, "P0")
        self.task_manager.assign_priority(task_id3, "P2")
        
        # 获取排序后的任务
        sorted_tasks = self.task_manager.get_all_tasks_sorted()
        self.assertEqual(len(sorted_tasks), 3)
        
        # 验证排序顺序：P0 -> P1 -> P2
        self.assertEqual(sorted_tasks[0].priority, "P0")
        self.assertEqual(sorted_tasks[1].priority, "P1")
        self.assertEqual(sorted_tasks[2].priority, "P2")


class TestTask(unittest.TestCase):
    """测试任务类"""
    
    def test_task_creation(self):
        """测试任务创建"""
        task = Task(id="test-id", description="测试任务")
        
        self.assertEqual(task.id, "test-id")
        self.assertEqual(task.description, "测试任务")
        self.assertEqual(task.status, "pending")
        self.assertIsNone(task.priority)
        self.assertIsNone(task.assigned_to)
    
    def test_task_to_dict(self):
        """测试任务转字典"""
        task = Task(
            id="test-id",
            description="测试任务",
            status="in_progress",
            priority="P0",
            assigned_to="Worker A"
        )
        
        task_dict = task.to_dict()
        
        self.assertEqual(task_dict["id"], "test-id")
        self.assertEqual(task_dict["description"], "测试任务")
        self.assertEqual(task_dict["status"], "in_progress")
        self.assertEqual(task_dict["priority"], "P0")
        self.assertEqual(task_dict["assigned_to"], "Worker A")
    
    def test_task_from_dict(self):
        """测试从字典创建任务"""
        task_dict = {
            "id": "test-id",
            "description": "测试任务",
            "status": "completed",
            "priority": "P1",
            "assigned_to": "Worker B"
        }
        
        task = Task.from_dict(task_dict)
        
        self.assertEqual(task.id, "test-id")
        self.assertEqual(task.description, "测试任务")
        self.assertEqual(task.status, "completed")
        self.assertEqual(task.priority, "P1")
        self.assertEqual(task.assigned_to, "Worker B")


class TestPrioritizationFlow(unittest.TestCase):
    """测试优先级排序流程"""
    
    def setUp(self):
        """设置测试环境"""
        self.flow = PrioritizationFlow()
    
    def test_create_task(self):
        """测试创建任务流程"""
        result = self.flow.create_task("创建一个测试任务")
        
        self.assertTrue(result["success"])
        self.assertIsNotNone(result["task_id"])
        self.assertIsNotNone(result["task"])
    
    def test_list_tasks(self):
        """测试列出任务流程"""
        # 先创建一个任务
        self.flow.create_task("测试任务")
        
        # 列出任务
        result = self.flow.list_tasks()
        
        self.assertTrue(result["success"])
        self.assertIsNotNone(result["task_list"])
    
    def test_update_task_status(self):
        """测试更新任务状态流程"""
        # 先创建一个任务
        create_result = self.flow.create_task("测试任务")
        task_id = create_result["task_id"]
        
        # 更新任务状态
        update_result = self.flow.update_task_status(task_id, "completed")
        
        self.assertTrue(update_result["success"])
        self.assertEqual(update_result["task"].status, "completed")
    
    def test_get_task_by_id(self):
        """测试根据ID获取任务"""
        # 先创建一个任务
        create_result = self.flow.create_task("测试任务")
        task_id = create_result["task_id"]
        
        # 获取任务
        task = self.flow.get_task_by_id(task_id)
        
        self.assertIsNotNone(task)
        self.assertEqual(task["id"], task_id)
        self.assertEqual(task["description"], "测试任务")
    
    def test_delete_task(self):
        """测试删除任务"""
        # 先创建一个任务
        create_result = self.flow.create_task("测试任务")
        task_id = create_result["task_id"]
        
        # 删除任务
        result = self.flow.delete_task(task_id)
        
        self.assertTrue(result)
        
        # 确认任务已删除
        task = self.flow.get_task_by_id(task_id)
        self.assertIsNone(task)


class TestInteractiveTaskManager(unittest.TestCase):
    """测试交互式任务管理器"""
    
    def setUp(self):
        """设置测试环境"""
        self.manager = InteractiveTaskManager()
    
    def test_task_creation_request(self):
        """测试任务创建请求"""
        result = self.manager.process_user_request("创建任务: 测试任务")
        
        self.assertTrue(result["success"])
        self.assertIn("任务已创建成功", result["message"])
        self.assertIsNotNone(result["task"])
    
    def test_task_list_request(self):
        """测试任务列表请求"""
        result = self.manager.process_user_request("列出任务")
        
        self.assertTrue(result["success"])
    
    def test_task_status_update_request(self):
        """测试任务状态更新请求"""
        # 先创建一个任务
        create_result = self.manager.process_user_request("创建任务: 测试任务")
        task_id = create_result["task"]["id"]
        
        # 更新任务状态
        update_result = self.manager.process_user_request(f"更新任务 {task_id} 状态为完成")
        
        self.assertTrue(update_result["success"])
        self.assertIn("任务状态已更新", update_result["message"])
    
    def test_task_delete_request(self):
        """测试任务删除请求"""
        # 先创建一个任务
        create_result = self.manager.process_user_request("创建任务: 测试任务")
        task_id = create_result["task"]["id"]
        
        # 删除任务
        delete_result = self.manager.process_user_request(f"删除任务 {task_id}")
        
        self.assertTrue(delete_result["success"])
        self.assertIn("已成功删除", delete_result["message"])
    
    def test_task_query_request(self):
        """测试任务查询请求"""
        # 先创建一些任务
        self.manager.process_user_request("创建任务: P0任务")
        self.manager.process_user_request("创建任务: P1任务")
        self.manager.process_user_request("创建任务: P2任务")
        
        # 查询P0任务
        p0_result = self.manager.process_user_request("查询P0优先级任务")
        self.assertTrue(p0_result["success"])
        
        # 查询所有任务
        all_result = self.manager.process_user_request("获取所有任务")
        self.assertTrue(all_result["success"])
    
    def test_unrecognized_request(self):
        """测试无法识别的请求"""
        result = self.manager.process_user_request("无法识别的请求")
        
        self.assertFalse(result["success"])
        self.assertIn("无法识别您的请求", result["message"])


if __name__ == "__main__":
    unittest.main()