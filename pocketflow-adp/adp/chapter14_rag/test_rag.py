#!/usr/bin/env python3
"""
简单的RAG测试
"""

import sys
sys.path.append('/nfs/FM/gongoubo/new_project/Agent-Handbook/pocketflow-adp')
from rag_flow import RAGFlow, sample_documents

def test_rag():
    print('创建RAG流程...')
    rag_flow = RAGFlow(retriever_type='vector', generator_type='basic')
    
    print('添加文档...')
    rag_flow.add_documents(sample_documents)
    
    print('运行查询...')
    result = rag_flow.run('什么是人工智能？')
    
    print('完成！')
    print('检索到文档数:', len(result['retrieved_documents']))
    print('响应长度:', len(result['response']))
    print('响应内容:', result['response'][:200] + '...' if len(result['response']) > 200 else result['response'])

if __name__ == "__main__":
    test_rag()