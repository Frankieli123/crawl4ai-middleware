#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
MCP服务器，提供crawl4ai的网页抓取功能
"""

import asyncio
import json
import httpx
import os
import re
import hashlib
import datetime
import traceback
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# 加载.env文件中的环境变量，设置silent=True避免文件不存在时抛出异常
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
if os.path.exists(env_path):
    try:
        load_dotenv(env_path)
        print(f"已加载环境变量配置文件: {env_path}")
    except Exception as e:
        print(f"加载环境变量配置文件失败: {str(e)}")
else:
    print("环境变量配置文件(.env)不存在，将使用默认配置")

# 初始化FastMCP服务器实例
mcp = FastMCP("crawl4ai")

# 配置日志
log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("crawl4ai")

# crawl4ai API配置
API_BASE = os.getenv("CRAWL4AI_API_BASE", "http://192.168.31.12:11235")
API_KEY = os.getenv("CRAWL4AI_API_KEY", "sk-3180623")
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# 定义保存抓取结果的目录
custom_output_dir = os.getenv("OUTPUT_DIR")
if custom_output_dir:
    URL_DIR = os.path.abspath(custom_output_dir)
else:
    URL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "url")

def ensure_url_dir():
    """确保url目录存在"""
    try:
        if not os.path.exists(URL_DIR):
            os.makedirs(URL_DIR, exist_ok=True)
            logger.info(f"创建目录: {URL_DIR}")
        return True
    except Exception as e:
        logger.error(f"创建目录失败: {URL_DIR}, 错误: {str(e)}")
        traceback.print_exc()
        return False

def generate_filename(url: str, task_id: str) -> str:
    """根据URL和task_id生成文件名"""
    # 提取域名作为文件名前缀
    domain = re.search(r"https?://(?:www\.)?([^/]+)", url)
    prefix = domain.group(1).replace(".", "_") if domain else "unknown"
    
    # 使用task_id的一部分，或者生成URL的哈希值
    if task_id:
        suffix = task_id[:8]
    else:
        suffix = hashlib.md5(url.encode()).hexdigest()[:8]
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    return f"extracted_{prefix}_{suffix}_{timestamp}.txt"

async def make_api_request(method: str, url: str, json_data: Optional[Dict] = None) -> Dict[str, Any]:
    """向crawl4ai API发起请求，并进行错误处理"""
    async with httpx.AsyncClient() as client:
        try:
            logger.debug(f"发送{method.upper()}请求到: {url}")
            if method.lower() == "post":
                response = await client.post(url, headers=HEADERS, json=json_data, timeout=30.0)
            else:
                response = await client.get(url, headers=HEADERS, timeout=30.0)
                
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"API请求失败: {str(e)}")
            return {"error": str(e)}

@mcp.tool()
async def create_crawl_task(url: str, priority: int = 10) -> str:
    """创建网页抓取任务并返回task_id
    
    参数:
        url: 要抓取的网页URL
        priority: 任务优先级（默认为10）
    """
    # 确保url目录存在，提前检查以便后续保存结果
    ensure_url_dir()
    
    api_url = f"{API_BASE}/crawl"
    data = {
        "urls": url,
        "priority": priority
    }
    
    logger.info(f"创建抓取任务: {url}, 优先级: {priority}")
    result = await make_api_request("post", api_url, data)
    
    if "error" in result:
        logger.error(f"创建抓取任务失败: {result['error']}")
        return f"创建抓取任务失败: {result['error']}"
    
    # 根据crawl4ai API的返回格式提取task_id
    task_id = result.get("task_id", "")
    if task_id:
        logger.info(f"抓取任务已创建，task_id为: {task_id}")
        return f"抓取任务已创建，task_id为: {task_id}"
    else:
        logger.warning(f"无法获取task_id，API返回: {result}")
        return f"无法获取task_id，API返回: {result}"

@mcp.tool()
async def get_crawl_result(task_id: str, url: str = "") -> str:
    """根据task_id获取网页抓取结果，并保存到本地文件
    
    参数:
        task_id: 抓取任务的ID
        url: 抓取的原始URL（可选，用于生成更好的文件名）
    """
    # 确保url目录存在
    if not ensure_url_dir():
        logger.error("无法创建保存目录")
        return "无法创建保存目录，请检查权限或路径是否正确"
    
    api_url = f"{API_BASE}/task/{task_id}"
    
    logger.info(f"获取抓取结果，task_id: {task_id}")
    result = await make_api_request("get", api_url)
    
    if "error" in result:
        logger.error(f"获取抓取结果失败: {result['error']}")
        return f"获取抓取结果失败: {result['error']}"
    
    # 处理结果数据
    status = result.get("status", "unknown")
    
    if status == "completed":
        try:
            # 获取内容并保存到文件
            content = result.get("content", "")
            source_url = result.get("url", url)
            filename = generate_filename(source_url, task_id)
            filepath = os.path.join(URL_DIR, filename)
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            
            logger.info(f"抓取完成，内容已保存到: {filepath}")
            return f"抓取完成。内容已保存到文件: {filepath}"
        except Exception as e:
            logger.error(f"保存文件失败: {str(e)}")
            return f"保存文件失败: {str(e)}"
    elif status == "pending":
        logger.info("抓取任务正在进行中")
        return "抓取任务正在进行中，请稍后再试"
    else:
        logger.warning(f"抓取状态: {status}")
        return f"抓取状态: {status}，返回数据: {result}"

@mcp.tool()
async def list_saved_results() -> str:
    """列出已保存的抓取结果文件"""
    # 确保url目录存在
    ensure_url_dir()
    
    try:
        files = [f for f in os.listdir(URL_DIR) if f.startswith("extracted_")]
        
        if not files:
            logger.info("没有找到已保存的抓取结果")
            return "没有找到已保存的抓取结果"
        
        file_list = "\n".join(f"- {f}" for f in files)
        logger.info(f"找到{len(files)}个已保存的抓取结果")
        return f"已保存的抓取结果文件：\n{file_list}"
    except Exception as e:
        logger.error(f"读取文件列表失败: {str(e)}")
        return f"读取文件列表失败: {str(e)}"

@mcp.tool()
async def read_saved_result(filename: str) -> str:
    """读取已保存的抓取结果文件
    
    参数:
        filename: 文件名（不包含路径）
    """
    # 确保url目录存在
    ensure_url_dir()
    
    filepath = os.path.join(URL_DIR, filename)
    
    if not os.path.exists(filepath):
        logger.warning(f"文件不存在: {filename}")
        return f"文件不存在: {filename}"
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 如果内容过大，返回摘要
        if len(content) > 1000:
            logger.info(f"读取文件: {filename} (内容已截断)")
            return f"文件内容（前1000字符）:\n{content[:1000]}...\n\n[内容已截断，完整内容请查看文件: {filepath}]"
        
        logger.info(f"读取文件: {filename}")
        return f"文件内容:\n{content}"
    except Exception as e:
        logger.error(f"读取文件失败: {str(e)}")
        return f"读取文件失败: {str(e)}"

if __name__ == "__main__":
    # 程序启动时确保url目录存在
    logger.info("启动crawl4ai MCP服务器...")
    logger.info(f"API基础URL: {API_BASE}")
    logger.info(f"输出目录: {URL_DIR}")
    ensure_url_dir()
    mcp.run(transport='stdio') 