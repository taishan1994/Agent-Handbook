from openai import AsyncOpenAI, OpenAI
import os
import asyncio

async def stream_llm(prompt: str):
    """
    异步调用本地或 OpenAI 的 LLM API 生成响应，失败时降级到模拟响应
    
    Args:
        prompt (str or list): 发送给LLM的提示文本，可以是字符串或 messages 列表
        
    Returns:
        str: LLM生成的响应内容
    """
    try:
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

        # 获取模型列表并选择第一个（可选）
        try:
            model_list = await client.models.list()
            model_name = model_list.data[0].id  
        except Exception:
            # 如果获取模型列表失败，使用默认模型名
            model_name = "gpt-3.5-turbo"

        # 调用 chat completions API（异步）
        stream = await client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_tokens=20000,  # 根据需要调整
            temperature=0.7,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
    except Exception as e:
        print(f"LLM API 调用失败: {e}，使用模拟响应")
        # 降级到模拟响应
        await asyncio.sleep(0.5)  # 模拟网络延迟
        response_text = "您好！这是一个模拟的响应。由于LLM服务暂时不可用，我使用了本地模拟来响应用户请求。如果您需要真实的AI回复，请确保OpenAI API或本地代理服务正常运行。"
        
        # 模拟流式输出
        for char in response_text:
            yield char
            await asyncio.sleep(0.05)  # 模拟打字效果


async def stream_llm_ori(messages):
    client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY", "your-api-key"))
    
    stream = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        stream=True,
        temperature=0.7
    )
    
    async for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            yield chunk.choices[0].delta.content

if __name__ == "__main__":
    import asyncio
    
    async def test():
        messages = [{"role": "user", "content": "Hello!"}]
        async for chunk in stream_llm(messages):
            print(chunk, end="", flush=True)
        print()
    
    asyncio.run(test())