"""
FastAPI 后端 —— ops-wiki-foundation 的 Markdown 在线编辑与校验触发服务。

端点：
    GET  /api/files                 列出 docs/ 下所有 .md 相对路径
    GET  /api/files/{file_path:path} 读取指定 Markdown 文件内容
    PUT  /api/files/{file_path:path} 写入指定 Markdown 文件内容
    POST /api/validate              运行 scripts/validate_docs.py 校验脚本

路径安全：所有文件读写均通过 resolve() + is_relative_to(DOCS_DIR) 双重校验，
拒绝任何 ../ 遍历或逃逸 docs/ 目录的访问（返回 403）。

运行：
    uvicorn backend.main:app --reload --port 8000
"""

import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# 路径常量（跨平台，使用 pathlib）
# ---------------------------------------------------------------------------

# 项目根目录：backend/main.py 的上级目录
BASE_DIR = Path(__file__).resolve().parent.parent
# 文档目录：docs/
DOCS_DIR = BASE_DIR / "docs"
# 校验脚本：scripts/validate_docs.py
VALIDATE_SCRIPT = BASE_DIR / "scripts" / "validate_docs.py"
# 表格 → 项目 同步脚本与固定输入快照（输入含聊天原文证据层，放 exports/ 已被 gitignore）
SYNC_SCRIPT = BASE_DIR / "scripts" / "sync_from_wecom.py"
SYNC_INPUT = BASE_DIR / "exports" / "wecom_cards.json"
NAV_SCRIPTS = [
    BASE_DIR / "scripts" / "build_sidebar_by_type.py",
    BASE_DIR / "scripts" / "build_faq_index.py",
]
REVIEW_SCRIPT = BASE_DIR / "scripts" / "feedback_review.py"
REVIEW_REPORT = BASE_DIR / "exports" / "feedback_review.md"
WEKNORA_EXPORT_SCRIPT = BASE_DIR / "scripts" / "export_for_weknora.py"
WEKNORA_EXPORT = BASE_DIR / "exports" / "weknora_import.json"
RAG_EXPORT = BASE_DIR / "exports" / "docs_export.json"
# 刷新按钮：企微 CLI 可执行文件路径。启动时解析绝对路径——Windows 上 wecom-cli 是
# .CMD 脚本，subprocess 只用裸命令名会 FileNotFoundError，必须用 which() 解析出的全路径。
WECOM_CLI = shutil.which("wecom-cli") or "wecom-cli"
WECOM_DOCID = "s3_AfsAUAYsANQCNg6CtWWh8RnK0zr3K"
WECOM_SHEET = "PM运维知识卡"
# 刷新只拉「已审核」卡片——表格即待处理队列：人工审核标「已审核」→ 刷新进快照 →
# 写入 Wiki 后自动反写为「已发布」→ 下次刷新不再拉到。RECORD_ID 是反写表格的主键。
REFRESH_SQL = (
    "SELECT `RECORD_ID`, `卡片编号`, `沉淀类型`, `状态`, `问题原话`, `处理结果一句话`, "
    "`业务规则与判断逻辑`, `标准操作步骤`, `注意事项/风险提示`, `根因分类`, "
    "`关键词/摘要`, `标签`, `适用系统/流程`, `影响范围说明`, `影响范围分类`, "
    "`涉及表单名称`, `模块`, `问题类型`, "
    "DATE_FORMAT(`处理日期`, \"%Y-%m-%d\") AS `处理日期`, `聊天原文`, "
    "`复用次数`, `满意度评分`, "
    "DATE_FORMAT(`最后复核日期`, \"%Y-%m-%d\") AS `最后复核日期` "
    f"FROM `{WECOM_SHEET}` WHERE `状态` = '已审核' LIMIT 500"
)
# 反写：写入成功后把对应表格行状态改成「已发布」（单选选项 ID JdaNKJ）
WRITEBACK_STATUS_TEXT = "已发布"
WRITEBACK_STATUS_ID = "JdaNKJ"
# Python 解释器：优先使用当前解释器，保证与运行后端的解释器一致
PYTHON = sys.executable or "python"


def resolve_docs_path(file_path: str) -> Path:
    """
    解析并校验文件路径，确保最终路径严格位于 DOCS_DIR 之内。

    任一环节失败都会抛出 HTTPException(403)，防止路径遍历攻击。

    校验逻辑：
        1. 拼接成绝对路径并 resolve()，消除 ..、.、符号链接。
        2. 用 is_relative_to(DOCS_DIR) 确认最终路径仍在 docs/ 内。
        3. 额外确认最终路径确实是 .md 文件（可选防御）。
    """
    # 归一化：去掉前导斜杠/反斜杠，避免 /etc/passwd 或 \\server\\share 之类
    # 被当作相对路径拼进 DOCS_DIR。
    cleaned = str(file_path).replace("\\", "/").lstrip("/")
    if not cleaned:
        raise HTTPException(status_code=403, detail="空文件路径被拒绝")

    candidate = (DOCS_DIR / cleaned).resolve()
    docs_root = DOCS_DIR.resolve()

    # 必须在 docs/ 内，且不能是 docs/ 本身
    if candidate == docs_root or not candidate.is_relative_to(docs_root):
        raise HTTPException(
            status_code=403,
            detail=f"路径访问被拒绝：{file_path} 不在 docs/ 目录内",
        )

    return candidate


# ---------------------------------------------------------------------------
# 导航注册辅助：新页面创建成功后，自动把链接加进 _sidebar.md 和分类 README
# ---------------------------------------------------------------------------

def extract_title(content: str) -> str:
    """从 Markdown frontmatter 中提取 title 字段；取不到则回退到第一个 # 标题。"""
    m = re.search(r"^---\s*\n(.*?)\n---", content, re.S)
    if m:
        fm = m.group(1)
        tm = re.search(r"^title:\s*[\"']?([^\"'\n]+)", fm, re.M)
        if tm:
            return tm.group(1).strip()
    hm = re.search(r"^#\s+(.+)$", content, re.M)
    if hm:
        return hm.group(1).strip()
    return "新页面"


CN_NUMERALS = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]


def strip_sidebar_number(text: str) -> str:
    """去掉侧边栏链接文字上已有的编号，只保留标题本身。"""
    return re.sub(
        r"^(?:[零一二三四五六七八九十]+、|\d+(?:\.\d+)*[、.]?\s+)", "", text
    ).strip()


def renumber_sidebar() -> None:
    """按缩进层级重排侧边栏编号：顶层「一、」，子层「1.1」「1.1.1」。"""
    sidebar_path = BASE_DIR / "_sidebar.md"
    if not sidebar_path.exists():
        return
    try:
        lines = sidebar_path.read_text(encoding="utf-8").split("\n")
    except OSError:
        return

    counters: dict[int, int] = {}
    stack: list[tuple[int, str]] = []
    out = []
    link_re = re.compile(r"^(\s*)-\s+\[([^\]]+)\]\(([^)]+)\)")

    for line in lines:
        match = link_re.match(line)
        if not match:
            out.append(line)
            continue

        indent = len(match.group(1))
        title = strip_sidebar_number(match.group(2))
        target = match.group(3)

        # 首页不参与编号，并重置计数器
        if target == "/":
            out.append(line)
            counters = {}
            stack = []
            continue

        # 层级变浅时清理更深层计数器；每层各自计数
        for key in list(counters):
            if key > indent:
                del counters[key]
        while stack and stack[-1][0] >= indent:
            stack.pop()

        if indent == 0 or not stack:
            counters[0] = counters.get(0, 0) + 1
            index = counters[0]
            label = CN_NUMERALS[index] if index < len(CN_NUMERALS) else str(index)
            new_title = f"{label}、{title}"
            stack = [(0, str(index))]
        else:
            parent_prefix = stack[-1][1]
            counters[indent] = counters.get(indent, 0) + 1
            number = f"{parent_prefix}.{counters[indent]}"
            new_title = f"{number} {title}"
            stack.append((indent, number))

        out.append(f"{' ' * indent}- [{new_title}]({target})")

    try:
        sidebar_path.write_text("\n".join(out), encoding="utf-8")
    except OSError:
        pass


def sidebar_parent_target(file_path: str) -> str:
    """根据文档路径找到它在侧边栏中的父级索引页链接。"""
    parts = file_path.split("/")
    category = parts[0]
    if category == "faqs" and len(parts) >= 4:
        # faqs/<系统>/<表单>/<问题>.md → 表单 README
        return "docs/" + "/".join(parts[:-1]) + "/README.md"
    if category == "faqs" and len(parts) == 3:
        return f"docs/faqs/{parts[1]}/README.md"
    return f"docs/{category}/README.md"


def register_new_page(file_path: str, content: str) -> None:
    """
    把新创建的页面注册进导航：
      1. _sidebar.md 中按其父级索引页插入子链接，随后整体重排编号
      2. 对应 README.md 的索引区追加链接（FAQ 追加到表单 README）

    file_path 为相对 docs/ 的路径（如 systems/foo.md），content 为新文件全文。
    """
    file_path = file_path.replace("\\", "/").lstrip("/")
    parts = file_path.split("/")
    if len(parts) < 2:
        return  # 不在分类子目录内，不处理
    category = parts[0]
    filename = parts[-1]
    title = extract_title(content)
    doc_link = f"docs/{file_path}"

    # ---- 1. 更新 _sidebar.md ----
    sidebar_path = BASE_DIR / "_sidebar.md"
    try:
        sidebar_text = sidebar_path.read_text(encoding="utf-8") if sidebar_path.exists() else ""
    except OSError:
        sidebar_text = ""

    if f"]({doc_link})" not in sidebar_text:
        parent_target = sidebar_parent_target(file_path)
        lines = sidebar_text.split("\n")
        parent_index = None
        for i, line in enumerate(lines):
            if line.strip().endswith(f"]({parent_target})"):
                parent_index = i
                break

        if parent_index is None:
            # 父级不存在时退化为分类索引页，仍找不到就放到末尾
            parent_target = f"docs/{category}/README.md"
            for i, line in enumerate(lines):
                if line.strip().endswith(f"]({parent_target})"):
                    parent_index = i
                    break

        if parent_index is None:
            child_indent = 2
            insert_at = len(lines)
        else:
            parent_indent = len(lines[parent_index]) - len(lines[parent_index].lstrip(" "))
            child_indent = parent_indent + 2
            insert_at = parent_index + 1
            # 跳过父项下的整棵子树，插到末尾
            while insert_at < len(lines):
                current = lines[insert_at]
                current_indent = len(current) - len(current.lstrip(" "))
                if current.strip() and current_indent > parent_indent:
                    insert_at += 1
                else:
                    break

        lines.insert(insert_at, f"{' ' * child_indent}- [{title}]({doc_link})")
        try:
            sidebar_path.write_text("\n".join(lines), encoding="utf-8")
        except OSError:
            pass
        renumber_sidebar()

    # ---- 2. 更新对应的 README.md ----
    readme_path = DOCS_DIR.joinpath(*parts[:-1], "README.md")
    category_readme = DOCS_DIR / category / "README.md"
    if not readme_path.exists():
        readme_path = category_readme
    nested = readme_path.parent != category_readme.parent

    try:
        readme_text = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""
    except OSError:
        readme_text = ""

    if filename not in readme_text:
        rel_link = filename if nested else doc_link
        entry = f"- [{title}]({rel_link})" if nested else f"- [{filename}]({rel_link}) — {title}"
        section = next(
            (s for s in ("## FAQ 索引", "## 示例", "## 页面") if s in readme_text),
            None,
        )
        if section is None:
            readme_text = readme_text.rstrip("\n") + f"\n\n## 页面\n\n{entry}\n"
        else:
            lines = readme_text.split("\n")
            idx = next(i for i, line in enumerate(lines) if line.strip() == section)
            insert_at = idx + 1
            while insert_at < len(lines) and not lines[insert_at].strip().startswith("## "):
                insert_at += 1
            while insert_at > idx + 1 and not lines[insert_at - 1].strip():
                insert_at -= 1
            lines.insert(insert_at, entry)
            readme_text = "\n".join(lines)
        try:
            readme_path.write_text(readme_text, encoding="utf-8")
        except OSError:
            pass


def unregister_page(file_path: str) -> None:
    """
    从导航中移除指定页面的链接（删除文档时调用），并重排侧边栏编号。
    file_path 为相对 docs/ 的路径（如 systems/foo.md）。
    """
    file_path = file_path.replace("\\", "/").lstrip("/")
    parts = file_path.split("/")
    if len(parts) < 2:
        return
    category = parts[0]
    filename = parts[-1]
    link_target = f"docs/{file_path}"

    # ---- 1. 从 _sidebar.md 移除 ----
    sidebar_path = BASE_DIR / "_sidebar.md"
    if sidebar_path.exists():
        try:
            lines = sidebar_path.read_text(encoding="utf-8").split("\n")
        except OSError:
            lines = []
        new_lines = [ln for ln in lines if f"]({link_target})" not in ln]
        if len(new_lines) != len(lines):
            try:
                sidebar_path.write_text("\n".join(new_lines), encoding="utf-8")
            except OSError:
                pass
            renumber_sidebar()

    # ---- 2. 从对应 README.md 移除 ----
    readme_path = DOCS_DIR.joinpath(*parts[:-1], "README.md")
    category_readme = DOCS_DIR / category / "README.md"
    candidates = [readme_path]
    if readme_path != category_readme:
        candidates.append(category_readme)
    for path in candidates:
        if not path.exists():
            continue
        try:
            lines = path.read_text(encoding="utf-8").split("\n")
        except OSError:
            continue
        new_lines = [
            ln for ln in lines
            if link_target not in ln and not (ln.strip().startswith("- [") and f"]({filename})" in ln)
        ]
        if len(new_lines) != len(lines):
            try:
                path.write_text("\n".join(new_lines), encoding="utf-8")
            except OSError:
                pass


# ---------------------------------------------------------------------------
# FastAPI 应用与 CORS
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Ops Wiki 编辑服务",
    description="为 Docsify 前端提供 Markdown 在线编辑与校验触发能力",
    version="1.0.0",
)

# CORS：允许局域网内各设备的来源访问。
# 本服务是纯局域网内部运维知识库（含编辑/校验），允许任意来源即可满足
# 局域网内同网段设备经 http://<本机IP>:8000 的访问。
# 如需严格限制，可改为 allow_origins=["http://192.168.1.10:8000", ...] 白名单。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class FileContent(BaseModel):
    """PUT /api/files 的请求体。"""

    content: str


class FilePathContent(BaseModel):
    """POST /api/validate-content 与 POST /api/files 的请求体。"""

    path: str
    content: str


class FeedbackPayload(BaseModel):
    """FAQ 反馈写回请求体。"""

    source_card_id: str
    rating: Optional[int] = None


# ---------------------------------------------------------------------------
# API 端点
# ---------------------------------------------------------------------------


@app.get("/api/files", response_model=List[str])
def list_files() -> List[str]:
    """递归列出 docs/ 下所有 .md 文件，返回相对于 docs/ 的 POSIX 路径。"""
    if not DOCS_DIR.exists():
        return []
    files = sorted(
        p.relative_to(DOCS_DIR).as_posix()
        for p in DOCS_DIR.rglob("*.md")
        if p.is_file()
    )
    return files


@app.get("/api/systems", response_model=List[str])
def list_systems() -> List[str]:
    """列出 docs/systems/ 下所有已登记系统的 title 名称，供「所属系统」下拉选择。"""
    systems_dir = DOCS_DIR / "systems"
    if not systems_dir.exists():
        return []
    titles = []
    for p in sorted(systems_dir.rglob("*.md")):
        if p.name == "README.md" or not p.is_file():
            continue
        try:
            content = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        title = extract_title(content)
        if title and title != "新页面":
            titles.append(title)
    # 去重并保持顺序
    seen = set()
    unique = []
    for t in titles:
        if t not in seen:
            seen.add(t)
            unique.append(t)
    return unique


@app.get("/api/forms/{system_slug}")
def list_forms(system_slug: str) -> list[dict]:
    """列出某系统下已建的表单目录，供 FAQ「所属表单」下拉选择。"""
    if not re.fullmatch(r"[A-Za-z0-9_-]+", system_slug):
        raise HTTPException(status_code=400, detail="系统标识不合法")
    system_dir = DOCS_DIR / "faqs" / system_slug
    if not system_dir.exists():
        return []

    forms = []
    for form_dir in sorted(p for p in system_dir.iterdir() if p.is_dir()):
        label = form_dir.name
        readme = form_dir / "README.md"
        if readme.exists():
            try:
                text = readme.read_text(encoding="utf-8")
                match = re.search(r"^#\s+(.+)$", text, re.M)
                if match:
                    label = match.group(1).strip()
            except (OSError, UnicodeDecodeError):
                pass
        forms.append({"value": form_dir.name, "label": label})
    return forms


@app.get("/api/files/{file_path:path}")
def read_file(file_path: str) -> dict:
    """读取指定 Markdown 文件，返回 {"path": ..., "content": ...}。"""
    target = resolve_docs_path(file_path)
    if not target.exists():
        raise HTTPException(status_code=404, detail=f"文件不存在：{file_path}")
    if not target.is_file():
        raise HTTPException(status_code=400, detail=f"不是常规文件：{file_path}")

    try:
        content = target.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # 兼容非 UTF-8 文件（如 GBK），使用替换策略避免崩溃
        content = target.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"读取失败：{exc}")

    return {"path": file_path, "content": content}


@app.put("/api/files/{file_path:path}")
def write_file(file_path: str, payload: FileContent) -> dict:
    """将请求体中的 content 写入指定 Markdown 文件。"""
    target = resolve_docs_path(file_path)

    # 仅允许 .md 扩展名（防止写任意文件）
    if target.suffix.lower() != ".md":
        raise HTTPException(status_code=400, detail="仅允许写入 .md 文件")

    # 确保父目录存在
    target.parent.mkdir(parents=True, exist_ok=True)

    try:
        target.write_text(payload.content, encoding="utf-8")
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"写入失败：{exc}")

    return {"path": file_path, "saved": True}


def run_validate_script() -> dict:
    """运行 scripts/validate_docs.py，返回 {"success", "stdout", "stderr"}。"""
    if not VALIDATE_SCRIPT.exists():
        return {
            "success": False,
            "stdout": "",
            "stderr": f"校验脚本不存在：{VALIDATE_SCRIPT}",
        }

    try:
        result = subprocess.run(
            [PYTHON, str(VALIDATE_SCRIPT)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",  # Windows 下避免 gbk 解码崩溃
            cwd=str(BASE_DIR),  # 脚本内部用相对路径定位 repo root
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": "校验脚本执行超时（>30 秒）",
        }
    except OSError as exc:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"无法启动校验脚本：{exc}",
        }

    return {
        "success": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


@app.post("/api/validate")
def validate() -> dict:
    """运行 scripts/validate_docs.py，返回 stdout / stderr / success。"""
    return run_validate_script()


# ---------------------------------------------------------------------------
# 表格 → 项目 同步：首页两个按钮（预览 / 正式写入）调用的接口。
# 输入文件路径固定为 exports/wecom_cards.json，禁止前端传入任意路径，
# 避免任意文件读取 / 命令注入；脚本本身只读该 JSON、只写 docs/faqs/ 下的 .md。
# ---------------------------------------------------------------------------

def _cell_text(value) -> str:
    """把表格单元格值规范成纯文本。

    企业微信 smartsheet 导出的字段值形如 [{"text": "..."}]，也可能是纯 str 或 None。
    统一成 str 便于比较与展示。
    """
    if isinstance(value, list) and value:
        first = value[0]
        if isinstance(first, dict):
            return str(first.get("text", "") or "")
        return str(first or "")
    if isinstance(value, dict):
        return str(value.get("text", "") or "")
    return "" if value is None else str(value)


# 生成"具体数据"报告时展示的字段顺序（表格里真正有内容的业务字段）
_REPORT_FIELDS = [
    "卡片编号", "状态", "沉淀类型", "问题原话", "处理结果一句话",
    "业务规则与判断逻辑", "标准操作步骤", "注意事项/风险提示", "根因分类",
    "关键词/摘要", "标签", "适用系统/流程", "影响范围说明", "影响范围分类",
    "涉及表单名称", "模块", "问题类型", "处理日期",
]


def _load_snapshot_rows(path: Path) -> list:
    """读取快照 JSON 里的 rows；失败返回空列表。"""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        vals = data.get("values", [])
        v = vals[0] if vals else {}
        if isinstance(v, str):
            v = json.loads(v)
        return v.get("rows", [])
    except Exception:  # noqa: BLE001
        return []


def build_diff_report(old_rows: list, new_rows: list) -> dict:
    """对比刷新前后的卡片数据，生成结构化变更报告（按卡片编号匹配）。

    返回：
        total / status_dist / type_dist：新快照的规模与分布
        added / removed：新增 / 消失的卡片（编号 + 问题原话）
        changed：内容有变化的卡片（编号 + 变化字段 + 前后值，值截断）
        unchanged_count：完全不变的卡片数
    """
    def index(rows):
        out = {}
        for r in rows:
            cid = _cell_text(r.get("卡片编号")).strip() or "(无编号)"
            out[cid] = r
        return out

    old_idx, new_idx = index(old_rows), index(new_rows)

    def brief(cid, row):
        return {"id": cid, "question": _cell_text(row.get("问题原话"))[:80]}

    added = [brief(c, new_idx[c]) for c in sorted(set(new_idx) - set(old_idx))]
    removed = [brief(c, old_idx[c]) for c in sorted(set(old_idx) - set(new_idx))]

    changed = []
    for cid in sorted(set(old_idx) & set(new_idx)):
        o, n = old_idx[cid], new_idx[cid]
        diffs = []
        for field in _REPORT_FIELDS:
            ov, nv = _cell_text(o.get(field)).strip(), _cell_text(n.get(field)).strip()
            if ov != nv:
                diffs.append({
                    "field": field,
                    "old": ov[:120],
                    "new": nv[:120],
                })
        if diffs:
            changed.append({
                "id": cid,
                "question": _cell_text(n.get("问题原话"))[:80],
                "diffs": diffs,
            })

    def dist(rows, field):
        counter = {}
        for r in rows:
            key = _cell_text(r.get(field)).strip() or "(空)"
            counter[key] = counter.get(key, 0) + 1
        return [{"name": k, "count": v}
                for k, v in sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))]

    common = len(set(old_idx) & set(new_idx))
    return {
        "semantics": "queue",  # 表格=待处理队列：已审核进来，处理后反写已发布离开
        "total": len(new_rows),
        "status_dist": dist(new_rows, "状态"),
        "type_dist": dist(new_rows, "沉淀类型"),
        "added": added,        # 新进入队列的已审核卡片
        "removed": removed,    # 离开队列的卡片（通常是已处理并反写为已发布）
        "changed": changed,
        "unchanged_count": common - len(changed),
    }


def sync_rows_payload() -> dict:
    """返回当前快照全部卡片的精简字段，供前端"全部数据"表格浏览。"""
    if not SYNC_INPUT.exists():
        return {"success": False, "rows": [], "input": sync_input_meta()}
    rows = _load_snapshot_rows(SYNC_INPUT)
    items = []
    for r in rows:
        items.append({field: _cell_text(r.get(field)) for field in _REPORT_FIELDS})
    return {"success": True, "rows": items, "input": sync_input_meta()}


def sync_input_meta() -> dict:
    """返回固定输入快照的元信息（是否存在、大小、修改时间、记录数），供前端展示。"""
    meta = {"path": "exports/wecom_cards.json", "exists": SYNC_INPUT.exists()}
    if not SYNC_INPUT.exists():
        return meta
    try:
        stat = SYNC_INPUT.stat()
        meta["size"] = stat.st_size
        meta["modified"] = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        data = json.loads(SYNC_INPUT.read_text(encoding="utf-8"))
        vals = data.get("values", [])
        v = vals[0] if vals else {}
        if isinstance(v, str):
            v = json.loads(v)
        meta["rows"] = len(v.get("rows", []))
    except Exception as exc:  # noqa: BLE001 - 元信息展示失败不应阻断接口
        meta["error"] = str(exc)
    return meta


def iso_date(value) -> str:
    """企微日期字段返回 Excel 序列号，转换成 YYYY-MM-DD 文本。"""
    if value in (None, ""):
        return ""
    if isinstance(value, (int, float)) and 20000 < float(value) < 70000:
        return (datetime(1899, 12, 30) + timedelta(days=int(value))).strftime("%Y-%m-%d")
    return str(value)


def _cli_json(cmd: list, timeout: int = 60) -> dict:
    """运行 wecom-cli 并解析其 JSON 输出（CLI 会在 JSON 前打印安全提示）。"""
    proc = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8",
        errors="replace", cwd=str(BASE_DIR), timeout=timeout,
    )
    raw = proc.stdout or ""
    start = raw.find("{")
    if start < 0:
        raise ValueError((proc.stderr or raw or "CLI 未返回 JSON")[:300])
    data = json.loads(raw[start:])
    if data.get("errcode") not in (None, 0):
        raise ValueError(str(data.get("errmsg") or data.get("errcode")))
    return data


def find_card_record(source_card_id: str) -> dict:
    """按卡片编号从企微表格定位 RECORD_ID 及当前反馈字段值。"""
    card = str(source_card_id or "").strip().replace("'", "''")
    if not card:
        raise ValueError("source_card_id 不能为空")
    cli = shutil.which("wecom-cli") or WECOM_CLI
    sql = (
        "SELECT `RECORD_ID`, `卡片编号`, `复用次数`, `满意度评分`, `最后复核日期` "
        f"FROM `{WECOM_SHEET}` WHERE `卡片编号` = '{card}' LIMIT 1"
    )
    data = _cli_json([
        cli, "smartsheet", "records", "query",
        "--docid", WECOM_DOCID, "--sql", sql,
    ])
    values = data.get("values") or []
    block = values[0] if values else {}
    if isinstance(block, str):
        block = json.loads(block)
    rows = block.get("rows") or []
    if not rows:
        raise ValueError(f"表格中找不到卡片编号 {source_card_id}")
    return rows[0]


def update_card_fields(record_id: str, values: dict) -> dict:
    """按 RECORD_ID 更新企微表格字段（字段名 → 值）。"""
    cli = shutil.which("wecom-cli") or WECOM_CLI
    payload = {
        "docid": WECOM_DOCID,
        "sheet_title": WECOM_SHEET,
        "key_type": "field_title",
        "type": "update",
        "records": [{"record_id": record_id, "values": values}],
    }
    _cli_json([
        cli, "smartsheet", "records", "update",
        "--json", json.dumps(payload, ensure_ascii=False),
    ], timeout=120)
    return {"success": True, "record_id": record_id, "values": values}


def writeback_status(written: list) -> dict:
    """把已成功写入 Wiki 的卡片在表格里反写状态为「已发布」。

    written: [{"card": 卡片编号, "record_id": 表格行ID}, ...]
    返回 {"attempted": n, "success": n, "failed": [{"card","record_id","error"}...]}
    仅在有有效 record_id 时调用 CLI；分批 2000 条以内（CLI 上限）。
    """
    result = {"attempted": 0, "success": 0, "failed": [], "skipped_no_rid": 0}
    valid = []
    for item in written:
        rid = str(item.get("record_id") or "").strip()
        if not rid:
            result["skipped_no_rid"] += 1
            continue
        valid.append({"card": str(item.get("card") or ""), "rid": rid})
    if not valid:
        return result

    cli = shutil.which("wecom-cli") or WECOM_CLI
    # 单选字段值格式：[{"id": "JdaNKJ", "text": "已发布"}]（与历史成功写入一致）
    records = [{
        "record_id": it["rid"],
        "values": {"状态": [{"id": WRITEBACK_STATUS_ID, "text": WRITEBACK_STATUS_TEXT}]},
    } for it in valid]
    payload = {
        "docid": WECOM_DOCID,
        "sheet_title": WECOM_SHEET,
        "key_type": "field_title",
        "type": "update",
        "records": records,
    }
    try:
        # 直接以字符串传 --json（与历史成功的 `--json "$(cat ...)"` 等价）
        cmd = [cli, "smartsheet", "records", "update", "--json",
               json.dumps(payload, ensure_ascii=False)]
        proc = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8",
            errors="replace", cwd=str(BASE_DIR), timeout=120,
        )
        raw = proc.stdout or ""
        parsed = {}
        try:
            s = raw.index("{")
            parsed = json.loads(raw[s:])
        except Exception:  # noqa: BLE001
            parsed = {}
        errcode = parsed.get("errcode")
        if proc.returncode == 0 and (errcode in (None, 0)):
            result["attempted"] = len(valid)
            result["success"] = len(valid)
        else:
            result["attempted"] = len(valid)
            errmsg = parsed.get("errmsg") or (proc.stderr or "反写失败")[:200]
            for it in valid:
                result["failed"].append({"card": it["card"], "record_id": it["rid"],
                                         "error": str(errmsg)})
    except subprocess.TimeoutExpired:
        result["attempted"] = len(valid)
        for it in valid:
            result["failed"].append({"card": it["card"], "record_id": it["rid"],
                                     "error": "反写超时（>120秒）"})
    except OSError as exc:
        result["attempted"] = len(valid)
        for it in valid:
            result["failed"].append({"card": it["card"], "record_id": it["rid"],
                                     "error": f"无法调用CLI：{exc}"})
    return result


def rebuild_navigation() -> dict:
    """正式写入后重建侧边栏和 FAQ 索引，保证左侧树立即显示新文档。"""
    details = []
    ok = True
    for script in NAV_SCRIPTS:
        if not script.exists():
            ok = False
            details.append(f"缺少脚本：{script.name}")
            continue
        try:
            result = subprocess.run(
                [PYTHON, str(script)], capture_output=True, text=True,
                encoding="utf-8", errors="replace",
                cwd=str(BASE_DIR), timeout=60,
            )
        except Exception as exc:  # noqa: BLE001
            ok = False
            details.append(f"{script.name} 执行失败：{exc}")
            continue
        if result.returncode != 0:
            ok = False
            details.append(f"{script.name} 退出码 {result.returncode}：{(result.stderr or result.stdout)[:200]}")
        else:
            details.append((result.stdout or f"{script.name} 完成").strip())
    return {"success": ok, "details": details}


def run_sync_script(apply: bool) -> dict:
    """调用 sync_from_wecom.py；apply=False 为 dry-run（不传 --apply）。"""
    meta = sync_input_meta()
    if not SYNC_SCRIPT.exists():
        return {"success": False, "stdout": "", "stderr": f"同步脚本不存在：{SYNC_SCRIPT}",
                "apply": apply, "input": meta}
    if not meta.get("exists"):
        return {"success": False, "stdout": "", "stderr": f"输入快照不存在：{SYNC_INPUT}",
                "apply": apply, "input": meta}

    cmd = [PYTHON, str(SYNC_SCRIPT), "--input", str(SYNC_INPUT)]
    report_path = SYNC_INPUT.parent / "sync_report.tmp.json"
    if apply:
        cmd.append("--apply")
        cmd += ["--report", str(report_path)]
    else:
        _safe_unlink(report_path)  # 清理可能残留的旧报告
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            cwd=str(BASE_DIR), timeout=120,
        )
    except subprocess.TimeoutExpired:
        return {"success": False, "stdout": "", "stderr": "同步脚本执行超时（>120 秒）",
                "apply": apply, "input": meta}
    except OSError as exc:
        return {"success": False, "stdout": "", "stderr": f"无法启动同步脚本：{exc}",
                "apply": apply, "input": meta}

    response = {
        "success": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "apply": apply,
        "input": meta,
    }

    # 正式写入成功后，把本次真正写入的卡片反写为「已发布」
    if apply and result.returncode == 0:
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
            written = report.get("written", [])
        except Exception:  # noqa: BLE001
            written = []
        finally:
            _safe_unlink(report_path)
        wb = writeback_status(written)
        response["writeback"] = wb
        success = result.stdout + (
            f"\n\n[反写表格状态] 尝试 {wb['attempted']} 条，成功 {wb['success']} 条，"
            f"失败 {len(wb['failed'])} 条，跳过(无RECORD_ID) {wb['skipped_no_rid']} 条。"
        )
        if wb["failed"]:
            success += "\n失败明细：" + "; ".join(
                f"#{x['card']}({x['error'][:40]})" for x in wb["failed"][:5]
            )
        # 重建左侧树与索引：否则正式写入成功后新文档不会出现在导航里。
        nav = rebuild_navigation()
        response["navigation_rebuild"] = nav
        success += ("\n\n[重建导航] " + ("成功" if nav["success"] else "部分失败")
                    + "\n" + "\n".join(nav["details"]))
        response["stdout"] = success

    return response


@app.get("/api/sync/status")
def sync_status() -> dict:
    """返回固定输入快照的元信息，供首页面板展示数据时间与记录数。"""
    return sync_input_meta()


@app.get("/api/sync/rows")
def sync_rows() -> dict:
    """返回当前快照全部卡片的精简字段，供首页"全部数据"表格浏览。"""
    return sync_rows_payload()


@app.post("/api/sync/preview")
def sync_preview() -> dict:
    """预览模式：运行同步脚本但不写任何文件（先看报告）。"""
    return run_sync_script(apply=False)


@app.post("/api/sync/apply")
def sync_apply() -> dict:
    """正式写入：把表格中已发布卡片同步进 docs/faqs/。"""
    return run_sync_script(apply=True)


@app.post("/api/sync/refresh")
def sync_refresh() -> dict:
    """刷新输入快照：用固定只读 SQL 从企微表格重新拉取全量卡片，校验后原子替换。

    流程：
      1. 检查 CLI 授权状态；未授权给出明确提示（不静默失败）。
      2. 拉取到同目录临时文件（避免中途失败破坏现有快照）。
      3. 校验 JSON 结构 / 记录数 / 必需字段，全部通过才原子替换。
    失败时原快照保持不变。
    """
    # 1. 授权检查（每次重新解析 CLI 路径，避免启动时 PATH 未就绪）
    cli = shutil.which("wecom-cli") or WECOM_CLI
    try:
        auth = subprocess.run(
            [cli, "auth", "show", "--status"],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", cwd=str(BASE_DIR), timeout=30,
        )
        status = (auth.stdout or "").strip().lower()
        if "unauthorized" in status or "未授权" in status:
            return {"success": False,
                    "stdout": "",
                    "stderr": "企微 CLI 未授权。请在终端运行 wecom-cli auth init --noninteractive 后用企业微信扫码重新授权。",
                    "input": sync_input_meta()}
    except FileNotFoundError:
        return {"success": False, "stdout": "",
                "stderr": "未找到 wecom-cli，请确认已安装（npm install -g @wecom/cli）。",
                "input": sync_input_meta()}
    except subprocess.TimeoutExpired:
        return {"success": False, "stdout": "", "stderr": "检查 CLI 授权超时（>30 秒）",
                "input": sync_input_meta()}
    except OSError as exc:
        return {"success": False, "stdout": "", "stderr": f"无法检查 CLI 授权：{exc}",
                "input": sync_input_meta()}

    # 2. 拉取到临时文件；替换前先留一份旧快照用于生成变更报告
    old_rows = _load_snapshot_rows(SYNC_INPUT) if SYNC_INPUT.exists() else []
    SYNC_INPUT.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = SYNC_INPUT.with_suffix(".json.tmp")
    cmd = [cli, "smartsheet", "records", "query",
           "--docid", WECOM_DOCID, "--sql", REFRESH_SQL, "-o", str(tmp_path)]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8",
            errors="replace", cwd=str(BASE_DIR), timeout=120,
        )
    except subprocess.TimeoutExpired:
        _safe_unlink(tmp_path)
        return {"success": False, "stdout": "", "stderr": "拉取表格超时（>120 秒）",
                "input": sync_input_meta()}
    except OSError as exc:
        _safe_unlink(tmp_path)
        return {"success": False, "stdout": "", "stderr": f"无法启动 wecom-cli：{exc}",
                "input": sync_input_meta()}

    if result.returncode != 0:
        _safe_unlink(tmp_path)
        return {"success": False, "stdout": result.stdout,
                "stderr": (result.stderr or "拉取失败") + "\n原快照未改动。",
                "input": sync_input_meta()}

    # 3. 校验后原子替换
    try:
        data = json.loads(tmp_path.read_text(encoding="utf-8"))
        vals = data.get("values", [])
        v = vals[0] if vals else {}
        if isinstance(v, str):
            v = json.loads(v)
        rows = v.get("rows", [])
        # 0 条是合法状态：已审核队列空了（都处理完并反写为已发布）
        required = {"RECORD_ID", "卡片编号", "状态", "问题原话"}
        missing = required - set(rows[0].keys()) if rows else set()
        if missing:
            raise ValueError(f"数据校验失败：记录数={len(rows)}，缺失字段={sorted(missing)}")
    except Exception as exc:  # noqa: BLE001
        _safe_unlink(tmp_path)
        return {"success": False, "stdout": result.stdout,
                "stderr": f"{exc}\n原快照未改动。", "input": sync_input_meta()}

    try:
        # Path.replace 在同盘内原子替换；Windows 上目标存在也可直接覆盖
        tmp_path.replace(SYNC_INPUT)
    except OSError as exc:
        _safe_unlink(tmp_path)
        return {"success": False, "stdout": "", "stderr": f"替换快照失败：{exc}",
                "input": sync_input_meta()}

    report = build_diff_report(old_rows, rows)
    # 首次从"全量快照"切到"已审核队列快照"是一次性迁移：旧的全量卡片并非真的被处理离队，
    # 把它们登记成"离队/变更"会误导。检测到此情形则清空逐条差异，只保留新快照概览。
    migration = len(old_rows) > 50 and len(rows) <= 50
    if migration:
        report["added"] = []
        report["removed"] = []
        report["changed"] = []
        report["unchanged_count"] = len(rows)
        report["migration"] = True
    return {
        "success": True,
        "stdout": (result.stdout or "").strip()
                  + f"\n\n已刷新 {len(rows)} 条待处理卡片（只含状态=已审核）。"
                  + "\n接下来可点「预览」查看变更，再点「正式写入」（写入后会自动反写为已发布）。",
        "stderr": result.stderr,
        "report": report,
        "input": sync_input_meta(),
    }


def _safe_unlink(path: Path) -> None:
    """尽力删除临时文件，忽略失败。"""
    try:
        if path.exists():
            path.unlink()
    except OSError:
        pass


@app.get("/api/feedback/status")
def feedback_status(source_card_id: str) -> dict:
    """查询某张卡片的反馈数据（复用次数 / 满意度 / 最后复核日期）。"""
    try:
        row = find_card_record(source_card_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=404, detail=str(exc))
    return {
        "success": True,
        "source_card_id": source_card_id,
        "reuse": row.get("复用次数") or 0,
        "rating": row.get("满意度评分"),
        "last_reviewed": iso_date(row.get("最后复核日期")),
    }


@app.post("/api/feedback/reuse")
def feedback_reuse(payload: FeedbackPayload) -> dict:
    """记录一次复用：表格里对应卡片的「复用次数」+1。"""
    try:
        row = find_card_record(payload.source_card_id)
        current = int(row.get("复用次数") or 0)
        result = update_card_fields(row["RECORD_ID"], {"复用次数": current + 1})
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc))
    return {"success": True, "source_card_id": payload.source_card_id,
            "reuse": current + 1, "record_id": result["record_id"]}


@app.post("/api/feedback/rating")
def feedback_rating(payload: FeedbackPayload) -> dict:
    """提交满意度评分（1-5），并更新「最后复核日期」。"""
    if payload.rating is None or not 1 <= payload.rating <= 5:
        raise HTTPException(status_code=400, detail="满意度评分必须是 1-5 的整数")
    try:
        row = find_card_record(payload.source_card_id)
        result = update_card_fields(row["RECORD_ID"], {
            "满意度评分": payload.rating,
            "最后复核日期": datetime.now().strftime("%Y-%m-%d"),
        })
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc))
    return {"success": True, "source_card_id": payload.source_card_id,
            "rating": payload.rating, "record_id": result["record_id"]}


@app.post("/api/feedback/review")
def feedback_review() -> dict:
    """运行复核提醒脚本，返回报告路径与内容。"""
    if not REVIEW_SCRIPT.exists():
        raise HTTPException(status_code=404, detail="复核脚本不存在")
    try:
        result = subprocess.run(
            [PYTHON, str(REVIEW_SCRIPT)], capture_output=True, text=True,
            encoding="utf-8", errors="replace", cwd=str(BASE_DIR), timeout=120,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"无法运行复核脚本：{exc}")
    response = {
        "success": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "report_path": "exports/feedback_review.md",
    }
    if response["success"] and REVIEW_REPORT.exists():
        response["report"] = REVIEW_REPORT.read_text(encoding="utf-8")
    return response


@app.post("/api/export/weknora")
def export_weknora() -> dict:
    """生成 WeKnora 导入 JSON，返回文件元信息。"""
    if not WEKNORA_EXPORT_SCRIPT.exists():
        raise HTTPException(status_code=404, detail="WeKnora 导出脚本不存在")
    try:
        result = subprocess.run(
            [PYTHON, str(WEKNORA_EXPORT_SCRIPT)], capture_output=True, text=True,
            encoding="utf-8", errors="replace", cwd=str(BASE_DIR), timeout=120,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"无法运行导出脚本：{exc}")
    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=(result.stderr or result.stdout)[:500])
    meta = {"path": "exports/weknora_import.json", "exists": WEKNORA_EXPORT.exists()}
    if WEKNORA_EXPORT.exists():
        meta["size"] = WEKNORA_EXPORT.stat().st_size
        data = json.loads(WEKNORA_EXPORT.read_text(encoding="utf-8"))
        meta["total_documents"] = data.get("total_documents", 0)
    return {"success": True, "stdout": result.stdout, "meta": meta}


@app.get("/api/ask/search")
def ask_search(q: str = "", limit: int = 8) -> dict:
    """本地检索接口：返回带 source_card_id 的 FAQ 片段，供企微 Agent 溯源。"""
    q = (q or "").strip()
    if not q:
        raise HTTPException(status_code=400, detail="查询词不能为空")
    if not RAG_EXPORT.exists():
        raise HTTPException(status_code=404, detail="未找到导出索引，请先运行 export_for_rag.py")
    data = json.loads(RAG_EXPORT.read_text(encoding="utf-8"))
    docs = data.get("documents") or []
    terms = [t for t in re.split(r"[\s,，、]+", q.lower()) if t]
    scored = []
    for doc in docs:
        title = str(doc.get("title") or "").lower()
        body = str(doc.get("body") or "").lower()
        score = sum(title.count(t) * 3 + body.count(t) for t in terms)
        if score:
            scored.append((score, doc))
    scored.sort(key=lambda x: -x[0])
    results = []
    for score, doc in scored[:max(1, min(limit, 50))]:
        fm = doc.get("frontmatter") or {}
        body = str(doc.get("body") or "")
        excerpt = body[:240].replace("\n", " ")
        results.append({
            "source_card_id": fm.get("source_card_id", ""),
            "title": doc.get("title", ""),
            "source_path": doc.get("source_path", ""),
            "problem_type": fm.get("problem_type", ""),
            "score": score,
            "excerpt": excerpt,
        })
    return {"query": q, "total_matches": len(scored), "results": results}


@app.get("/api/ask/faq/{source_card_id}")
def ask_faq(source_card_id: str) -> dict:
    """按卡片编号取回完整 FAQ，供 MCP 工具与 Agent 引用。"""
    if not RAG_EXPORT.exists():
        raise HTTPException(status_code=404, detail="未找到导出索引，请先运行 export_for_rag.py")
    data = json.loads(RAG_EXPORT.read_text(encoding="utf-8"))
    for doc in data.get("documents") or []:
        fm = doc.get("frontmatter") or {}
        if str(fm.get("source_card_id") or "") == str(source_card_id):
            return {
                "source_card_id": source_card_id,
                "title": doc.get("title", ""),
                "source_path": doc.get("source_path", ""),
                "frontmatter": fm,
                "body": doc.get("body", ""),
            }
    raise HTTPException(status_code=404, detail=f"找不到卡片编号 {source_card_id}")


@app.post("/api/validate-content")
def validate_content(payload: FilePathContent) -> dict:
    """
    校验一段新内容是否可通过文档校验，但不写入正式文件。

    做法：临时把内容写到目标路径（若目标原本不存在），运行校验脚本，
    随后立即清理临时文件。若目标原本已存在，则不触碰（返回错误提示，
    因为该接口面向"新增页面"场景）。
    """
    target = resolve_docs_path(payload.path)

    if target.suffix.lower() != ".md":
        raise HTTPException(status_code=400, detail="仅支持校验 .md 文件")

    if target.exists():
        raise HTTPException(
            status_code=409,
            detail=f"目标已存在，请改用编辑模式：{payload.path}",
        )

    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        target.write_text(payload.content, encoding="utf-8")
        result = run_validate_script()
    finally:
        # 无论校验结果如何，都删除临时文件（确保不残留新页面内容）
        try:
            if target.exists():
                target.unlink()
        except OSError:
            pass

    return result


@app.post("/api/files/{file_path:path}")
def create_file(file_path: str, payload: FileContent) -> dict:
    """
    创建新的 Markdown 文档。若目标已存在则返回 409。

    安全兜底：写盘前先对内容做一次强制校验，校验不通过则返回 422，
    不合规的文档不会被保存（即使前端被绕过，直接调用本接口也无法存下）。
    """
    target = resolve_docs_path(file_path)

    if target.suffix.lower() != ".md":
        raise HTTPException(status_code=400, detail="仅允许创建 .md 文件")

    if target.exists():
        raise HTTPException(
            status_code=409,
            detail=f"文件已存在，请改用编辑模式：{file_path}",
        )

    # ---- 强制内容校验兜底：不通过则拒绝落盘 ----
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        target.write_text(payload.content, encoding="utf-8")
        validation = run_validate_script()
    finally:
        # 无论结果如何都删除临时校验文件（不残留半成品）
        try:
            if target.exists():
                target.unlink()
        except OSError:
            pass

    if not validation.get("success"):
        detail = (
            "内容校验未通过，已阻止保存。请修正后重试。\n"
            f"{validation.get('stdout', '')}{validation.get('stderr', '')}"
        ).strip()
        raise HTTPException(status_code=422, detail=detail)

    # ---- 校验通过，正式创建 ----
    try:
        target.write_text(payload.content, encoding="utf-8")
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"创建失败：{exc}")

    # 创建成功后，自动把新页面注册进 _sidebar.md 与分类 README.md，
    # 使前端刷新后能直接在导航/索引页看到新页面。
    register_new_page(file_path, payload.content)

    return {"path": file_path, "created": True}


@app.delete("/api/files/{file_path:path}")
def delete_file(file_path: str) -> dict:
    """
    删除指定 Markdown 文档，并同步从导航（_sidebar.md 与分类 README.md）移除其链接。

    保护：不允许删除 README.md（分类索引页），避免破坏导航结构。
    """
    target = resolve_docs_path(file_path)

    if target.suffix.lower() != ".md":
        raise HTTPException(status_code=400, detail="仅允许删除 .md 文件")

    if target.name.upper() == "README.MD":
        raise HTTPException(
            status_code=400, detail="不允许删除分类索引页（README.md）"
        )

    if not target.exists():
        raise HTTPException(status_code=404, detail=f"文件不存在：{file_path}")
    if not target.is_file():
        raise HTTPException(status_code=400, detail=f"不是常规文件：{file_path}")

    try:
        target.unlink()
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"删除失败：{exc}")

    # 同步从导航移除该页面的链接
    unregister_page(file_path)

    return {"path": file_path, "deleted": True}


@app.get("/api/health")
def health() -> dict:
    """健康检查端点，便于前端确认后端可达。"""
    return {"status": "ok", "docs_dir": str(DOCS_DIR)}


# 托管前端静态文件（index.html、docs/、assets/ 等），使前后端同端口、同源。
# 必须放在所有 API 路由之后作为兜底，否则 "/" 挂载会遮蔽 /api/* 请求。
# html=True 使 "/" 返回 index.html，且不区分大小写地解析 .md 等静态资源。
app.mount("/", StaticFiles(directory=str(BASE_DIR), html=True), name="static")


if __name__ == "__main__":
    import uvicorn

    # 0.0.0.0 监听所有网卡，使局域网内其他设备可通过本机局域网 IP 访问。
    # 若只需本机访问，可改回 host="127.0.0.1"。
    uvicorn.run(app, host="0.0.0.0", port=8000)
