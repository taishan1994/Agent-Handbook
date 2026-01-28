import asyncio
import httpx
import json

async def test_stream():
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream(
            "POST",
            "http://localhost:8000/v1/chat/completions",
            json={
                "model": "agent-model",
                "messages": [{"role": "user", "content": "埃菲尔铁塔与最高建筑相比有多高？"}],
                "stream": True
            }
        ) as response:
            print(f"Status: {response.status_code}")
            chunk_count = 0
            async for chunk in response.aiter_lines():
                if chunk.startswith("data: "):
                    data = chunk[6:].strip()
                    if data == "[DONE]":
                        # print("Stream completed!")
                        break
                    
                    try:
                        json_data = json.loads(data)
                        content = json_data["choices"][0]["delta"].get("content", "")
                        if content:
                            print(content, end="", flush=True)
                            chunk_count += 1
                            # if chunk_count >= 20:
                            #     print("\n... (truncated)")
                            #     break
                    except:
                        pass

if __name__ == "__main__":
    asyncio.run(test_stream())
