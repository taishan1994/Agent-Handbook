import asyncio
import json
import sys
import uuid
from datetime import datetime
from typing import AsyncGenerator, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
from langchain.agents import create_agent
from langchain.agents.middleware.todo import TodoListMiddleware
from langchain.chat_models import init_chat_model
from langchain_mcp_adapters.client import MultiServerMCPClient
from text_tool_calls_middleware import TextToolCallsMiddleware

app = FastAPI(
    title="Agent API",
    description="OpenAI 格式的 Agent API 接口",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 系统提示词 (保持不变)
SYSTEM_PROMPT = """
你是一位研究专家，根据用户要求进行研究并撰写报告。

## 工作流程
1. 理解核心需求，识别关键要素
2. **必须使用 write_todos 工具制定任务规划**，明确待办事项
3. 逐步研究，记录发现，验证结论
4. 整体结果和审查，必要时重新制定解决链路
5. 输出详细研究报告
6. **重要：在输出最终答案前，必须调用 write_todos 将所有任务标记为 completed**

## 工具使用
- web_search: 网络搜索工具
- extract: 网页内容提取工具
- write_todos: **任务规划工具（必须使用）**
"""

# Pydantic 模型 (保持不变)
class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[Message]
    stream: Optional[bool] = False

# 全局变量
agent_executor = None

async def get_agent():
    global agent_executor
    if agent_executor is not None:
        return agent_executor
    
    llm = init_chat_model(
        model="openai:/nfs/FM/gongoubo/checkpoints/Qwen/Qwen3-30B-A3B-Instruct-2507",
        base_url="http://192.168.16.44:11384/v1",
        api_key="none",
        temperature=0,
    )
    
    client = MultiServerMCPClient(
        connections={"web-search": {"url": "http://localhost:6030/sse", "transport": "sse"}}
    )
    
    tools = await client.get_tools()
    agent_executor = create_agent(
        model=llm,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        middleware=[TextToolCallsMiddleware(), TodoListMiddleware()],
        debug=False
    )
    return agent_executor

# ==========================================================
# 核心修复：唯一的、深度过滤的流式处理函数
# ==========================================================
async def stream_chat_completions(agent_executor, user_input: str, model: str) -> AsyncGenerator[str, None]:
    """流式输出聊天补全结果 - 间距绝对控制版"""
    
    response_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"
    created = int(datetime.timestamp(datetime.now()))
    
    active_tools = {}     
    in_json_block = False 
    json_depth = 0        
    
    # 核心控制状态
    has_sent_content = False  # 页面是否已有任何内容
    pending_sep = False       # 是否需要一个块间距 (两个换行)

    try:
        input_data = {"messages": [{"role": "user", "content": user_input}]}
        
        # 初始 Role
        yield f"data: {json.dumps({'id': response_id, 'object': 'chat.completion.chunk', 'created': created, 'model': model, 'choices': [{'index': 0, 'delta': {'role': 'assistant', 'content': ''}, 'finish_reason': None}]}, ensure_ascii=False)}\n\n"
        
        async for event in agent_executor.astream_events(
            input=input_data, version="v2", config={"recursion_limit": 50}
        ):
            event_type = event["event"]
            
            # 1. 模型文本处理 - 过滤所有无意义空白
            if event_type == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if not content: continue

                # 拦截 JSON 块
                stripped_chunk = content.strip()
                if not in_json_block and (stripped_chunk.startswith('{') or stripped_chunk.startswith('```json')):
                    in_json_block = True
                
                if in_json_block:
                    json_depth += content.count('{') - content.count('}')
                    if json_depth <= 0:
                        in_json_block, json_depth = False, 0
                    continue 

                # 【核心修复】如果输出全是空白（换行/空格），直接扔掉！
                # 这种空白通常是模型在 JSON 前后的过渡，由我们自己接管
                if not stripped_chunk:
                    continue
                
                if "<think>" in content or "</think>" in content: continue

                # 到这里说明是真正的文本内容
                output_prefix = ""
                if pending_sep:
                    output_prefix = "\n\n"
                    pending_sep = False
                
                has_sent_content = True
                yield f"data: {json.dumps({
                    'id': response_id, 'model': model,
                    'choices': [{'index': 0, 'delta': {'content': output_prefix + content}, 'finish_reason': None}]
                }, ensure_ascii=False)}\n\n"

            # 2. 工具开始
            elif event_type == "on_tool_start":
                run_id = event["run_id"]
                tool_name = event["name"]
                tool_input = event["data"].get("input", {})
                
                # 确定块前缀
                output_prefix = ""
                if pending_sep:
                    output_prefix = "\n\n"
                    pending_sep = False
                elif has_sent_content:
                    # 如果不是第一个块，但 pending_sep 没被触发，预防性给一个换行
                    output_prefix = "\n"

                if tool_name == "write_todos":
                    todos = tool_input.get("todos", [])
                    ui_text = output_prefix + "┌─────────────────────────────────────────────┐\n"
                    ui_text += "│ 📋 TODO List 更新                           │\n"
                    ui_text += "├─────────────────────────────────────────────┤\n"
                    for i, todo in enumerate(todos, 1):
                        icon = {"pending": "⏳", "in_progress": "🔄", "completed": "✅"}.get(todo.get("status"), "❓")
                        label = {"pending": "待处理", "in_progress": "进行中", "completed": "已完成"}.get(todo.get("status"), "未知")
                        # 格式化，确保边框对齐
                        c_text = todo.get('content', '')[:35]
                        ui_text += f"│ {i}. {icon} {label.ljust(6)} │ {c_text.ljust(27)} │\n"
                    ui_text += "└─────────────────────────────────────────────┘"
                    
                    has_sent_content = True
                    pending_sep = True # TODO 列表作为一个独立块，结束后需要间距
                    yield f"data: {json.dumps({'id': response_id, 'model': model, 'choices': [{'index': 0, 'delta': {'content': ui_text}, 'finish_reason': None}]}, ensure_ascii=False)}\n\n"
                
                else:
                    active_tools[run_id] = tool_name
                    # 合并工具调用信息
                    display_info = f"{output_prefix}🔧 **调用工具**: `{tool_name}`"
                    if tool_name == "web_search":
                        display_info += f" | 🔍 搜索: `{tool_input.get('query', '')}`"
                    elif tool_name == "extract":
                        url = tool_input.get('url', '')
                        display_info += f" | 📄 提取: `{url[:50]}...`"
                    
                    has_sent_content = True
                    yield f"data: {json.dumps({'id': response_id, 'model': model, 'choices': [{'index': 0, 'delta': {'content': display_info}, 'finish_reason': None}]}, ensure_ascii=False)}\n\n"

            # 3. 工具结束
            elif event_type == "on_tool_end":
                run_id = event["run_id"]
                if run_id in active_tools:
                    active_tools.pop(run_id)
                    pending_sep = True # 工具执行完，标记下一个内容需要间距
                    yield f"data: {json.dumps({'id': response_id, 'model': model, 'choices': [{'index': 0, 'delta': {'content': " ✨ 完成"}, 'finish_reason': None}]}, ensure_ascii=False)}\n\n"

        # 发送 Stop
        yield f"data: {json.dumps({'id': response_id, 'model': model, 'choices': [{'index': 0, 'delta': {}, 'finish_reason': 'stop'}]}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'id': response_id, 'model': model, 'choices': [{'index': 0, 'delta': {'content': f'\\n\\n[Error]: {str(e)}'}, 'finish_reason': 'error'}]})}\n\n"

# API 路由保持不变 (调用上面的 stream_chat_completions)
@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    agent_exec = await get_agent()
    user_input = next((m.content for m in reversed(request.messages) if m.role == "user"), None)
    if not user_input: raise HTTPException(status_code=400, detail="No user message")
    
    if request.stream:
        return StreamingResponse(stream_chat_completions(agent_exec, user_input, request.model), media_type="text/event-stream")
    else:
        # 简单实现非流式逻辑... (略)
        pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)