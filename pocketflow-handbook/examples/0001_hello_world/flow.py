# 导入PocketFlow的核心类：Node和Flow
from pocketflow import Node, Flow
# 导入之前创建的LLM调用工具
from utils.call_llm import call_llm

# 创建一个继承自Node的自定义节点类
class AnswerNode(Node):
    """
    回答问题的节点类
    
    这是PocketFlow中最基本的节点类型，展示了节点的三个核心方法：
    1. prep - 准备阶段，从共享数据中获取输入
    2. exec - 执行阶段，处理输入并生成输出
    3. post - 后续处理阶段，将输出结果存储回共享数据
    """
    
    def prep(self, shared):
        """
        准备阶段：从共享数据中读取问题
        
        Args:
            shared (dict): 共享数据字典，包含流程中传递的数据
            
        Returns:
            str: 提取的问题文本
        """
        # 从共享数据中读取问题
        return shared["question"]
    
    def exec(self, question):
        """
        执行阶段：调用LLM回答问题
        
        Args:
            question (str): 要回答的问题
            
        Returns:
            str: LLM生成的回答
        """
        # 调用LLM获取回答
        return call_llm(question)
    
    def post(self, shared, prep_res, exec_res):
        """
        后续处理阶段：将回答存储到共享数据中
        
        Args:
            shared (dict): 共享数据字典
            prep_res: prep方法的返回结果
            exec_res: exec方法的返回结果（回答）
        """
        # 将回答存储在共享数据中
        shared["answer"] = exec_res

# 创建节点实例
answer_node = AnswerNode()

# 创建流程实例，设置起始节点为answer_node
# Flow是PocketFlow中组织节点执行的容器
qa_flow = Flow(start=answer_node)