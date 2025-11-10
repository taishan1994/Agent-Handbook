import asyncio
import json
from pocketflow import AsyncNode
from utils.stream_llm import stream_llm

class StreamingChatNode(AsyncNode):
    async def prep_async(self, shared):
        user_message = shared.get("user_message", "")
        websocket = shared.get("websocket")
        
        if not websocket:
            raise ValueError("WebSocket连接未提供")
        
        conversation_history = shared.get("conversation_history", [])
        conversation_history.append({"role": "user", "content": user_message})
        
        return conversation_history, websocket
    
    async def exec_async(self, prep_res):
        messages, websocket = prep_res
        
        full_response = ""
        try:
            # 发送开始标记
            await websocket.send_text(json.dumps({"type": "start", "content": ""}))
            
            # 尝试获取LLM流式响应
            try:
                async for chunk_content in stream_llm(messages):
                    full_response += chunk_content
                    # 尝试发送内容，如果失败则继续（不会中断整个流程）
                    try:
                        await websocket.send_text(json.dumps({
                            "type": "chunk", 
                            "content": chunk_content
                        }))
                    except Exception as send_error:
                        print(f"发送WebSocket消息失败: {send_error}")
                        # 继续收集响应，但停止发送
                        continue
            except Exception as llm_error:
                print(f"LLM流式处理错误: {llm_error}")
                # 发送错误消息
                error_message = f"处理响应时发生错误: {str(llm_error)}"
                await websocket.send_text(json.dumps({
                    "type": "chunk", 
                    "content": error_message
                }))
                full_response = error_message
            
            # 确保发送结束标记
            try:
                await websocket.send_text(json.dumps({"type": "end", "content": ""}))
            except Exception as end_error:
                print(f"发送结束标记失败: {end_error}")
                # 即使结束标记发送失败，也返回已收集的响应
                
        except Exception as e:
            print(f"exec_async中的未捕获错误: {e}")
            # 发生严重错误时，尝试发送错误消息和结束标记
            try:
                await websocket.send_text(json.dumps({"type": "start", "content": ""}))
                await websocket.send_text(json.dumps({
                    "type": "chunk", 
                    "content": f"发生内部错误: {str(e)}"
                }))
                await websocket.send_text(json.dumps({"type": "end", "content": ""}))
            except:
                pass
            full_response = f"发生内部错误: {str(e)}"
        
        return full_response, websocket
    
    async def post_async(self, shared, prep_res, exec_res):
        try:
            full_response, websocket = exec_res
            
            conversation_history = shared.get("conversation_history", [])
            conversation_history.append({"role": "assistant", "content": full_response})
            shared["conversation_history"] = conversation_history 
            # 限制对话历史长度，避免内存占用过大
            if len(shared["conversation_history"]) > 20:  # 最多保留20轮对话
                shared["conversation_history"] = shared["conversation_history"][-20:]
        except Exception as e:
            print(f"post_async中的错误: {e}")
            # 即使post处理失败，也不应中断流程