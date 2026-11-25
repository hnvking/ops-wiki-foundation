#!/usr/bin/env python3
"""把运维知识库暴露为 MCP Server，供 WeKnora / 其它 Agent 调用。

默认只监听 127.0.0.1:8001，MCP 端点 http://127.0.0.1:8001/mcp。
部署到内网/公网时，用环境变量 WIKI_MCP_HOST / WIKI_MCP_PORT 控制监听地址，
并在前面加反向代理与鉴权。本服务本身不带鉴权，别直接暴露到公网。
"""
import asyncio
import json
import os
from urllib.parse import quote
from urllib.request import Request, urlopen

from mcp.server.mcpserver import MCPServer

WIKI_BASE = os.getenv("WIKI_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
MCP_HOST = os.getenv("WIKI_MCP_HOST", "127.0.0.1")
MCP_PORT = int(os.getenv("WIKI_MCP_PORT", "8001"))

server = MCPServer("ops-wiki-tools", version="1.0.0")


def call_wiki(path, method="GET", payload=None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = Request(WIKI_BASE + path, data=data, method=method)
    if data:
        req.add_header("Content-Type", "application/json")
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


@server.tool(description="按关键词检索运维 FAQ，返回带 source_card_id 的溯源片段。")
def search_faq(query: str, limit: int = 5) -> dict:
    path = "/api/ask/search?q=" + quote(query) + "&limit=" + str(limit)
    return call_wiki(path)


@server.tool(description="按卡片编号读取完整 FAQ 正文与元数据。")
def get_faq(source_card_id: str) -> dict:
    return call_wiki("/api/ask/faq/" + quote(str(source_card_id)))


@server.tool(description="记录一次 FAQ 复用，写回企微表格的「复用次数」。")
def record_reuse(source_card_id: str) -> dict:
    return call_wiki("/api/feedback/reuse", "POST", {"source_card_id": str(source_card_id)})


@server.tool(description="提交 FAQ 满意度评分（1-5），写回企微表格。")
def record_rating(source_card_id: str, rating: int) -> dict:
    return call_wiki("/api/feedback/rating", "POST", {
        "source_card_id": str(source_card_id), "rating": int(rating),
    })


@server.tool(description="生成 FAQ 定期复核提醒报告。")
def run_feedback_review() -> dict:
    return call_wiki("/api/feedback/review", "POST", {})


async def main():
    await server.run_streamable_http_async(
        host=MCP_HOST, port=MCP_PORT, streamable_http_path="/mcp"
    )


if __name__ == "__main__":
    asyncio.run(main())
