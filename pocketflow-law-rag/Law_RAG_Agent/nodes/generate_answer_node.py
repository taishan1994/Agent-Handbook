from pocketflow import Node, Flow, BatchNode
from Law_RAG_Agent.utils.llm_utils import call_llm, call_embedding 


class GenerateAnswerNode(Node):
    def prep(self, shared):
        """Get query, retrieved documents, and any other context needed"""
        return shared["query"], shared["retrieved_documents"]
    
    def exec(self, inputs):
        """Generate an answer using the LLM"""
        query, retrieved_docs = inputs
        
        # Combine the top retrieved documents as context
        context = "\n\n".join([
            f"Document {doc['rank']} (Relevance: {1-doc['distance']:.2f}): {doc['text']}"
            for doc in retrieved_docs
        ])
        
        prompt = f"""
Based on the following legal documents, please answer the question: "{query}"

Relevant Legal Documents:
{context}

Please provide a comprehensive answer based on the legal documents above, citing the most relevant information.
Answer:
"""
        
        answer = call_llm(prompt)
        return answer
    
    def post(self, shared, prep_res, exec_res):
        """Store generated answer in shared store"""
        shared["generated_answer"] = exec_res
        print("\n🤖 Generated Answer:")
        print(exec_res)
        return "default"
