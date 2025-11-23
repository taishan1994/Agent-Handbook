import os
from openai import OpenAI
from pathlib import Path

# Get the project root directory (parent of utils directory)
ROOT_DIR = Path(__file__).parent.parent

# Initialize OpenAI client with API key from environment

def call_llm(prompt):    
    # client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "your-api-key"))
    # r = client.chat.completions.create(
    #     model="gpt-4o",
    #     messages=[{"role": "user", "content": prompt}]
    # )
    # return r.choices[0].message.content
    client = OpenAI(
        # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
        api_key="",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    if isinstance(prompt, str):
        messages = [
            {"role": "user", "content": prompt},
        ]
    else:
        messages = prompt

    response = client.chat.completions.create(
        model="qwen3-30b-a3b-instruct-2507",
        messages=messages,
        temperature=0.01,
        max_tokens=4000,
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    # Test LLM call
    response = call_llm("What is web search?")
    print("Response:", response)
