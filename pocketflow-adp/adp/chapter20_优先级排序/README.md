# Chapter 20: 优先级排序

本章实现了使用PocketFlow的任务优先级排序系统，可以根据任务的重要性和紧急性自动分配优先级，并将任务分配给合适的工作人员。

## 功能概述

该系统提供以下功能：

1. **任务创建**：创建新任务并自动分配优先级和工作人员
2. **任务列表**：显示所有任务及其状态
3. **任务查询**：根据优先级或分配对象查询任务
4. **任务状态更新**：更新任务的状态（如进行中、已完成等）
5. **任务删除**：删除不需要的任务

## 文件结构

```
chapter20_优先级排序/
├── __init__.py          # Python包初始化文件
├── README.md            # 本文档
├── main.py              # 主程序入口
├── test.py              # 测试用例
├── task_manager.py      # 任务管理器和任务模型
├── task_nodes.py        # PocketFlow节点实现
└── flow.py              # 优先级排序流程和交互式管理器
```

## 核心组件

### 1. Task类 (`task_manager.py`)

使用dataclass定义的任务模型，包含以下属性：

- `id`: 任务唯一标识符（UUID）
- `description`: 任务描述
- `status`: 任务状态（pending, in_progress, completed, paused）
- `priority`: 任务优先级（P0, P1, P2）
- `assigned_to`: 任务分配对象（Worker A, Worker B, Review Team）

### 2. TaskManager类 (`task_manager.py`)

任务管理器，负责管理所有任务，提供以下方法：

- `create_task(description)`: 创建新任务
- `assign_priority(task_id, priority)`: 分配任务优先级
- `assign_task(task_id, assignee)`: 分配任务给工作人员
- `update_task_status(task_id, status)`: 更新任务状态
- `delete_task(task_id)`: 删除任务
- `get_task(task_id)`: 根据ID获取任务
- `get_all_tasks_sorted()`: 获取按优先级排序的所有任务
- `get_tasks_by_priority(priority)`: 根据优先级获取任务
- `get_tasks_by_assignee(assignee)`: 根据分配对象获取任务

### 3. PocketFlow节点 (`task_nodes.py`)

实现任务管理操作的各种节点：

- `TaskCreationNode`: 创建新任务
- `TaskPriorityNode`: 为任务分配优先级
- `TaskAssignmentNode`: 将任务分配给工作人员
- `TaskListingNode`: 列出所有任务
- `TaskStatusUpdateNode`: 更新任务状态

每个节点都实现了`prep`、`exec`和`post`方法，符合PocketFlow的节点规范。

### 4. PrioritizationFlow类 (`flow.py`)

任务优先级排序流程，组合多个节点形成完整的工作流：

- `create_task()`: 创建任务并分配优先级和工作人员
- `list_tasks()`: 列出所有任务
- `update_task_status()`: 更新任务状态
- `get_task_by_id()`: 根据ID获取任务
- `get_all_tasks()`: 获取所有任务
- `get_tasks_by_priority()`: 根据优先级获取任务
- `get_tasks_by_assignee()`: 根据分配对象获取任务
- `delete_task()`: 删除任务

### 5. InteractiveTaskManager类 (`flow.py`)

交互式任务管理器，提供自然语言接口处理用户请求：

- `process_user_request(user_request)`: 处理用户请求并返回结果

支持的自然语言请求类型：

- 任务创建："创建任务: [任务描述]"
- 任务列表："列出任务"、"任务列表"、"显示任务"
- 任务状态更新："更新任务 [任务ID] 状态为完成"
- 任务删除："删除任务 [任务ID]"
- 任务查询："查询P0优先级任务"、"查看Worker A的任务"

## 使用方法

### 运行演示模式

```bash
python main.py --demo
# 或
python main.py -d
```

这将运行一个完整的演示，展示系统的所有功能。

### 运行交互式模式

```bash
python main.py --interactive
# 或
python main.py -i
```

这将启动交互式模式，您可以输入自然语言命令来操作系统。

### 运行测试

```bash
python test.py
```

这将运行所有测试用例，验证系统功能是否正常。

## 示例交互

### 创建任务

```
用户: 创建任务: 修复登录页面的显示问题
系统: 任务已创建成功！
任务ID: 12345678-1234-1234-1234-123456789012
描述: 修复登录页面的显示问题
优先级: P1
分配给: Worker A
```

### 列出任务

```
用户: 列出任务
系统: 任务列表:
==================================================
ID: 12345678-...
描述: 修复登录页面的显示问题
优先级: P1
分配给: Worker A
状态: pending
------------------------------
ID: 87654321-4321-4321-4321-210987654321
描述: 优化数据库查询性能
优先级: P0
分配给: Worker B
状态: pending
------------------------------
```

### 更新任务状态

```
用户: 更新任务 12345678-1234-1234-1234-123456789012 状态为完成
系统: 任务状态已更新！
任务ID: 12345678-...
新状态: completed
```

### 查询任务

```
用户: 查询P0优先级任务
系统: P0优先级任务:
==================================================
ID: 87654321-...
描述: 优化数据库查询性能
优先级: P0
分配给: Worker B
状态: pending
------------------------------
```

## 技术特点

1. **模块化设计**：将功能拆分为独立的模块，便于维护和扩展
2. **PocketFlow集成**：使用PocketFlow框架实现工作流管理
3. **自然语言处理**：支持自然语言命令，提高用户体验
4. **智能优先级分配**：使用LLM分析任务并自动分配优先级
5. **灵活的任务查询**：支持多种查询方式，如按优先级、按分配对象等

## 依赖项

- `pocketflow`: 工作流管理框架
- `utils`: 包含LLM调用和搜索功能的工具模块

## 扩展建议

1. **任务依赖关系**：添加任务之间的依赖关系管理
2. **任务截止日期**：为任务添加截止日期和提醒功能
3. **任务标签**：为任务添加标签，便于分类和搜索
4. **任务评论**：添加任务评论功能，支持团队协作
5. **任务统计**：添加任务统计和报告功能
6. **用户权限**：添加用户权限管理，控制任务访问和操作

## 总结

本章实现了一个基于PocketFlow的任务优先级排序系统，展示了如何使用工作流框架来管理复杂的业务逻辑。通过结合LLM的自然语言处理能力，系统提供了直观的用户界面，使用户能够以自然的方式创建、管理和查询任务。这种设计模式可以应用于各种需要工作流管理的场景，如项目管理、客户服务、审批流程等。