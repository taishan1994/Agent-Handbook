# Chapter 14: Knowledge Retrieval (RAG) - PocketFlow实现

本目录包含了使用PocketFlow框架实现的RAG（检索增强生成）系统，基于Chapter 14中描述的知识检索模式。

## 文件结构

- `document_retriever.py`: 文档检索节点实现
  - `DocumentRetriever`: 基于Exa搜索引擎的文档检索
  - `VectorDocumentRetriever`: 基于向量相似度的文档检索

- `response_generator.py`: 响应生成节点实现
  - `ResponseGenerator`: 基础版响应生成器
  - `AgenticResponseGenerator`: 智能版响应生成器，包含文档相关性评估

- `rag_flow.py`: 完整的RAG流程实现
  - `RAGFlow`: 基础RAG流程
  - `AgenticRAGFlow`: 智能RAG流程，包含额外分析和验证步骤

- `rag_example.py`: 示例和测试代码
  - 演示如何使用不同类型的RAG系统
  - 性能比较和交互式测试

## 主要特性

1. **模块化设计**: 检索和生成功能分离为独立节点，便于扩展和替换
2. **多种检索方式**: 支持基于Web搜索和向量相似度的文档检索
3. **智能生成**: 包含文档相关性评估和答案生成优化
4. **PocketFlow集成**: 充分利用PocketFlow的流程编排能力

## 使用方法

### 基础RAG流程

```python
from rag_flow import RAGFlow

# 创建基于Web检索的RAG流程
rag_flow = RAGFlow(retriever_type="web", generator_type="basic")

# 运行查询
result = rag_flow.run("什么是深度学习？")
print(result["response"])
```

### 向量检索RAG流程

```python
from rag_flow import RAGFlow, sample_documents

# 创建基于向量检索的RAG流程
rag_flow = RAGFlow(retriever_type="vector", generator_type="basic")

# 添加文档
rag_flow.add_documents(sample_documents)

# 运行查询
result = rag_flow.run("深度学习与机器学习的关系")
print(result["response"])
```

### 智能RAG流程

```python
from rag_flow import AgenticRAGFlow

# 创建智能RAG流程
agentic_rag = AgenticRAGFlow(retriever_type="vector")
agentic_rag.add_documents(sample_documents)

# 运行查询并获取分析结果
result = agentic_rag.run_with_analysis("深度学习在计算机视觉中的应用")
print(f"分析: {result['analysis']}")
print(f"回答: {result['response']}")
```

## 运行示例

```bash
cd /nfs/FM/gongoubo/new_project/Agent-Handbook/pocketflow-adp/adp/chapter14_rag
python rag_example.py
```

## 依赖项

- PocketFlow框架
- OpenAI API (用于LLM调用)
- Exa搜索API (用于Web检索)
- 向量数据库 (用于向量检索)
- 其他Python标准库

## 注意事项

1. 确保已正确配置API密钥和环境变量
2. 向量检索需要预先添加文档到向量数据库
3. 智能RAG流程可能需要更长的处理时间

## 扩展建议

1. 添加更多检索策略（如混合检索）
2. 实现更复杂的文档相关性评估
3. 添加缓存机制提高性能
4. 支持多模态文档检索和生成