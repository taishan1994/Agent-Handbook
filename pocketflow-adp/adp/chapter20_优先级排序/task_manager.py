from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class Task:
    """表示系统中的单个任务"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    priority: Optional[str] = None  # P0, P1, P2
    assigned_to: Optional[str] = None  # 工作人员名称
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "pending"  # pending, in_progress, completed
    
    def to_dict(self) -> Dict:
        """将任务转换为字典格式"""
        return {
            "id": self.id,
            "description": self.description,
            "priority": self.priority,
            "assigned_to": self.assigned_to,
            "created_at": self.created_at.isoformat(),
            "status": self.status
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Task':
        """从字典创建任务对象"""
        task = cls(
            id=data.get("id", str(uuid.uuid4())),
            description=data.get("description", ""),
            priority=data.get("priority"),
            assigned_to=data.get("assigned_to")
        )
        if "created_at" in data:
            task.created_at = datetime.fromisoformat(data["created_at"])
        if "status" in data:
            task.status = data["status"]
        return task


class TaskManager:
    """高效且健壮的内存任务管理器"""
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
    
    def create_task(self, description: str) -> str:
        """创建新任务并返回任务ID"""
        task = Task(description=description)
        self.tasks[task.id] = task
        return task.id
    
    def assign_priority(self, task_id: str, priority: str) -> bool:
        """为任务分配优先级"""
        if task_id in self.tasks and priority in ["P0", "P1", "P2"]:
            self.tasks[task_id].priority = priority
            return True
        return False
    
    def assign_task(self, task_id: str, assignee: str) -> bool:
        """将任务分配给工作人员"""
        if task_id in self.tasks:
            self.tasks[task_id].assigned_to = assignee
            return True
        return False
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """获取指定ID的任务"""
        return self.tasks.get(task_id)
    
    def list_all_tasks(self) -> List[Task]:
        """列出所有任务"""
        return list(self.tasks.values())
    
    def get_tasks_by_priority(self, priority: str) -> List[Task]:
        """获取按优先级排序的任务列表"""
        if priority not in ["P0", "P1", "P2"]:
            return []
        
        priority_order = {"P0": 0, "P1": 1, "P2": 2}
        filtered_tasks = [task for task in self.tasks.values() if task.priority == priority]
        return sorted(filtered_tasks, key=lambda t: (priority_order.get(t.priority, 3), t.created_at))
    
    def get_all_tasks_sorted(self) -> List[Task]:
        """获取按优先级和创建时间排序的所有任务"""
        priority_order = {"P0": 0, "P1": 1, "P2": 2}
        # 未分配优先级的任务放在最后
        return sorted(
            self.tasks.values(), 
            key=lambda t: (priority_order.get(t.priority, 3), t.created_at)
        )
    
    def update_task_status(self, task_id: str, status: str) -> bool:
        """更新任务状态"""
        if task_id in self.tasks and status in ["pending", "in_progress", "completed"]:
            self.tasks[task_id].status = status
            return True
        return False
    
    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            return True
        return False
    
    def get_tasks_by_assignee(self, assignee: str) -> List[Task]:
        """获取分配给特定工作人员的任务"""
        return [task for task in self.tasks.values() if task.assigned_to == assignee]