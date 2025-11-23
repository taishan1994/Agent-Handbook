"""
Chapter 17 推理技术综合演示

本文件演示了所有推理技术的使用方法，包括：
1. 思维链(CoT)推理技术
2. 自我纠正推理技术
3. ReAct推理技术
4. 辩论链(CoD)推理技术
5. Deep Research深度研究推理系统

通过这个综合演示，您可以了解不同推理技术的特点和适用场景。
"""

import sys
import os
import asyncio
import time
import traceback
from typing import Dict, List, Any

# 添加当前目录路径以便导入
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# 导入所有推理技术（除了思维树）
from chain_of_thought import (
    ChainOfThoughtNode, 
    FewShotCoTNode, 
    create_cot_workflow,
    demo_chain_of_thought
)

# 注意：思维树(ToT)推理技术已从演示中移除

from self_correction import (
    SelfCorrectionNode,
    ReflexionNode,
    create_self_correction_workflow,
    demo_self_correction
)

from react import (
    ReActNode,
    ReActWithToolsNode,
    create_react_workflow,
    demo_react
)

from chain_of_debate import (
    ChainOfDebateNode,
    GraphOfDebateNode,
    create_cod_workflow,
    demo_cod
)

from deep_research import (
    ResearchPlannerNode,
    ResearchExecutorNode,
    ResearchSynthesizerNode,
    create_deep_research_workflow,
    demo_deep_research
)


async def compare_reasoning_techniques():
    """
    比较不同推理技术的性能和结果
    
    使用相同的问题测试不同的推理技术，比较它们的结果和特点。
    """
    # 测试问题
    test_questions = [
        "如果一个房间里有3只猫，每只猫抓了2只老鼠，那么房间里一共有多少只动物？",
        "解释为什么天空是蓝色的，但日落时却是红色或橙色的？",
        "设计一个解决方案，帮助减少城市交通拥堵问题。"
    ]
    
    # 创建推理技术工作流（不包括思维树）
    cot_workflow = create_cot_workflow()
    self_correction_workflow = create_self_correction_workflow("standard")
    react_workflow = create_react_workflow()
    debate_workflow = create_cod_workflow()
    deep_research_workflow = create_deep_research_workflow()
    
    print("=== 推理技术比较演示 ===\n")
    
    for i, question in enumerate(test_questions, 1):
        print(f"问题{i}: {question}")
        print("-" * 50)
        
        # 测试思维链
        print("\n1. 思维链(CoT)推理:")
        start_time = time.time()
        shared_data = {'question': question}
        await cot_workflow._run_async(shared_data)
        cot_time = time.time() - start_time
        cot_result = shared_data.get('cot_results', [{}])[-1]  # 获取最后一个结果
        print(f"答案: {cot_result.get('answer', '无答案')}")
        print(f"推理时间: {cot_time:.2f}秒")
        
        # 测试自我纠正
        print("\n2. 自我纠正推理:")
        start_time = time.time()
        shared_data = {'question': question}
        await self_correction_workflow._run_async(shared_data)
        sc_time = time.time() - start_time
        # 从shared_data中获取结果
        sc_results = shared_data.get('self_correction_results', [])
        if sc_results:
            sc_result = sc_results[-1]  # 获取最后一个结果
            print(f"[DEBUG] sc_result type: {type(sc_result)}")
            print(f"[DEBUG] sc_result value: {sc_result}")
            print(f"答案: {sc_result.get('answer', '无答案')}")
            print(f"纠正次数: {len(sc_result.get('iterations', []))}")
        else:
            print("错误: 未找到自我纠正结果")
        print(f"推理时间: {sc_time:.2f}秒")
        
        # 测试ReAct
        print("\n3. ReAct推理:")
        start_time = time.time()
        shared_data = {'question': question}
        await react_workflow._run_async(shared_data)
        react_time = time.time() - start_time
        # ReAct工作流结果存储在shared_data中
        react_answer = shared_data.get('react_answer', '无答案')
        print(f"答案: {react_answer}")
        print(f"推理时间: {react_time:.2f}秒")
        
        # 测试辩论链
        print("\n4. 辩论链(CoD)推理:")
        start_time = time.time()
        shared_state = {'question': question}
        await debate_workflow._run_async(shared_state)
        cod_time = time.time() - start_time
        
        # 从共享状态中获取辩论结果
        cod_results = shared_state.get('cod_results', [])
        if cod_results and isinstance(cod_results[-1], dict):
            cod_result = cod_results[-1]
            print(f"答案: {cod_result.get('conclusion', '无答案')}")
            print(f"辩论轮次: {len(cod_result.get('debate_history', []))}")
        else:
            print("答案: 无答案")
            print("辩论轮次: 0")
        print(f"推理时间: {cod_time:.2f}秒")
        
        # 测试Deep Research（仅对复杂问题）
        if i > 1:  # 跳过简单问题
            print("\n5. Deep Research深度研究:")
            start_time = time.time()
            dr_shared_state = {'question': question}
            await deep_research_workflow._run_async(dr_shared_state)
            dr_time = time.time() - start_time
            
            # 从共享状态中获取深度研究结果
            dr_results = dr_shared_state.get('deep_research_results', {})
            if dr_results and isinstance(dr_results, dict):
                print(f"答案: {dr_results.get('conclusion', '无答案')}")
                print(f"搜索次数: {len(dr_results.get('research_results', []))}")
            else:
                print("答案: 无答案")
                print("搜索次数: 0")
            print(f"推理时间: {dr_time:.2f}秒")
        
        print("\n" + "=" * 80 + "\n")


async def demonstrate_technique_specialties():
    """
    演示不同推理技术的特长和适用场景
    
    为每种推理技术选择最适合的问题，展示其优势。
    """
    print("=== 推理技术特长演示 ===\n")
    
    # 1. 思维链适合数学推理
    print("1. 思维链(CoT) - 适合数学推理:")
    math_problem = "小明有10个苹果，他给了小红3个，又买了5个，然后吃了2个，最后小明有多少个苹果？"
    cot_workflow = create_cot_workflow()
    shared_data = {'question': math_problem}
    await cot_workflow._run_async(shared_data)
    cot_result = shared_data.get('cot_results', [{}])[-1]  # 获取最后一个结果
    print(f"问题: {math_problem}")
    print(f"思维链推理过程: {cot_result.get('reasoning', '无推理过程')}")
    print(f"答案: {cot_result.get('answer', '无答案')}")
    print()
    
    # 2. 自我纠正适合复杂问题
    print("2. 自我纠正 - 适合复杂问题:")
    complex_problem = "解释量子纠缠现象，并讨论其在量子计算中的应用。"
    sc_workflow = create_self_correction_workflow("standard")
    shared_data = {'question': complex_problem}
    await sc_workflow._run_async(shared_data)
    # 从shared_data中获取结果
    sc_results = shared_data.get('self_correction_results', [])
    if sc_results:
        sc_result = sc_results[-1]  # 获取最后一个结果
        print(f"问题: {complex_problem}")
        print(f"初始答案: {sc_result.get('iterations', [{}])[0].get('answer', '无初始答案')}")
        print(f"最终答案: {sc_result.get('answer', '无最终答案')}")
        print(f"纠正次数: {len(sc_result.get('iterations', []))}")
    else:
        print("错误: 未找到自我纠正结果")
    print()
    
    # 3. ReAct适合需要外部信息的问题
    print("3. ReAct - 适合需要外部信息的问题:")
    info_problem = "最近发布的GPT-5模型有哪些新功能和改进？"
    react_workflow = create_react_workflow()
    shared_data = {'question': info_problem}
    await react_workflow._run_async(shared_data)
    print(f"问题: {info_problem}")
    # ReAct工作流结果存储在shared_data中
    react_answer = shared_data.get('react_answer', '无答案')
    print(f"答案: {react_answer}")
    print()
    
    # 4. 辩论链适合有争议的问题
    print("4. 辩论链(CoD) - 适合有争议的问题:")
    controversial_problem = "人工智能是否会取代人类工作？"
    cod_workflow = create_cod_workflow()
    shared_state = {'question': controversial_problem}
    await cod_workflow._run_async(shared_state)
    
    # 从共享状态中获取辩论结果
    cod_results = shared_state.get('cod_results', [])
    if cod_results and isinstance(cod_results[-1], dict):
        cod_result = cod_results[-1]
        print(f"问题: {controversial_problem}")
        print(f"最终答案: {cod_result.get('conclusion', '无最终答案')}")
        print(f"辩论轮次: {len(cod_result.get('debate_history', []))}")
    else:
        print(f"问题: {controversial_problem}")
        print("最终答案: 无最终答案")
        print("辩论轮次: 0")
    print()
    
    # 5. Deep Research适合深度研究问题
    print("5. Deep Research - 适合深度研究问题:")
    research_problem = "分析全球气候变化的后果对农业的影响及应对策略。"
    dr_workflow = create_deep_research_workflow()
    dr_shared_state = {'question': research_problem}
    await dr_workflow._run_async(dr_shared_state)
    
    # 从共享状态中获取深度研究结果
    dr_results = dr_shared_state.get('deep_research_results', {})
    if dr_results and isinstance(dr_results, dict):
        print(f"问题: {research_problem}")
        print(f"结论: {dr_results.get('conclusion', '无结论')}")
        print(f"搜索次数: {len(dr_results.get('research_results', []))}")
    else:
        print(f"问题: {research_problem}")
        print("结论: 无结论")
        print("搜索次数: 0")
    print()


async def interactive_demo():
    """
    交互式演示
    
    允许用户选择推理技术并输入问题，查看结果。
    """
    print("=== 交互式推理技术演示 ===")
    print("请选择推理技术:")
    print("1. 思维链(CoT)")
    print("2. 自我纠正")
    print("3. ReAct")
    print("4. 辩论链(CoD)")
    print("5. Deep Research")
    print("6. 运行所有技术")
    print("0. 退出")
    
    while True:
        try:
            choice = input("\n请输入选择(0-6): ").strip()
            
            if choice == '0':
                print("退出演示。")
                break
            
            if choice not in ['1', '2', '3', '4', '5', '6']:
                print("无效选择，请重新输入。")
                continue
            
            question = input("请输入您的问题: ").strip()
            if not question:
                print("问题不能为空。")
                continue
            
            print("\n处理中，请稍候...")
            
            if choice == '1':
                # 思维链
                cot_workflow = create_cot_workflow()
                shared_data = {'question': question}
                await cot_workflow._run_async(shared_data)
                result = shared_data.get('cot_results', [{}])[-1]  # 获取最后一个结果
                print(f"\n思维链推理结果:\n{result.get('answer', '无答案')}")
                
            elif choice == '2':
                # 自我纠正
                sc_workflow = create_self_correction_workflow("standard")
                shared_data = {'question': question}
                await sc_workflow._run_async(shared_data)
                # 从shared_data中获取结果
                sc_results = shared_data.get('self_correction_results', [])
                if sc_results:
                    sc_result = sc_results[-1]  # 获取最后一个结果
                    print(f"\n自我纠正推理结果:\n{sc_result.get('answer', '无答案')}")
                else:
                    print("\n错误: 未找到自我纠正结果")
                
            elif choice == '3':
                # ReAct
                react_workflow = create_react_workflow()
                shared_data = {'question': question}
                await react_workflow._run_async(shared_data)
                # ReAct工作流结果存储在shared_data中
                react_answer = shared_data.get('react_answer', '无答案')
                print(f"\nReAct推理结果:\n{react_answer}")
                
            elif choice == '4':
                # 辩论链
                cod_workflow = create_cod_workflow()
                shared_state = {'question': question}
                await cod_workflow._run_async(shared_state)
                
                # 从共享状态中获取辩论结果
                cod_results = shared_state.get('cod_results', [])
                if cod_results and isinstance(cod_results[-1], dict):
                    cod_result = cod_results[-1]
                    print(f"\n辩论链推理结果:\n{cod_result.get('conclusion', '无最终答案')}")
                else:
                    print("\n辩论链推理结果:\n无最终答案")
                
            elif choice == '5':
                # Deep Research
                dr_workflow = create_deep_research_workflow()
                dr_shared_state = {'question': question}
                await dr_workflow._run_async(dr_shared_state)
                
                # 从共享状态中获取深度研究结果
                dr_results = dr_shared_state.get('deep_research_results', {})
                if dr_results and isinstance(dr_results, dict):
                    print(f"\nDeep Research推理结果:\n{dr_results.get('conclusion', '无结论')}")
                else:
                    print("\nDeep Research推理结果:\n无结论")
                
            elif choice == '6':
                # 运行所有技术
                print("\n=== 所有推理技术结果 ===")
                
                # 思维链
                cot_workflow = create_cot_workflow()
                shared_data = {'question': question}
                await cot_workflow._run_async(shared_data)
                cot_result = shared_data.get('cot_results', [{}])[-1]  # 获取最后一个结果
                print(f"\n1. 思维链(CoT):\n{cot_result.get('answer', '无答案')}")
                
                # 自我纠正
                sc_workflow = create_self_correction_workflow("standard")
                sc_shared_data = {'question': question}
                await sc_workflow._run_async(sc_shared_data)
                # 从shared_data中获取结果
                sc_results = sc_shared_data.get('self_correction_results', [])
                if sc_results:
                    sc_result = sc_results[-1]  # 获取最后一个结果
                    print(f"\n2. 自我纠正:\n{sc_result.get('answer', '无答案')}")
                else:
                    print("\n2. 自我纠正: 无结果")
                
                # ReAct
                react_workflow = create_react_workflow()
                react_shared_data = {'question': question}
                await react_workflow._run_async(react_shared_data)
                # ReAct工作流结果存储在shared_data中
                react_answer = react_shared_data.get('react_answer', '无答案')
                print(f"\n3. ReAct:\n{react_answer}")
                
                # 辩论链
                cod_workflow = create_cod_workflow()
                cod_shared_state = {'question': question}
                await cod_workflow._run_async(cod_shared_state)
                # 从共享状态中获取辩论结果
                cod_results = cod_shared_state.get('cod_results', [])
                if cod_results and isinstance(cod_results[-1], dict):
                    cod_result = cod_results[-1]
                    print(f"\n4. 辩论链(CoD):\n{cod_result.get('conclusion', '无最终答案')}")
                else:
                    print("\n4. 辩论链(CoD):\n无最终答案")
                
                # Deep Research
                dr_workflow = create_deep_research_workflow()
                dr_shared_state = {'question': question}
                await dr_workflow._run_async(dr_shared_state)
                
                # 从共享状态中获取深度研究结果
                dr_results = dr_shared_state.get('deep_research_results', {})
                if dr_results and isinstance(dr_results, dict):
                    print(f"\n5. Deep Research:\n{dr_results.get('conclusion', '无结论')}")
                else:
                    print("\n5. Deep Research:\n无结论")
            
            print("\n" + "=" * 50)
            
        except KeyboardInterrupt:
            print("\n\n退出演示。")
            break
        except Exception as e:
            print(f"\n发生错误: {e}")
            print("\n错误详情:")
            traceback.print_exc()


async def main():
    """
    主演示函数
    
    提供菜单选择不同的演示。
    """
    print("Chapter 17 推理技术综合演示")
    print("=" * 50)
    print("1. 比较不同推理技术")
    print("2. 演示推理技术特长")
    print("3. 交互式演示")
    print("4. 运行所有单独演示")
    print("0. 退出")
    
    while True:
        try:
            choice = input("\n请选择演示类型(0-4): ").strip()
            
            if choice == '0':
                print("退出演示。")
                break
            
            if choice == '1':
                await compare_reasoning_techniques()
            elif choice == '2':
                await demonstrate_technique_specialties()
            elif choice == '3':
                await interactive_demo()
            elif choice == '4':
                print("\n运行所有单独演示...")
                print("\n1. 思维链演示:")
                await demo_chain_of_thought()
                
                print("\n2. 自我纠正演示:")
                await demo_self_correction()
                
                print("\n3. ReAct演示:")
                await demo_react()
                
                print("\n4. 辩论链演示:")
                await demo_cod()
                
                print("\n5. Deep Research演示:")
                await demo_deep_research()
            else:
                print("无效选择，请重新输入。")
                
        except KeyboardInterrupt:
            print("\n\n退出演示。")
            break
        except Exception as e:
            print(f"\n发生错误: {e}")
            print("\n错误详情:")
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())