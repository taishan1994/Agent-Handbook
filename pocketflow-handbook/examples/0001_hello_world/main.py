# 导入之前创建的流程
from flow import qa_flow

# 示例主函数
def main():
    """
    主函数：演示PocketFlow流程的基本使用方法
    
    1. 创建共享数据字典
    2. 运行PocketFlow流程
    3. 输出结果
    """
    # 创建共享数据字典
    # 这个字典会在流程执行过程中在各个节点之间传递数据
    shared = {
        "question": "你是谁？",
        "answer": None  # 初始化为None，稍后会被填充
    }

    # 运行流程
    # flow.run(shared) 会按照流程定义执行所有节点
    # 节点会修改shared字典中的内容
    qa_flow.run(shared)
    
    # 输出结果
    # 现在shared字典中的answer已经被节点填充
    print("Question:", shared["question"])
    print("Answer:", shared["answer"])

# 当直接运行此文件时执行main函数
if __name__ == "__main__":
    main()