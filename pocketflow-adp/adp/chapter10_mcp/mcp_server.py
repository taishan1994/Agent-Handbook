#!/usr/bin/env python3
"""
MCP服务器实现 - 基于Chapter 10的示例
提供文件系统交互和Web搜索功能
"""

import os
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastmcp import FastMCP

# 创建MCP服务器实例
mcp = FastMCP("File System and Web Search Server")

@mcp.tool()
def read_file(file_path: str) -> str:
    """
    读取文件内容
    
    Args:
        file_path: 要读取的文件路径
        
    Returns:
        文件内容
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

@mcp.tool()
def write_file(file_path: str, content: str) -> str:
    """
    写入内容到文件
    
    Args:
        file_path: 要写入的文件路径
        content: 要写入的内容
        
    Returns:
        操作结果
    """
    try:
        # 检查文件路径是否为空
        if not file_path or file_path.strip() == "":
            return "Error writing file: file_path cannot be empty"
        
        # 确保目录存在
        dir_path = os.path.dirname(file_path)
        # 只有当目录路径不为空时才创建目录
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to {file_path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

@mcp.tool()
def list_directory(dir_path: str) -> List[Dict[str, Any]]:
    """
    列出目录内容
    
    Args:
        dir_path: 要列出的目录路径
        
    Returns:
        包含文件和子目录信息的列表
    """
    try:
        items = []
        path = Path(dir_path)
        
        if not path.exists():
            return [{"error": f"Directory {dir_path} does not exist"}]
            
        if not path.is_dir():
            return [{"error": f"{dir_path} is not a directory"}]
            
        for item in path.iterdir():
            item_info = {
                "name": item.name,
                "path": str(item),
                "type": "directory" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else None
            }
            items.append(item_info)
            
        return items
    except Exception as e:
        return [{"error": f"Error listing directory: {str(e)}"}]

@mcp.tool()
def web_search(query: str, num_results: int = 5) -> str:
    """
    使用Exa API进行网络搜索
    
    Args:
        query: 搜索查询
        num_results: 返回结果数量，默认为5
        
    Returns:
        搜索结果字符串
    """
    try:
        # 导入Exa搜索功能
        import sys
        sys.path.append('/nfs/FM/gongoubo/new_project/Agent-Handbook/pocketflow-adp/utils')
        from exa_search_main import exa_web_search, extract_relevant_info
        
        # 直接调用Exa API，不获取网页内容
        url = "https://api.exa.ai/search"
        search_results = exa_web_search(query, url, num_result=num_results)
        
        # 提取基本信息
        extracted_info = extract_relevant_info(search_results)
        
        # 格式化结果为字符串
        results_str = "\n\n".join([
            f"Title: {info['title']}\nURL: {info['url']}\nSnippet: {info['snippet']}"
            for info in extracted_info
        ])
        
        return results_str
    except Exception as e:
        return f"Error performing web search: {str(e)}"

@mcp.tool()
def analyze_file_content(file_path: str, analysis_type: str = "summary") -> Dict[str, Any]:
    """
    分析文件内容
    
    Args:
        file_path: 要分析的文件路径
        analysis_type: 分析类型，可以是"summary", "keywords", "structure"
        
    Returns:
        分析结果
    """
    try:
        # 直接读取文件内容，而不是调用read_file工具
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 简化分析，不使用LLM
        if analysis_type == "summary":
            result = f"文件 {file_path} 的内容摘要：\n{content[:200]}..." if len(content) > 200 else f"文件 {file_path} 的内容：\n{content}"
        elif analysis_type == "keywords":
            # 简单的关键词提取
            words = content.split()
            result = f"文件 {file_path} 的关键词：\n{', '.join(words[:10])}"
        elif analysis_type == "structure":
            # 简单的结构分析
            lines = content.split('\n')
            result = f"文件 {file_path} 的结构：\n总行数: {len(lines)}"
        else:
            result = f"文件 {file_path} 的分析：\n{content[:100]}..." if len(content) > 100 else f"文件 {file_path} 的内容：\n{content}"
        
        return {
            "file_path": file_path,
            "analysis_type": analysis_type,
            "result": result
        }
    except Exception as e:
        return {"error": f"Error analyzing file: {str(e)}"}

# 启动服务器
if __name__ == "__main__":
    # 打印服务器启动信息
    print("Starting MCP server 'File System and Web Search Server' with transport 'stdio'")
    # 启动服务器
    mcp.run()