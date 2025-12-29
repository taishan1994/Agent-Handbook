from pocketflow import Node, Flow, BatchNode
import faiss
import os
import numpy as np
import pickle

class CreateIndexNode(Node):
    def prep(self, shared):
        """Get embeddings from shared store and check if index path exists"""
        embeddings = shared["embeddings"]
        
        # Check if index path is provided in shared
        index_path = shared.get("index_path", None)
        
        print("embeddings shape:", embeddings.shape)

        return {
            "embeddings": embeddings,
            "index_path": index_path
        }
    
    def exec(self, inputs):
        """Load existing index if path exists, otherwise create new FAISS index"""
        embeddings = inputs["embeddings"]
        index_path = inputs["index_path"]
        
        # If index path exists and file exists, load the index
        if index_path and os.path.exists(index_path):
            print(f"📁 Loading existing index from {index_path}...")
            try:
                index = faiss.read_index(index_path)
                print(f"✅ Loaded index with {index.ntotal} vectors")
                return index
            except Exception as e:
                print(f"⚠️ Failed to load index: {e}. Creating new index...")
        
        # Create a new index
        print("🔍 Creating search index...")
        print(embeddings.shape)

        dimension = embeddings.shape[1]
        
        # Create a flat L2 index
        index = faiss.IndexFlatL2(dimension)
        
        # Add the embeddings to the index
        index.add(embeddings)
        
        return index
    
    def post(self, shared, prep_res, exec_res):
        """Store the index in shared store and save to disk if path is provided"""
        shared["index"] = exec_res
        
        # Save index to disk if path is provided
        index_path = shared.get("index_path", None)
        if index_path and not os.path.exists(index_path):
            print(f"💾 Saving index to {index_path}...")
            try:
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(index_path), exist_ok=True)
                faiss.write_index(exec_res, index_path)
                print(f"✅ Index saved to {index_path}")
                
                # Also save the texts to a corresponding file
                texts_path = index_path.replace('.faiss', '_texts.pkl')
                with open(texts_path, 'wb') as f:
                    pickle.dump(shared["texts"], f)
                print(f"✅ Texts saved to {texts_path}")
            except Exception as e:
                print(f"⚠️ Failed to save index or texts: {e}")
        
        print(f"✅ Index ready with {exec_res.ntotal} vectors")
        return "default"