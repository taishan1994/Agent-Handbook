#!/usr/bin/env python3
"""
Chapter 20: 优先级排序
使用PocketFlow实现的任务优先级排序系统
"""

import os
import sys
import argparse
from flow import InteractiveTaskManager


def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(description="任务优先级排序系统")
    parser.add_argument("--interactive", "-i", action="store_true", 
                        help="启动交互式模式")
    parser.add_argument("--demo", "-d", action="store_true", 
                        help="运行演示模式")
    
    args = parser.parse_args()
    
    task_manager = InteractiveTaskManager()
    
    if args.demo:
        run_demo(task_manager)
    elif args.interactive:
        run_interactive_mode(task_manager)
    else:
        # 默认运行演示模式
        run_demo(task_manager)


def run_demo(task_manager):
    """运行演示模式"""
    print("=" * 60)
    print("任务优先级排序系统演示")
    print("=" * 60)
    
    # 演示创建任务
    print("\n1. 创建任务演示:")
    print("-" * 30)
    
    demo_requests = [
        "创建任务：修复关键的安全漏洞",
        "创建任务：优化数据库查询性能",
        "创建任务：更新用户界面文档",
        "创建任务：添加新的用户反馈功能",
        "创建任务：修复次要的UI显示问题"
    ]
    
    for request in demo_requests:
        print(f"\n用户请求: {request}")
        result = task_manager.process_user_request(request)
        print(f"系统响应: {result['message']}")
    
    # 演示列出任务
    print("\n\n2. 列出所有任务:")
    print("-" * 30)
    result = task_manager.process_user_request("列出任务")
    print(result['message'])
    
    # 演示按优先级查询
    print("\n\n3. 按优先级查询:")
    print("-" * 30)
    for priority in ["P0", "P1", "P2"]:
        result = task_manager.process_user_request(f"查询{priority}优先级任务")
        print(f"\n{result['message']}")
    
    # 演示更新任务状态
    print("\n\n4. 更新任务状态:")
    print("-" * 30)
    # 获取第一个任务ID
    tasks = task_manager.prioritization_flow.get_all_tasks()
    if tasks:
        first_task_id = tasks[0]["id"]
        result = task_manager.process_user_request(f"更新任务 {first_task_id} 状态为完成")
        print(f"用户请求: 更新任务 {first_task_id[:8]}... 状态为完成")
        print(f"系统响应: {result['message']}")
    
    # 演示删除任务
    print("\n\n5. 删除任务:")
    print("-" * 30)
    if len(tasks) > 1:
        second_task_id = tasks[1]["id"]
        result = task_manager.process_user_request(f"删除任务 {second_task_id}")
        print(f"用户请求: 删除任务 {second_task_id[:8]}...")
        print(f"系统响应: {result['message']}")
    
    # 最终任务列表
    print("\n\n6. 最终任务列表:")
    print("-" * 30)
    result = task_manager.process_user_request("列出任务")
    print(result['message'])
    
    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)


def run_interactive_mode(task_manager):
    """运行交互式模式"""
    print("=" * 60)
    print("任务优先级排序系统 - 交互式模式")
    print("=" * 60)
    print("输入 'help' 查看帮助信息，输入 'quit' 或 'exit' 退出程序")
    print("-" * 60)
    
    while True:
        try:
            user_input = input("\n请输入您的请求: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', '退出']:
                print("感谢使用任务优先级排序系统，再见！")
                break
            
            if user_input.lower() in ['help', '帮助']:
                show_help()
                continue
            
            # 处理用户请求
            result = task_manager.process_user_request(user_input)
            print(f"\n系统响应: {result['message']}")
            
        except KeyboardInterrupt:
            print("\n\n程序被用户中断，再见！")
            break
        except Exception as e:
            print(f"\n发生错误: {str(e)}")


def show_help():
    """显示帮助信息"""
    help_text = """
    可用命令:
    
    1. 创建任务:
       - "创建任务: [任务描述]"
       - "新建任务: [任务描述]"
       - "添加任务: [任务描述]"
       - "create task: [任务描述]"
       - "new task: [任务描述]"
       - "add task: [任务描述]"
    
    2. 列出任务:
       - "列出任务"
       - "任务列表"
       - "显示任务"
       - "list tasks"
       - "show tasks"
       - "all tasks"
    
    3. 更新任务状态:
       - "更新任务 [任务ID] 状态为完成"
       - "修改任务 [任务ID] 状态为开始"
       - "任务 [任务ID] 已完成"
       - "update task [任务ID] status complete"
       - "task [任务ID] completed"
    
    4. 删除任务:
       - "删除任务 [任务ID]"
       - "移除任务 [任务ID]"
       - "delete task [任务ID]"
       - "remove task [任务ID]"
    
    5. 查询任务:
       - "查询P0优先级任务"
       - "查看Worker A的任务"
       - "获取所有任务"
       - "search P0 tasks"
       - "get Worker A tasks"
       - "find all tasks"
    
    6. 其他:
       - "help" 或 "帮助" - 显示此帮助信息
       - "quit" 或 "exit" 或 "退出" - 退出程序
    
    示例:
       - 创建任务: 修复登录页面的显示问题
       - 列出任务
       - 更新任务 12345678-1234-1234-1234-123456789012 状态为完成
       - 查询P0优先级任务
       - 删除任务 12345678-1234-1234-1234-123456789012
    """
    print(help_text)


if __name__ == "__main__":
    main()