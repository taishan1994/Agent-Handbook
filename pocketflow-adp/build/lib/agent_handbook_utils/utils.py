import numpy as np
import asyncio
from openai import OpenAI
from openai import AsyncOpenAI
import aiohttp
import json
from typing import List, Dict, Any

def call_llm(prompt):    
    client = OpenAI(
        # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
        api_key="",
        base_url="http://192.168.16.2:18001/v1",
    )
    if isinstance(prompt, str):
        messages = [
            {"role": "user", "content": prompt},
        ]
    else:
        messages = prompt

    model = client.models.list().data[0].id

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.01,
        max_tokens=4000,
    )
    return response.choices[0].message.content

async def call_llm_async(prompt):
    """异步版本的call_llm函数"""
    client = AsyncOpenAI(
        # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
        api_key="",
        base_url="http://192.168.16.2:18001/v1",
        timeout=30.0,  # 设置30秒超时
    )
    if isinstance(prompt, str):
        messages = [
            {"role": "user", "content": prompt},
        ]
    else:
        messages = prompt

    # 异步获取模型列表
    models = await client.models.list()
    model = models.data[0].id

    response = await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.01,
        max_tokens=4000,
    )
    return response.choices[0].message.content

def get_embedding(text):

    client = OpenAI(
        # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
        api_key="",
        base_url="http://192.168.16.2:18000/v1",
    )
    if isinstance(text, str):
        text = [text]

    model = client.models.list().data[0].id

    responses = client.embeddings.create(
            model=model,
            input=text   
    )

    embeddings = responses.data[0].embedding
    return np.array(embeddings, dtype=np.float32)

def get_embedding_batch(text):

    client = OpenAI(
        # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
        api_key="",
        base_url="http://192.168.16.2:18000/v1",
    )
    if isinstance(text, str):
        text = [text]

    model = client.models.list().data[0].id

    responses = client.embeddings.create(
            model=model,
            input=text   
    )

    embeddings = [d.embedding for d in responses.data]
    return np.array(embeddings, dtype=np.float32)


async def search_web_exa(query: str, num_results: int = 3) -> List[Dict[str, str]]:
    """
    使用Exa搜索引擎进行网络搜索
    
    Args:
        query: 搜索查询
        num_results: 返回结果数量
        
    Returns:
        搜索结果列表，每个结果包含title、snippet和url字段
    """
    # 使用DuckDuckGo作为备选方案，因为Exa可能需要API密钥
    url = "https://api.duckduckgo.com/"
    params = {
        "q": query,
        "format": "json",
        "no_html": 1,
        "skip_disambig": 1
    }
    
    try:
        timeout = aiohttp.ClientTimeout(total=5)  # 设置5秒超时
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    results = []
                    
                    # DuckDuckGo返回的结果格式
                    for i, result in enumerate(data.get("Results", [])[:num_results]):
                        results.append({
                            "title": result.get("Text", ""),
                            "snippet": result.get("Text", ""),
                            "url": result.get("FirstURL", "")
                        })
                    
                    # 如果没有结果，尝试使用AbstractText
                    if not results and "AbstractText" in data and data["AbstractText"]:
                        results.append({
                            "title": data.get("Abstract", ""),
                            "snippet": data.get("AbstractText", ""),
                            "url": data.get("AbstractURL", "")
                        })
                    
                    return results
                else:
                    print(f"搜索失败，状态码: {response.status}")
                    return []
    except asyncio.TimeoutError:
        print("搜索超时")
        return []
    except Exception as e:
        print(f"搜索错误: {str(e)}")
        # 返回模拟结果，以便程序继续运行
        return [
            {
                "title": f"关于'{query}'的搜索结果",
                "snippet": f"这是关于'{query}'的模拟搜索结果。由于网络限制，无法获取实际搜索结果。",
                "url": "https://example.com"
            }
        ]


if __name__ == '__main__':
    prompt = "你好"
    print(call_llm(prompt))
    prompt = ["你是谁？", "你好"]
    print(get_embedding(prompt))
