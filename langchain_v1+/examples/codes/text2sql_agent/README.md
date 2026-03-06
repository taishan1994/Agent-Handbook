# Text2SQL Agent - 结合Skills的数据库查询Agent

这是一个使用deepagents框架结合Skills功能的Text2SQL Agent，能够理解用户的自然语言查询，生成正确的SQL语句，执行查询并返回结果。

## 功能特点

- ✅ **自然语言查询**: 用户可以用自然语言提问，Agent自动生成SQL
- ✅ **Skills集成**: 使用SQL技能提供专业的数据库操作指导
- ✅ **智能表结构识别**: 自动识别表结构和关系
- ✅ **结果解释**: 以自然语言解释查询结果
- ✅ **多表查询**: 支持复杂的JOIN查询和聚合操作

## 项目结构

```
text2sql_agent/
├── agent.py              # 主程序，交互式查询
├── test_agent.py         # 测试脚本
├── db_tools.py           # 数据库工具
├── skills/               # 技能目录
│   └── sql-query/
│       └── SKILL.md      # SQL查询技能
└── data/
    └── chinook.db        # Chinook数据库
```

## 环境准备

### 1. 安装依赖

```bash
cd /nfs/FM/gongoubo/new_project/Agent-Handbook/langchain_v1+/examples/codes/deepagents_with_mcp
pip install -r requirements.txt
```

### 2. 下载数据库

数据库已经存在于 `data/chinook.db`，如果需要重新下载：

```bash
cd /nfs/FM/gongoubo/new_project/Agent-Handbook/langchain_v1+/examples/codes/text2sql_agent
curl -L -o data/chinook.db https://github.com/lerocha/chinook-database/raw/master/ChinookDatabase/DataSources/Chinook_Sqlite.sqlite
```

## 使用方法

### 方法1: 交互式查询

```bash
cd /nfs/FM/gongoubo/new_project/Agent-Handbook/langchain_v1+/examples/codes/text2sql_agent
python agent.py
```

然后输入你的查询问题，例如：
- "列出所有的艺术家"
- "查询有多少个专辑"
- "查询最贵的5首歌曲"
- "查询每个客户的消费总额，按消费金额降序排列，只显示前10名"

输入 `quit` 或 `exit` 退出。

### 方法2: 测试脚本

```bash
python test_agent.py
```

这将运行一组预定义的测试查询。

## 数据库表结构

Chinook数据库包含以下主要表：

### Artist (艺术家表)
- ArtistId: 主键
- Name: 艺术家名称

### Album (专辑表)
- AlbumId: 主键
- Title: 专辑标题
- ArtistId: 外键，关联到Artist表

### Track (曲目表)
- TrackId: 主键
- Name: 曲目名称
- AlbumId: 外键，关联到Album表
- MediaTypeId: 外键，关联到MediaType表
- GenreId: 外键，关联到Genre表
- Composer: 作曲者
- Milliseconds: 时长（毫秒）
- Bytes: 文件大小
- UnitPrice: 单价

### Genre (流派表)
- GenreId: 主键
- Name: 流派名称

### MediaType (媒体类型表)
- MediaTypeId: 主键
- Name: 媒体类型名称

### Customer (客户表)
- CustomerId: 主键
- FirstName: 名
- LastName: 姓
- Company: 公司
- Address: 地址
- City: 城市
- State: 州/省
- Country: 国家
- PostalCode: 邮政编码
- Phone: 电话
- Fax: 传真
- Email: 邮箱
- SupportRepId: 外键，关联到Employee表

### Employee (员工表)
- EmployeeId: 主键
- LastName: 姓
- FirstName: 名
- Title: 职位
- ReportsTo: 上级ID
- BirthDate: 出生日期
- HireDate: 入职日期
- Address: 地址
- City: 城市
- State: 州/省
- Country: 国家
- PostalCode: 邮政编码
- Phone: 电话
- Fax: 传真
- Email: 邮箱

### Invoice (发票表)
- InvoiceId: 主键
- CustomerId: 外键，关联到Customer表
- InvoiceDate: 发票日期
- BillingAddress: 账单地址
- BillingCity: 账单城市
- BillingState: 账单州/省
- BillingCountry: 账单国家
- BillingPostalCode: 账单邮政编码
- Total: 总金额

### InvoiceLine (发票明细表)
- InvoiceLineId: 主键
- InvoiceId: 外键，关联到Invoice表
- TrackId: 外键，关联到Track表
- UnitPrice: 单价
- Quantity: 数量

### Playlist (播放列表表)
- PlaylistId: 主键
- Name: 播放列表名称

### PlaylistTrack (播放列表曲目关联表)
- PlaylistId: 外键，关联到Playlist表
- TrackId: 外键，关联到Track表

## 可用工具

Agent提供以下数据库工具：

1. **execute_sql**: 执行SQL查询
   - 参数: query (SQL语句), limit (最大行数)
   - 返回: JSON格式的查询结果

2. **get_table_schema**: 获取表结构
   - 参数: table_name (表名)
   - 返回: 表的结构信息

3. **list_tables**: 列出所有表
   - 返回: 所有表的名称列表

4. **get_sample_data**: 获取表的样本数据
   - 参数: table_name (表名), limit (样本行数)
   - 返回: 表的样本数据

## SQL技能

SQL技能 (`skills/sql-query/SKILL.md`) 提供了：

- 完整的数据库表结构说明
- 表之间的外键关系
- 常用查询模式和示例
- SQL最佳实践
- 工作流程指导

## 查询示例

### 简单查询
- "列出所有的艺术家"
- "查询有多少个专辑"
- "查询最贵的5首歌曲"

### 聚合查询
- "查询每个客户的消费总额，按消费金额降序排列，只显示前10名"
- "统计每个流派的曲目数量"
- "查询每个艺术家的专辑数量"

### 多表查询
- "查询艺术家及其专辑"
- "查询专辑及其曲目数量"
- "查询最流行的流派"

### 复杂查询
- "查询2023年的销售总额"
- "查询消费最多的客户及其详细信息"
- "查询每个国家的客户数量"

## 配置说明

### 模型配置

在 `agent.py` 和 `test_agent.py` 中修改模型配置：

```python
model = init_chat_model(
    model="openai:/nfs/FM/gongoubo/checkpoints/Qwen/Qwen3-30B-A3B-Instruct-2507",
    base_url="http://192.168.16.44:11384/v1",
    api_key="none",
    temperature=0,
)
```

### Backend配置

使用FilesystemBackend加载Skills：

```python
backend=FilesystemBackend(
    root_dir=os.path.join(os.path.dirname(__file__)),
    virtual_mode=False
)
```

## 工作原理

1. **理解需求**: Agent分析用户的自然语言查询
2. **加载技能**: 从Skills目录加载SQL查询技能
3. **生成SQL**: 根据技能指导和表结构生成正确的SQL语句
4. **执行查询**: 使用数据库工具执行SQL
5. **解释结果**: 以自然语言解释查询结果

## 技术栈

- **deepagents**: Agent框架
- **LangChain**: 工具和中间件
- **SQLite**: 数据库
- **Skills**: 技能系统

## 注意事项

- 确保模型服务器正常运行
- 确保数据库文件存在于 `data/chinook.db`
- 对于复杂查询，Agent会先查看表结构
- 使用LIMIT限制结果数量，避免返回过多数据
- 查询结果会以JSON格式返回，Agent会解释为自然语言

## 扩展功能

### 添加新的技能

在 `skills/` 目录下创建新的技能目录和SKILL.md文件：

```
skills/
└── my-skill/
    └── SKILL.md
```

然后在创建Agent时添加技能路径：

```python
agent = create_deep_agent(
    skills=["/skills/sql-query/", "/skills/my-skill/"],
    ...
)
```

### 添加新的工具

在 `db_tools.py` 中添加新的工具函数：

```python
@tool
def my_new_tool(param: str) -> str:
    """工具描述"""
    # 实现逻辑
    return result
```

然后在创建Agent时添加工具：

```python
tools = [execute_sql, get_table_schema, list_tables, get_sample_data, my_new_tool]
```

## 故障排除

### 连接错误

如果遇到 "Connection error"，请检查：
1. 模型服务器是否正常运行
2. 模型URL和端口是否正确
3. 网络连接是否正常

### 数据库错误

如果遇到数据库相关错误，请检查：
1. 数据库文件是否存在: `data/chinook.db`
2. 数据库文件是否可读
3. 表名是否正确（注意大小写）

### Skills加载错误

如果遇到Skills加载错误，请检查：
1. Skills目录路径是否正确
2. SKILL.md文件格式是否正确
3. YAML frontmatter是否完整

## 许可证

MIT License
