---
title: 入库量超过订单量、申购剩余量、控制点
type: faq
related_system: 简道云 PM 系统
related_form: material-receipt
severity: low
resolution: resolved
last_reviewed: 2026-11-16
description: IT 运维组明确申购总量不是控制点、申购剩余量才是控制点，并给出可查询申购剩余量的位置。
owner: IT 运维组
source_card_id: 43
tags:
  - 入库
  - 采购订单
  - 常见问题
content_hash: 3907b3ae8c632676
generated_hash: cf58bab046fc6d8b
---
# 入库量超过订单量、申购剩余量、控制点

## 问题描述

业务同事反馈：这个无订单入库，提示入库量超过订单量，提交不了黄经理

## 影响范围

- **影响系统:** 简道云 PM 系统
- **受影响用户:** 入库、对账相关岗位
- **影响数据:** 影响无订单入库提交时的超量判断。

## 原因分析

- 流程规则不清：控制点是申购剩余量，而非申购总量。

## 解决方案

1. 在业务同事截图所指位置查询申购剩余量后判断能否提交

## 预防措施

- 在流程说明中明确相关规则，避免重复咨询。

## 相关页面

- [简道云 PM 系统](../../../systems/jiandaoyun-pm-system.md) — 系统技术文档
- [material-receipt 常见问题](../material-receipt/README.md) — 相关 FAQ 索引

## 变更记录

| 日期 | 作者 | 摘要 |
|-----------|-----------|--------------|
| 2026-11-16 | IT 运维组 | 依据知识卡 #43 提炼创建 |
