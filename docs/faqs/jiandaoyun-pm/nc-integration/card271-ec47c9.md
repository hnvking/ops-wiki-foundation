---
title: 材料付款单 缺少订单编码 未推NC
type: faq
related_system: 简道云 PM 系统
related_form: nc-integration
severity: low
resolution: resolved
last_reviewed: 2026-11-13
description: 三笔材料付款单未推NC的原因为缺少订单编码，需反查单据来源补齐。
owner: IT 运维组
source_card_id: 271
tags:
  - NC同步
  - 采购订单
problem_type: 缺陷与数据问题
content_hash: af1bbdc61d3741be
generated_hash: 8efaef299a8e6886
---
# 材料付款单 缺少订单编码 未推NC

## 问题描述

业务同事反馈：@微信 这三个材料付款单少了 订单编码，需要反查来源，帮忙看下

## 影响范围

- **影响系统:** 简道云 PM 系统
- **受影响用户:** NC 接口相关岗位
- **影响数据:** 相关单据与流程数据

## 原因分析

- 数据异常：材料付款单推送NC需带订单编码，缺订单编码会导致推送异常。

## 解决方案

1. 材料付款单推送NC需带订单编码，缺订单编码会导致推送异常。 三笔材料付款单未推NC的原因为缺少订单编码，需反查单据来源补齐

## 预防措施

- 在流程说明中明确相关规则，避免重复咨询。

## 相关页面

- [简道云 PM 系统](../../../systems/jiandaoyun-pm-system.md) — 系统技术文档
- [nc-integration 常见问题](../nc-integration/README.md) — 相关 FAQ 索引

## 变更记录

| 日期 | 作者 | 摘要 |
|-----------|-----------|--------------|
| 2026-11-13 | IT 运维组 | 依据知识卡 #271 提炼创建 |
