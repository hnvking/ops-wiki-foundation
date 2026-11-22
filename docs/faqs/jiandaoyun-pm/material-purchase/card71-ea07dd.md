---
title: 采购执行人显示为发起人、激活给订单组负责人
type: faq
related_system: 简道云 PM 系统
related_form: material-purchase
severity: medium
resolution: resolved
last_reviewed: 2026-11-09
description: 因未选择相应标志导致没有对应采购执行人，已帮忙激活给订单组负责人。
owner: IT 运维组
source_card_id: 71
tags:
  - 审批流
problem_type: 审批流与权限
content_hash: f0869486d6d316ee
generated_hash: 0971b1544b2ab7e2
---
# 采购执行人显示为发起人、激活给订单组负责人

## 问题描述

业务同事反馈：黄经理：这两个流程我发起，怎么采购执行人还是我？

## 影响范围

- **影响系统:** 简道云 PM 系统
- **受影响用户:** 采购、申购相关岗位
- **影响数据:** 相关某角色数据

## 原因分析

- 配置缺失：是否选择对应标志决定是否有采购执行人，未选则默认发起人为采购执行人。

## 解决方案

1. 由管理员激活流程给订单组负责人

## 预防措施

- 在流程说明中明确相关规则，避免重复咨询。

## 相关页面

- [简道云 PM 系统](../../../systems/jiandaoyun-pm-system.md) — 系统技术文档
- [material-purchase 常见问题](../material-purchase/README.md) — 相关 FAQ 索引

## 变更记录

| 日期 | 作者 | 摘要 |
|-----------|-----------|--------------|
| 2026-11-09 | IT 运维组 | 依据知识卡 #71 提炼创建 |
