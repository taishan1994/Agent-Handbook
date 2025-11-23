#!/usr/bin/env python3
"""
智能RAG测试
"""

import sys
sys.path.append('/nfs/FM/gongoubo/new_project/Agent-Handbook/pocketflow-adp')
from rag_flow import AgenticRAGFlow, sample_documents

def test_agentic_rag():
    print('创建智能RAG流程...')
    agentic_rag = AgenticRAGFlow(retriever_type='vector')
    
    print('添加文档...')
    agentic_rag.add_documents(sample_documents)
    
    print('运行查询...')
    result = agentic_rag.run_with_analysis('深度学习与机器学习的关系')
    
    print('完成！')
    print('检索到文档数:', len(result['retrieved_documents']))
    print('分析长度:', len(result.get('analysis', '')))
    print('响应长度:', len(result['response']))
    print('响应内容:', result['response'][:200] + '...' if len(result['response']) > 200 else result['response'])

if __name__ == "__main__":
    test_agentic_rag()