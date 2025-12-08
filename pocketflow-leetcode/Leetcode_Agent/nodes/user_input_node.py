"""
User Input Node for LeetCode Agent

This node handles user input, including problem URLs or direct problem descriptions.
"""
from typing import Dict, Any, Optional

from pocketflow import Node
from Leetcode_Agent.utils.logger import get_logger
from Leetcode_Agent.utils.leetcode_scraper import LeetCodeAPI

class UserInputNode(Node):
    """
    Node for handling user input.
    """
    
    def __init__(self, llm_client=None):
        """
        Initialize the UserInputNode.
        
        Args:
            llm_client: LLM client instance (not used in this node)
        """
        super().__init__()
        self.llm_client = llm_client
        self.leetcode_api = LeetCodeAPI(cookie="aliyungf_tc=b661ee8dba2eed7d24bbdca13c2ff05c3ac01550ae1bcf0136f23bdd5888949c; sl-session=evKXDk+nMmnCJgYELzPXKg==; csrftoken=JAhWyIhlyk3mrsZkTY6WOo6APrNMXMja; gr_user_id=398e40e9-0a2f-4bfa-9a65-cd03a57e4588; Hm_lvt_f0faad39bcf8471e3ab3ef70125152c3=1764840915; HMACCOUNT=0567C89CFD22D8D2; a2873925c34ecbd2_gr_last_sent_cs1=bo-er; _gid=GA1.2.1949930630.1764840931; tfstk=gK9IF6DGzy4IiQOAOToaGKzxIl6S0ckqRusJm3eU29BKV8T2Dp7ErDA1PF_ixpuhL8dWm3bdU9JEFQ_Op_AFzw75F3Yjbqkq3HxhEO3quxuoiC5hnzedvzSTBiW5vhPaSGxhET3NN9Q7lHYFVprFeTn1Bgs4yTe8pcNOxNed2JI8WcslWTIL9WBOBgI4e7QJyhn1qNQReTLRBcslWaBRebYQcgGC-HicJfXYnuo-5Ne8edsC6f-dWb86BM9hlHpQe8nAA6_vvNgI96UO63fWEu25NHdDriLLJ4_kChppME3aTwdfVnRWvveOLpxpM_pxr7KhLw69pIZ8eh6CyEShGyg1kpx9nOCZHmt9Ie-HC3r-eG8VWHvdFxncd9QdCGvrSJQW6QpFtT4KPav6Xpd54CwVll6UNl10FG_qfcNuZz6vG4zs6C3F9GjC_ci_JQfdjG_qfcNuZ6IGAiosfydl.; a2873925c34ecbd2_gr_session_id=538c8bf4-f000-4143-be44-6e714019c4e6; a2873925c34ecbd2_gr_last_sent_sid_with_cs1=538c8bf4-f000-4143-be44-6e714019c4e6; a2873925c34ecbd2_gr_session_id_sent_vst=538c8bf4-f000-4143-be44-6e714019c4e6; LEETCODE_SESSION=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuZXh0X2FmdGVyX29hdXRoIjoiLyIsIl9hdXRoX3VzZXJfaWQiOiIyNjA1NTYiLCJfYXV0aF91c2VyX2JhY2tlbmQiOiJkamFuZ28uY29udHJpYi5hdXRoLmJhY2tlbmRzLk1vZGVsQmFja2VuZCIsIl9hdXRoX3VzZXJfaGFzaCI6ImRmN2RjMWFkZGJkMGM0ZTE3ZjVmNTVkOTc2NzUyYTYxMDlmMmEyZmRmNzhkODJiOWE2ZDcwYzBlZDVjMWVlODAiLCJpZCI6MjYwNTU2LCJlbWFpbCI6IjQ2MTYwMDM3MUBxcS5jb20iLCJ1c2VybmFtZSI6ImJvLWVyIiwidXNlcl9zbHVnIjoiYm8tZXIiLCJhdmF0YXIiOiJodHRwczovL2Fzc2V0cy5sZWV0Y29kZS5jbi9hbGl5dW4tbGMtdXBsb2FkL3VzZXJzL2JvLWVyL2F2YXRhcl8xNTQwODg1MjA0LnBuZyIsInBob25lX3ZlcmlmaWVkIjp0cnVlLCJpcCI6IjU4LjI1MC4yNTAuMjQiLCJfdGltZXN0YW1wIjoxNzY0ODQwOTI3LjY5NTE2NDQsImV4cGlyZWRfdGltZV8iOjE3NjczODA0MDAsInZlcnNpb25fa2V5XyI6MCwiZGV2aWNlX2lkIjoiNGEzMzQyMGYyZDBjMGZmMGExMDljZGUwYTc2ZmZmZjQiLCJsYXRlc3RfdGltZXN0YW1wXyI6MTc2NDkwMTMwMn0.UMLC4Ex19BSjpqFKI3kMplVs_XWw7qxh2FfDNuNqkBo; a2873925c34ecbd2_gr_cs1=bo-er; Hm_lpvt_f0faad39bcf8471e3ab3ef70125152c3=1764901324; _ga=GA1.2.2063381244.1764840930; _ga_PDVPZYN3CW=GS2.1.s1764901011$o4$g1$t1764901714$j60$l0$h0", csrftoken="JAhWyIhlyk3mrsZkTY6WOo6APrNMXMja") 
        self.logger = get_logger("user_input_node")
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare the input for processing.
        
        Args:
            shared: Shared state dictionary
            
        Returns:
            Dictionary with prepared input data
        """
        # Get user input from shared state
        leetcode_url = shared.get("leetcode_url", "")
        language_preference = shared.get("language_preference", "python3")
        max_iterations = shared.get("max_iterations", 3)
        self.logger.info(f"leetcode_url：{leetcode_url}")
        self.logger.info(f"language_preference:{language_preference}")
        self.logger.info(f"max_iterations:{max_iterations}")


        return {
            "leetcode_url": leetcode_url,
            "language_preference": language_preference,
            "max_iterations": max_iterations
        }
    
    def exec(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the user input.
        
        Args:
            inputs: Prepared input data
            
        Returns:
            Dictionary with processed input data
        """
        leetcode_url = inputs["leetcode_url"]
        language_preference = inputs["language_preference"]
        problem_desc, problem_slug = self.leetcode_api.fetch_problem_plain_text(link=leetcode_url)
        function_desc = self.leetcode_api.generate_template(problem_slug=problem_slug, code_lang=language_preference)


        self.logger.info(f"题目标题：{str(problem_slug)}")
        self.logger.info(f"题目描述：{str(problem_desc)}")
        self.logger.info(f"函数描述：{str(function_desc)}")   
        
        return {
            "problem_desc": problem_desc,
            "function_desc": function_desc,
            "problem_slug": problem_slug,
        }
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """
        Update the shared state with the processed input.
        
        Args:
            shared: Shared state dictionary
            prep_res: Result from prep method
            exec_res: Result from exec method
            
        Returns:
            String indicating the next action for the flow
        """
        # Update shared state with processed input
        shared["problem_desc"] = exec_res["problem_desc"]
        shared["problem_slug"] = exec_res["problem_slug"]
        shared["function_desc"] = exec_res["function_desc"]
        
        # Initialize iteration count
        shared["iteration_count"] = 0
        
        # Always proceed to parse problem
        return "default"
