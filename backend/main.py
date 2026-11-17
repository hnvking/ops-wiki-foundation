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

# 分类目录名 → 侧边栏展示名（显示名含 "系统 Systems" 这类中英文）
CATEGORY_LABELS = {
    "systems": "系统 Systems",
    "services": "服务 Services",
    "integrations": "集成 Integrations",
    "runbooks": "应急手册 Runbooks",
}


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


def register_new_page(file_path: str, content: str) -> None:
    """
    把新创建的页面注册进导航：
      1. _sidebar.md 的分类父项下追加子链接
      2. docs/<category>/README.md 的「示例」区追加链接

    file_path 为相对 docs/ 的路径（如 systems/foo.md），content 为新文件全文。
    """
    file_path = file_path.replace("\\", "/").lstrip("/")
    parts = file_path.split("/")
    if len(parts) < 2:
        return  # 不在分类子目录内，不处理
    category = parts[0]
    filename = parts[-1]
    title = extract_title(content)

    # ---- 1. 更新 _sidebar.md ----
    sidebar_path = BASE_DIR / "_sidebar.md"
    if sidebar_path.exists():
        try:
            sidebar_text = sidebar_path.read_text(encoding="utf-8")
        except OSError:
            sidebar_text = ""
    else:
        sidebar_text = ""

    # 已存在该链接则跳过
    if filename not in sidebar_text:
        label = CATEGORY_LABELS.get(category, category)
        parent_prefix = f"- [{label}](docs/{category}/README.md)"
        new_line = f"  - [{title}](docs/{file_path})"
        if parent_prefix in sidebar_text:
            # 在父项行之后插入子链接
            lines = sidebar_text.split("\n")
            for i, line in enumerate(lines):
                if line.strip() == parent_prefix.strip():
                    # 跳过父项后已有的子项，找到插入位置
                    insert_at = i + 1
                    while insert_at < len(lines) and lines[insert_at].startswith("  - "):
                        insert_at += 1
                    lines.insert(insert_at, new_line)
                    break
            sidebar_text = "\n".join(lines)
        else:
            # 找不到父项，追加到末尾
            if sidebar_text and not sidebar_text.endswith("\n"):
                sidebar_text += "\n"
            sidebar_text += new_line + "\n"
        try:
            sidebar_path.write_text(sidebar_text, encoding="utf-8")
        except OSError:
            pass

    # ---- 2. 更新 docs/<category>/README.md ----
    readme_path = DOCS_DIR / category / "README.md"
    if readme_path.exists():
        try:
            readme_text = readme_path.read_text(encoding="utf-8")
        except OSError:
            readme_text = ""
    else:
        readme_text = ""

    rel_link = f"docs/{file_path}"
    if filename not in readme_text:
        entry = f"- [{filename}]({rel_link}) — {title}"
        if "## 示例" in readme_text:
            # 在「示例」区末尾追加
            lines = readme_text.split("\n")
            idx = None
            for i, line in enumerate(lines):
                if line.strip() == "## 示例":
                    idx = i
                    break
            if idx is not None:
                insert_at = idx + 1
                while insert_at < len(lines) and (
                    not lines[insert_at].startswith("#") or lines[insert_at].strip() == ""
                ):
                    # 停在下一个 ## 标题前
                    if lines[insert_at].strip().startswith("## ") and lines[insert_at].strip() != "## 示例":
                        break
                    insert_at += 1
                # 往回退，插到下一个 ## 前（若正好在下一个标题上）
                lines.insert(insert_at, entry)
                readme_text = "\n".join(lines)
            else:
                readme_text += "\n" + entry + "\n"
        else:
            if readme_text and not readme_text.endswith("\n"):
                readme_text += "\n"
            readme_text += "\n## 页面\n\n" + entry + "\n"
        try:
            readme_path.write_text(readme_text, encoding="utf-8")
        except OSError:
            pass


def unregister_page(file_path: str) -> None:
    """
    从导航中移除指定页面的链接（删除文档时调用）：
      1. _sidebar.md 中删除指向该页面的子链接
      2. docs/<category>/README.md 的「示例」区删除对应条目

    file_path 为相对 docs/ 的路径（如 systems/foo.md）。
    只移除精确匹配 `docs/<file_path>` 链接的行，不影响其它链接。
    """
    file_path = file_path.replace("\\", "/").lstrip("/")
    parts = file_path.split("/")
    if len(parts) < 2:
        return  # 不在分类子目录内，不处理
    category = parts[0]
    link_target = f"docs/{file_path}"

    # ---- 1. 从 _sidebar.md 移除 ----
    sidebar_path = BASE_DIR / "_sidebar.md"
    if sidebar_path.exists():
        try:
            lines = sidebar_path.read_text(encoding="utf-8").split("\n")
        except OSError:
            lines = []
        new_lines = [ln for ln in lines if link_target not in ln]
        if len(new_lines) != len(lines):
            try:
                sidebar_path.write_text(
                    "\n".join(new_lines).rstrip("\n") + "\n", encoding="utf-8"
                )
            except OSError:
                pass

    # ---- 2. 从 docs/<category>/README.md 移除 ----
    readme_path = DOCS_DIR / category / "README.md"
    if readme_path.exists():
        try:
            lines = readme_path.read_text(encoding="utf-8").split("\n")
        except OSError:
            lines = []
        new_lines = [ln for ln in lines if link_target not in ln]
        if len(new_lines) != len(lines):
            try:
                readme_path.write_text(
                    "\n".join(new_lines).rstrip("\n") + "\n", encoding="utf-8"
                )
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

# CORS：允许本地前端访问。默认允许 localhost 任意端口，方便本地开发。
# 如需在生产环境限制，可修改 allow_origins 为具体域名列表。
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
    ],
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

    uvicorn.run(app, host="127.0.0.1", port=8000)
