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

import re
import subprocess
import sys
from pathlib import Path
from typing import List

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
