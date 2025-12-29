import numpy as np
from openai import OpenAI

def call_llm(prompt):    
    client = OpenAI(
        # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
        api_key="",
        base_url="http://192.168.16.24:18000/v1",
    )
    if isinstance(prompt, str):
        messages = [
            {"role": "user", "content": prompt},
        ]
    else:
        messages = prompt

    model_name = client.models.list().data[0].id

    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=0.01,
        max_tokens=4000,
    )
    return response.choices[0].message.content

def call_embedding(text):
    client = OpenAI(
        # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
        api_key="",
        base_url="http://192.168.16.19:18001/v1",
    )
    if isinstance(text, str):
        text = [text]

    model_name = client.models.list().data[0].id

    responses = client.embeddings.create(
            model=model_name,
            input=text   
    )

    if isinstance(responses.data[0].embedding[0], float):
        embeddings = [responses.data[0].embedding]
    else:
        embeddings = [d.embedding[0] for d in responses.data]
    
    print(np.array(embeddings, dtype=np.float32).shape)
    return np.array(embeddings, dtype=np.float32)




if __name__ == "__main__":
    print("=== Testing call_llm ===")
    prompt = "In a few words, what is the meaning of life?"
    print(f"Prompt: {prompt}")
    response = call_llm(prompt)
    print(f"Response: {response}")

    print("=== Testing embedding function ===")
    
    text1 = "The quick brown fox jumps over the lazy dog."
    text2 = "Python is a popular programming language for data science."
    
    oai_emb1 = call_embedding(text1)
    oai_emb2 = call_embedding(text2)
    print(f"OpenAI Embedding 1 shape: {oai_emb1.shape}")
    oai_similarity = np.dot(oai_emb1, oai_emb2)
    print(f"OpenAI similarity between texts: {oai_similarity:.4f}")