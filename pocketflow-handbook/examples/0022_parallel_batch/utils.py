from openai import AsyncOpenAI, OpenAI
import os
import asyncio

async def call_llm_async(prompt: str):
    """
    异步调用本地或 OpenAI 的 LLM API 生成响应
    
    Args:
        prompt (str or list): 发送给LLM的提示文本，可以是字符串或 messages 列表
        
    Returns:
        str: LLM生成的响应内容
    """
    # 初始化异步客户端
    client = AsyncOpenAI(
        api_key=os.getenv("OPENAI_API_KEY", "your-api-key"),  # 推荐通过环境变量设置
        base_url="http://192.168.16.24:13360/v1"  # 如果是本地代理或兼容 OpenAI 的接口
    )

    # 构建 messages
    if isinstance(prompt, str):
        messages = [{"role": "user", "content": prompt}]
    else:
        messages = prompt

    try:
        # 获取模型列表并选择第一个（可选）
        model_list = await client.models.list()
        model_name = model_list.data[0].id  

        # 调用 chat completions API（异步）
        r = await client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_tokens=20000,  # 根据需要调整
            temperature=0.7,
        )

        # 提取并返回生成的内容
        return r.choices[0].message.content

    except Exception as e:
        print(f"Error calling LLM: {e}")
        raise

    finally:
        await client.close()  # 推荐关闭客户端连接池

def call_llm(prompt):    
    """
    调用OpenAI的LLM API生成响应
    
    Args:
        prompt (str): 发送给LLM的提示文本
        
    Returns:
        str: LLM生成的响应内容
    """
    # 初始化OpenAI客户端
    # 注意：实际使用时需要替换为有效的API密钥
    client = OpenAI(api_key="YOUR_API_KEY_HERE", base_url="http://192.168.16.23:13360/v1")
    if isinstance(prompt, str):
        messages = [{"role": "user", "content": prompt}]
    else:
        messages = prompt
    
    model_name = client.models.list().data[0].id

    # 调用chat completions API
    r = client.chat.completions.create(
        model=model_name,  # 使用GPT-4o模型 
        messages=messages  # 构建消息格式
    )
    
    # 提取并返回生成的内容
    return r.choices[0].message.content

# Async version of the simple wrapper, using Anthropic
# async def call_llm(prompt):
#     """Async wrapper for Anthropic API call."""
#     client = AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", "your-api-key"))
#     response = await client.messages.create(
#         model="claude-3-7-sonnet-20250219",
#         max_tokens=20000,
#         thinking={
#             "type": "enabled",
#             "budget_tokens": 16000
#         },
#         messages=[
#             {"role": "user", "content": prompt}
#         ],
#     )
#     return response.content[1].text

if __name__ == "__main__":
    async def run_test():
        print("## Testing async call_llm with Anthropic")
        prompt = "In a few words, what is the meaning of life?"
        print(f"## Prompt: {prompt}")
        response = await call_llm_async(prompt)
        print(f"## Response: {response}")

    asyncio.run(run_test()) 