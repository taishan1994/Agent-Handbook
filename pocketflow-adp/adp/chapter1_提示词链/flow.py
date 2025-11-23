import sys
import os
# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
# 添加PocketFlow目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'PocketFlow'))

from pocketflow import Node, Flow
from utils.utils import call_llm

class ExtractSpecificationsNode(Node):
    """
    第一步：从文本中提取技术规格信息
    """
    def prep(self, shared):
        # 从共享状态中获取输入文本
        return shared["input_text"]
    
    def exec(self, text_input):
        # 使用LLM提取技术规格
        prompt = f"""从以下文本中提取技术规格：

{text_input}

请提取出处理器、内存、存储等相关信息，并以简洁的方式描述。"""
        return call_llm(prompt)
    
    def post(self, shared, prep_res, exec_res):
        # 将提取结果存储到共享状态
        shared["extracted_specs"] = exec_res

class TransformToJSONNode(Node):
    """
    第二步：将提取的规格转换为JSON格式
    """
    def prep(self, shared):
        # 从共享状态中获取提取的规格
        return shared["extracted_specs"]
    
    def exec(self, specifications):
        # 使用LLM将规格转换为JSON格式
        prompt = f"""将以下规格转换为JSON对象，使用 'cpu'、'memory' 和 'storage' 作为键：

{specifications}

请确保输出是有效的JSON格式。"""
        return call_llm(prompt)
    
    def post(self, shared, prep_res, exec_res):
        # 将JSON结果存储到共享状态
        shared["json_output"] = exec_res

class ValidateJSONNode(Node):
    """
    第三步：验证JSON格式是否正确
    """
    def prep(self, shared):
        # 从共享状态中获取JSON输出
        return shared["json_output"]
    
    def exec(self, json_output):
        # 验证JSON格式并尝试修复
        prompt = f"""验证以下JSON格式是否正确，如果不正确请修复：

{json_output}

请确保输出是有效的JSON格式，包含cpu、memory、storage三个键。
只返回JSON对象，不要添加任何解释或说明文字。"""
        return call_llm(prompt)
    
    def post(self, shared, prep_res, exec_res):
        # 存储验证后的最终结果
        shared["final_result"] = exec_res

# 创建节点实例
extract_node = ExtractSpecificationsNode()
transform_node = TransformToJSONNode()
validate_node = ValidateJSONNode()

# 构建流程链：提取 → 转换 → 验证
extract_node.next(transform_node)
transform_node.next(validate_node)

# 创建流程，以extract_node为起点
spec_flow = Flow(start=extract_node)