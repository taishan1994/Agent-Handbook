from pocketflow import AsyncFlow
from nodes import StreamingChatNode

def create_streaming_chat_flow():
    chat_node = StreamingChatNode()
    return AsyncFlow(start=chat_node) 