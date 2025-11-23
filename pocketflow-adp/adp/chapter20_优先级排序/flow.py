from typing import Dict, Any, List, Optional
from pocketflow import Flow
from task_manager import TaskManager
from task_nodes import (
    TaskCreationNode, 
    TaskPriorityNode, 
    TaskAssignmentNode, 
    TaskListingNode, 
    TaskStatusUpdateNode
)


class PrioritizationFlow:
    """任务优先级排序流程"""
    
    def __init__(self):
        self.task_manager = TaskManager()
        
        # 创建节点
        self.task_creation_node = TaskCreationNode(self.task_manager)
        self.task_priority_node = TaskPriorityNode(self.task_manager)
        self.task_assignment_node = TaskAssignmentNode(self.task_manager)
        self.task_listing_node = TaskListingNode(self.task_manager)
        self.task_status_update_node = TaskStatusUpdateNode(self.task_manager)
        
        # 创建任务创建流程
        # 使用 >> 操作符连接节点
        self.task_creation_node >> self.task_priority_node >> self.task_assignment_node
        self.create_task_flow = Flow(start=self.task_creation_node)
        
        # 创建任务列表流程
        self.list_tasks_flow = Flow(start=self.task_listing_node)
        
        # 创建任务状态更新流程
        self.update_status_flow = Flow(start=self.task_status_update_node)
    
    def create_task(self, user_request: str, task_description: str = "") -> Dict[str, Any]:
        """创建新任务并分配优先级和工作人员"""
        shared_state = {
            "user_request": user_request,
            "task_description": task_description
        }
        
        # 执行创建任务流程
        result = self.create_task_flow.run(shared_state)
        
        return {
            "task_id": shared_state.get("task_id"),
            "task": shared_state.get("current_task"),
            "success": shared_state.get("task_id") is not None
        }
    
    def list_tasks(self) -> Dict[str, Any]:
        """列出所有任务"""
        shared_state = {}
        
        # 执行任务列表流程
        result = self.list_tasks_flow.run(shared_state)
        
        return {
            "task_list": shared_state.get("task_list"),
            "success": True
        }
    
    def update_task_status(self, task_id: str, new_status: str) -> Dict[str, Any]:
        """更新任务状态"""
        shared_state = {
            "task_id": task_id,
            "new_status": new_status
        }
        
        # 执行状态更新流程
        result = self.update_status_flow.run(shared_state)
        
        return {
            "task_id": task_id,
            "task": shared_state.get("current_task"),
            "success": shared_state.get("current_task") is not None
        }
    
    def get_task_by_id(self, task_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取任务"""
        task = self.task_manager.get_task(task_id)
        if task:
            return task.to_dict()
        return None
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """获取所有任务"""
        tasks = self.task_manager.get_all_tasks_sorted()
        return [task.to_dict() for task in tasks]
    
    def get_tasks_by_priority(self, priority: str) -> List[Dict[str, Any]]:
        """根据优先级获取任务"""
        tasks = self.task_manager.get_tasks_by_priority(priority)
        return [task.to_dict() for task in tasks]
    
    def get_tasks_by_assignee(self, assignee: str) -> List[Dict[str, Any]]:
        """根据分配对象获取任务"""
        tasks = self.task_manager.get_tasks_by_assignee(assignee)
        return [task.to_dict() for task in tasks]
    
    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        return self.task_manager.delete_task(task_id)


class InteractiveTaskManager:
    """交互式任务管理器"""
    
    def __init__(self):
        self.prioritization_flow = PrioritizationFlow()
    
    def process_user_request(self, user_request: str) -> Dict[str, Any]:
        """处理用户请求"""
        user_request = user_request.strip().lower()
        
        # 检查是否是创建任务请求
        if self._is_task_creation_request(user_request):
            return self._handle_task_creation(user_request)
        
        # 检查是否是任务列表请求
        elif self._is_task_list_request(user_request):
            return self._handle_task_list()
        
        # 检查是否是任务状态更新请求
        elif self._is_task_status_update_request(user_request):
            return self._handle_task_status_update(user_request)
        
        # 检查是否是任务删除请求
        elif self._is_task_delete_request(user_request):
            return self._handle_task_delete(user_request)
        
        # 检查是否是查询请求
        elif self._is_task_query_request(user_request):
            return self._handle_task_query(user_request)
        
        # 无法识别的请求
        else:
            return {
                "success": False,
                "message": "无法识别您的请求。请尝试创建任务、列出任务或更新任务状态。"
            }
    
    def _is_task_creation_request(self, user_request: str) -> bool:
        """检查是否是任务创建请求"""
        keywords = ["创建任务", "新建任务", "添加任务", "create task", "new task", "add task"]
        return any(keyword in user_request for keyword in keywords)
    
    def _is_task_list_request(self, user_request: str) -> bool:
        """检查是否是任务列表请求"""
        keywords = ["列出任务", "任务列表", "显示任务", "list tasks", "show tasks", "all tasks"]
        return any(keyword in user_request for keyword in keywords)
    
    def _is_task_status_update_request(self, user_request: str) -> bool:
        """检查是否是任务状态更新请求"""
        keywords = ["更新状态", "修改状态", "完成", "开始", "update status", "change status", "complete", "start"]
        return any(keyword in user_request for keyword in keywords)
    
    def _is_task_delete_request(self, user_request: str) -> bool:
        """检查是否是任务删除请求"""
        keywords = ["删除任务", "移除任务", "delete task", "remove task"]
        return any(keyword in user_request for keyword in keywords)
    
    def _is_task_query_request(self, user_request: str) -> bool:
        """检查是否是任务查询请求"""
        keywords = ["查询", "查看", "获取", "search", "get", "find", "show"]
        return any(keyword in user_request for keyword in keywords)
    
    def _handle_task_creation(self, user_request: str) -> Dict[str, Any]:
        """处理任务创建请求"""
        result = self.prioritization_flow.create_task(user_request)
        
        if result["success"]:
            task = result["task"]
            return {
                "success": True,
                "message": f"任务已创建成功！\n任务ID: {task.id[:8]}...\n描述: {task.description}\n优先级: {task.priority}\n分配给: {task.assigned_to}",
                "task": task.to_dict()
            }
        else:
            return {
                "success": False,
                "message": "创建任务失败，请重试。"
            }
    
    def _handle_task_list(self) -> Dict[str, Any]:
        """处理任务列表请求"""
        result = self.prioritization_flow.list_tasks()
        
        return {
            "success": True,
            "message": result["task_list"]
        }
    
    def _handle_task_status_update(self, user_request: str) -> Dict[str, Any]:
        """处理任务状态更新请求"""
        # 提取任务ID和新状态
        import re
        
        # 尝试提取任务ID
        task_id_match = re.search(r'(?:任务|task)\s*([a-f0-9-]+)', user_request)
        if not task_id_match:
            # 如果没有明确的任务ID，尝试从其他地方提取
            return {
                "success": False,
                "message": "无法识别任务ID。请提供完整的任务ID。"
            }
        
        task_id = task_id_match.group(1)
        
        # 确定新状态
        new_status = "in_progress"  # 默认状态
        
        if any(word in user_request for word in ["完成", "complete", "done"]):
            new_status = "completed"
        elif any(word in user_request for word in ["开始", "start", "进行"]):
            new_status = "in_progress"
        elif any(word in user_request for word in ["暂停", "pause", "hold"]):
            new_status = "paused"
        
        # 更新任务状态
        result = self.prioritization_flow.update_task_status(task_id, new_status)
        
        if result["success"]:
            task = result["task"]
            return {
                "success": True,
                "message": f"任务状态已更新！\n任务ID: {task.id[:8]}...\n新状态: {task.status}",
                "task": task.to_dict()
            }
        else:
            return {
                "success": False,
                "message": "更新任务状态失败，请检查任务ID是否正确。"
            }
    
    def _handle_task_delete(self, user_request: str) -> Dict[str, Any]:
        """处理任务删除请求"""
        import re
        
        # 尝试提取任务ID
        task_id_match = re.search(r'(?:任务|task)\s*([a-f0-9-]+)', user_request)
        if not task_id_match:
            return {
                "success": False,
                "message": "无法识别任务ID。请提供完整的任务ID。"
            }
        
        task_id = task_id_match.group(1)
        
        # 删除任务
        success = self.prioritization_flow.delete_task(task_id)
        
        if success:
            return {
                "success": True,
                "message": f"任务 {task_id[:8]}... 已成功删除。"
            }
        else:
            return {
                "success": False,
                "message": "删除任务失败，请检查任务ID是否正确。"
            }
    
    def _handle_task_query(self, user_request: str) -> Dict[str, Any]:
        """处理任务查询请求"""
        # 检查是否是按优先级查询
        if "p0" in user_request.lower():
            tasks = self.prioritization_flow.get_tasks_by_priority("P0")
            return self._format_query_result("P0优先级任务", tasks)
        elif "p1" in user_request.lower():
            tasks = self.prioritization_flow.get_tasks_by_priority("P1")
            return self._format_query_result("P1优先级任务", tasks)
        elif "p2" in user_request.lower():
            tasks = self.prioritization_flow.get_tasks_by_priority("P2")
            return self._format_query_result("P2优先级任务", tasks)
        
        # 检查是否是按分配对象查询
        elif "worker a" in user_request.lower():
            tasks = self.prioritization_flow.get_tasks_by_assignee("Worker A")
            return self._format_query_result("Worker A的任务", tasks)
        elif "worker b" in user_request.lower():
            tasks = self.prioritization_flow.get_tasks_by_assignee("Worker B")
            return self._format_query_result("Worker B的任务", tasks)
        elif "review" in user_request.lower():
            tasks = self.prioritization_flow.get_tasks_by_assignee("Review Team")
            return self._format_query_result("Review Team的任务", tasks)
        
        # 默认返回所有任务
        else:
            tasks = self.prioritization_flow.get_all_tasks()
            return self._format_query_result("所有任务", tasks)
    
    def _format_query_result(self, title: str, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """格式化查询结果"""
        if not tasks:
            return {
                "success": True,
                "message": f"{title}: 无任务"
            }
        
        message = f"{title}:\n"
        message += "=" * 50 + "\n"
        
        for task in tasks:
            priority = task.get("priority", "未设置")
            assignee = task.get("assigned_to", "未分配")
            status = task.get("status", "未设置")
            
            message += f"ID: {task['id'][:8]}...\n"
            message += f"描述: {task['description']}\n"
            message += f"优先级: {priority}\n"
            message += f"分配给: {assignee}\n"
            message += f"状态: {status}\n"
            message += "-" * 30 + "\n"
        
        return {
            "success": True,
            "message": message,
            "tasks": tasks
        }