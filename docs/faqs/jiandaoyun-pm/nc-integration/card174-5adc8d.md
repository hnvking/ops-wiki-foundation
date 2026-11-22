---
title: 分包付款、NC同步结果、流程插件
type: faq
related_system: 简道云 PM 系统
related_form: nc-integration
severity: low
resolution: in-progress
last_reviewed: 2026-10-21
description: 明确付款单已修改为按流程插件推给NC、原智能助手后续不再推NC，付款单根据修改表体数据触发后推给NC，并提议增加同步NC结果字段作为最终结果判断。
owner: IT 运维组
source_card_id: 174
tags:
  - NC同步
  - 对账
problem_type: 配置与报表
content_hash: 65f90bdf5384fefa
generated_hash: 2e1be6aab6014ab1
---
# 分包付款、NC同步结果、流程插件

## 问题描述

业务同事反馈：我有个问题想问一下，这个分包付款，NC同步结果是怎么样填入的

## 影响范围

- **影响系统:** 简道云 PM 系统
- **受影响用户:** NC 接口相关岗位
- **影响数据:** 分包付款/付款单NC同步触发方式及同步结果字段

## 原因分析

- 外部系统对接：付款单根据修改表体数据触发后推给NC；现已改为按流程插件推给NC，原来的智能助手后续不会推给NC。

## 解决方案

1. 付款单根据修改表体数据触发后推给NC
2. 现已改为按流程插件推给NC，原来的智能助手后续不会推给NC。 明确付款单已修改为按流程插件推给NC、原智能助手后续不再推NC，付款单根据修改表体数据触发后推给NC，并提议增加同步NC结果字段作为最终结果判断

## 预防措施

- 若仍依赖原智能助手推NC，改造后将不再生效；可增加字段作为同步NC最终结果的判断依据。
- 在流程说明中明确相关规则，避免重复咨询。

## 相关页面

- [简道云 PM 系统](../../../systems/jiandaoyun-pm-system.md) — 系统技术文档
- [nc-integration 常见问题](../nc-integration/README.md) — 相关 FAQ 索引

## 变更记录

| 日期 | 作者 | 摘要 |
|-----------|-----------|--------------|
| 2026-10-21 | IT 运维组 | 依据知识卡 #174 提炼创建 |
