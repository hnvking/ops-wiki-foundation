---
title: 入库单金额带不出、只有附加费入库
type: faq
related_system: 简道云 PM 系统
related_form: material-receipt
severity: low
resolution: resolved
last_reviewed: 2026-11-14
description: 排查发现该入库单没有物料入库、只有附加费入库，故对账单不带出金额。
owner: IT 运维组
source_card_id: 75
tags:
  - 对账
  - 入库
content_hash: 8df4a02ea21df7af
generated_hash: 957ab6b1e1676253
---
# 入库单金额带不出、只有附加费入库

## 问题描述

业务同事反馈：[单据编号]00000086业务同事这个入库单金额带不出来

## 影响范围

- **影响系统:** 简道云 PM 系统
- **受影响用户:** 入库、对账相关岗位
- **影响数据:** 相关单据与流程数据

## 原因分析

- 流程规则不清：仅附加费入库、无物料入库的入库单不计算对账金额。

## 解决方案

1. 仅附加费入库、无物料入库的入库单不计算对账金额。 排查发现该入库单没有物料入库、只有附加费入库，故对账单不带出金额

## 预防措施

- 纯附加费入库单做对账时无金额。
- 在流程说明中明确相关规则，避免重复咨询。

## 相关页面

- [简道云 PM 系统](../../../systems/jiandaoyun-pm-system.md) — 系统技术文档
- [material-receipt 常见问题](../material-receipt/README.md) — 相关 FAQ 索引

## 变更记录

| 日期 | 作者 | 摘要 |
|-----------|-----------|--------------|
| 2026-11-14 | IT 运维组 | 依据知识卡 #75 提炼创建 |
