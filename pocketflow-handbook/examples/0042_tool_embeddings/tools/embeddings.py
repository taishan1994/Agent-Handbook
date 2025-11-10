from openai import OpenAI
import numpy as np

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


    embeddings = [d.embedding for d in responses.data]

    return np.array(embeddings, dtype=np.float32)