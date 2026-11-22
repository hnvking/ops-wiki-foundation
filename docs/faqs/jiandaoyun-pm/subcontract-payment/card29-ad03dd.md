---
title: 对账单、无合同、订单通过
type: faq
related_system: 简道云 PM 系统
related_form: subcontract-payment
severity: low
resolution: resolved
last_reviewed: 2026-10-31
description: IT 运维组明确对账等订单通过再提交，否则对账没有意义。
owner: IT 运维组
source_card_id: 29
tags:
  - 对账
  - 采购订单
  - 审批流
problem_type: 审批流与权限
content_hash: e472381815209597
generated_hash: 4be27676218ddbe7
---
# 对账单、无合同、订单通过

## 问题描述

业务同事反馈：这个入库单单价没问题。但是涉及到做对账单，只能选无合同的，选有合同就带不出入库明细。因为之前做预入库合同还没下来，所以选的无合同。 像这种情况，后续会不会影响供应链的付款流程这些，如果没影响对账就可以直接提交。

## 影响范围

- **影响系统:** 简道云 PM 系统
- **受影响用户:** 相关业务岗位
- **影响数据:** 影响预入库无合同场景下的对账单提交时机。

## 原因分析

- 流程规则不清：订单通过之后才能提交对账，订单未通过时对账没有意义。

## 解决方案

1. 等待订单审批通过后再提交对账单

## 预防措施

- 在流程说明中明确相关规则，避免重复咨询。

## 相关页面

- [简道云 PM 系统](../../../systems/jiandaoyun-pm-system.md) — 系统技术文档
- [subcontract-payment 常见问题](../subcontract-payment/README.md) — 相关 FAQ 索引

## 变更记录

| 日期 | 作者 | 摘要 |
|-----------|-----------|--------------|
| 2026-10-31 | IT 运维组 | 依据知识卡 #29 提炼创建 |
