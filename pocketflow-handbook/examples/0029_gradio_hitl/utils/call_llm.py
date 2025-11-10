import os

from openai import OpenAI
from openai.types.chat.chat_completion import ChatCompletion

# api_key = os.getenv("OPENAI_API_KEY")
# base_url = "https://api.openai.com/v1"
# model = "gpt-4o"


# def call_llm(message: str):
#     print(f"Calling LLM with message: \n{message}")
#     client = OpenAI(api_key=api_key, base_url=base_url)
#     response: ChatCompletion = client.chat.completions.create(
#         model=model, messages=[{"role": "user", "content": message}]
#     )
#     return response.choices[0].message.content

def call_llm(messages):    
    """
    调用OpenAI的LLM API生成响应
    
    Args:
        prompt (str): 发送给LLM的提示文本
        
    Returns:
        str: LLM生成的响应内容
    """
    if isinstance(messages, str):
        messages = [{"role": "user", "content": messages}]
    
    # 初始化OpenAI客户端
    # 注意：实际使用时需要替换为有效的API密钥
    client = OpenAI(api_key="YOUR_API_KEY_HERE", base_url="http://192.168.16.24:13360/v1")
    
    model_name = client.models.list().data[0].id

    # 调用chat completions API
    r = client.chat.completions.create(
        model=model_name,  # 使用GPT-4o模型 
        messages=messages  # 构建消息格式
    )
    
    # 提取并返回生成的内容
    return r.choices[0].message.content


if __name__ == "__main__":
    print(call_llm("Hello, how are you?"))
