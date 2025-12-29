from pocketflow import Node, Flow, BatchNode
from pathlib import Path
import json
from Law_RAG_Agent.utils.chunk_utils import fixed_size_chunk

# Nodes for the offline flow
class ChunkDocumentsNode(BatchNode):
    def prep(self, shared):
        """Read texts from shared store"""
        return shared["texts"]
    
    def exec(self, text):
        """Chunk a single text into smaller pieces"""
        return fixed_size_chunk(text)
    
    def post(self, shared, prep_res, exec_res_list):
        """Store chunked texts in the shared store"""
        # Flatten the list of lists into a single list of chunks
        all_chunks = []
        for chunks in exec_res_list:
            all_chunks.extend(chunks)
        
        # Replace the original texts with the flat list of chunks
        shared["texts"] = all_chunks
        
        print(f"✅ Created {len(all_chunks)} chunks from {len(prep_res)} files")
        return "default"

class ChunkLawDocumentsNode(BatchNode):
    def prep(self, shared):
        """Read texts from shared store"""
        json_path = Path(shared["json_path"])
        files = list(json_path.glob("*.json"))

        print("files：", files)
        return files
    
    def exec(self, file):
        """Process a single JSON file and extract law contents"""
        # 框架内部传过来的是一个file
        chunks = []
        with open(file, "r") as f:
            data = json.load(f)
            for law_name, contents in data.items():
                for zhangjie, contents_tmp in contents.items():
                    for tiaoli, final_content in contents_tmp.items():
                        # Create a chunk for each law article
                        # chunk = {
                        #     "law_name": law_name,
                        #     "chapter": zhangjie,
                        #     "article": tiaoli,
                        #     "content": final_content
                        # }
                        chunk = law_name + "\t" + zhangjie + "\t" + tiaoli + "\t" + final_content
                        chunks.append(chunk)
                        # print(law_name, zhangjie, tiaoli, final_content)
        return chunks
    
    def post(self, shared, prep_res, exec_res_list):
        """Store chunked texts in the shared store"""
        # Flatten the list of lists into a single list of chunks    
        # Replace the original texts with the flat list of chunks
        all_chunks = []
        for chunks in exec_res_list:
            all_chunks.extend(chunks)
        
        # all_chunks = all_chunks[:1000]
        shared["texts"] = all_chunks
        print(f"✅ Created {len(all_chunks)} chunks from {len(prep_res)} documents")
        return "default"
    
    