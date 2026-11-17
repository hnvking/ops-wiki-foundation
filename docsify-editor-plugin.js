/**
 * docsify-editor-plugin.js
 *
 * Docsify 前端插件 —— 为 Markdown 知识库提供在线编辑、校验与新增页面能力。
 *
 * 功能：
 *   1. 文档页（如 docs/systems/xxx.md）→ "✏️ 编辑此页" 按钮，EasyMDE 编辑已有文档。
 *   2. 分类索引页（如 docs/systems/README.md）→ "➕ 新增页面" 按钮，从 0 到 1 新建文档。
 *   3. "▶️ 运行校验" 按钮：调用后端校验（编辑模式校验全库；新增模式校验待写内容）。
 *   4. 保存/提交成功后自动刷新页面，回显最新内容。
 *
 * 路径映射说明：
 *   侧边栏链接是相对仓库根的路径（如 docs/systems/xxx.md），
 *   而后端 API 期望相对 docs/ 的路径（如 systems/xxx.md）。
 *   因此本插件会把 vm.route.file 的 "docs/" 前缀去掉，再传给后端。
 *
 * 后端 API 地址通过全局变量 API_BASE 配置，默认使用相对路径（同源）。
 *
 * 用法：在 index.html 中先加载本插件，再加载 docsify.min.js。
 */

(function () {
  // -------------------------------------------------------------------------
  // 配置
  // -------------------------------------------------------------------------
  var API_BASE = (typeof window.API_BASE !== "undefined" && window.API_BASE) || "";

  // -------------------------------------------------------------------------
  // 缓存绕过：Docsify 用原生 XMLHttpRequest 请求 .md 文件，浏览器 HTTP 缓存
  // 可能在保存后仍返回旧内容（导致新段落不渲染）。这里给所有 .md 的 GET 请求
  // 追加一个时间戳参数，强制走网络、绕过浏览器缓存。
  // -------------------------------------------------------------------------
  (function patchXhrCacheBust() {
    try {
      var origOpen = XMLHttpRequest.prototype.open;
      XMLHttpRequest.prototype.open = function (method, url) {
        try {
          if (
            (method === "GET" || method === "get") &&
            typeof url === "string" &&
            /\.md(\?|$)/i.test(url) &&
            url.indexOf("/api/") === -1
          ) {
            var sep = url.indexOf("?") >= 0 ? "&" : "?";
            url = url + sep + "_=" + Date.now();
          }
        } catch (e) { /* 忽略，不影响原有行为 */ }
        return origOpen.apply(this, arguments);
      };
    } catch (e) { /* 若浏览器不支持，跳过 */ }
  })();

  // 当前路由状态
  var routeInfo = { mode: "home" }; // mode: home | index | doc
  // 编辑/新增的目标文件（相对 docs/），如 systems/xxx.md
  var currentFile = null;
  // 当前分类目录（相对 docs/），如 systems（仅 index 模式使用）
  var currentCategory = null;

  var easyMDE = null;

  // -------------------------------------------------------------------------
  // 工具函数
  // -------------------------------------------------------------------------

  /** 分析路由，得出页面类型与文档路径。 */
  function analyzeRoute(routeFile) {
    var raw = routeFile ? String(routeFile).replace(/\\/g, "/").replace(/^\/+/, "") : "";
    if (!raw) return { mode: "home" };
    // 首页（homepage 指向 docsify/README.md，或根 README）
    if (raw === "docsify/README.md" || raw === "README.md") return { mode: "home" };

    // 分类页：docs/<category>/<rest>
    var m = raw.match(/^docs\/([^/]+)\/(.+)$/);
    if (m) {
      var category = m[1];
      var rel = m[2];
      if (rel === "README.md") {
        return { mode: "index", category: category, file: category + "/README.md" };
      }
      return { mode: "doc", category: category, file: category + "/" + rel };
    }

    // 兜底：无 docs/ 前缀，直接视为相对 docs/ 的路径
    if (raw.endsWith("README.md")) {
      var cat = raw.split("/")[0];
      return { mode: "index", category: cat, file: raw };
    }
    return { mode: "doc", category: raw.split("/")[0], file: raw };
  }

  /** 发起 JSON 请求的 fetch 封装。 */
  async function apiFetch(url, options) {
    var resp = await fetch(API_BASE + url, options);
    if (!resp.ok) {
      var errText = "";
      try {
        var j = await resp.json();
        errText = j.detail || JSON.stringify(j);
      } catch (e) {
        errText = await resp.text().catch(function () { return ""; });
      }
      throw new Error("HTTP " + resp.status + ": " + errText);
    }
    return resp.json();
  }

  /** 提示消息（toast）。 */
  function toast(message, type) {
    var box = document.getElementById("wiki-toast");
    if (!box) {
      box = document.createElement("div");
      box.id = "wiki-toast";
      document.body.appendChild(box);
    }
    box.textContent = message;
    box.className = "wiki-toast wiki-toast-" + (type || "info");
    box.style.opacity = "1";
    clearTimeout(box._timer);
    box._timer = setTimeout(function () {
      box.style.opacity = "0";
    }, 3000);
  }

  /** 设置校验结果区域内容与样式。 */
  function renderValidationResult(result) {
    var area = document.getElementById("wiki-validate-result");
    if (!area) return;
    var ok = result && result.success;
    var text = "";
    if (result) {
      text = (result.stdout || "") + (result.stderr ? "\n[stderr]\n" + result.stderr : "");
      if (!text.trim()) text = ok ? "校验通过（无输出）" : "校验失败（无输出）";
    } else {
      text = "无校验结果";
    }
    area.textContent = text;
    area.className = "wiki-validate-result " + (ok ? "wiki-ok" : "wiki-fail");
    area.scrollTop = 0;
  }

  /** 刷新页面以回显最新内容（保持当前路由 hash）。 */
  function refreshPage() {
    window.location.reload();
  }

  // -------------------------------------------------------------------------
  // 模态框构建
  // -------------------------------------------------------------------------

  function buildModal() {
    if (document.getElementById("wiki-editor-modal")) return;

    var modal = document.createElement("div");
    modal.id = "wiki-editor-modal";
    modal.className = "wiki-modal";
    modal.innerHTML =
      '<div class="wiki-modal-overlay" data-close></div>' +
      '<div class="wiki-modal-content">' +
      '  <div class="wiki-modal-header">' +
      '    <span class="wiki-modal-title" id="wiki-modal-title">✏️ 编辑</span>' +
      '    <button class="wiki-modal-close" data-close title="关闭">×</button>' +
      "  </div>" +
      '  <div class="wiki-modal-body">' +
      '    <div class="wiki-new-path-row" id="wiki-new-path-row" style="display:none">' +
      '      <label>文件路径（相对 docs/）：</label>' +
      '      <input type="text" id="wiki-new-path" placeholder="systems/my-new-page.md" spellcheck="false">' +
      "    </div>" +
      '    <textarea id="wiki-editor"></textarea>' +
      "  </div>" +
      '  <div class="wiki-modal-footer">' +
      '    <button id="wiki-btn-validate" class="wiki-btn wiki-btn-secondary">▶️ 运行校验</button>' +
      '    <div class="wiki-validate-result" id="wiki-validate-result" style="display:none"></div>' +
      '    <span class="wiki-spacer"></span>' +
      '    <button id="wiki-btn-cancel" class="wiki-btn" data-close>取消</button>' +
      '    <button id="wiki-btn-save" class="wiki-btn wiki-btn-primary">💾 保存</button>' +
      "  </div>" +
      "</div>";
    document.body.appendChild(modal);

    modal.addEventListener("click", function (e) {
      var t = e.target;
      if (t.hasAttribute("data-close") || t.closest("[data-close]")) {
        closeModal();
      }
    });

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && modal.classList.contains("wiki-open")) {
        closeModal();
      }
    });

    document.getElementById("wiki-btn-save").addEventListener("click", function () {
      if (routeInfo.mode === "create") submitNewFile();
      else saveCurrentFile();
    });
    document.getElementById("wiki-btn-validate").addEventListener("click", function () {
      if (routeInfo.mode === "create") validateNewContent();
      else runValidation();
    });
  }

  /** 打开模态框。mode: "edit" | "create"。 */
  async function openModal(mode, filePath, category) {
    buildModal();
    routeInfo.mode = mode;
    currentFile = filePath || null;
    currentCategory = category || null;

    var titleEl = document.getElementById("wiki-modal-title");
    var saveBtn = document.getElementById("wiki-btn-save");
    var newPathRow = document.getElementById("wiki-new-path-row");
    var newPathInput = document.getElementById("wiki-new-path");

    if (mode === "create") {
      titleEl.textContent = "➕ 新增页面" + (category ? "（" + category + "/）" : "");
      saveBtn.textContent = "✅ 提交";
      newPathRow.style.display = "flex";
      // 预填分类目录，用户补充文件名
      newPathInput.value = category ? category + "/" : "";
    } else {
      titleEl.textContent = "✏️ 编辑：" + filePath;
      saveBtn.textContent = "💾 保存";
      newPathRow.style.display = "none";
    }

    var modal = document.getElementById("wiki-editor-modal");
    modal.classList.add("wiki-open");
    document.body.style.overflow = "hidden";

    // 重置校验结果
    var area = document.getElementById("wiki-validate-result");
    if (area) {
      area.style.display = "none";
      area.textContent = "";
      area.className = "wiki-validate-result";
    }

    // 延迟初始化 EasyMDE，确保模态框已可见（display:flex）后再挂载，
    // 否则 CodeMirror 在隐藏容器中尺寸计算错误。
    setTimeout(function () {
      ensureEasyMDE();
      if (mode === "create") {
        if (easyMDE && easyMDE.value) easyMDE.value("");
        else document.getElementById("wiki-editor").value = "";
      } else {
        // 编辑模式：从后端拉取当前文档内容并回填到编辑器
        loadFileContent(filePath);
      }
    }, 60);
  }

  function closeModal() {
    var modal = document.getElementById("wiki-editor-modal");
    if (modal) modal.classList.remove("wiki-open");
    document.body.style.overflow = "";
  }

  /** 确保 EasyMDE 已加载并初始化。 */
  function ensureEasyMDE() {
    if (typeof window.EasyMDE === "undefined") {
      toast("EasyMDE 未加载，请检查网络或资源。", "error");
      return;
    }
    if (easyMDE) return;
    var el = document.getElementById("wiki-editor");
    easyMDE = new window.EasyMDE({
      element: el,
      spellChecker: false,
      autofocus: true,
      status: ["lines", "words", "cursor"],
      toolbar: [
        "bold", "italic", "heading", "|",
        "quote", "unordered-list", "ordered-list", "|",
        "link", "image", "code", "table", "|",
        "preview", "side-by-side", "fullscreen", "|",
        "guide",
      ],
      placeholder: "在这里输入 Markdown 内容…",
    });
  }

  /** 从后端加载文件内容并回填到编辑器。 */
  async function loadFileContent(filePath) {
    try {
      var data = await apiFetch("/api/files/" + encodeURIComponent(filePath));
      if (easyMDE && easyMDE.value) {
        easyMDE.value(data.content || "");
      } else {
        document.getElementById("wiki-editor").value = data.content || "";
      }
    } catch (err) {
      toast("加载文件失败：" + err.message, "error");
    }
  }

  /** 获取编辑器内容。 */
  function getEditorContent() {
    return easyMDE && easyMDE.value ? easyMDE.value() : document.getElementById("wiki-editor").value;
  }

  /** 获取当前目标路径（新增模式从输入框取，编辑模式用 currentFile）。 */
  function getTargetPath() {
    if (routeInfo.mode === "create") {
      return document.getElementById("wiki-new-path").value.trim();
    }
    return currentFile;
  }

  /**
   * 校验新增页面的目标路径是否合法（必须以 .md 结尾、不能是纯目录）。
   * 合法返回 null；不合法返回提示文案。
   */
  function validateNewPath(path) {
    if (!path) {
      return "请先填写文件路径";
    }
    if (!/\.md$/i.test(path)) {
      return "文件路径必须以 .md 结尾（例如 systems/my-page.md）";
    }
    if (path.replace(/\\/g, "/").split("/").pop().replace(/\.md$/i, "").trim() === "") {
      return "文件路径缺少文件名（例如 systems/my-page.md）";
    }
    return null;
  }

  // -------------------------------------------------------------------------
  // 保存（编辑已有文档）
  // -------------------------------------------------------------------------

  async function saveCurrentFile() {
    if (!currentFile) return;
    var btn = document.getElementById("wiki-btn-save");
    var content = getEditorContent();
    btn.disabled = true;
    btn.textContent = "保存中…";
    try {
      await apiFetch("/api/files/" + encodeURIComponent(currentFile), {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: content }),
      });
      toast("保存成功 ✅", "success");
      setTimeout(closeModal, 300);
      setTimeout(refreshPage, 600); // 刷新回显最新内容
    } catch (err) {
      toast("保存失败：" + err.message, "error");
    } finally {
      btn.disabled = false;
      btn.textContent = "💾 保存";
    }
  }

  // -------------------------------------------------------------------------
  // 新增页面
  // -------------------------------------------------------------------------

  /** 校验待新增内容（不落盘）。 */
  async function validateNewContent() {
    var area = document.getElementById("wiki-validate-result");
    var btn = document.getElementById("wiki-btn-validate");
    var path = getTargetPath();
    var pathErr = validateNewPath(path);
    if (pathErr) {
      toast(pathErr, "warn");
      return;
    }
    area.style.display = "block";
    area.textContent = "校验中…";
    area.className = "wiki-validate-result";
    btn.disabled = true;
    try {
      var result = await apiFetch("/api/validate-content", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path: path, content: getEditorContent() }),
      });
      renderValidationResult(result);
    } catch (err) {
      renderValidationResult({ success: false, stdout: "", stderr: err.message });
    } finally {
      btn.disabled = false;
    }
  }

  /** 提交新增：先校验，通过后创建。 */
  async function submitNewFile() {
    var btn = document.getElementById("wiki-btn-save");
    var path = getTargetPath();
    var pathErr = validateNewPath(path);
    if (pathErr) {
      toast(pathErr, "warn");
      return;
    }
    btn.disabled = true;
    btn.textContent = "校验中…";
    try {
      // 1) 校验内容是否合规
      var check = await apiFetch("/api/validate-content", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path: path, content: getEditorContent() }),
      });
      if (!check.success) {
        renderValidationResult(check);
        toast("校验未通过，请修正后再提交", "error");
        return;
      }
      // 2) 校验通过，创建文件
      btn.textContent = "提交中…";
      await apiFetch("/api/files/" + encodeURIComponent(path), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: getEditorContent() }),
      });
      toast("新增成功 ✅", "success");
      setTimeout(closeModal, 300);
      setTimeout(refreshPage, 600);
    } catch (err) {
      toast("新增失败：" + err.message, "error");
    } finally {
      btn.disabled = false;
      btn.textContent = "✅ 提交";
    }
  }

  // -------------------------------------------------------------------------
  // 运行全库校验（编辑模式）
  // -------------------------------------------------------------------------

  async function runValidation() {
    var area = document.getElementById("wiki-validate-result");
    var btn = document.getElementById("wiki-btn-validate");
    if (area) {
      area.style.display = "block";
      area.textContent = "校验中…";
      area.className = "wiki-validate-result";
    }
    btn.disabled = true;
    try {
      var result = await apiFetch("/api/validate", { method: "POST" });
      renderValidationResult(result);
    } catch (err) {
      renderValidationResult({ success: false, stdout: "", stderr: err.message });
    } finally {
      btn.disabled = false;
    }
  }

  // -------------------------------------------------------------------------
  // 注入按钮（分层：首页无按钮 / 分类索引页新增 / 文档页编辑）
  // -------------------------------------------------------------------------

  function getContentEl() {
    return document.querySelector("#main") ||
      document.querySelector("article.markdown-section") ||
      document.querySelector(".content article") ||
      document.querySelector("article");
  }

  function ensureButton(id, text, className) {
    var content = getContentEl();
    if (!content) return null;
    var btn = document.getElementById(id);
    if (!btn || !btn.isConnected) {
      btn = document.createElement("button");
      btn.id = id;
      btn.className = className;
      btn.textContent = text;
      var first = content.firstChild;
      if (first) content.insertBefore(btn, first);
      else content.appendChild(btn);
    }
    return btn;
  }

  function injectButtons() {
    var editBtn = document.getElementById("wiki-edit-btn");
    var newBtn = document.getElementById("wiki-new-btn");

    if (routeInfo.mode === "doc") {
      // 文档页：显示编辑按钮
      if (!editBtn || !editBtn.isConnected) {
        editBtn = ensureButton("wiki-edit-btn", "✏️ 编辑此页", "wiki-edit-btn");
        if (editBtn) {
          editBtn.addEventListener("click", function () {
            if (currentFile) openModal("edit", currentFile, routeInfo.category);
          });
        }
      }
      if (editBtn) editBtn.style.display = "inline-block";
      if (newBtn) newBtn.style.display = "none";
    } else if (routeInfo.mode === "index") {
      // 分类索引页：显示新增按钮
      if (!newBtn || !newBtn.isConnected) {
        newBtn = ensureButton("wiki-new-btn", "➕ 新增页面", "wiki-new-btn");
        if (newBtn) {
          newBtn.addEventListener("click", function () {
            if (currentCategory) openModal("create", null, currentCategory);
          });
        }
      }
      if (newBtn) newBtn.style.display = "inline-block";
      if (editBtn) editBtn.style.display = "none";
    } else {
      // 首页：不显示任何按钮
      if (editBtn) editBtn.style.display = "none";
      if (newBtn) newBtn.style.display = "none";
    }
  }

  // -------------------------------------------------------------------------
  // Docsify 插件注册
  // -------------------------------------------------------------------------

  window.$docsify = window.$docsify || {};
  window.$docsify.plugins = (window.$docsify.plugins || []).concat([
    function (hook, vm) {
      function updateRoute() {
        var info = analyzeRoute(vm.route && vm.route.file);
        routeInfo = info;
        if (info.mode === "doc") {
          currentFile = info.file;
          currentCategory = info.category;
        } else if (info.mode === "index") {
          currentFile = null;
          currentCategory = info.category;
        } else {
          currentFile = null;
          currentCategory = null;
        }
        injectButtons();
      }
      hook.doneEach(updateRoute);
      hook.mounted(updateRoute);
    },
  ]);
})();
