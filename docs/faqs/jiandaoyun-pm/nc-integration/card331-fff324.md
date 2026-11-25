---
title: "pk_dept[01]、NC部门、部门编码"
type: faq
related_system: 简道云 PM 系统
related_form: nc-integration
severity: low
resolution: resolved
last_reviewed: 2026-11-25
description: "已解释 pk_dept[01] 未匹配到 NC 部门数据的原因，并提示不能随意删除部门，需重选部门带出"
owner: IT 运维组
source_card_id: 331
problem_type: 系统对接与集成
content_hash: 6f3dcb6172590d5d
generated_hash: 3603ead8b3fc142d
tags:
  - NC同步
---
# pk_dept[01]、NC部门、部门编码

## 问题描述

业务同事反馈：请问这个如何处理呢？

## 影响范围

- **影响系统:** 简道云 PM 系统
- **受影响用户:** NC 接口相关岗位
- **影响数据:** 相关单据与流程数据

## 原因分析

- 配置缺失：没有带 B 字母开头的都不是部门或部门编码不对；带 B 但匹配不上可能是非一级部门编码、部门不在所属公司下或 NC 没有该部门；01 是资源环保的编码。

## 解决方案

1. 没有带 B 字母开头的都不是部门或部门编码不对
2. 带 B 但匹配不上可能是非一级部门编码、部门不在所属公司下或 NC 没有该部门
3. 01 是资源环保的编码 已解释 pk_dept[01] 未匹配到 NC 部门数据的原因，并提示不能随意删除部门，需重选部门带出

## 预防措施

- 三个部门没有问题，不能删除，影响企微和 OA。
- 在流程说明中明确相关规则，避免重复咨询。

## 相关页面

- [简道云 PM 系统](../../../systems/jiandaoyun-pm-system.md) — 系统技术文档
- [nc-integration 常见问题](../nc-integration/README.md) — 相关 FAQ 索引

## 变更记录

| 日期 | 作者 | 摘要 |
|-----------|-----------|--------------|
| 2026-11-25 | IT 运维组 | 依据知识卡 #331 提炼创建 |
