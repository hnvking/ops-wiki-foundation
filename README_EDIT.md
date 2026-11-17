# ops-wiki-foundation 在线编辑与校验

为 Docsify 知识库增加 Markdown 在线编辑与校验触发能力。后端使用 FastAPI，前端使用 Docsify 插件 + EasyMDE。

## 项目结构（新增部分）

```
backend/
  └── main.py                 # FastAPI 后端：文件读写 API + 校验触发
docsify-editor-plugin.js      # Docsify 前端插件：编辑按钮 + 模态框 + EasyMDE
index.html                    # 已集成 EasyMDE 样式/JS 与插件
requirements.txt              # 已追加 fastapi / uvicorn / pydantic
```

## 快速开始

### 1. 安装后端依赖

```bash
python -m pip install -r requirements.txt
```

### 2. 启动后端

```bash
# 在项目根目录执行
uvicorn backend.main:app --reload --port 8000
```

后端默认运行在 `http://localhost:8000`。启动后可用浏览器访问 `http://localhost:8000/docs` 查看自动生成的 API 文档（Swagger UI）。

### 3. 启动前端（Docsify）

前端与后端**同端口**部署最简单：后端本身通过 `http.server` 或 FastAPI 提供静态文件时，`API_BASE` 留空即可（同源，使用相对路径）。

若前后端**分离**（例如前端 :3000、后端 :8000）：

- 修改 `index.html` 中 `window.API_BASE`，或直接在 `docsify-editor-plugin.js` 顶部调整：
  ```js
  var API_BASE = "http://localhost:8000";
  ```
- 后端 CORS 已默认允许 `localhost:3000/5173/8000`，如需其它端口请在 `backend/main.py` 的 `allow_origins` 中添加。

> 本项目默认用 `python -m http.server 8000` 在根目录提供静态文件，此时前端即 `http://localhost:8000`，与后端同端口，`API_BASE` 为空即可。

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET  | `/api/files` | 列出 `docs/` 下所有 `.md` 相对路径 |
| GET  | `/api/files/{path}` | 读取指定 Markdown 内容 |
| PUT  | `/api/files/{path}` | 写入指定 Markdown 内容 |
| POST | `/api/validate` | 运行 `scripts/validate_docs.py` 并返回结果 |
| GET  | `/api/health` | 健康检查 |

所有文件读写均通过 `resolve()` + `is_relative_to(DOCS_DIR)` 校验，拒绝路径遍历（返回 403）。

## 前端使用

打开任一文档页，点击内容区上方的 **“✏️ 编辑此页”** 按钮：

1. 弹出模态框，用 EasyMDE 编辑当前 Markdown。
2. 点击 **“💾 保存”** 调用 `PUT /api/files/...` 保存。
3. 点击 **“▶️ 运行校验”** 调用 `POST /api/validate`，结果（绿色=通过 / 红色=失败）显示在下方滚动区域。

## 说明

- 路径安全：`vm.route.file` 可能带前导 `/`，插件已去除；后端用 `pathlib` 处理跨平台路径。
- 校验脚本输出编码：后端以 `encoding="utf-8", errors="replace"` 运行，避免 Windows `gbk` 解码问题。
- EasyMDE 通过 CDN（jsdelivr）加载，需联网；离线部署请自行下载到本地 `assets/` 并替换引用。
