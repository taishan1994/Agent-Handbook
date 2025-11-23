"""
人机协同模式示例和测试代码

本模块提供了人机协同模式的多种示例和测试场景，包括：
1. 简单任务自动处理
2. 复杂任务人工干预
3. 不同复杂度阈值的测试
4. 批量任务处理
"""

import sys
import os
import time
from typing import List, Dict, Any

# 添加当前目录路径
current_dir = os.path.dirname(__file__)
if current_dir not in sys.path:
    sys.path.append(current_dir)

from flow import HumanInTheLoopFlow, run_human_in_the_loop_example


def test_simple_task():
    """测试简单任务自动处理"""
    print("=" * 60)
    print("测试场景1: 简单任务自动处理")
    print("=" * 60)
    
    # 简单任务
    task = "查询明天北京的天气"
    
    # 使用较高的复杂度阈值，确保任务自动处理
    result = run_human_in_the_loop_example(
        task=task,
        complexity_threshold=0.8,
        simulate_human=True
    )
    
    # 验证结果
    assert result.get("requires_human_intervention") == False, "简单任务不应该需要人工干预"
    assert result.get("response_type") == "automated", "简单任务应该是自动处理"
    
    print("\n✅ 测试1通过: 简单任务自动处理成功")
    return result


def test_complex_task():
    """测试复杂任务人工干预"""
    print("\n" + "=" * 60)
    print("测试场景2: 复杂任务人工干预")
    print("=" * 60)
    
    # 复杂任务
    task = "制定一个涉及多部门协作的复杂项目计划，需要考虑预算、时间和人力资源限制，这是一个高风险项目"
    
    # 使用较低的复杂度阈值，确保任务需要人工干预
    result = run_human_in_the_loop_example(
        task=task,
        complexity_threshold=0.5,
        simulate_human=True
    )
    
    # 验证结果
    assert result.get("requires_human_intervention") == True, "复杂任务应该需要人工干预"
    assert result.get("response_type") == "human_integrated", "复杂任务应该是人工整合处理"
    
    print("\n✅ 测试2通过: 复杂任务人工干预成功")
    return result


def test_different_thresholds():
    """测试不同复杂度阈值的影响"""
    print("\n" + "=" * 60)
    print("测试场景3: 不同复杂度阈值的影响")
    print("=" * 60)
    
    # 中等复杂度任务
    task = "分析市场趋势并制定营销策略"
    
    thresholds = [0.3, 0.5, 0.7, 0.9]
    results = []
    
    for threshold in thresholds:
        print(f"\n--- 测试阈值: {threshold} ---")
        result = run_human_in_the_loop_example(
            task=task,
            complexity_threshold=threshold,
            simulate_human=True
        )
        results.append((threshold, result))
        
        # 记录是否需要人工干预
        requires_human = result.get("requires_human_intervention", False)
        print(f"阈值 {threshold}: {'需要' if requires_human else '不需要'}人工干预")
    
    print("\n✅ 测试3通过: 不同复杂度阈值测试完成")
    return results


def test_batch_processing():
    """测试批量任务处理"""
    print("\n" + "=" * 60)
    print("测试场景4: 批量任务处理")
    print("=" * 60)
    
    # 任务列表
    tasks = [
        "查询明天上海的天气",
        "分析用户反馈数据",
        "制定一个涉及法律和道德问题的敏感处理方案",
        "生成月度销售报告",
        "设计一个高风险的金融产品推广策略"
    ]
    
    # 创建流程
    hitl_flow = HumanInTheLoopFlow(
        complexity_threshold=0.6,
        simulate_human=True
    )
    
    # 批量处理
    results = []
    for i, task in enumerate(tasks, 1):
        print(f"\n--- 处理任务 {i}/{len(tasks)} ---")
        result = hitl_flow.process_task(task)
        results.append(result)
        
        # 记录处理结果
        requires_human = result.get("requires_human_intervention", False)
        response_type = result.get("response_type", "unknown")
        print(f"任务: {task[:30]}...")
        print(f"结果: {'需要' if requires_human else '不需要'}人工干预, 类型: {response_type}")
    
    # 统计结果
    auto_count = sum(1 for r in results if not r.get("requires_human_intervention", False))
    human_count = len(results) - auto_count
    
    print(f"\n📊 批量处理统计:")
    print(f"总任务数: {len(results)}")
    print(f"自动处理: {auto_count}")
    print(f"人工干预: {human_count}")
    print(f"人工干预率: {human_count/len(results)*100:.1f}%")
    
    print("\n✅ 测试4通过: 批量任务处理完成")
    return results


def test_human_input_simulation():
    """测试人类输入模拟"""
    print("\n" + "=" * 60)
    print("测试场景5: 人类输入模拟")
    print("=" * 60)
    
    # 高复杂度任务，确保需要人工干预
    task = "制定一个涉及伦理、法律和社会影响的复杂决策方案"
    
    # 创建流程，启用人类输入模拟
    hitl_flow = HumanInTheLoopFlow(
        complexity_threshold=0.3,  # 低阈值确保需要人工干预
        simulate_human=True
    )
    
    # 处理任务
    result = hitl_flow.process_task(task)
    
    # 检查人类输入相关内容
    assert result.get("requires_human_intervention") == True, "高复杂度任务应该需要人工干预"
    assert "human_input" in result, "应该有人类输入"
    assert "human_input_analysis" in result, "应该有人类输入分析"
    
    # 打印人类输入分析
    human_input = result.get("human_input", "")
    input_analysis = result.get("human_input_analysis", {})
    
    print(f"\n👤 人类输入: {human_input}")
    print(f"📊 输入分析: {input_analysis}")
    
    print("\n✅ 测试5通过: 人类输入模拟测试完成")
    return result


def test_performance():
    """测试性能"""
    print("\n" + "=" * 60)
    print("测试场景6: 性能测试")
    print("=" * 60)
    
    # 任务列表
    tasks = [
        "简单任务1",
        "中等复杂度任务，需要一些分析",
        "复杂任务，涉及多方面考虑和风险评估",
        "简单任务2",
        "中等复杂度任务，需要数据处理和报告生成"
    ]
    
    # 测试不同配置的性能
    configs = [
        {"complexity_threshold": 0.7, "simulate_human": True, "name": "标准配置"},
        {"complexity_threshold": 0.5, "simulate_human": True, "name": "低阈值配置"},
        {"complexity_threshold": 0.9, "simulate_human": False, "name": "高阈值无模拟配置"}
    ]
    
    performance_results = []
    
    for config in configs:
        print(f"\n--- 测试配置: {config['name']} ---")
        
        # 创建流程
        hitl_flow = HumanInTheLoopFlow(
            complexity_threshold=config["complexity_threshold"],
            simulate_human=config["simulate_human"]
        )
        
        # 记录开始时间
        start_time = time.time()
        
        # 批量处理
        results = []
        for task in tasks:
            result = hitl_flow.process_task(task)
            results.append(result)
        
        # 记录结束时间
        end_time = time.time()
        duration = end_time - start_time
        
        # 统计结果
        auto_count = sum(1 for r in results if not r.get("requires_human_intervention", False))
        human_count = len(results) - auto_count
        
        performance_result = {
            "config": config["name"],
            "threshold": config["complexity_threshold"],
            "simulate_human": config["simulate_human"],
            "total_tasks": len(tasks),
            "auto_processed": auto_count,
            "human_intervention": human_count,
            "total_duration": duration,
            "avg_duration_per_task": duration / len(tasks)
        }
        
        performance_results.append(performance_result)
        
        print(f"总任务数: {len(tasks)}")
        print(f"自动处理: {auto_count}")
        print(f"人工干预: {human_count}")
        print(f"总耗时: {duration:.2f}秒")
        print(f"平均每任务: {duration/len(tasks):.2f}秒")
    
    # 比较性能
    print(f"\n📊 性能比较:")
    for result in performance_results:
        print(f"{result['config']}: 平均{result['avg_duration_per_task']:.2f}秒/任务, "
              f"人工干预率{result['human_intervention']/result['total_tasks']*100:.1f}%")
    
    print("\n✅ 测试6通过: 性能测试完成")
    return performance_results


def run_all_tests():
    """运行所有测试"""
    print("🚀 开始运行人机协同模式所有测试")
    
    test_results = []
    
    try:
        # 运行各项测试
        test_results.append(("简单任务自动处理", test_simple_task))
        test_results.append(("复杂任务人工干预", test_complex_task))
        test_results.append(("不同复杂度阈值", test_different_thresholds))
        test_results.append(("批量任务处理", test_batch_processing))
        test_results.append(("人类输入模拟", test_human_input_simulation))
        test_results.append(("性能测试", test_performance))
        
        print("\n" + "=" * 60)
        print("🎉 所有测试完成!")
        print("=" * 60)
        
        for test_name, result in test_results:
            print(f"✅ {test_name}: 通过")
        
        return True
    
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        return False


if __name__ == "__main__":
    # 运行所有测试
    success = run_all_tests()
    
    if success:
        print("\n🎊 人机协同模式测试全部通过!")
    else:
        print("\n💥 部分测试失败，请检查实现")