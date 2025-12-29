# 导入所有节点
from tracemalloc import start
from Law_RAG_Agent.nodes.chunk_document_node import *
from Law_RAG_Agent.nodes.create_index_node import *
from Law_RAG_Agent.nodes.embed_document_node import *
from Law_RAG_Agent.nodes.embed_query_node import *
from Law_RAG_Agent.nodes.generate_answer_node import *
from Law_RAG_Agent.nodes.retrieval_document_node import *

# 导入工具函数
from Law_RAG_Agent.utils.process_law_data import *
from Law_RAG_Agent.utils.chunk_utils import *
from Law_RAG_Agent.utils.llm_utils import *

# 导入异步流程
import asyncio
from pocketflow import AsyncFlow
import os
import faiss
import pickle

async def create_index_flow(shared):
    # Check if index already exists
    if os.path.exists(shared["index_path"]):
        print(f"📁 Index already exists at {shared['index_path']}, skipping document processing...")
        
        # Load the existing index
        index = faiss.read_index(shared["index_path"])
        shared["index"] = index
        
        # Load the texts from the corresponding file
        texts_path = shared["index_path"].replace('.faiss', '_texts.pkl')
        if os.path.exists(texts_path):
            with open(texts_path, 'rb') as f:
                shared["texts"] = pickle.load(f)
            print(f"✅ Loaded {len(shared['texts'])} texts from {texts_path}")
        else:
            print(f"⚠️ Texts file not found at {texts_path}")
            shared["texts"] = []
            
        print(f"✅ Loaded existing index with {index.ntotal} vectors")
    else:
        print("🔍 Creating new index from documents...")
        chunk_law_documents_node = ChunkLawDocumentsNode()
        # embed_documents_node = EmbedDocumentsNode()
        embed_documents_node = AsyncEmbedDocumentsNode()
        create_index_node = CreateIndexNode()

        chunk_law_documents_node >> embed_documents_node >> create_index_node

        flow = AsyncFlow(start=chunk_law_documents_node)
        await flow.run_async(shared)

    print(shared.keys())

def create_rag_flow(shared):
    query_node = EmbedQueryNode()
    retrieval_node = RetrieveDocumentNode()
    generate_answer_node = GenerateAnswerNode()

    query_node >> retrieval_node >> generate_answer_node
    flow = Flow(start=query_node)
    flow.run(shared)

async def main():
    shared = {
        "json_path": "Law_RAG_Agent/database/laws",
        "index_path": "Law_RAG_Agent/database/index/law_index.faiss",  # Path to save/load the index
    }

    query = "醉酒驾驶的标准是什么？"
    query = "一个女孩今天13岁，和A自愿发生了关系。她明天生日，后天和B发生了关系。请问A和B负法律责任吗？"

    shared["query"] = query


    await create_index_flow(shared)
    create_rag_flow(shared)

if __name__ == "__main__":
    asyncio.run(main())
