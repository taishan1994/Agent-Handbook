import os
import numpy as np
from openai import OpenAI

def call_llm(prompt):    
    # client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "your-api-key"))
    # r = client.chat.completions.create(
    #     model="gpt-4o",
    #     messages=[{"role": "user", "content": prompt}]
    # )
    # return r.choices[0].message.content
    client = OpenAI(
        # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
        api_key="sk-c083635aa07d4753a83d481b97e4824c",
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

def get_embedding(text):
    # client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "your-api-key"))
    
    # response = client.embeddings.create(
    #     model="text-embedding-ada-002",
    #     input=text
    # )
    
    # # Extract the embedding vector from the response
    # embedding = response.data[0].embedding
    
    # # Convert to numpy array for consistency with other embedding functions
    # return np.array(embedding, dtype=np.float32)

    client = OpenAI(
        # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
        api_key="sk-c083635aa07d4753a83d481b97e4824c",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    if isinstance(text, str):
        text = [text]

    responses = client.embeddings.create(
            model="text-embedding-v4",
            input=text   
    )

    embeddings = [d.embedding[0] for d in responses.data]
    return np.array(embeddings, dtype=np.float32)


def fixed_size_chunk(text, chunk_size=2000):
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunks.append(text[i : i + chunk_size])
    return chunks

if __name__ == "__main__":
    print("=== Testing call_llm ===")
    prompt = "In a few words, what is the meaning of life?"
    print(f"Prompt: {prompt}")
    response = call_llm(prompt)
    print(f"Response: {response}")

    print("=== Testing embedding function ===")
    
    text1 = "The quick brown fox jumps over the lazy dog."
    text2 = "Python is a popular programming language for data science."
    
    oai_emb1 = get_embedding(text1)
    oai_emb2 = get_embedding(text2)
    print(f"OpenAI Embedding 1 shape: {oai_emb1.shape}")
    oai_similarity = np.dot(oai_emb1, oai_emb2)
    print(f"OpenAI similarity between texts: {oai_similarity:.4f}")