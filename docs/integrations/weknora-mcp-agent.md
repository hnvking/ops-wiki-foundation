---
title: "WeKnora 问答 Agent 与 MCP 工具接入"
type: integration
status: draft
owner: "IT 运维组"
last_reviewed: "2026-11-23"
description: "用 WeKnora 内置问答 Agent 承接企微问答，本知识库通过 MCP 提供 FAQ 检索、溯源与反馈写回能力。"
systems:
  - "简道云 PM 系统"
  - "WeKnora"
direction: two-way
protocol: API
tags:
  - WeKnora
  - MCP
  - 企业微信
  - RAG
---

# WeKnora 问答 Agent 与 MCP 工具接入

## 结论

**可以直接用 WeKnora 自带的问答 Agent 做生成，不需要另写一套答案生成逻辑。** WeKnora 已经提供企业微信 IM 渠道、RAG 问答、引用溯源和 Agent 能力。

本项目负责的是 WeKnora 不天然具备的两件事：

1. 稳定的卡片编号溯源（`source_card_id`）。
2. 把「复用次数 / 满意度评分」写回企微表格，形成反馈闭环。

为此本项目提供一个 MCP Server，让 WeKnora Agent 在对话中调用本地工具。

## 架构

```text
企业微信用户
   ↓  IM 渠道（WeKnora 内置）
WeKnora 问答 Agent  ←→  WeKnora 知识库（上传本项目导出的 FAQ）
   ↓  MCP（Streamable HTTP）
ops-wiki MCP Server（mcp_server.py）
   ↓  HTTP API
本知识库后端（backend/main.py）
   ↓  wecom-cli
企微智能表格「PM运维知识卡」
```

## 1. 导入知识库

```bash
python scripts/export_for_rag.py
python scripts/export_for_weknora.py
```

产出两份文件：

- `exports/weknora_import.json`：172 篇，文档 ID 优先使用 `source_card_id`，适合程序化导入。
- `exports/weknora_upload/`：同样内容的 Markdown 文件，文件名带卡片编号，可直接打包上传到 WeKnora 知识库。

WeKnora 的文档导入路径和请求体随版本变化，本项目不硬编码。使用者填好 `WEKNORA_BASE_URL` 与 `WEKNORA_API_KEY` 后，按所用版本的官方 API 导入；没配 API Key 时，直接上传 `weknora_upload/` 目录同样可用。

## 2. 启动 MCP Server

```bash
# 依赖：pip install -r requirements.txt（已含 mcp>=2.3.0）
python mcp_server.py
```

默认只监听 `127.0.0.1:8001`，MCP 端点为 `http://127.0.0.1:8001/mcp`。需要给 WeKnora 容器/另一台机器访问时：

```bash
set WIKI_MCP_HOST=0.0.0.0
set WIKI_MCP_PORT=8001
python mcp_server.py
```

MCP Server 本身不带鉴权。**不要直接暴露到公网**，用内网地址或反向代理 + 鉴权。

提供的工具：

| 工具 | 作用 |
|---|---|
| `search_faq(query, limit)` | 关键词检索，返回带卡片编号的 FAQ 片段 |
| `get_faq(source_card_id)` | 按卡片编号读取完整 FAQ |
| `record_reuse(source_card_id)` | 复用次数 +1，写回企微表格 |
| `record_rating(source_card_id, rating)` | 提交 1-5 分满意度，写回企微表格 |
| `run_feedback_review()` | 生成定期复核提醒报告 |

## 3. 在 WeKnora 中配置 MCP

进入「工具箱 → MCP服务」，新建服务：

- 类型：Streamable HTTP
- URL：`http://<MCP服务器地址>:8001/mcp`
- 认证：内网部署可先留空；公网部署配 Bearer Token
- 同步工具后，在目标 Agent 的工具清单里勾选上表工具

Agent 系统提示词建议：

```text
回答运维问题时，必须先用 search_faq 检索，再用 get_faq 读取原文。
每个回答末尾列出来源卡片编号 source_card_id。
用户确认答案有帮助时调用 record_reuse；用户给出 1-5 分评分时调用 record_rating。
检索不到时明确说「知识库未覆盖」，不要自行编造。
```

## 4. 在 WeKnora 中配置企微 IM

在 WeKnora「设置 → IM 集成」中创建企业微信渠道：

1. 企业微信后台创建自建应用，拿到 CorpID、AgentID、Secret。
2. WeKnora 配置企微应用参数，生成回调 Token 与 EncodingAESKey。
3. 把回调地址填回企微后台。Webhook 模式地址形如
   `https://<weknora域名>/api/v1/im/callback/<channel_id>`，必须是公网 HTTPS。
4. 把企业微信服务器 IP 加入可信 IP 列表。
5. 在企微里给应用发消息验证连通。

WebSocket / Stream 模式不需要公网回调地址，按 WeKnora 当前版本的渠道配置选择即可。

## 5. 配置说明

复制 `.env.example` 为 `.env` 并填写，`WIKI_BASE_URL` 保持指向本知识库后端。真实 API Key 不要提交到仓库。

## 相关页面

- [运维问题 FAQ 总索引](../faqs/README.md)
- [企业微信 SSO 集成](jiandaoyun-wecom-sso.md)
