from openai import OpenAI

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
    client = OpenAI(api_key="YOUR_API_KEY_HERE", base_url="http://192.168.16.23:13360/v1")
    
    model_name = client.models.list().data[0].id

    # 调用chat completions API
    r = client.chat.completions.create(
        model=model_name,  # 使用GPT-4o模型 
        messages=messages  # 构建消息格式
    )
    
    # 提取并返回生成的内容
    return r.choices[0].message.content

if __name__ == "__main__":
    print("## Testing call_llm")
    prompt = "In a few words, what is the meaning of life?"
    print(f"## Prompt: {prompt}")
    response = call_llm(prompt)
    print(f"## Response: {response}")