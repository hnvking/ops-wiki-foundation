---
title: 无订单入库对账关联不到、订单未走完
type: faq
related_system: 简道云 PM 系统
related_form: material-receipt
severity: low
resolution: resolved
last_reviewed: 2026-11-06
description: 对应订单没走完导致发起不了对账单，需等入库单上有订单编号后再发起。
owner: IT 运维组
source_card_id: 69
tags:
  - 对账
  - 入库
  - 采购订单
content_hash: 3907b3ae8c632676
generated_hash: d079442cf776b037
---
# 无订单入库对账关联不到、订单未走完

## 问题描述

业务同事反馈：无订单入库 对不了帐 关联不来

## 影响范围

- **影响系统:** 简道云 PM 系统
- **受影响用户:** 入库、对账相关岗位
- **影响数据:** 相关单据与流程数据

## 原因分析

- 流程规则不清：对应订单流程走完会反写入库单订单编号，有订单编号后才能做对账单。

## 解决方案

1. 等采购订单流程结束并反写入库单订单编号后，再发起对账单

## 预防措施

- 在流程说明中明确相关规则，避免重复咨询。

## 相关页面

- [简道云 PM 系统](../../../systems/jiandaoyun-pm-system.md) — 系统技术文档
- [material-receipt 常见问题](../material-receipt/README.md) — 相关 FAQ 索引

## 变更记录

| 日期 | 作者 | 摘要 |
|-----------|-----------|--------------|
| 2026-11-06 | IT 运维组 | 依据知识卡 #69 提炼创建 |
