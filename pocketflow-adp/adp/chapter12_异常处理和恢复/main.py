"""
Chapter 12: Exception Handling and Recovery - Main Example
使用PocketFlow实现的异常处理和恢复模式示例和测试
"""

import sys
import os

# 添加当前目录到路径
sys.path.append(os.path.dirname(__file__))

from flow import run_exception_handling_example


def test_basic_question():
    """测试基本问题处理"""
    print("\n" + "=" * 60)
    print("测试1: 基本问题处理")
    print("=" * 60)
    
    question = "刘翔获得了多少次世界冠军？"
    result = run_exception_handling_example(question)
    
    return result.get("processing_success", False)


def test_complex_question():
    """测试复杂问题处理"""
    print("\n" + "=" * 60)
    print("测试2: 复杂问题处理")
    print("=" * 60)
    
    question = "请详细分析刘翔的运动生涯，包括他的主要成就、伤病情况以及对亚洲田径的影响"
    context = "用户是一位体育爱好者，希望了解中国田径运动员的详细信息"
    result = run_exception_handling_example(question, context)
    
    return result.get("processing_success", False)


def test_with_context():
    """测试带上下文的问题处理"""
    print("\n" + "=" * 60)
    print("测试3: 带上下文的问题处理")
    print("=" * 60)
    
    question = "他的最好成绩是多少？"
    context = "用户之前询问了关于刘翔的信息，这里的'他'指的是刘翔"
    result = run_exception_handling_example(question, context)
    
    return result.get("processing_success", False)


def test_multiple_runs():
    """测试多次运行，观察异常处理和恢复的不同情况"""
    print("\n" + "=" * 60)
    print("测试4: 多次运行，观察异常处理和恢复情况")
    print("=" * 60)
    
    question = "中国运动员在奥运会上获得了多少金牌？"
    
    success_count = 0
    total_runs = 5
    
    for i in range(total_runs):
        print(f"\n第 {i+1} 次运行:")
        result = run_exception_handling_example(question)
        
        if result.get("processing_success", False):
            success_count += 1
        
        print(f"处理结果: {'成功' if result.get('processing_success', False) else '失败'}")
        print(f"重试次数: {result.get('retry_count', 0)}")
    
    print(f"\n总计: {success_count}/{total_runs} 次成功")
    
    return success_count == total_runs


def interactive_test():
    """交互式测试，允许用户输入自己的问题"""
    print("\n" + "=" * 60)
    print("交互式测试")
    print("=" * 60)
    print("输入您的问题 (输入 'quit' 退出):")
    
    while True:
        question = input("\n> ")
        
        if question.lower() in ['quit', 'exit', 'q']:
            break
        
        if not question.strip():
            continue
        
        print("\n处理中...")
        result = run_exception_handling_example(question)
        
        print(f"\n处理结果: {'成功' if result.get('processing_success', False) else '失败'}")
        print(f"重试次数: {result.get('retry_count', 0)}")


def main():
    """主函数，运行所有测试"""
    print("Chapter 12: 异常处理和恢复模式 - PocketFlow实现")
    print("=" * 60)
    
    # 运行测试
    tests = [
        ("基本问题处理", test_basic_question),
        ("复杂问题处理", test_complex_question),
        ("带上下文的问题处理", test_with_context),
        ("多次运行测试", test_multiple_runs)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"测试 '{test_name}' 发生异常: {str(e)}")
            results.append((test_name, False))
    
    # 打印测试结果摘要
    print("\n" + "=" * 60)
    print("测试结果摘要")
    print("=" * 60)
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name}: {status}")
    
    passed_count = sum(1 for _, success in results if success)
    total_count = len(results)
    
    print(f"\n总计: {passed_count}/{total_count} 测试通过")
    
    # 询问是否进行交互式测试
    choice = input("\n是否进行交互式测试? (y/n): ").lower()
    if choice in ['y', 'yes']:
        interactive_test()
    
    print("\n测试完成!")


if __name__ == "__main__":
    main()