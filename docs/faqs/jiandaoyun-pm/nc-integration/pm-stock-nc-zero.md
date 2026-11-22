---
title: 系统显示有库存但出库提示 NC 库存为零
type: faq
related_system: 简道云 PM 系统
related_form: nc-integration
severity: medium
resolution: resolved
last_reviewed: 2026-11-06
description: 系统显示有库存但出库时提示 NC 库存为零；原因是预入库流程结束后数据才会同步到 NC。
owner: IT 运维组
source_card_id: 35
tags:
  - 出库
  - NC同步
  - 入库
  - 常见问题
problem_type: 用户操作FAQ
content_hash: afa5725b4a9123ce
generated_hash: 8f4185846100ad37
---
# 系统显示有库存但出库提示 NC 库存为零

## 问题描述

业务同事反馈：系统中明明显示有库存，出库时却弹出库存不足的提示。

## 影响范围

- **影响系统:** 简道云 PM 系统、NC 系统
- **受影响用户:** 物资出库相关岗位
- **影响数据:** 出库操作受阻

## 原因分析

- 系统显示的库存与 NC 库存口径不同：预入库流程结束后数据才会同步到 NC，流程未结束时 NC 库存仍为零。

## 解决方案

1. 确认该批库存是否已完成预入库流程。
2. 若预入库流程尚未结束，等待流程完成后数据同步至 NC 再执行出库。
3. 同步完成后重新发起出库操作。

## 预防措施

- 出库前先确认预入库流程是否已结束，避免以系统显示的库存作为唯一依据。

## 相关页面

- [简道云 PM 系统](../../../systems/jiandaoyun-pm-system.md) — 系统技术文档
- [NC 接口同步失败](../nc-integration/nc-interface-sync-fail.md) — 相关 FAQ

## 变更记录

| 日期 | 作者 | 摘要 |
|-----------|-----------|--------------|
| 2026-11-06 | IT 运维组 | 依据知识卡 #35 提炼创建 |
