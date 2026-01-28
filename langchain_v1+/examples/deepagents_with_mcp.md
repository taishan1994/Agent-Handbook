# 说明

安装基础环境：
```shell
pip install deepagents tavily-python
pip install fastmcp
pip install tavily
pip install langchain-mcp-adapters

Successfully installed anthropic-0.76.0 bracex-2.6 deepagents-0.3.7 filetype-1.2.0 google-auth-2.47.0 google-genai-1.60.0 jsonpatch-1.33 jsonpointer-3.0.0 langchain-1.2.6 langchain-anthropic-1.3.1 langchain-core-1.2.7 langchain-google-genai-4.2.0 langgraph-1.0.6 langgraph-checkpoint-4.0.0 langgraph-prebuilt-1.0.6 langgraph-sdk-0.3.3 langsmith-0.6.4 ormsgpack-1.12.2 pyasn1-0.6.2 pyasn1-modules-0.4.2 requests-toolbelt-1.0.0 rsa-4.9.1 tavily-python-0.7.19 uuid-utils-0.14.0 wcmatch-10.1 fastmcp-2.14.3 tavily-1.0.0 langchain-mcp-adapters-0.2.1

```

使用deepagents结合mcp，构建一个能够自己搜索的智能体。

deepagents地址：https://github.com/langchain-ai/deepagents

支持以下参数：
```python
create_deep_agent(
    model: str | BaseChatModel | None = None,
    tools: Sequence[BaseTool | Callable | dict[str, Any]] | None = None,
    *,
    system_prompt: str | SystemMessage | None = None,
    middleware: Sequence[AgentMiddleware] = (),
    subagents: list[SubAgent | CompiledSubAgent] | None = None,
    skills: list[str] | None = None,
    memory: list[str] | None = None,
    response_format: ResponseFormat | None = None,
    context_schema: type[Any] | None = None,
    checkpointer: Checkpointer | None = None,
    store: BaseStore | None = None,
    backend: BackendProtocol | BackendFactory | None = None,
    interrupt_on: dict[str, bool | InterruptOnConfig] | None = None,
    debug: bool = False,
    name: str | None = None,
    cache: BaseCache | None = None,
) -> CompiledStateGraph
```
其余函数的输入参数可以参考这里：https://reference.langchain.com/python/deepagents/

## 部署模型
我们可以使用外部的大模型，也可以自己部署，这里我们自己部署一个Qwen3-30B-A3B的模型用作实验。
```shell
CUDA_VISIBLE_DEVICES=0 vllm serve Qwen/Qwen3-30B-A3B-Instruct-2507--host 0.0.0.0 --port 18000 --tensor-parallel-size 1 --gpu-memory-utilization 0.95 --max-model-len 16000 --enable-auto-tool-choice --tool-call-parser pythonic
```

## 构建一个tavily的mcp服务
注册并申请一个api key：https://app.tavily.com/home 

langchain中如何使用可以参考这里： https://docs.tavily.com/documentation/integrations/langchain

travily的接口文档参考这里：https://docs.tavily.com/documentation/api-reference/endpoint/search

我们可以使用langchain内置的travily工具，也可以自己用fastmcp来封装一个mcp，为了能够让以后我们能够自定义各种mcp，我们这里自定义一个travli mcp：
```python
from mcp.server.fastmcp import FastMCP
from typing import Literal
from tavily import TavilyClient

mcp = FastMCP("Web-Search-Server")

tavily_client = TavilyClient(api_key="tvly-xxxx") ## 修改为你的key


@mcp.tool()
def web_search(query: str, max_results: int = 5,
               topic: Literal["general", "news", "finance"] = "general",
               include_raw_content: bool = False):
    """Run a web search"""
    return tavily_client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )
    
@mcp.tool()
def extract(url: str):
    """Extract web page content from URL."""
    return tavily_client.extract(url)

if __name__ == "__main__":
    mcp.settings.port = 6030
    mcp.run("sse")
```
## 自定义模型
结合上面我们启动的服务，我们可以自定义一个模型，参考代码如下：
```python
model = init_chat_model(
    model="/nfs/FM/gongoubo/checkpoints/Qwen/Qwen3-30B-A3B-Instruct-2507",
    model_provider="openai",
    base_url="http://localhost:16000/v1",
    api_key="none",
)
```

## 解析工具
由于我们部署模型的时候指定了工具调用的格式为pythonic，langchain的智能体不会会自动执行该工具（会生成调用工具的结果），具体表现是模型输出调用工具的文本，而在openai返回的结果中，tool_calls是空的，因此不会自动执行该工具。我们需要构建一个中间件，该中间件用于解析文本，并将其结果赋值给tool_calls，并用AIMessage来包装。

## 流式输出
流式输出这里我们使用的是astream_events，这个之前在流式组件学习的时候好像没有见到。在调用这个时，我们可以选择从中间件里面打印不同阶段的信息，从而控制流式输出哪些信息。

## 客户端调用
将agent分装为fastapi（可使用openai格式调用），然后构建了一个简单的可视化页面来调用该api。

启动服务端：`python agent_apt.py`

访问：http://192.168.16.24:8080/web_demo.html

![image-20260128173554843](./deepagents_with_mcp.assets/image-20260128173554843.png)

会流式输出相关的tolist、相关工具的调用信息、llm的总结。

# 代码参考

部分代码参考：

> https://mp.weixin.qq.com/s/F4dDJIe_Qj-yJD8WDogHEQ