#!/usr/bin/env python3
"""
RAG系统示例和测试代码
演示如何使用基于PocketFlow的RAG系统
"""

import os
import sys
import time

# 添加上级目录到路径，以便导入相关模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from rag_flow import RAGFlow, AgenticRAGFlow, sample_documents

def test_web_rag():
    """测试基于Web检索的RAG系统"""
    print("=" * 50)
    print("测试基于Web检索的RAG系统")
    print("=" * 50)
    
    # 创建基于Web检索的RAG流程
    rag_flow = RAGFlow(retriever_type="web", generator_type="basic")
    
    # 测试查询
    queries = [
        "什么是深度学习？",
        "人工智能的应用领域有哪些？",
        "机器学习的主要算法类型"
    ]
    
    for query in queries:
        print(f"\n查询: {query}")
        print("-" * 40)
        
        start_time = time.time()
        result = rag_flow.run(query)
        end_time = time.time()
        
        print(f"检索到 {len(result['retrieved_documents'])} 个文档")
        print(f"回答: {result['response']}")
        print(f"耗时: {end_time - start_time:.2f}秒")


def test_vector_rag():
    """测试基于向量检索的RAG系统"""
    print("\n" + "=" * 50)
    print("测试基于向量检索的RAG系统")
    print("=" * 50)
    
    # 创建基于向量检索的RAG流程
    rag_flow = RAGFlow(retriever_type="vector", generator_type="basic")
    
    # 添加示例文档
    print("添加示例文档到向量数据库...")
    rag_flow.add_documents(sample_documents)
    print(f"已添加 {len(sample_documents)} 个文档")
    
    # 测试查询
    queries = [
        "什么是人工智能？",
        "深度学习与机器学习的关系",
        "自然语言处理的应用"
    ]
    
    for query in queries:
        print(f"\n查询: {query}")
        print("-" * 40)
        
        start_time = time.time()
        result = rag_flow.run(query)
        end_time = time.time()
        
        print(f"检索到 {len(result['retrieved_documents'])} 个文档")
        print(f"回答: {result['response']}")
        print(f"耗时: {end_time - start_time:.2f}秒")


def test_agentic_rag():
    """测试智能RAG系统"""
    print("\n" + "=" * 50)
    print("测试智能RAG系统")
    print("=" * 50)
    
    # 创建智能RAG流程
    agentic_rag = AgenticRAGFlow(retriever_type="vector")
    
    # 添加示例文档
    print("添加示例文档到向量数据库...")
    agentic_rag.add_documents(sample_documents)
    print(f"已添加 {len(sample_documents)} 个文档")
    
    # 测试查询
    queries = [
        "深度学习在计算机视觉中的应用",
        "机器学习算法的分类",
        "自然语言处理的发展历程"
    ]
    
    for query in queries:
        print(f"\n查询: {query}")
        print("-" * 40)
        
        start_time = time.time()
        result = agentic_rag.run_with_analysis(query)
        end_time = time.time()
        
        print(f"检索到 {len(result['retrieved_documents'])} 个文档")
        print(f"分析: {result.get('analysis', '')}")
        print(f"回答: {result['response']}")
        print(f"耗时: {end_time - start_time:.2f}秒")


def test_comparison():
    """比较不同RAG系统的性能"""
    print("\n" + "=" * 50)
    print("比较不同RAG系统的性能")
    print("=" * 50)
    
    # 测试查询
    query = "什么是深度学习？"
    
    # 1. 基于Web检索的RAG
    print("\n1. 基于Web检索的RAG:")
    web_rag = RAGFlow(retriever_type="web", generator_type="basic")
    start_time = time.time()
    web_result = web_rag.run(query)
    web_time = time.time() - start_time
    print(f"   耗时: {web_time:.2f}秒")
    print(f"   检索文档数: {len(web_result['retrieved_documents'])}")
    print(f"   回答长度: {len(web_result['response'])}字符")
    
    # 2. 基于向量检索的RAG
    print("\n2. 基于向量检索的RAG:")
    vector_rag = RAGFlow(retriever_type="vector", generator_type="basic")
    vector_rag.add_documents(sample_documents)
    start_time = time.time()
    vector_result = vector_rag.run(query)
    vector_time = time.time() - start_time
    print(f"   耗时: {vector_time:.2f}秒")
    print(f"   检索文档数: {len(vector_result['retrieved_documents'])}")
    print(f"   回答长度: {len(vector_result['response'])}字符")
    
    # 3. 智能RAG
    print("\n3. 智能RAG:")
    agentic_rag = AgenticRAGFlow(retriever_type="vector")
    agentic_rag.add_documents(sample_documents)
    start_time = time.time()
    agentic_result = agentic_rag.run_with_analysis(query)
    agentic_time = time.time() - start_time
    print(f"   耗时: {agentic_time:.2f}秒")
    print(f"   检索文档数: {len(agentic_result['retrieved_documents'])}")
    print(f"   回答长度: {len(agentic_result['response'])}字符")
    print(f"   分析长度: {len(agentic_result.get('analysis', ''))}字符")


def interactive_test():
    """交互式测试"""
    print("\n" + "=" * 50)
    print("交互式RAG测试")
    print("=" * 50)
    print("请选择RAG类型:")
    print("1. 基于Web检索的RAG")
    print("2. 基于向量检索的RAG")
    print("3. 智能RAG")
    
    choice = input("请输入选择(1-3): ").strip()
    
    if choice == "1":
        rag = RAGFlow(retriever_type="web", generator_type="basic")
    elif choice == "2":
        rag = RAGFlow(retriever_type="vector", generator_type="basic")
        rag.add_documents(sample_documents)
    elif choice == "3":
        rag = AgenticRAGFlow(retriever_type="vector")
        rag.add_documents(sample_documents)
    else:
        print("无效选择，使用默认的Web检索RAG")
        rag = RAGFlow(retriever_type="web", generator_type="basic")
    
    while True:
        query = input("\n请输入查询(输入'退出'结束): ").strip()
        if query.lower() in ["退出", "exit", "quit"]:
            break
        
        print("正在处理查询...")
        start_time = time.time()
        if choice == "3":
            result = rag.run_with_analysis(query)
            print(f"分析: {result.get('analysis', '')}")
        else:
            result = rag.run(query)
        end_time = time.time()
        
        print(f"回答: {result['response']}")
        print(f"耗时: {end_time - start_time:.2f}秒")


if __name__ == "__main__":
    print("RAG系统示例和测试")
    print("1. 测试基于Web检索的RAG系统")
    print("2. 测试基于向量检索的RAG系统")
    print("3. 测试智能RAG系统")
    print("4. 比较不同RAG系统")
    print("5. 交互式测试")
    
    choice = input("请选择测试类型(1-5): ").strip()
    
    if choice == "1":
        test_web_rag()
    elif choice == "2":
        test_vector_rag()
    elif choice == "3":
        test_agentic_rag()
    elif choice == "4":
        test_comparison()
    elif choice == "5":
        interactive_test()
    else:
        print("运行所有测试...")
        test_web_rag()
        test_vector_rag()
        test_agentic_rag()
        test_comparison()
    
    print("\n测试完成!")