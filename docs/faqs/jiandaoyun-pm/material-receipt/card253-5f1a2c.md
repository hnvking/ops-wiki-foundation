---
title: 生产订单 完工状态 入库时点与查询时点不一致
type: faq
related_system: 简道云 PM 系统
related_form: material-receipt
severity: medium
resolution: resolved
last_reviewed: 2026-09-30
description: 订单状态不会随查询时点变更，8月查询时系统已按实际入库事实将订单置为完工状态。
owner: IT 运维组
source_card_id: 253
tags:
  - 入库
  - 常见问题
content_hash: d0843afa8add6630
generated_hash: aefa5fb9b1cc6bd8
---
# 生产订单 完工状态 入库时点与查询时点不一致

## 问题描述

业务同事反馈：王老师：为什么这些生产订单9月份才入完库，8月份在生产备料执行查询的时候，订单就显示已经完工了呢？

## 影响范围

- **影响系统:** 简道云 PM 系统
- **受影响用户:** 入库、对账相关岗位
- **影响数据:** 相关某模块数据

## 原因分析

- 流程规则不清：订单完工状态依据实际入库事实判定，不随用户查询时间或查询动作变化。

## 解决方案

1. 订单完工状态依据实际入库事实判定，不随用户查询时间或查询动作变化。 订单状态不会随查询时点变更，8月查询时系统已按实际入库事实将订单置为完工状态

## 预防措施

- 在流程说明中明确相关规则，避免重复咨询。

## 相关页面

- [简道云 PM 系统](../../../systems/jiandaoyun-pm-system.md) — 系统技术文档
- [material-receipt 常见问题](../material-receipt/README.md) — 相关 FAQ 索引

## 变更记录

| 日期 | 作者 | 摘要 |
|-----------|-----------|--------------|
| 2026-09-30 | IT 运维组 | 依据知识卡 #253 提炼创建 |
