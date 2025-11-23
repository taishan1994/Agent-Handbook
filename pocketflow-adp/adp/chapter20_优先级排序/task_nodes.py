from typing import Dict, List, Any, Optional
import re
import json
from pocketflow import Node
from task_manager import TaskManager, Task
import sys
import os
# 添加项目根目录到路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    
# 直接导入 call_llm 函数
from agent_handbook_utils import call_llm


class TaskCreationNode(Node):
    """创建新任务的节点"""
    
    def __init__(self, task_manager: TaskManager):
        super().__init__()
        self.task_manager = task_manager
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：从共享状态中提取任务描述"""
        return {
            "description": shared.get("task_description", ""),
            "user_request": shared.get("user_request", "")
        }
    
    def exec(self, prep_res: Dict[str, Any]) -> None:
        """执行阶段：创建新任务"""
        description = prep_res["description"]
        if not description:
            # 如果没有明确的任务描述，尝试从用户请求中提取
            user_request = prep_res["user_request"]
            description = self._extract_task_description(user_request)
        
        task_id = self.task_manager.create_task(description)
        # 将任务ID存储在共享状态中
        prep_res["task_id"] = task_id
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: None) -> str:
        """后处理阶段：将任务ID保存到共享状态"""
        task_id = prep_res.get("task_id")
        if task_id:
            shared["task_id"] = task_id
            shared["current_task"] = self.task_manager.get_task(task_id)
        return "default"
    
    def _extract_task_description(self, user_request: str) -> str:
        """从用户请求中提取任务描述"""
        # 使用LLM提取任务描述
        prompt = f"""
        从以下用户请求中提取任务描述。只返回任务描述本身，不要包含其他信息。
        
        用户请求: {user_request}
        
        任务描述:
        """
        return call_llm(prompt).strip()


class TaskPriorityNode(Node):
    """为任务分配优先级的节点"""
    
    def __init__(self, task_manager: TaskManager):
        super().__init__()
        self.task_manager = task_manager
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：获取任务和用户请求信息"""
        task_id = shared.get("task_id")
        task = self.task_manager.get_task(task_id) if task_id else None
        user_request = shared.get("user_request", "")
        
        return {
            "task": task,
            "user_request": user_request
        }
    
    def exec(self, prep_res: Dict[str, Any]) -> None:
        """执行阶段：分析并分配优先级"""
        task = prep_res["task"]
        user_request = prep_res["user_request"]
        
        if not task:
            return
        
        # 使用LLM分析优先级
        priority = self._analyze_priority(user_request, task.description)
        
        # 如果LLM无法确定优先级，使用默认值
        if priority not in ["P0", "P1", "P2"]:
            priority = "P1"  # 默认中等优先级
        
        self.task_manager.assign_priority(task.id, priority)
        # 将优先级存储在共享状态中
        prep_res["priority"] = priority
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: None) -> str:
        """后处理阶段：更新任务信息"""
        task_id = shared.get("task_id")
        if task_id:
            shared["task_id"] = task_id
            shared["current_task"] = self.task_manager.get_task(task_id)
        return "default"
    
    def _analyze_priority(self, user_request: str, task_description: str) -> str:
        """使用LLM分析任务优先级"""
        prompt = f"""
        分析以下任务的优先级。根据任务描述和用户请求，确定优先级为P0（最高）、P1（中等）或P2（最低）。
        
        任务描述: {task_description}
        用户请求: {user_request}
        
        只返回优先级代码（P0、P1或P2），不要包含其他解释。
        
        优先级:
        """
        return call_llm(prompt).strip()


class TaskAssignmentNode(Node):
    """将任务分配给工作人员的节点"""
    
    def __init__(self, task_manager: TaskManager):
        super().__init__()
        self.task_manager = task_manager
        self.available_workers = ["Worker A", "Worker B", "Review Team"]
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：获取任务和用户请求信息"""
        task_id = shared.get("task_id")
        task = self.task_manager.get_task(task_id) if task_id else None
        user_request = shared.get("user_request", "")
        
        return {
            "task": task,
            "user_request": user_request
        }
    
    def exec(self, prep_res: Dict[str, Any]) -> None:
        """执行阶段：分配任务给执行者"""
        task = prep_res["task"]
        user_request = prep_res["user_request"]
        
        if not task:
            return
        
        # 使用LLM分析任务分配
        assignee = self._analyze_assignment(user_request, task.description)
        
        # 如果LLM无法确定执行者，使用默认值
        if not assignee:
            assignee = "待分配"  # 默认状态
        
        self.task_manager.assign_task(task.id, assignee)
        # 将执行者存储在共享状态中
        prep_res["assignee"] = assignee
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: None) -> str:
        """后处理阶段：更新任务信息"""
        task_id = shared.get("task_id")
        if task_id:
            shared["current_task"] = self.task_manager.get_task(task_id)
        return "default"
    
    def _analyze_assignment(self, user_request: str, task_description: str) -> str:
        """使用LLM分析任务分配"""
        prompt = f"""
        分析以下任务应该分配给哪个工作人员。根据任务描述和用户请求，确定最合适的工作人员。
        
        可用工作人员: Worker A, Worker B, Review Team
        
        任务描述: {task_description}
        用户请求: {user_request}
        
        只返回工作人员名称，不要包含其他解释。
        
        工作人员:
        """
        return call_llm(prompt).strip()


class TaskListingNode(Node):
    """列出所有任务的节点"""
    
    def __init__(self, task_manager: TaskManager):
        super().__init__()
        self.task_manager = task_manager
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：获取任务列表"""
        tasks = self.task_manager.get_all_tasks_sorted()
        return {"tasks": tasks}
    
    def exec(self, prep_res: Dict[str, Any]) -> str:
        """执行阶段：格式化任务列表"""
        tasks = prep_res["tasks"]
        if not tasks:
            return "当前没有任务。"
        
        # 格式化任务列表
        result = "任务列表:\n"
        result += "=" * 50 + "\n"
        
        for task in tasks:
            priority = task.priority or "未设置"
            assignee = task.assigned_to or "未分配"
            status = task.status
            
            result += f"ID: {task.id[:8]}...\n"
            result += f"描述: {task.description}\n"
            result += f"优先级: {priority}\n"
            result += f"分配给: {assignee}\n"
            result += f"状态: {status}\n"
            result += "-" * 30 + "\n"
        
        return result
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: str) -> str:
        """后处理阶段：保存任务列表到共享状态"""
        shared["task_list"] = exec_res
        return "default"


class TaskStatusUpdateNode(Node):
    """更新任务状态的节点"""
    
    def __init__(self, task_manager: TaskManager):
        super().__init__()
        self.task_manager = task_manager
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：获取任务ID和新状态"""
        return {
            "task_id": shared.get("task_id"),
            "new_status": shared.get("new_status", "in_progress")
        }
    
    def exec(self, prep_res: Dict[str, Any]) -> str:
        """执行阶段：更新任务状态"""
        task_id = prep_res["task_id"]
        new_status = prep_res["new_status"]
        
        if not task_id:
            return "failed"
        
        success = self.task_manager.update_task_status(task_id, new_status)
        return "success" if success else "failed"
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: str) -> str:
        """后处理阶段：更新任务信息"""
        task_id = prep_res["task_id"]
        if task_id and exec_res == "success":
            shared["current_task"] = self.task_manager.get_task(task_id)
        return "default"