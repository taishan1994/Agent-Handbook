from pocketflow import Node, Flow, BatchNode, AsyncBatchNode
import numpy as np
import asyncio
from tqdm import tqdm
from Law_RAG_Agent.utils.llm_utils import call_llm, call_embedding 

class EmbedDocumentsNode(BatchNode):
    def prep(self, shared):
        """Read texts from shared store and return as an iterable with indices"""
        texts = shared["texts"]
        # Return list of (index, text) tuples to maintain order
        return [(i, text) for i, text in enumerate(texts)]
    
    def exec(self, item):
        """Embed a single text"""
        index, text = item
        embedding = call_embedding(text)
        return (index, embedding)
    
    def post(self, shared, prep_res, exec_res_list):
        """Store embeddings in the shared store in the correct order"""
        # Sort by original index to maintain order
        exec_res_list.sort(key=lambda x: x[0])
        
        # Extract embeddings in the correct order
        embeddings = np.array([item[1] for item in exec_res_list], dtype=np.float32)
        shared["embeddings"] = embeddings
        print(f"✅ Created {len(embeddings)} document embeddings")
        return "default"
    
    def exec_batch(self, batch):
        """Override exec_batch to show progress bar"""
        results = []
        # Create progress bar
        pbar = tqdm(batch, desc="Embedding documents", unit="doc")
        for item in pbar:
            result = self.exec(item)
            results.append(result)
            # Update progress bar description with current count
            pbar.set_postfix({"completed": f"{len(results)}/{len(batch)}"})
        pbar.close()
        return results


class AsyncEmbedDocumentsNode(AsyncBatchNode):
    """Async version of EmbedDocumentsNode for parallel processing of embeddings"""
    
    async def prep_async(self, shared):
        """Read texts from shared store and return as an iterable with indices"""
        texts = shared["texts"]
        # Return list of (index, text) tuples to maintain order
        return [(i, text) for i, text in enumerate(texts)]
    
    async def exec_async(self, item):
        """Embed a single text asynchronously"""
        index, text = item
        # Run the synchronous call_embedding in an executor to avoid blocking
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(None, call_embedding, text)
        return (index, embedding)
    
    async def post_async(self, shared, prep_res, exec_res_list):
        """Store embeddings in the shared store in the correct order"""
        # Sort by original index to maintain order
        exec_res_list.sort(key=lambda x: x[0])
        
        # Extract embeddings in the correct order
        embeddings = np.array([item[1] for item in exec_res_list], dtype=np.float32)
        embeddings = embeddings.reshape(-1, embeddings.shape[-1])
        shared["embeddings"] = embeddings
        print(f"✅ Created {len(embeddings)} document embeddings asynchronously")
        return "default"
    
    async def _exec(self, items):
        """Override _exec to show progress bar during async processing"""
        results = []
        # Create progress bar
        pbar = tqdm(items, desc="Embedding documents (async)", unit="doc")
        
        # Process items one by one to update progress bar
        for item in pbar:
            result = await self.exec_async(item)
            results.append(result)
            # Update progress bar description with current count
            pbar.set_postfix({"completed": f"{len(results)}/{len(items)}"})
        
        pbar.close()
        return results