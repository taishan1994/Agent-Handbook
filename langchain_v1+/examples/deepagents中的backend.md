## 1. FilesystemBackend（文件系统后端）

### 功能特点
- 直接从实际文件系统读写文件
- 支持相对路径和绝对路径
- 提供路径安全控制（virtual_mode）
- 使用ripgrep或Python进行文件搜索

### 安全警告
⚠️ **高风险**：此backend授予Agent直接文件系统访问权限

**适用场景**：
- ✅ 本地开发CLI工具（编码助手、开发工具）
- ✅ CI/CD流水线（需注意安全）
- ❌ Web服务器或HTTP API（应使用StateBackend、StoreBackend或SandboxBackend）

### 用法示例

```python
from deepagents.backends.filesystem import FilesystemBackend

# 基本用法 - 使用当前工作目录
backend = FilesystemBackend()

# 带根目录的用法
backend = FilesystemBackend(root_dir="/path/to/project")

# 安全模式 - 限制访问范围
backend = FilesystemBackend(
    root_dir="/safe/directory",
    virtual_mode=True,  # 阻止路径遍历（..、~）
    max_file_size_mb=10
)

# 操作文件
backend.write("/test.txt", "Hello World")
content = backend.read("/test.txt")
backend.edit("/test.txt", "Hello", "Hi")
matches = backend.grep_raw("pattern", path="/")
```

### 安全建议
1. 启用人机协同(HITL)中间件审查敏感操作
2. 从可访问路径中排除密钥文件
3. 生产环境使用SandboxBackend
4. **始终**使用`virtual_mode=True`配合`root_dir`

---

## 2. StoreBackend（存储后端）

### 功能特点
- 使用LangGraph的BaseStore持久化存储
- 跨线程、跨会话持久化
- 支持命名空间隔离
- 支持多Agent隔离（通过assistant_id）

### 适用场景
- ✅ 需要跨会话持久化的文件存储
- ✅ 多Agent环境下的文件隔离
- ✅ 需要长期保存的文档和记忆

### 用法示例

```python
from deepagents.backends.store import StoreBackend
from langchain.tools import ToolRuntime

# 初始化
runtime = ToolRuntime(store=your_langgraph_store)
backend = StoreBackend(runtime)

# 写入文件
result = backend.write("/document.txt", "Content here")
# 自动使用命名空间：(assistant_id, "filesystem")

# 读取文件
content = backend.read("/document.txt")

# 异步操作
await backend.awrite("/async.txt", "Async content")
content = await backend.aread("/async.txt")

# 编辑文件
backend.edit("/document.txt", "old text", "new text")

# 搜索文件
matches = backend.grep_raw("pattern", path="/")

# 上传/下载文件
upload_result = backend.upload_files([("/file1.txt", b"content")])
download_result = backend.download_files(["/file1.txt"])
```

### 命名空间规则
1. 优先使用`runtime.config`中的`assistant_id`
2. 回退到`langgraph.config.get_config()`
3. 默认：`("filesystem",)`
4. 有assistant_id：`(assistant_id, "filesystem")`

---

## 3. StateBackend（状态后端）

### 功能特点
- 在LangGraph agent状态中存储文件
- 临时性：仅在对话线程内持久化
- 自动检查点：每步后自动保存
- 返回Command对象更新状态

### 适用场景
- ✅ 临时文件和草稿
- ✅ 对话期间的中间结果
- ✅ 不需要跨会话保存的内容

### 用法示例

```python
from deepagents.backends.state import StateBackend
from langchain.tools import ToolRuntime

# 初始化
runtime = ToolRuntime(state={"files": {}})
backend = StateBackend(runtime)

# 写入文件 - 返回Command对象
result = backend.write("/temp.txt", "Temporary content")
# result.files_update = {"/temp.txt": file_data}

# 读取文件
content = backend.read("/temp.txt")

# 编辑文件
backend.edit("/temp.txt", "old", "new")

# 列出文件
infos = backend.ls_info("/")
# 返回: [{"path": "/temp.txt", "is_dir": False, "size": 16, ...}]

# 搜索
matches = backend.grep_raw("pattern", path="/")

# 下载文件
download_result = backend.download_files(["/temp.txt"])
```

### 特殊处理
- 操作返回`Command`对象而非`None`
- 通过`uses_state=True`标志标识
- 状态必须通过Command对象更新，不能直接修改

---

## 4. BaseSandbox（沙箱基类）

### 功能特点
- 抽象基类，提供默认实现
- 通过`execute()`方法执行shell命令
- 子类只需实现`execute()`方法
- 支持文件操作、搜索、glob等

### 适用场景
- ✅ 需要安全隔离的代码执行
- ✅ 需要限制文件系统访问
- ✅ 生产环境的文件操作

### 用法示例

```python
from deepagents.backends.sandbox import BaseSandbox

class MySandbox(BaseSandbox):
    @property
    def id(self) -> str:
        return "my_sandbox"
    
    def execute(self, command: str) -> ExecuteResponse:
        # 实现你的沙箱执行逻辑
        # 例如：Docker容器、Firecracker microVM等
        result = run_in_sandbox(command)
        return ExecuteResponse(
            output=result.stdout,
            exit_code=result.returncode,
            signal=None,
            truncated=False
        )
    
    def upload_files(self, files):
        # 实现文件上传到沙箱
        pass
    
    def download_files(self, paths):
        # 实现从沙箱下载文件
        pass

# 使用
sandbox = MySandbox()
sandbox.write("/test.txt", "content")
result = sandbox.execute("ls -la")
matches = sandbox.grep_raw("pattern")
```

### 内置方法
- `ls_info()` - 列出目录
- `read()` - 读取文件
- `write()` - 写入文件
- `edit()` - 编辑文件
- `grep_raw()` - 搜索文件
- `glob_info()` - glob匹配

---

## 5. CompositeBackend（复合后端）

### 功能特点
- 根据路径前缀路由到不同backend
- 支持混合存储策略
- 最长前缀匹配优先
- 路径前缀恢复

### 适用场景
- ✅ 需要不同路径使用不同存储策略
- ✅ 临时文件用State，持久文件用Store
- ✅ 多存储后端统一接口

### 用法示例

```python
from deepagents.backends.composite import CompositeBackend
from deepagents.backends.state import StateBackend
from deepagents.backends.store import StoreBackend

# 初始化
runtime = ToolRuntime(
    state={"files": {}},
    store=your_langgraph_store
)

composite = CompositeBackend(
    default=StateBackend(runtime),
    routes={
        "/memories/": StoreBackend(runtime),
        "/cache/": StoreBackend(runtime),
        "/persistent/": StoreBackend(runtime)
    }
)

# 写入到不同后端
composite.write("/temp.txt", "ephemeral")  # StateBackend
composite.write("/memories/note.md", "persistent")  # StoreBackend
composite.write("/cache/data.json", "cache")  # StoreBackend

# 列出根目录 - 聚合所有后端
infos = composite.ls_info("/")
# 返回: ["/temp.txt", "/memories/", "/cache/", "/persistent/"]

# 列出特定路由
infos = composite.ls_info("/memories/")
# 只返回StoreBackend中的文件

# 搜索 - 可以跨后端
matches = composite.grep_raw("pattern", path="/")  # 搜索所有后端
matches = composite.grep_raw("pattern", path="/memories/")  # 只搜索memories

# 读取
content = composite.read("/memories/note.md")  # 自动路由到StoreBackend
```

### 路由规则
1. 最长前缀匹配优先
2. 未匹配路径使用default backend
3. 路径前缀必须以`/`开头，建议以`/`结尾
4. 返回结果时恢复完整路径前缀

---

## Backend对比总结

| 特性 | FilesystemBackend | StoreBackend | StateBackend | SandboxBackend | CompositeBackend |
|------|-----------------|--------------|--------------|-----------------|------------------|
| 持久性 | 永久 | 永久 | 临时 | 取决于实现 | 取决于路由 |
| 跨会话 | ✅ | ✅ | ❌ | 取决于实现 | 取决于路由 |
| 安全性 | 低（需virtual_mode） | 中 | 高 | 高 | 取决于路由 |
| 隔离性 | 无 | 命名空间 | 线程级 | 进程级 | 路径级 |
| 适用场景 | 本地开发 | 持久存储 | 临时文件 | 生产环境 | 混合策略 |

## 选择建议

1. **本地开发工具** → FilesystemBackend（启用virtual_mode）
2. **需要持久化** → StoreBackend
3. **临时文件** → StateBackend
4. **生产环境** → SandboxBackend
5. **混合需求** → CompositeBackend组合使用

## 最佳实践

1. **安全优先**：生产环境避免FilesystemBackend
2. **明确隔离**：使用命名空间和路径前缀
3. **异步支持**：StoreBackend和StateBackend支持异步操作
4. **错误处理**：检查返回结果的error字段
5. **路径规范**：统一使用绝对路径，以`/`开头

这些backend提供了灵活的文件操作抽象，可以根据不同场景选择合适的实现，确保安全性和性能的平衡。