import os
from openai import AsyncOpenAI

async def stream_llm(messages):
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