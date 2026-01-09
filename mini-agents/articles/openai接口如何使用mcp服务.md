# 环境构建
这里我们以tavily搜索mcp为例，首先是安装相关的依赖环境：
```shell
apt update
apt install nodejs npm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
source ~/.bashrc
nvm install 20.18.1
nvm use 20.18.1

pip install mcp

git clone https://github.com/tavily-ai/tavily-mcp.git
cd tavily-mcp


npm install
npm run build
```

# mcp使用
在`test_llm_client_with_mcp_tools.py`文件中：

- 使用`load_mcp_tools_async`函数来加载所有的mcp工具，mcp工具在config/mcp.json中进行定义，这里我们使用了tavily搜索工具。
- 在调用llm的时候，将mcp工具列表赋值给tool属性。然后llm会根据情况调用mcp工具，并返回`<tool></tool>`来说明是调用了工具。
- 然后我们解析llm生成的工具，真正将其分装成mcp需要的格式。mcp将结果返回。
- 最后将结果传递给LLM，让其进行总结回答。