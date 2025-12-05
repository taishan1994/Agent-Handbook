# LeetCode Agent

正在适配中！！！！尚未完成！！！

一个基于PocketFlow的智能LeetCode问题解决代理，能够自动解析题目、设计解决方案、生成代码并进行测试优化。

## 功能特性

- 🧠 智能题目解析：支持LeetCode URL或直接问题描述
- 📝 解法设计：自动生成解题思路和算法设计
- 💻 代码生成：生成高质量、可运行的代码实现
- 🧪 测试用例生成：自动创建全面的测试用例
- 🔄 反馈循环：基于测试结果进行代码优化
- 📊 结果输出：格式化的解决方案展示

## 安装要求

- Python 3.8+
- OpenAI API Key
- 依赖包（见requirements.txt）

## 安装步骤

1. 克隆仓库：
```bash
git clone <repository-url>
cd pocketflow-leetcode/leetcode-agent
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 设置OpenAI API Key：
```bash
export OPENAI_API_KEY="your-api-key-here"
```

## 使用方法

### 基本用法

```bash
python main.py "https://leetcode.com/problems/two-sum/"
```

### 使用问题描述

```bash
python main.py "Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target."
```

### 高级选项

```bash
python main.py "https://leetcode.com/problems/two-sum/" \
    --language python \
    --optimize time \
    --max-iterations 5 \
    --output solution.txt
```

### 命令行参数

- `problem_input`: LeetCode问题URL或问题描述（必需）
- `--language, -l`: 编程语言（默认：python）
  - 可选值：python, java, cpp, javascript
- `--optimize, -o`: 优化目标（默认：time）
  - 可选值：time, space
- `--max-iterations, -m`: 反馈循环最大迭代次数（默认：3）
- `--api-key, -k`: OpenAI API密钥（可选，也可通过环境变量设置）
- `--output, -out`: 输出文件路径（可选）

## 工作流程

1. **用户输入**: 接收LeetCode URL或问题描述
2. **题目解析**: 提取题目信息、约束条件和示例
3. **解法设计**: 生成解题思路和算法设计
4. **代码生成**: 基于设计生成代码实现
5. **测试用例生成**: 创建全面的测试用例
6. **测试运行**: 执行测试并收集结果
7. **反馈循环**: 根据测试结果优化代码（可选）
8. **结果输出**: 格式化并展示最终解决方案

## 示例输出

```
==================================================
SOLUTION RESULT
==================================================
Problem: Two Sum
Difficulty: Easy

Description:
Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.

Solution Approach:
We can solve this problem using a hash map to store the numbers we've seen so far. For each number, we check if its complement (target - current number) exists in the hash map. If it does, we've found our solution.

Algorithm Steps:
1. Create an empty hash map to store number -> index pairs
2. Iterate through the array with index i and value num
3. Calculate complement = target - num
4. If complement exists in the hash map, return [hash_map[complement], i]
5. Otherwise, store num in the hash map with its index
6. If no solution is found, return an empty array

Time Complexity: O(n)
Space Complexity: O(n)

Code (python):
```python
def twoSum(nums, target):
    num_map = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in num_map:
            return [num_map[complement], i]
        num_map[num] = i
    return []
```

Test Results: 5/5 passed
All test cases passed successfully!
```

## 项目结构

```
leetcode-agent/
├── main.py                 # 主程序入口
├── flow.py                 # 工作流程定义
├── nodes/                  # 节点实现
│   ├── __init__.py
│   ├── user_input.py       # 用户输入节点
│   ├── parse_problem.py    # 题目解析节点
│   ├── solution_design.py  # 解法设计节点
│   ├── code_gen.py         # 代码生成节点
│   ├── test_case_gen.py    # 测试用例生成节点
│   ├── test_run.py         # 测试运行节点
│   ├── feedback_loop.py    # 反馈循环节点
│   └── output.py           # 输出节点
├── utils/                  # 工具类
│   ├── __init__.py
│   ├── llm_client.py       # LLM客户端
│   ├── code_executor.py    # 代码执行器
│   └── leetcode_scraper.py # LeetCode爬虫
├── templates/              # 提示模板
│   ├── solution_design.txt
│   ├── code_generation.txt
│   ├── test_generation.txt
│   └── optimization.txt
├── validators/             # 验证器
│   ├── __init__.py
│   ├── problem_validator.py
│   ├── solution_validator.py
│   ├── code_validator.py
│   └── test_validator.py
└── README.md               # 说明文档
```

## 贡献指南

欢迎提交Issue和Pull Request来改进这个项目！

## 许可证

MIT License