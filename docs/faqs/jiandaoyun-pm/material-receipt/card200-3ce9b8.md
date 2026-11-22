---
title: 对账单、月份选择、直入直出
type: faq
related_system: 简道云 PM 系统
related_form: material-receipt
severity: low
resolution: resolved
last_reviewed: 2026-11-02
description: 答复这3张都是10月份的，对账单也要选到10月份才能选到。
owner: IT 运维组
source_card_id: 200
tags:
  - 对账
  - 入库
content_hash: d62a91fa822aa39e
generated_hash: 48fda47ffb7e83dc
---
# 对账单、月份选择、直入直出

## 问题描述

业务同事反馈：亿创这家 10 月份的对账单流程按照你提示的操作还是只能关联到 9 张入库单信息 另外三张直入直出单流程都过了也没看到对应入库单信息[叹气]

## 影响范围

- **影响系统:** 简道云 PM 系统
- **受影响用户:** 入库、对账相关岗位
- **影响数据:** 只能关联到9张入库单信息，另外3张直入直出单未看到对应入库单信息

## 原因分析

- 用户操作：对账单月份范围需覆盖待关联单据月份；10月份单据要选到10月份才能选到。

## 解决方案

1. 发起对账单时选择对应月份范围，使其覆盖10月份单据

## 预防措施

- 对账单月份未选到对应月份会导致关联不到入库单。
- 在流程说明中明确相关规则，避免重复咨询。

## 相关页面

- [简道云 PM 系统](../../../systems/jiandaoyun-pm-system.md) — 系统技术文档
- [material-receipt 常见问题](../material-receipt/README.md) — 相关 FAQ 索引

## 变更记录

| 日期 | 作者 | 摘要 |
|-----------|-----------|--------------|
| 2026-11-02 | IT 运维组 | 依据知识卡 #200 提炼创建 |
