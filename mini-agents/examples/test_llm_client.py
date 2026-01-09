import asyncio
from Mini_Agents import LLMClient, Message

async def main():
    # Initialize the client
    client = LLMClient(
        api_key="test-key",
        api_base="http://192.168.16.14:18000/v1",
        provider="openai",  # openai/anthropic
        model="/nfs/FM/gongoubo/checkpoints/Qwen/Qwen3-30B-A3B-Instruct-2507"
    )

    # Send a message
    messages = [Message(role="user", content="你是谁？")]
    response = await client.generate(messages)

    print(response.content)

if __name__ == "__main__":
    asyncio.run(main())