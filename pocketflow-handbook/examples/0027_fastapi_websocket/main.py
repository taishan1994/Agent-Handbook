import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from flow import create_streaming_chat_flow

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def get_chat_interface():
    return FileResponse("static/index.html")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # Initialize conversation history for this connection
    shared_store = {
        "websocket": websocket,
        "conversation_history": []
    }
    
    try:
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Update only the current message, keep conversation history
                shared_store["user_message"] = message.get("content", "")
                
                # Create a new flow instance for each message
                flow = create_streaming_chat_flow()
                await flow.run_async(shared_store)
                
            except json.JSONDecodeError:
                # Handle invalid JSON
                await websocket.send_text(json.dumps({
                    "type": "start",
                    "content": ""
                }))
                await websocket.send_text(json.dumps({
                    "type": "chunk", 
                    "content": "接收到无效的消息格式，请重试。"
                }))
                await websocket.send_text(json.dumps({
                    "type": "end", 
                    "content": ""
                }))
            except Exception as e:
                # Handle any other errors during processing
                print(f"处理消息时出错: {e}")
                # Send error message to client
                await websocket.send_text(json.dumps({
                    "type": "start",
                    "content": ""
                }))
                await websocket.send_text(json.dumps({
                    "type": "chunk", 
                    "content": f"处理消息时发生错误: {str(e)}"
                }))
                await websocket.send_text(json.dumps({
                    "type": "end", 
                    "content": ""
                }))
                # Continue processing next messages instead of disconnecting
                continue
            
    except WebSocketDisconnect:
        print("客户端断开连接")
    except Exception as e:
        print(f"WebSocket错误: {e}")
        try:
            await websocket.close(code=1011, reason=f"服务错误: {str(e)}")
        except:
            pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)