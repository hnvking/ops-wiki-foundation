---
title: 含税单价截切重贴后NC同步成功
type: faq
related_system: 简道云 PM 系统
related_form: nc-integration
severity: low
resolution: resolved
last_reviewed: 2026-09-24
description: 两条同步失败的单据通过将含税单价截切后重新张贴回去的操作方式已同步成功。
owner: IT 运维组
source_card_id: 52
tags:
  - NC同步
  - 单价
content_hash: e72d94e9cce9c295
generated_hash: 1393aca9bd51a897
---
# 含税单价截切重贴后NC同步成功

## 问题描述

业务同事反馈：[单据编号]00000187这个是昨天业务同事改了，又能同步。还剩下两个PMCLRKD-202609-[编号]，[单据编号]，同步失败。

## 影响范围

- **影响系统:** 简道云 PM 系统
- **受影响用户:** NC 接口相关岗位
- **影响数据:** 相关单据与流程数据

## 原因分析

- 用户操作：两条同步失败的单据通过将含税单价截切后重新张贴回去的操作方式已同步成功。

## 解决方案

1. 把含税单价截切，然后再张贴回去，再同步NC

## 预防措施

- 含税单价字段异常时可尝试截切重贴以触发重新赋值。

## 相关页面

- [简道云 PM 系统](../../../systems/jiandaoyun-pm-system.md) — 系统技术文档
- [nc-integration 常见问题](../nc-integration/README.md) — 相关 FAQ 索引

## 变更记录

| 日期 | 作者 | 摘要 |
|-----------|-----------|--------------|
| 2026-09-24 | IT 运维组 | 依据知识卡 #52 提炼创建 |
