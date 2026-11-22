---
title: 分供商入库 NC已有 禁止重复添加 启光没有 录不了
type: faq
related_system: 简道云 PM 系统
related_form: nc-integration
severity: low
resolution: in-progress
last_reviewed: 2026-10-30
description: IT 运维组说明该供应商NC已存在，不允许重复添加；沈洛疑随后反馈启光上没有且仍录不了。
owner: IT 运维组
source_card_id: 151
tags:
  - NC同步
problem_type: 缺陷与数据问题
content_hash: 77ef070d7ac59873
generated_hash: 6eca8278268ea374
---
# 分供商入库 NC已有 禁止重复添加 启光没有 录不了

## 问题描述

业务同事反馈：请问这是什么问题呀，在分供商入库的时候

## 影响范围

- **影响系统:** 简道云 PM 系统
- **受影响用户:** NC 接口相关岗位
- **影响数据:** 影响分供商入库、供应商主数据补录。

## 原因分析

- 外部系统对接：供应商在NC已存在时不允许重复添加；NC有而启光没有时仍可能无法录入。

## 解决方案

1. 供应商在NC已存在时不允许重复添加
2. NC有而启光没有时仍可能无法录入。 IT 运维组说明该供应商NC已存在，不允许重复添加
3. 沈洛疑随后反馈启光上没有且仍录不了

## 预防措施

- NC已有供应商不能重复添加；启光缺失供应商需进一步处理同步/补录。
- 在流程说明中明确相关规则，避免重复咨询。

## 相关页面

- [简道云 PM 系统](../../../systems/jiandaoyun-pm-system.md) — 系统技术文档
- [nc-integration 常见问题](../nc-integration/README.md) — 相关 FAQ 索引

## 变更记录

| 日期 | 作者 | 摘要 |
|-----------|-----------|--------------|
| 2026-10-30 | IT 运维组 | 依据知识卡 #151 提炼创建 |
