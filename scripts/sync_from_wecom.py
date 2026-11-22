# -*- coding: utf-8 -*-
"""Incrementally sync approved IT-ops cards from WeCom smartsheet into FAQ docs.

Design goals (see README "Overall Architecture" section):
  - Primary key = 卡片编号 (source_card_id), never fuzzy text matching.
  - Gate = card's 状态 is 已发布/已审核 (approved only). C-class / unpublished skipped.
  - content_hash: if 聊天原文 (raw chat evidence) is present, hash THAT (raw-first),
    else fall back to the legacy key fields (so the 153 existing docs keep baseline).
    Raw-first means: once the original conversation is corrected/expanded, a reprocess
    is triggered even if the derived fields stayed the same.
  - generated_hash: hash of the body at generation time -> detects human edits.
    If a doc's current body differs from generated_hash, a human edited it ->
    SKIP and report a conflict; NEVER overwrite (the Git repo is the
    human-approved source of truth).
  - Report four buckets: added / updated / conflict-skipped / unchanged.

Usage:
  python scripts/sync_from_wecom.py --input export.json --dry-run
  python scripts/sync_from_wecom.py --input export.json --apply
  python scripts/sync_from_wecom.py --input export.json --apply --report sync_report.json

The input JSON is the raw output of `wecom-cli smartsheet records query`
(shape: {"values":[{"rows":[...]}]}). Minimal deps: Python 3.9+ stdlib only.
"""
import argparse
import hashlib
import json
import os
import re
import sys

# ---------------------------------------------------------------- repo paths
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DOCS = os.path.join(REPO, "docs", "faqs", "jiandaoyun-pm")

# ---------------------------------------------------------------- desensitize
NAMES = ["黄念黄总", "黄念", "张津宁", "津宁总", "陈郁", "韩鸣", "孙建明", "孙江总", "孙江",
         "周伟", "何敏", "刘付茵", "王乐", "陈明胜", "陈明英", "洪熙", "王伟荣", "林健", "李一飞",
         "张总", "黄总", "广昱集团", "PM小资", "戴南晓", "梁家主", "樊朗", "袁小发",
         "汤伟轩", "孔学思", "罗宇晟"]


def clean(text):
    if not text:
        return ""
    s = str(text)
    s = re.sub(r"\[图片\|media_id:[^\]]*\]", "[图片]", s)
    s = s.replace("多选转发begin", "").replace("多选转发end", "")
    s = re.sub(r"\*\*quote\*\*", "", s)
    s = re.sub(r"[\(（][a-z][a-z0-9_]{2,}[\)）]", "", s)
    for n in NAMES:
        s = s.replace("@" + n, "业务同事")
    verbs = "说明|确认|表示|反馈|回复|提到|指出|答复|明确|于\\d|将|建议|解释|补充"
    for n in NAMES:
        s = re.sub(re.escape(n) + r"(?=(?:%s))" % verbs, "IT 运维组", s)
    for n in NAMES:
        s = s.replace(n, "业务同事")
    s = re.sub(r"\b[A-Z]{2,}[A-Z0-9]*-\d{4,}[-\d]*\b", "[单据编号]", s)
    s = re.sub(r"\b\d{8,}\b", "[编号]", s)
    s = re.sub(r"于\s*\d{1,2}[:-]\d{1,2}", "", s)
    s = re.sub(r"(?<![0-9])\d{1,2}[-:]\d{1,2}(?![0-9])", "", s)
    s = s.replace("后续讨论确认", "确认").replace("后续确认", "确认")
    s = re.sub(r"\s+", " ", s).strip()
    s = s.replace("IT 运维组IT 运维组", "IT 运维组").replace("业务同事业务同事", "业务同事")
    return s


# ---------------------------------------------------------------- classify
FORM_MAP = [
    ("nc-integration", ["NC", "nc", "接口同步", "同步失败"]),
    ("invoice-registration", ["发票", "进项票", "开票", "税率"]),
    ("subcontract-payment", ["分包", "付款", "计量", "回退", "流程删除"]),
    ("supplier-penalty", ["扣罚", "供应商处罚", "正负"]),
    ("system-access", ["登录", "SSO", "权限", "账号", "开通", "回收"]),
    ("material-receipt", ["入库", "预入库", "直入直出", "收货", "对账"]),
    ("material-purchase", ["采购订单", "采购合同", "乙方合同", "申购", "招标", "询价", "采购任务", "采购明细"]),
    ("material-inventory", ["出库", "库存", "班组", "工作面", "物资", "领料", "退货", "预出库", "编码"]),
]


def classify(r):
    form = str(r.get("涉及表单名称") or "")
    kw = str(r.get("关键词/摘要") or "")
    tv = r.get("标签")
    tags = " ".join(str(x) for x in tv) if isinstance(tv, list) else str(tv or "")
    blob = form + " " + tags + " " + kw
    for d, kws in FORM_MAP:
        for k in kws:
            if k in blob:
                return d
    if r.get("模块") == "采购模块":
        return "material-purchase"
    if r.get("模块") == "物资模块":
        return "material-inventory"
    return "material-inventory"


SEV = {"全局": "high", "某模块": "medium", "某角色": "medium", "单据与流程": "low"}
RESOLVE = {"配置缺失": "resolved", "流程规则不清": "resolved", "数据异常": "resolved",
           "用户操作": "resolved", "权限配置": "resolved", "系统缺陷": "in-progress",
           "外部系统对接": "in-progress"}


def title_of(r):
    s = clean(r.get("关键词/摘要") or "")
    if not s:
        s = clean(r.get("处理结果一句话") or "")[:30]
    parts = [p.strip() for p in re.split(r"[,，、/]", s) if p.strip()]
    t = "、".join(parts[:3]) if len(parts) >= 2 else s
    return t[:40].rstrip("，,、")


def slug_of(r):
    card = str(r.get("卡片编号") or "x")
    h = hashlib.md5((str(r.get("问题原话")) + card).encode("utf-8")).hexdigest()[:6]
    return "card%s-%s" % (card, h)


def yaml_str(s):
    s = str(s).replace("\r", " ").replace("\n", " ")
    if s == "":
        return '""'
    if any(c in s for c in [":", "#", "[", "]", "{", "}", "&", "*", "!", "|", ">", "'", '"', "%", "@", "`"]) or s.strip() != s:
        s = s.replace("\\", "\\\\").replace('"', '\\"')
        return '"' + s + '"'
    return s


def build_body(r, title, form):
    q = clean(r.get("问题原话") or "")
    res = clean(r.get("处理结果一句话") or "")
    rule = clean(r.get("业务规则与判断逻辑") or "")
    steps = clean(r.get("标准操作步骤") or "")
    note = clean(r.get("注意事项/风险提示") or "")
    root = clean(r.get("根因分类") or "")
    scope = clean(r.get("影响范围说明") or "")
    scope_cat = str(r.get("影响范围分类") or "")
    desc_q = re.sub(r"^业务同事\s*", "", q)
    if len(desc_q) > 180:
        desc_q = desc_q[:180] + "…"
    qsec = "业务同事反馈：" + (desc_q or "相关业务问题") if desc_q else "业务同事反馈相关业务问题。"
    imp = ["- **影响系统:** 简道云 PM 系统"]
    affected = "相关业务岗位"
    for f, a in [("material-receipt", "入库、对账相关岗位"), ("material-purchase", "采购、申购相关岗位"),
                 ("material-inventory", "物资、出库相关岗位"), ("nc-integration", "NC 接口相关岗位"),
                 ("system-access", "系统用户与管理员")]:
        if form == f:
            affected = a
    imp.append("- **受影响用户:** " + affected)
    imp.append("- **影响数据:** " + (scope if scope else ("相关" + (scope_cat or "业务") + "数据")))
    causes = []
    if root:
        causes.append("- " + root + "：" + (rule if rule else (res[:80] if res else "详见解决方案")))
    elif rule:
        causes.append("- " + rule)
    else:
        causes.append("- " + (res[:100] if res else "依据处理记录提炼"))
    if not causes[0].endswith("。"):
        causes[0] += "。"
    sol = []
    if steps:
        for line in re.split(r"[;；\n]|(?<=\。)", steps):
            line = line.strip(" 。;；")
            if line and len(line) > 2:
                sol.append(line)
    if not sol:
        raw = (rule + " " + res).strip()
        parts = [p.strip(" 。;；") for p in re.split(r"[;；]", raw) if p.strip(" 。;；")]
        for p in parts[:4]:
            if len(p) > 3:
                sol.append(p)
    if not sol and res:
        sol = [res]
    if not sol:
        sol = ["依据处理记录执行相应配置或流程调整。"]
    prev = []
    if note:
        prev.append("- " + (note if note.endswith("。") else note + "。"))
    if rule and rule not in " ".join(prev):
        prev.append("- 在流程说明中明确相关规则，避免重复咨询。")
    if not prev:
        prev.append("- 留存处理记录，遇到同类问题可参照本文档。")
    return "\n".join([
        "# " + title, "", "## 问题描述", "", qsec, "",
        "## 影响范围", "", "\n".join(imp), "",
        "## 原因分析", "", "\n".join(causes), "",
        "## 解决方案", "", "\n".join("%d. %s" % (i + 1, s) for i, s in enumerate(sol)), "",
        "## 预防措施", "", "\n".join(prev), "",
        "## 相关页面", "",
        "- [简道云 PM 系统](../../../systems/jiandaoyun-pm-system.md) — 系统技术文档",
        "- [%s 常见问题](../%s/README.md) — 相关 FAQ 索引" % (form, form), "",
        "## 变更记录", "", "| 日期 | 作者 | 摘要 |", "|-----------|-----------|--------------|",
        "| %s | IT 运维组 | 依据知识卡 #%s 提炼创建 |" % (
            str(r.get("处理日期") or "2026-01-01")[:10], str(r.get("卡片编号") or "")), "",
    ])


def build_yaml(r, title, form, content_hash, generated_hash, extra=None):
    date = str(r.get("处理日期") or "2026-01-01")[:10]
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
        date = "2026-01-01"
    root = str(r.get("根因分类") or "")
    sev = SEV.get(str(r.get("影响范围分类") or ""), "medium")
    res = RESOLVE.get(root, "resolved")
    desc = clean(r.get("处理结果一句话") or r.get("业务规则与判断逻辑") or "")[:120]
    tags = []
    tv = r.get("标签")
    if isinstance(tv, list):
        tags = [str(x) for x in tv]
    elif tv:
        tags = [str(tv)]
    lines = ["---", "title: " + yaml_str(title), "type: faq",
             "related_system: 简道云 PM 系统", "related_form: " + form,
             "severity: " + sev, "resolution: " + res, "last_reviewed: " + date,
             "description: " + yaml_str(desc if desc else title), "owner: IT 运维组",
             "source_card_id: " + yaml_str(str(r.get("卡片编号") or "")),
             "content_hash: " + content_hash, "generated_hash: " + generated_hash]
    if tags:
        lines.append("tags:")
        lines += ["  - " + yaml_str(t) for t in tags[:6]]
    else:
        lines.append("tags: []")
    if extra:
        for k, v in extra.items():
            lines.append("%s: %s" % (k, yaml_str(v)))
    lines.append("---")
    return "\n".join(lines)


# ---------------------------------------------------------------- hashing
KEY_FIELDS = ["问题原话", "处理结果一句话", "业务规则与判断逻辑", "标准操作步骤",
              "注意事项/风险提示", "根因分类", "关键词/摘要", "标签", "适用系统/流程",
              "影响范围说明", "影响范围分类", "涉及表单名称", "处理日期"]

RAW_FIELD = "聊天原文"  # raw, immutable chat evidence; the authoritative source for reprocessing


def raw_text_of(r):
    """Return the raw chat transcript for a card (may be empty for legacy cards)."""
    v = r.get(RAW_FIELD)
    if isinstance(v, list):  # defensive: text normally returns str
        return "\n".join(str(x) for x in v)
    return str(v or "").strip()


def content_hash_of(r):
    """Raw-first hashing.

    If the card carries 聊天原文 (new pattern), hash the raw transcript itself:
    any fix/addition to the original evidence triggers a reprocess, regardless of
    whether the derived (AI-summarised) fields changed. Otherwise fall back to the
    legacy key-field hash so the 153 already-basedlined docs stay unchanged.
    """
    raw = raw_text_of(r)
    if raw:
        payload = {"__raw__": raw}
    else:
        payload = {k: r.get(k) for k in KEY_FIELDS}
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]


def body_hash_of(body):
    return hashlib.sha256(body.strip().encode("utf-8")).hexdigest()[:16]


def split_doc(path):
    """Return (frontmatter dict-ish raw lines, body string) or (None, None)."""
    text = open(path, encoding="utf-8").read().replace("\r", "")
    if not text.startswith("---"):
        return None, None
    end = text.find("\n---", 3)
    if end < 0:
        return None, None
    fm = text[3:end].strip("\n")
    body = text[end + 4:].strip("\n")
    return fm, body


def fm_value(fm, key):
    m = re.search(r"^%s:\s*(.+)$" % re.escape(key), fm, re.M)
    return m.group(1).strip().strip('"') if m else None


# ---------------------------------------------------------------- index docs
def index_existing():
    """Map source_card_id -> (path, fm, body, generated_hash)."""
    idx = {}
    for root, _, files in os.walk(DOCS):
        for f in files:
            if not f.endswith(".md") or f == "README.md":
                continue
            p = os.path.join(root, f)
            fm, body = split_doc(p)
            if fm is None:
                continue
            sid = fm_value(fm, "source_card_id")
            if sid:
                idx[str(sid).strip()] = (p, fm, body, fm_value(fm, "generated_hash"))
    return idx


# ---------------------------------------------------------------- gate
def gate_pass(r):
    dep = str(r.get("沉淀类型") or "")
    st = r.get("状态")
    if isinstance(st, list) and st:
        st = st[0].get("text") if isinstance(st[0], dict) else str(st[0])
    st = str(st or "")
    return dep.startswith("B") and st in ("已发布", "已审核")


def rows_of(data):
    vals = data.get("values", [])
    v = vals[0] if vals else {}
    if isinstance(v, str):
        v = json.loads(v)
    return v.get("rows", [])


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Path to wecom records-query JSON")
    ap.add_argument("--apply", action="store_true", help="Write changes (default: dry-run)")
    ap.add_argument("--report", help="Write JSON report to this path")
    args = ap.parse_args()

    data = json.load(open(args.input, encoding="utf-8"))
    rows = rows_of(data)
    idx = index_existing()
    print("表格记录: %d | 现有FAQ文档(带溯源): %d" % (len(rows), len(idx)))

    report = {"added": [], "updated": [], "conflict": [], "unchanged": [], "baseline": [],
              # written: 本次 --apply 真正写入/建立基线的卡片，供后端反写表格状态用。
              # 每项含 card(卡片编号) 与 record_id(表格行主键)。conflict/unchanged 不在内。
              "written": []}
    total_gate = 0
    for r in rows:
        if not gate_pass(r):
            continue
        total_gate += 1
        card = str(r.get("卡片编号") or "").strip()
        chash = content_hash_of(r)
        if card not in idx:
            report["added"].append(card)
            if args.apply:
                form = classify(r)
                title = title_of(r)
                body = build_body(r, title, form)
                ghash = body_hash_of(body)
                content = build_yaml(r, title, form, chash, ghash) + "\n" + body
                folder = os.path.join(DOCS, form)
                os.makedirs(folder, exist_ok=True)
                path = os.path.join(folder, slug_of(r) + ".md")
                with open(path, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(content)
                report["written"].append({"card": card,
                                          "record_id": str(r.get("RECORD_ID") or "").strip()})
            continue

        path, fm, body, ghash = idx[card]
        fm_chash = fm_value(fm, "content_hash")
        if not ghash:
            # Old doc generated before hash tracking -> establish baseline.
            # Preserve existing frontmatter AND body verbatim; only append hash fields.
            report["baseline"].append(card)
            if args.apply:
                gh = body_hash_of(body)
                lines = [ln for ln in fm.split("\n")
                         if not re.match(r"^(content_hash|generated_hash):", ln)]
                lines.append("content_hash: " + (fm_chash or chash))
                lines.append("generated_hash: " + gh)
                with open(path, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write("---\n" + "\n".join(lines) + "\n---\n" + body + "\n")
                report["written"].append({"card": card,
                                          "record_id": str(r.get("RECORD_ID") or "").strip()})
            continue

        cur_body_hash = body_hash_of(body)
        if cur_body_hash != ghash:
            # Human edited the body -> protect it, skip, report conflict.
            report["conflict"].append({"card": card, "path": os.path.relpath(path, REPO)})
            continue
        if fm_chash == chash:
            report["unchanged"].append(card)
            continue
        # Table changed, body untouched by human -> regenerate.
        report["updated"].append(card)
        if args.apply:
            form = classify(r)
            title = title_of(r)
            new_body = build_body(r, title, form)
            new_ghash = body_hash_of(new_body)
            content = build_yaml(r, title, form, chash, new_ghash) + "\n" + new_body
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(content)
            report["written"].append({"card": card,
                                      "record_id": str(r.get("RECORD_ID") or "").strip()})

    print("\n闸门内卡片: %d" % total_gate)
    for k in ("added", "updated", "conflict", "unchanged", "baseline", "written"):
        print("  %-10s %d" % (k, len(report[k])))
    if args.report:
        json.dump(report, open(args.report, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print("报告已写入:", args.report)
    if not args.apply:
        print("\n[DRY-RUN] 未写入任何文件。加 --apply 正式执行。")


if __name__ == "__main__":
    main()
