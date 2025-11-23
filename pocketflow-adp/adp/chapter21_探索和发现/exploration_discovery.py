#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chapter 21: 探索和发现 (Exploration and Discovery)

使用PocketFlow框架实现多智能体系统，用于自动化科学研究和数据准备
包含ReviewersAgent实现三方Agentic判断机制，以及多个专业Agent协同工作
"""

import asyncio
import os
import sys
import json
from typing import Dict, List, Optional, Any

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
# 添加PocketFlow目录到Python路径
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'PocketFlow'))

from pocketflow import Node, Flow

# 导入工具函数
if os.path.exists(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'utils', 'utils.py')):
    from utils.utils import call_llm, call_llm_async, search_web_exa
else:
    # 如果utils包不存在，提供模拟函数
    def call_llm(prompt, model="gpt-4"):
        """模拟LLM调用函数"""
        print(f"[模拟LLM调用]\n{prompt}\n")
        return f"模拟响应: 已处理提示词，长度为{len(prompt)}字符"
    
    async def call_llm_async(prompt, model="gpt-4"):
        """模拟异步LLM调用函数"""
        print(f"[模拟异步LLM调用]\n{prompt}\n")
        await asyncio.sleep(1)
        return f"模拟异步响应: 已处理提示词，长度为{len(prompt)}字符"
    
    def search_web_exa(query):
        """模拟网络搜索函数"""
        print(f"[模拟网络搜索]\n{query}\n")
        return [f"搜索结果 {i+1}: 关于'{query}'的相关信息" for i in range(3)]

# 定义研究审查节点
class ReviewersNode(Node):
    """研究审查节点，实现三方专家评审机制"""
    def __init__(self, name="reviewers_node"):
        super().__init__(name)
        self.reviewers = ["学术专家", "行业专家", "方法学专家"]
    
    def prep(self, shared):
        """准备阶段：获取研究主题和已有的研究方向"""
        return {
            "research_topic": shared.get("research_topic", ""),
            "existing_directions": shared.get("existing_directions", [])
        }
    
    def exec(self, inputs):
        """执行阶段：进行三方评审"""
        research_topic = inputs["research_topic"]
        existing_directions = inputs["existing_directions"]
        
        reviews = []
        # 为每个评审专家生成评审意见
        for reviewer in self.reviewers:
            prompt = f"作为{reviewer}，请对'{research_topic}'研究主题进行评估和建议。\n"
            if existing_directions:
                prompt += f"当前研究方向包括：{', '.join(existing_directions)}\n"
            prompt += "请提供：1) 对研究主题的评价，2) 潜在的研究价值，3) 可能的创新点，4) 实施建议"
            
            review = call_llm(prompt)
            reviews.append({
                "reviewer": reviewer,
                "content": review
            })
        
        # 综合三方意见
        synthesis_prompt = f"请综合以下三位专家对'{research_topic}'的评审意见，形成最终的研究建议：\n\n"
        for review in reviews:
            synthesis_prompt += f"[{review['reviewer']}]\n{review['content']}\n\n"
        
        final_recommendation = call_llm(synthesis_prompt)
        
        return {
            "individual_reviews": reviews,
            "final_recommendation": final_recommendation
        }
    
    def post(self, shared, prep_res, exec_res):
        """后处理阶段：将评审结果存入共享状态"""
        shared["review_results"] = exec_res
        shared["research_recommendations"] = exec_res["final_recommendation"]
        return shared

# 定义教授节点（研究设计）
class ProfessorNode(Node):
    """教授节点，负责研究设计和方法论指导"""
    def __init__(self, name="professor_node"):
        super().__init__(name)
    
    def prep(self, shared):
        """准备阶段：获取研究主题和评审建议"""
        return {
            "research_topic": shared.get("research_topic", ""),
            "research_recommendations": shared.get("research_recommendations", "")
        }
    
    def exec(self, inputs):
        """执行阶段：设计研究方案"""
        research_topic = inputs["research_topic"]
        research_recommendations = inputs["research_recommendations"]
        
        # 设计研究方法
        method_prompt = f"作为研究方法学专家，请基于以下信息设计'{research_topic}'的详细研究方案：\n\n"
        method_prompt += f"专家评审建议：{research_recommendations}\n\n"
        method_prompt += "请提供：1) 研究问题和假设，2) 研究方法和步骤，3) 数据收集和分析计划，4) 预期成果"
        
        research_methodology = call_llm(method_prompt)
        
        # 生成README文件内容
        readme_prompt = f"基于以下研究方案，创建一个详细的README.md文件：\n\n"
        readme_prompt += f"研究主题：{research_topic}\n"
        readme_prompt += f"研究方案：{research_methodology}\n\n"
        readme_prompt += "README应包括：项目背景、研究目标、方法学、实施步骤、预期成果、参考文献"
        
        readme = call_llm(readme_prompt)
        
        return {
            "research_methodology": research_methodology,
            "readme": readme
        }
    
    def post(self, shared, prep_res, exec_res):
        """后处理阶段：将研究设计结果存入共享状态"""
        shared["research_methodology"] = exec_res["research_methodology"]
        shared["readme"] = exec_res["readme"]
        return shared

# 定义博士后节点（文献综述）
class PostdocNode(Node):
    """博士后节点，负责文献综述和背景研究"""
    def __init__(self, name="postdoc_node"):
        super().__init__(name)
    
    def prep(self, shared):
        """准备阶段：获取研究主题"""
        return {
            "research_topic": shared.get("research_topic", "")
        }
    
    async def exec(self, inputs):
        """执行阶段：进行文献综述"""
        research_topic = inputs["research_topic"]
        
        # 网络搜索相关文献和研究
        # 确保search_web_exa是同步调用，不是异步的
        search_results = search_web_exa(f"最新研究 {research_topic} 学术文献 综述")
        
        # 异步分析每篇文献
        async def analyze_paper(paper_info):
            prompt = f"请分析以下研究信息，并提取关键发现、方法和与'{research_topic}'的相关性：\n{paper_info}"
            return await call_llm_async(prompt)
        
        # 确保search_results是可迭代对象
        if asyncio.iscoroutine(search_results):
            search_results = await search_results
        
        paper_analyses = await asyncio.gather(
            *[analyze_paper(result) for result in search_results]
        )
        
        # 生成综合文献综述
        literature_review_prompt = f"请基于以下文献分析，为'{research_topic}'生成一份全面的文献综述：\n\n"
        for i, analysis in enumerate(paper_analyses):
            literature_review_prompt += f"文献{i+1}分析：\n{analysis}\n\n"
        
        literature_review_prompt += "请包括：研究现状总结、主要研究流派、关键发现、研究空白、未来方向"
        literature_review = await call_llm_async(literature_review_prompt)
        
        return {
            "search_results": search_results,
            "paper_analyses": paper_analyses,
            "literature_review": literature_review
        }
    
    def post(self, shared, prep_res, exec_res):
        """后处理阶段：将文献综述结果存入共享状态"""
        shared["literature_review"] = exec_res["literature_review"]
        shared["search_results"] = exec_res["search_results"]
        return shared

# 定义机器学习工程师节点（数据准备）
class MLEngineerNode(Node):
    """机器学习工程师节点，负责数据准备和模型设计"""
    def __init__(self, name="ml_engineer_node"):
        super().__init__(name)
    
    def prep(self, shared):
        """准备阶段：获取研究主题和README"""
        return {
            "research_topic": shared.get("research_topic", ""),
            "readme": shared.get("readme", "")
        }
    
    def exec(self, inputs):
        """执行阶段：设计数据准备方案"""
        research_topic = inputs["research_topic"]
        readme = inputs["readme"]
        
        # 获取README首行作为项目标题
        readme_first_line = readme.split('\n')[0] if readme else ""
        
        # 设计数据准备方案
        data_prompt = f"为'{research_topic}'研究项目准备数据，支持{readme_first_line}\n\n"
        data_prompt += "请提供：1) 所需数据类型和来源，2) 数据收集策略，3) 数据预处理步骤，4) 数据质量评估方法"
        
        data_solution = call_llm(data_prompt)
        
        # 设计模型架构（如果适用）
        model_prompt = f"为'{research_topic}'研究项目设计适当的机器学习模型架构（如适用）：\n\n"
        model_prompt += f"数据需求：{data_solution}\n\n"
        model_prompt += "请提供：1) 适合的模型类型，2) 模型架构设计，3) 训练策略，4) 评估指标"
        
        model_architecture = call_llm(model_prompt)
        
        return {
            "data_solution": data_solution,
            "model_architecture": model_architecture
        }
    
    def post(self, shared, prep_res, exec_res):
        """后处理阶段：将数据准备结果存入共享状态"""
        shared["data_solution"] = exec_res["data_solution"]
        shared["model_architecture"] = exec_res["model_architecture"]
        return shared

# 定义软件工程师节点（实现优化）
class SoftwareEngineerNode(Node):
    """软件工程师节点，负责实现代码和优化"""
    def __init__(self, name="software_engineer_node"):
        super().__init__(name)
    
    def prep(self, shared):
        """准备阶段：获取所有必要信息"""
        return {
            "research_topic": shared.get("research_topic", ""),
            "research_methodology": shared.get("research_methodology", ""),
            "data_solution": shared.get("data_solution", ""),
            "model_architecture": shared.get("model_architecture", "")
        }
    
    def exec(self, inputs):
        """执行阶段：生成实现代码"""
        research_topic = inputs["research_topic"]
        research_methodology = inputs["research_methodology"]
        data_solution = inputs["data_solution"]
        model_architecture = inputs["model_architecture"]
        
        # 生成实现代码
        code_prompt = f"为'{research_topic}'研究项目生成实现代码：\n\n"
        code_prompt += f"研究方法：{research_methodology}\n"
        code_prompt += f"数据解决方案：{data_solution}\n"
        code_prompt += f"模型架构：{model_architecture}\n\n"
        code_prompt += "请提供完整的Python代码，包括数据加载、预处理、模型定义、训练和评估功能。代码应具有良好的可维护性和可扩展性。"
        
        implementation_code = call_llm(code_prompt)
        
        # 生成优化建议
        optimization_prompt = f"为以下代码提供性能优化建议：\n\n{implementation_code}\n\n"
        optimization_prompt += "请考虑：1) 算法优化，2) 并行计算，3) 内存使用，4) 代码结构改进"
        
        optimization_suggestions = call_llm(optimization_prompt)
        
        return {
            "implementation_code": implementation_code,
            "optimization_suggestions": optimization_suggestions
        }
    
    def post(self, shared, prep_res, exec_res):
        """后处理阶段：将实现结果存入共享状态"""
        shared["implementation_code"] = exec_res["implementation_code"]
        shared["optimization_suggestions"] = exec_res["optimization_suggestions"]
        return shared

# 创建研究探索流水线
class ResearchExplorationFlow:
    """研究探索流水线，整合所有节点"""
    def __init__(self, name="research_exploration_flow"):
        self.name = name
        
        # 创建各个节点
        self.reviewers_node = ReviewersNode()
        self.professor_node = ProfessorNode()
        self.postdoc_node = PostdocNode()
        self.ml_engineer_node = MLEngineerNode()
        self.software_engineer_node = SoftwareEngineerNode()
    
    async def run(self, initial_state):
        """运行整个研究探索流程"""
        # 初始化共享状态
        shared_state = initial_state.copy()
        
        # 运行评审节点
        prep_data = self.reviewers_node.prep(shared_state)
        exec_result = self.reviewers_node.exec(prep_data) if not asyncio.iscoroutinefunction(self.reviewers_node.exec) else await self.reviewers_node.exec(prep_data)
        shared_state = self.reviewers_node.post(shared_state, prep_data, exec_result)
        
        # 并行运行教授节点和博士后节点
        async def process_node(node, state):
            prep_data = node.prep(state)
            exec_result = node.exec(prep_data) if not asyncio.iscoroutinefunction(node.exec) else await node.exec(prep_data)
            return node.post(state, prep_data, exec_result)
        
        professor_state, postdoc_state = await asyncio.gather(
            process_node(self.professor_node, shared_state.copy()),
            process_node(self.postdoc_node, shared_state.copy())
        )
        
        # 合并结果
        shared_state.update(professor_state)
        shared_state.update(postdoc_state)
        
        # 运行机器学习工程师节点
        ml_prep = self.ml_engineer_node.prep(shared_state)
        ml_exec = self.ml_engineer_node.exec(ml_prep) if not asyncio.iscoroutinefunction(self.ml_engineer_node.exec) else await self.ml_engineer_node.exec(ml_prep)
        shared_state = self.ml_engineer_node.post(shared_state, ml_prep, ml_exec)
        
        # 运行软件工程师节点
        se_prep = self.software_engineer_node.prep(shared_state)
        se_exec = self.software_engineer_node.exec(se_prep) if not asyncio.iscoroutinefunction(self.software_engineer_node.exec) else await self.software_engineer_node.exec(se_prep)
        shared_state = self.software_engineer_node.post(shared_state, se_prep, se_exec)
        
        return shared_state

# 保存结果到文件
async def save_results(results, output_dir="research_results"):
    """保存研究结果到文件"""
    # 创建输出目录
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 保存README
    with open(os.path.join(output_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write(results.get("readme", "# 研究项目README"))
    
    # 保存评审结果
    with open(os.path.join(output_dir, "review_results.json"), "w", encoding="utf-8") as f:
        json.dump(results.get("review_results", {}), f, ensure_ascii=False, indent=2)
    
    # 保存文献综述
    with open(os.path.join(output_dir, "literature_review.md"), "w", encoding="utf-8") as f:
        f.write(results.get("literature_review", "# 文献综述"))
    
    # 保存数据解决方案
    with open(os.path.join(output_dir, "data_solution.md"), "w", encoding="utf-8") as f:
        f.write(results.get("data_solution", "# 数据解决方案"))
    
    # 保存模型架构
    with open(os.path.join(output_dir, "model_architecture.md"), "w", encoding="utf-8") as f:
        f.write(results.get("model_architecture", "# 模型架构"))
    
    # 保存实现代码
    with open(os.path.join(output_dir, "implementation.py"), "w", encoding="utf-8") as f:
        f.write(results.get("implementation_code", "# 实现代码"))
    
    # 保存优化建议
    with open(os.path.join(output_dir, "optimization_suggestions.md"), "w", encoding="utf-8") as f:
        f.write(results.get("optimization_suggestions", "# 优化建议"))
    
    print(f"所有结果已保存到 {output_dir} 目录")

# 示例运行
async def main():
    # 定义研究主题
    research_topic = "大语言模型在科学研究中的应用与局限"
    
    # 初始状态
    initial_state = {
        "research_topic": research_topic,
        "existing_directions": ["自动化文献分析", "实验设计辅助", "数据分析与可视化"]
    }
    
    # 创建并运行研究探索流水线
    flow = ResearchExplorationFlow()
    print(f"开始研究探索流程: {research_topic}")
    
    # 运行流水线
    results = await flow.run(initial_state)
    
    # 打印结果摘要
    print("\n研究探索流程完成！")
    print(f"研究主题: {results.get('research_topic', '')}")
    print(f"评审结果: {len(results.get('review_results', {}).get('individual_reviews', []))} 位专家评审完成")
    print(f"文献综述: 已生成")
    print(f"数据解决方案: 已生成")
    print(f"模型架构: 已生成")
    print(f"实现代码: 已生成")
    print(f"优化建议: 已生成")
    
    # 保存结果
    await save_results(results)

# 运行主函数
if __name__ == "__main__":
    asyncio.run(main())