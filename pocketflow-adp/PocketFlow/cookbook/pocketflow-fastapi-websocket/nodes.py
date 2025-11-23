import asyncio
import json
from pocketflow import AsyncNode
from utils.stream_llm import stream_llm

class StreamingChatNode(AsyncNode):
    async def prep_async(self, shared):
        user_message = shared.get("user_message", "")
        websocket = shared.get("websocket")
        
        conversation_history = shared.get("conversation_history", [])
        conversation_history.append({"role": "user", "content": user_message})
        
        return conversation_history, websocket
    
    async def exec_async(self, prep_res):
        messages, websocket = prep_res
        
        await websocket.send_text(json.dumps({"type": "start", "content": ""}))
        
        full_response = ""
        async for chunk_content in stream_llm(messages):
            full_response += chunk_content
            await websocket.send_text(json.dumps({
                "type": "chunk", 
                "content": chunk_content
            }))
        
        await websocket.send_text(json.dumps({"type": "end", "content": ""}))
        
        return full_response, websocket
    
    async def post_async(self, shared, prep_res, exec_res):
        full_response, websocket = exec_res
        
        conversation_history = shared.get("conversation_history", [])
        conversation_history.append({"role": "assistant", "content": full_response})
        shared["conversation_history"] = conversation_history 