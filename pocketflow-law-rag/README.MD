# 总览

```shell
cd Law_RAG_Agent

rm -rf Laws

git clone https://github.com/LawRefBook/Laws.git

# 生成知识库所需要的输入数据
cd utils && python process_law_data.py

# 修改utils/llm_utils.py里面的服务为自己部署的服务
# 这里面使用Qwen3模型以及Qwen3-4B-Embedding，使用vllm或者sglang进行部署

# 分块（我们已经提前将每一条法律构建chunk，不需要额外的分块）
# 将chunk进行向量化并存入到faiss索引中
# 对输入进行向量化并使用faiss进行索引，选择距离最近的前20条，加入到llm的输入中进行回答
python3 flow.py
```

**为什么我们需要一个基础的RAG系统？**

整体的RAG架构十分简单，pocketflow的底层只有100行代码，易于理解和扩展。这里我们的RAG系统基本功能已有，后续有新的RAG优化方法，可以基于这个框架进行改造。





