# openai格式请求调用工具
- 这里我们使用的接口是asyncopenai
- tool的格式需要组装成xxx
- 自己使用vllm部署需要在部署时：

```shell
model_path=/nfs/FM/gongoubo/checkpoints/Qwen/Qwen3-30B-A3B-Instruct-2507
port=18000

CUDA_VISIBLE_DEVICES=0 vllm serve ${model_path} --host 0.0.0.0 --port ${port} --tensor-parallel-size 1 --gpu-memory-utilization 0.95 --max-model-len 16000 --enable-auto-tool-choice --tool-call-parser pythonic
```

# 其它

本项目主要是对Minimax的Mini-Agents进行拆解，包括工具的使用、mcp的使用、skills的使用以及构建一个可以执行工具、mcp和skills的agent。

其它部分参考文章以及examples里面的样例。