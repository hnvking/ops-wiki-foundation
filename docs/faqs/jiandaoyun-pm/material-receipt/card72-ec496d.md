---
title: 入库单只带出一份、采购订单未走完未反写
type: faq
related_system: 简道云 PM 系统
related_form: material-receipt
severity: low
resolution: resolved
last_reviewed: 2026-11-11
description: 原因是采购订单还没走完，订单流程结束反写后就能做对账单。
owner: IT 运维组
source_card_id: 72
tags:
  - 对账
  - 入库
  - 采购订单
content_hash: 22173f72a8a66f27
generated_hash: 8dade0720b689573
---
# 入库单只带出一份、采购订单未走完未反写

## 问题描述

业务同事反馈：徐闻一期入库单只带出了一份，还有几份没带出来

## 影响范围

- **影响系统:** 简道云 PM 系统
- **受影响用户:** 入库、对账相关岗位
- **影响数据:** 相关单据与流程数据

## 原因分析

- 流程规则不清：采购订单流程结束会反写，反写后入库单才能被对账单带出。

## 解决方案

1. 等采购订单流程结束反写后再做对账单

## 预防措施

- 预入库单据需关注对应订单流程状态。
- 在流程说明中明确相关规则，避免重复咨询。

## 相关页面

- [简道云 PM 系统](../../../systems/jiandaoyun-pm-system.md) — 系统技术文档
- [material-receipt 常见问题](../material-receipt/README.md) — 相关 FAQ 索引

## 变更记录

| 日期 | 作者 | 摘要 |
|-----------|-----------|--------------|
| 2026-11-11 | IT 运维组 | 依据知识卡 #72 提炼创建 |
