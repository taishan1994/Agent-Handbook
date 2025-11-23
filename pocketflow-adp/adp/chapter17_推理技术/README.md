# Chapter 17: 推理技术实现

本章实现了多种高级推理技术，基于PocketFlow框架构建，并集成了utils中的LLM调用和搜索功能。

## 实现的推理技术

1. **思维链(Chain of Thought, CoT)** - 引导模型逐步思考问题
2. **自我纠正(Self-Correction)** - 检测并修正推理过程中的错误
3. **ReAct(Reasoning and Acting)** - 结合推理和行动的循环过程
4. **辩论链(Chain of Debate, CoD)** - 通过多轮辩论提高推理质量
5. **Deep Research** - 结合多种推理技术的深度研究系统

## 文件结构

```
chapter17_推理技术/
├── __init__.py              # 模块初始化文件
├── chain_of_thought.py      # 思维链推理技术实现
├── self_correction.py       # 自我纠正推理技术实现
├── react.py                 # ReAct推理技术实现
├── chain_of_debate.py       # 辩论链推理技术实现
├── deep_research.py         # Deep Research深度研究系统实现
├── demo.py                  # 综合演示脚本
└── README.md                # 本文件
```

## 使用方法

### 运行综合演示

```bash
python demo.py
```

这将启动一个交互式菜单，您可以选择：

1. 比较不同推理技术 - 使用相同的问题测试不同的推理技术
2. 演示推理技术特长 - 为每种推理技术选择最适合的问题
3. 交互式演示 - 选择推理技术并输入问题
4. 运行所有单独演示 - 依次运行每种推理技术的单独演示

### 在代码中使用

```python
import asyncio
from chapter17_推理技术 import (
    create_cot_workflow,
    create_react_workflow,
    create_self_correction_workflow,
    create_cod_workflow,
    create_deep_research_workflow
)

async def example():
    # 创建思维链工作流
    cot_workflow = create_cot_workflow()
    shared_data = {'question': '1+1等于几？'}
    await cot_workflow._run_async(shared_data)
    result = shared_data.get('cot_results', [{}])[-1]
    print(f"思维链结果: {result.get('answer', '无答案')}")
    
    # 创建ReAct工作流
    react_workflow = create_react_workflow()
    shared_data = {'question': '1+1等于几？'}
    await react_workflow._run_async(shared_data)
    react_answer = shared_data.get('react_answer', '无答案')
    print(f"ReAct结果: {react_answer}")

# 运行示例
asyncio.run(example())
```

## 推理技术特点

### 思维链(CoT)
- 适合数学推理和逻辑问题
- 引导模型逐步思考
- 推理过程透明

### 自我纠正
- 适合复杂问题
- 检测并修正推理错误
- 提高答案准确性

### ReAct
- 适合需要外部信息的问题
- 结合推理和行动
- 支持搜索工具

### 辩论链(CoD)
- 适合有争议的问题
- 通过多轮辩论提高质量
- 考虑多种观点

### Deep Research
- 适合深度研究问题
- 结合多种推理技术
- 提供全面分析

## 依赖

- PocketFlow框架
- utils模块中的call_llm和search_web_exa函数

## 注意事项

- 所有推理技术都需要配置LLM服务
- ReAct和Deep Research需要网络连接进行搜索
- 某些复杂问题可能需要较长的处理时间