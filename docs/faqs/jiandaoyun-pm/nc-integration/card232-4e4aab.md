---
title: 英德项目入库单因超申购量删除且NC关账后无法删除
type: faq
related_system: 简道云 PM 系统
related_form: nc-integration
severity: low
resolution: in-progress
last_reviewed: 2026-11-16
description: IT 运维组答复应该是超申购量了，IT 运维组说明启光已没有但NC有且NC已关账删不掉。
owner: IT 运维组
source_card_id: 232
tags:
  - 入库
  - NC同步
content_hash: 6882c72f66d88446
generated_hash: d99fabe98de899e7
---
# 英德项目入库单因超申购量删除且NC关账后无法删除

## 问题描述

业务同事反馈：PMCLRKD-W-202610-[编号] PMCLRKD-W-202610-[编号] 英德项目的，是删了这两个入库单号吗

## 影响范围

- **影响系统:** 简道云 PM 系统
- **受影响用户:** NC 接口相关岗位
- **影响数据:** 相关单据与流程数据

## 原因分析

- 外部系统对接：入库单被删除与超申购量有关；NC已关账后对应单据删不掉，启光与NC数据不一致。

## 解决方案

1. 入库单被删除与超申购量有关
2. NC已关账后对应单据删不掉，启光与NC数据不一致 IT 运维组答复应该是超申购量了，IT 运维组说明启光已没有但NC有且NC已关账删不掉

## 预防措施

- NC已关账时无法删除对应单据。
- 在流程说明中明确相关规则，避免重复咨询。

## 相关页面

- [简道云 PM 系统](../../../systems/jiandaoyun-pm-system.md) — 系统技术文档
- [nc-integration 常见问题](../nc-integration/README.md) — 相关 FAQ 索引

## 变更记录

| 日期 | 作者 | 摘要 |
|-----------|-----------|--------------|
| 2026-11-16 | IT 运维组 | 依据知识卡 #232 提炼创建 |
