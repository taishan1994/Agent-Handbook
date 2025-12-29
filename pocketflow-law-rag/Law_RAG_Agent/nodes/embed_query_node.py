import numpy as np
from pocketflow import Node, Flow, BatchNode
from Law_RAG_Agent.utils.llm_utils import call_llm, call_embedding 


# Nodes for the online flow
class EmbedQueryNode(Node):
    def prep(self, shared):
        """Get query from shared store"""
        return shared["query"]
    
    def exec(self, query):
        """Embed the query"""
        print(f"🔍 Embedding query: {query}")
        query_embedding = call_embedding(query)
        return query_embedding
    
    def post(self, shared, prep_res, exec_res):
        """Store query embedding in shared store"""
        shared["query_embedding"] = exec_res
        return "default"