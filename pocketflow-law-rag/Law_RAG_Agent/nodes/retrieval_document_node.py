from pocketflow import Node, Flow, BatchNode
from Law_RAG_Agent.utils.llm_utils import call_llm, call_embedding 

class RetrieveDocumentNode(Node):
    def prep(self, shared):
        """Get query embedding, index, and texts from shared store"""
        return shared["query_embedding"], shared["index"], shared["texts"]
    
    def exec(self, inputs):
        """Search the index for similar documents"""
        print("🔎 Searching for relevant documents...")
        query_embedding, index, texts = inputs

        print(query_embedding.shape)
        
        # Search for top 10 most similar documents
        distances, indices = index.search(query_embedding, k=10)
        
        # Get the indices and distances of the top 10 documents
        top_indices = indices[0]
        top_distances = distances[0]
        
        # Get the corresponding texts
        retrieved_docs = []
        for i, (idx, distance) in enumerate(zip(top_indices, top_distances)):
            retrieved_docs.append({
                "text": texts[idx],
                "index": idx,
                "distance": distance,
                "rank": i + 1
            })
        
        return retrieved_docs
    
    def post(self, shared, prep_res, exec_res):
        """Store retrieved documents in shared store"""
        shared["retrieved_documents"] = exec_res
        print(f"📄 Retrieved {len(exec_res)} relevant documents:")
        for doc in exec_res:
            print(f"  Rank {doc['rank']}: (index: {doc['index']}, distance: {doc['distance']:.4f})")
            print(f"  Text: \"{doc['text'][:100]}{'...' if len(doc['text']) > 100 else ''}\"")
        return "default"