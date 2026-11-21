---
title: NC系统 启光系统 供应商补录 编码一致 无法关联 入库单录入
type: faq
related_system: 简道云 PM 系统
related_form: nc-integration
severity: low
resolution: in-progress
last_reviewed: 2026-11-02
description: 业务同事要求补录的供应商编码需与NC保持一致，并反馈开发修复后入库单现在应该可以正常录入、可再试。
owner: IT 运维组
source_card_id: 144
tags:
  - NC同步
  - 入库
content_hash: 3907b3ae8c632676
generated_hash: a17af0126fce0d71
---
# NC系统 启光系统 供应商补录 编码一致 无法关联 入库单录入

## 问题描述

业务同事反馈：这个公司说是NC系统有，但是启光系统上没有，那启光系统能正常签订合同吗？

## 影响范围

- **影响系统:** 简道云 PM 系统
- **受影响用户:** NC 接口相关岗位
- **影响数据:** 影响供应商无法关联、合同签订及入库单录入。

## 原因分析

- 外部系统对接：补录供应商编码必须与NC保持一致；NC已有但启光没有的供应商需补录后才能关联。

## 解决方案

1. 补录供应商时保持供应商编码与NC一致
2. 开发修复后重试入库单录入

## 预防措施

- 补录供应商编码与NC不一致会导致无法关联。
- 在流程说明中明确相关规则，避免重复咨询。

## 相关页面

- [简道云 PM 系统](../../../systems/jiandaoyun-pm-system.md) — 系统技术文档
- [nc-integration 常见问题](../nc-integration/README.md) — 相关 FAQ 索引

## 变更记录

| 日期 | 作者 | 摘要 |
|-----------|-----------|--------------|
| 2026-11-02 | IT 运维组 | 依据知识卡 #144 提炼创建 |
