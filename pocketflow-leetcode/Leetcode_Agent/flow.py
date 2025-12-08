from pocketflow import Flow

from Leetcode_Agent.utils.logger import get_logger
from Leetcode_Agent.nodes.user_input_node import UserInputNode
from Leetcode_Agent.nodes.parse_problem_node import ParseProblemNode
from Leetcode_Agent.utils.llm_client import LLMClient
from Leetcode_Agent.nodes.exec_python3_node import ExecPython3Node
from Leetcode_Agent.nodes.code_regen_node import CodeRegenNode



def create_leetcode_flow() -> Flow:
    """
    Create the LeetCode problem solving workflow.
    
    Args:
        llm_client: LLM client instance
        code_executor: Code executor instance
        
    Returns:
        Configured workflow for LeetCode problem solving
    """

    # Initialize logger
    logger = get_logger("leetcode_flow")
    logger.info("Creating LeetCode workflow")
    
    llm_client = LLMClient()

    user_input_node = UserInputNode(llm_client)
    parse_problem_node = ParseProblemNode(llm_client)
    exec_python3_node = ExecPython3Node(llm_client)
    code_regen_node = CodeRegenNode(llm_client)
    
    user_input_node >> parse_problem_node
    parse_problem_node >> exec_python3_node
    exec_python3_node >> code_regen_node
    code_regen_node - "regen" >> parse_problem_node

    flow = Flow(user_input_node)

    return flow 


if __name__ == "__main__":
    flow = create_leetcode_flow()

    # https://leetcode.cn/problems/trapping-rain-water
    # https://leetcode.com/problems/two-sum/

    shared = {
        "leetcode_url": "https://leetcode.cn/problems/sliding-window-maximum/",
        "language_preference": "python3",
        "max_iterations": 5,
    }

    flow.run(shared)
