"""数据库工具模块，提供SQL查询执行功能。"""

import sqlite3
from typing import Any
from langchain.tools import tool


@tool
def execute_sql(query: str, limit: int = 100) -> str:
    """执行SQL查询并返回结果。
    
    Args:
        query: 要执行的SQL查询语句
        limit: 返回结果的最大行数，默认为100
        
    Returns:
        查询结果的JSON格式字符串，包含列名和数据行
    """
    try:
        conn = sqlite3.connect("data/chinook.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 添加LIMIT子句（如果查询中没有）
        if "LIMIT" not in query.upper() and "INSERT" not in query.upper() and "UPDATE" not in query.upper() and "DELETE" not in query.upper():
            query = f"{query} LIMIT {limit}"
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # 获取列名
        columns = [description[0] for description in cursor.description] if cursor.description else []
        
        # 转换为字典列表
        result = {
            "columns": columns,
            "rows": [dict(row) for row in rows],
            "row_count": len(rows)
        }
        
        conn.close()
        
        import json
        return json.dumps(result, ensure_ascii=False, indent=2, default=str)
        
    except Exception as e:
        return f"查询执行错误: {str(e)}"


@tool
def get_table_schema(table_name: str) -> str:
    """获取指定表的结构信息。
    
    Args:
        table_name: 表名
        
    Returns:
        表的结构信息，包括列名、数据类型、是否可为空等
    """
    try:
        conn = sqlite3.connect("data/chinook.db")
        cursor = conn.cursor()
        
        # 获取表结构
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        result = f"表名: {table_name}\n\n"
        result += "列名 | 类型 | 可为空 | 默认值 | 主键\n"
        result += "-" * 60 + "\n"
        
        for col in columns:
            col_id, name, col_type, not_null, default_val, pk = col
            result += f"{name} | {col_type} | {'否' if not_null else '是'} | {default_val} | {'是' if pk else '否'}\n"
        
        # 获取外键信息
        cursor.execute(f"PRAGMA foreign_key_list({table_name})")
        fks = cursor.fetchall()
        
        if fks:
            result += "\n外键:\n"
            for fk in fks:
                result += f"  {fk[3]} -> {fk[2]}.{fk[4]}\n"
        
        conn.close()
        return result
        
    except Exception as e:
        return f"获取表结构错误: {str(e)}"


@tool
def list_tables() -> str:
    """列出数据库中所有表。
    
    Returns:
        所有表的名称列表
    """
    try:
        conn = sqlite3.connect("data/chinook.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        result = "数据库中的表:\n\n"
        for table in tables:
            result += f"- {table[0]}\n"
        
        conn.close()
        return result
        
    except Exception as e:
        return f"列出表错误: {str(e)}"


@tool
def get_sample_data(table_name: str, limit: int = 5) -> str:
    """获取表的样本数据。
    
    Args:
        table_name: 表名
        limit: 返回的样本行数，默认为5
        
    Returns:
        表的样本数据
    """
    try:
        conn = sqlite3.connect("data/chinook.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = f"SELECT * FROM {table_name} LIMIT {limit}"
        cursor.execute(query)
        rows = cursor.fetchall()
        
        columns = [description[0] for description in cursor.description] if cursor.description else []
        
        result = f"表 {table_name} 的样本数据 (前{limit}行):\n\n"
        
        # 表头
        result += " | ".join(columns) + "\n"
        result += "-" * (len(" | ".join(columns))) + "\n"
        
        # 数据行
        for row in rows:
            result += " | ".join(str(row[col]) for col in columns) + "\n"
        
        conn.close()
        return result
        
    except Exception as e:
        return f"获取样本数据错误: {str(e)}"


if __name__ == "__main__":
    print("测试数据库工具...")
    print("\n1. 列出所有表:")
    print(list_tables.invoke({}))
    
    print("\n2. 获取Artist表结构:")
    print(get_table_schema.invoke({"table_name": "Artist"}))
    
    print("\n3. 获取Artist表样本数据:")
    print(get_sample_data.invoke({"table_name": "Artist"}))
    
    print("\n4. 执行SQL查询:")
    print(execute_sql.invoke({"query": "SELECT * FROM Artist LIMIT 3"}))
