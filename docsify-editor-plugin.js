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
    // docsify/ 下其它页面（如校验规则）：只读展示，不显示编辑/删除按钮
    if (raw.indexOf("docsify/") === 0) return { mode: "plain" };

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
  // 元数据表单：必填字段抽离为表单输入框，富文本只填正文。
  // -------------------------------------------------------------------------

  // 分类 → 默认文档类型
  var CATEGORY_TYPE = {
    systems: "system",
    services: "service",
    integrations: "integration",
    runbooks: "runbook",
  };

  // 字段定义：label / key / kind(text|select|date|list|textarea) / options / required / help
  var FIELD_DEFS = {
    title: { label: "标题 title", kind: "text", required: true, help: "文档标题，如「OA 系统」" },
    type: {
      label: "类型 type", kind: "select", required: true,
      options: [
        { v: "system", t: "system（系统）" },
        { v: "service", t: "service（服务）" },
        { v: "integration", t: "integration（集成）" },
        { v: "runbook", t: "runbook（应急手册）" },
      ],
      help: "决定文档归属的目录与必填字段",
    },
    status: {
      label: "状态 status", kind: "select", required: true,
      options: [
        { v: "active", t: "active（在用）" },
        { v: "deprecated", t: "deprecated（已弃用）" },
        { v: "draft", t: "draft（草稿）" },
        { v: "needs-review", t: "needs-review（待评审）" },
      ],
      help: "文档当前状态",
    },
    owner: { label: "负责人 owner", kind: "text", required: true, help: "负责团队或角色，如「行政管理团队」" },
    last_reviewed: { label: "最近评审 last_reviewed", kind: "date", required: true, help: "最近评审日期，格式 YYYY-MM-DD" },
    description: { label: "描述 description", kind: "textarea", help: "一句话概述（可选）" },
    vendor: { label: "厂商 vendor", kind: "text", help: "厂商或供应商（可选）" },
    hosting: {
      label: "托管 hosting", kind: "select",
      options: [{ v: "on-prem", t: "on-prem（本地）" }, { v: "cloud", t: "cloud（云）" }, { v: "hybrid", t: "hybrid（混合）" }, { v: "unknown", t: "unknown" }],
      help: "托管方式（可选）",
    },
    authentication: {
      label: "认证 authentication", kind: "select",
      options: [{ v: "SSO", t: "SSO" }, { v: "LDAP", t: "LDAP" }, { v: "local", t: "local" }, { v: "none", t: "none" }, { v: "unknown", t: "unknown" }],
      help: "认证方式（可选）",
    },
    tier: {
      label: "服务级别 tier", kind: "select",
      options: [{ v: "tier-1", t: "tier-1" }, { v: "tier-2", t: "tier-2" }, { v: "tier-3", t: "tier-3" }, { v: "unknown", t: "unknown" }],
      help: "服务级别（可选）",
    },
    systems: { label: "关联系统 systems", kind: "list", required: true, help: "关联的系统，多个用英文逗号分隔" },
    direction: {
      label: "数据方向 direction", kind: "select",
      options: [{ v: "one-way", t: "one-way（单向）" }, { v: "two-way", t: "two-way（双向）" }, { v: "unknown", t: "unknown" }],
      help: "数据流向（可选）",
    },
    protocol: {
      label: "协议 protocol", kind: "select",
      options: [{ v: "API", t: "API" }, { v: "SFTP", t: "SFTP" }, { v: "LDAP", t: "LDAP" }, { v: "SAML", t: "SAML" }, { v: "SCIM", t: "SCIM" }, { v: "OAuth", t: "OAuth" }, { v: "webhook", t: "webhook" }, { v: "unknown", t: "unknown" }],
      help: "集成协议（可选）",
    },
    severity: {
      label: "严重级别 severity", kind: "select", required: true,
      options: [{ v: "critical", t: "critical（危急）" }, { v: "high", t: "high（高）" }, { v: "medium", t: "medium（中）" }, { v: "low", t: "low（低）" }, { v: "unknown", t: "unknown" }],
      help: "事件严重级别",
    },
    dependencies: { label: "依赖 dependencies", kind: "list", help: "依赖项，多个用英文逗号分隔（可选）" },
    tags: { label: "标签 tags", kind: "list", help: "标签，多个用英文逗号分隔（可选）" },
    related_services: { label: "相关服务 related_services", kind: "list", help: "相关服务，多个用英文逗号分隔（可选）" },
  };

  // 各类型展示的字段顺序（必填在前，常用可选在后）
  var TYPE_FIELDS = {
    system: ["title", "type", "status", "owner", "last_reviewed", "description", "vendor", "hosting", "authentication", "dependencies", "tags"],
    service: ["title", "type", "status", "owner", "last_reviewed", "description", "tier", "tags"],
    integration: ["title", "type", "status", "owner", "last_reviewed", "systems", "description", "direction", "protocol", "tags"],
    runbook: ["title", "type", "status", "owner", "last_reviewed", "severity", "description", "related_services", "tags"],
  };

  /** 解析 Markdown 内容 → { fm: 对象, body: 正文 }。无 frontmatter 时 body 为全文。 */
  function parseFrontmatter(content) {
    var text = String(content || "").replace(/^\uFEFF/, "");
    var m = text.match(/^---\s*\n([\s\S]*?)\n---\s*\n?/);
    if (!m) return { fm: {}, body: text };
    var fm = {};
    var lines = m[1].split("\n");
    var i = 0;
    while (i < lines.length) {
      var line = lines[i];
      var kv = line.match(/^([A-Za-z_][\w-]*):\s*(.*)$/);
      if (kv) {
        var key = kv[1];
        var val = kv[2].trim();
        // 引号包裹
        var q = val.match(/^["'](.*)["']$/);
        if (q) fm[key] = q[1];
        else if (val === "true") fm[key] = true;
        else if (val === "false") fm[key] = false;
        else if (val !== "" && !isNaN(Number(val))) fm[key] = Number(val);
        else if (val === "") {
          // 可能是列表（后续以 - 开头）
          var list = [];
          var j = i + 1;
          while (j < lines.length && /^\s*-\s+/.test(lines[j])) {
            list.push(lines[j].replace(/^\s*-\s+/, "").trim());
            j++;
          }
          if (list.length) { fm[key] = list; i = j - 1; }
          else fm[key] = "";
        } else fm[key] = val;
      }
      i++;
    }
    return { fm: fm, body: text.slice(m[0].length).replace(/^\s*\n/, "") };
  }

  /** 把表单值组装成 YAML frontmatter 字符串。 */
  function buildFrontmatter(values) {
    var keys = ["title", "type", "status", "owner", "last_reviewed",
      "description", "vendor", "hosting", "authentication", "tier",
      "systems", "direction", "protocol", "severity",
      "dependencies", "tags", "related_services"];
    var out = ["---"];
    keys.forEach(function (k) {
      var v = values[k];
      if (v === undefined || v === null || v === "") return;
      if (Array.isArray(v)) {
        if (!v.length) return;
        out.push(k + ":");
        v.forEach(function (item) { out.push("  - " + item); });
      } else {
        out.push(k + ": " + v);
      }
    });
    out.push("---");
    return out.join("\n");
  }

  /** 收集表单当前值。 */
  function collectFormValues() {
    var values = {};
    var inputs = document.querySelectorAll("#wiki-meta-form [data-key]");
    for (var i = 0; i < inputs.length; i++) {
      var el = inputs[i];
      var key = el.getAttribute("data-key");
      if (el.type === "checkbox") {
        values[key] = el.checked ? el.value : "";
      } else if (el.tagName === "SELECT") {
        values[key] = el.value || "";
      } else {
        values[key] = el.value.trim();
      }
    }
    // 列表字段：逗号分隔字符串 → 数组
    ["systems", "dependencies", "tags", "related_services"].forEach(function (k) {
      if (typeof values[k] === "string" && values[k] !== "") {
        values[k] = values[k].split(",").map(function (s) { return s.trim(); }).filter(Boolean);
      }
    });
    return values;
  }

  /** 根据类型渲染表单字段区。所有字段直接平铺显示，不折叠。 */
  function renderMetaForm(type) {
    var container = document.getElementById("wiki-meta-form");
    if (!container) return;
    var keys = TYPE_FIELDS[type] || TYPE_FIELDS.system;

    var html = "";
    keys.forEach(function (key) {
      var def = FIELD_DEFS[key];
      if (!def) return;
      var req = def.required ? " <span class='wiki-req'>*</span>" : "";
      var reqAttr = def.required ? " required" : "";
      var help = def.help ? "<div class='wiki-field-help'>" + def.help + "</div>" : "";
      var input = "";
      if (def.kind === "select") {
        input = "<select data-key='" + key + "'" + reqAttr + ">";
        input += "<option value=''></option>";
        (def.options || []).forEach(function (o) {
          input += "<option value='" + o.v + "'>" + o.t + "</option>";
        });
        input += "</select>";
      } else if (def.kind === "date") {
        input = "<input type='date' data-key='" + key + "'" + reqAttr + ">";
      } else if (def.kind === "textarea") {
        input = "<textarea data-key='" + key + "' rows='2'" + reqAttr + "></textarea>";
      } else {
        input = "<input type='text' data-key='" + key + "' spellcheck='false'" + reqAttr + ">";
      }
      html += "<div class='wiki-field' data-field='" + key + "'><label>" + def.label + req + "</label>" + input + help + "</div>";
    });
    container.innerHTML = html;
    // 回填 type 下拉当前值（新增/切换类型后保持选中，避免下拉被重置为空）
    var typeSel = container.querySelector('[data-key="type"]');
    if (typeSel && type) typeSel.value = type;
  }

  /** 把已解析的 frontmatter 回填到表单。 */
  function fillForm(values) {
    var inputs = document.querySelectorAll("#wiki-meta-form [data-key]");
    for (var i = 0; i < inputs.length; i++) {
      var el = inputs[i];
      var key = el.getAttribute("data-key");
      var v = values[key];
      if (v === undefined || v === null) continue;
      if (Array.isArray(v)) v = v.join(", ");
      if (el.tagName === "SELECT") {
        // 逐项匹配 value（避免选项文本带中文导致不匹配）
        for (var j = 0; j < el.options.length; j++) {
          if (el.options[j].value === String(v)) { el.value = String(v); break; }
        }
      } else {
        el.value = String(v);
      }
    }
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
      '    <div class="wiki-meta-scroll" id="wiki-meta-scroll">' +
      '      <div class="wiki-meta-title">📋 元数据（必填项已抽离，富文本只需填正文）</div>' +
      '      <div class="wiki-meta-grid" id="wiki-meta-form"></div>' +
      "    </div>" +
      '    <div class="wiki-body-label">📄 正文内容</div>' +
      '    <button id="wiki-insert-body" class="wiki-btn wiki-btn-primary" style="display:none">✏️ 插入正文</button>' +
      '    <div class="wiki-editor-wrap" id="wiki-editor-wrap" style="display:none"><textarea id="wiki-editor"></textarea></div>' +
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

    // 点击「插入正文」后才初始化并显示富文本编辑器（新增与编辑模式统一）。
    // 编辑模式的正文内容已由 openModal -> loadFileContent 在打开时回填
    // （首次编辑写入 textarea，EasyMDE 初始化时自动读取；后续编辑直接写入 easyMDE）。
    document.getElementById("wiki-insert-body").addEventListener("click", function () {
      var btn = document.getElementById("wiki-insert-body");
      var wrap = document.getElementById("wiki-editor-wrap");
      btn.style.display = "none";
      wrap.style.display = "flex";
      ensureEasyMDE();
      if (easyMDE) {
        // 等布局稳定后再刷新，避免 CodeMirror 在 flex 布局完成前计算错误尺寸
        setTimeout(function () {
          easyMDE.codemirror && easyMDE.codemirror.refresh();
        }, 80);
      }
    });

    // 类型切换时，按新类型重新渲染表单字段区
    document.getElementById("wiki-meta-form").addEventListener("change", function (e) {
      var t = e.target;
      if (t && t.getAttribute && t.getAttribute("data-key") === "type") {
        var newType = t.value || "system";
        var prevType = window.__wikiMetaType || "system";
        if (newType !== prevType) {
          window.__wikiMetaType = newType;
          renderMetaForm(newType);
        }
      }
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

    // 根据模式确定默认类型
    var defaultType = "system";
    if (mode === "create" && category) {
      defaultType = CATEGORY_TYPE[category] || "system";
    } else if (mode === "edit") {
      defaultType = null; // 编辑时由回填内容决定，先渲染默认再覆盖
    }

    if (mode === "create") {
      titleEl.textContent = "➕ 新增页面" + (category ? "（" + category + "/）" : "");
      saveBtn.textContent = "✅ 提交";
      newPathRow.style.display = "flex";
      // 预填分类目录，用户补充文件名
      newPathInput.value = category ? category + "/" : "";
      // 渲染空表单（默认类型）
      window.__wikiMetaType = defaultType;
      renderMetaForm(defaultType);
    } else {
      titleEl.textContent = "✏️ 编辑：" + filePath;
      saveBtn.textContent = "💾 保存";
      newPathRow.style.display = "none";
      // 编辑：点「编辑此页」即拉取并回填元数据字段（正文仍由「插入正文」带出）。
      // loadFileContent 会按实际 type 重渲染表单并回填字段；正文暂存到 textarea，
      // 待「插入正文」初始化 EasyMDE 时读取。
      if (currentFile) loadFileContent(currentFile);
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

    // 正文编辑区显示控制：两种模式统一 —— 默认只显示「插入正文」按钮，
    // 点击后才初始化并显示富文本编辑器。
    //   新增模式：点击后初始化空编辑器
    //   编辑模式：点击后初始化编辑器并拉取当前文档内容回填
    var insertBtn = document.getElementById("wiki-insert-body");
    var editorWrap = document.getElementById("wiki-editor-wrap");
    insertBtn.style.display = "inline-block";
    editorWrap.style.display = "none";
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
      // 高度由 CSS 全权控制（.wiki-editor-wrap 内 flex 撑满剩余空间），
      // 不再设置 maxHeight/minHeight，避免编辑器只显示一部分高度。
    });
  }

  /** 从后端加载文件内容，解析后回填元数据表单与正文编辑器。 */
  async function loadFileContent(filePath) {
    try {
      var data = await apiFetch("/api/files/" + encodeURIComponent(filePath));
      var parsed = parseFrontmatter(data.content || "");
      // 按实际 type 重渲染表单（保证字段正确），再回填
      var type = parsed.fm.type || "system";
      window.__wikiMetaType = type;
      renderMetaForm(type);
      fillForm(parsed.fm);
      if (easyMDE && easyMDE.value) {
        easyMDE.value(parsed.body || "");
      } else {
        document.getElementById("wiki-editor").value = parsed.body || "";
      }
    } catch (err) {
      toast("加载文件失败：" + err.message, "error");
    }
  }

  /** 获取编辑器内容。 */
  function getEditorContent() {
    return easyMDE && easyMDE.value ? easyMDE.value() : document.getElementById("wiki-editor").value;
  }

  /** 校验必填元数据字段，返回错误文案或 null。 */
  function validateMetaForm() {
    var inputs = document.querySelectorAll("#wiki-meta-form [data-key][required]");
    for (var i = 0; i < inputs.length; i++) {
      var el = inputs[i];
      var v = el.value ? el.value.trim() : "";
      if (!v) {
        var label = el.closest(".wiki-field") ? el.closest(".wiki-field").querySelector("label") : null;
        var name = label ? label.textContent.replace("*", "").trim() : el.getAttribute("data-key");
        return "请填写必填字段：" + name;
      }
    }
    return null;
  }

  /** 组装完整内容：frontmatter（来自表单）+ 正文（来自编辑器）。 */
  function composeFullContent() {
    var values = collectFormValues();
    var fm = buildFrontmatter(values);
    var body = getEditorContent();
    if (body && !body.replace(/\s/g, "")) body = "";
    return (fm + "\n\n" + body).replace(/\n{3,}/g, "\n\n").trim() + "\n";
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
    // 必填元数据校验
    var metaErr = validateMetaForm();
    if (metaErr) {
      toast(metaErr, "warn");
      return;
    }
    var content = composeFullContent();
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
    var metaErr = validateMetaForm();
    if (metaErr) {
      toast(metaErr, "warn");
      return;
    }
    var content = composeFullContent();
    area.style.display = "block";
    area.textContent = "校验中…";
    area.className = "wiki-validate-result";
    btn.disabled = true;
    try {
      var result = await apiFetch("/api/validate-content", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path: path, content: content }),
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
    var metaErr = validateMetaForm();
    if (metaErr) {
      toast(metaErr, "warn");
      return;
    }
    var content = composeFullContent();
    btn.disabled = true;
    btn.textContent = "校验中…";
    try {
      // 1) 校验内容是否合规
      var check = await apiFetch("/api/validate-content", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path: path, content: content }),
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
        body: JSON.stringify({ content: content }),
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
  // 删除页面
  // -------------------------------------------------------------------------

  /** 删除当前文档：二次确认后调用后端 DELETE，成功后刷新页面。 */
  async function deleteCurrentFile() {
    if (!currentFile) return;
    var ok = window.confirm(
      "确定要删除「" + currentFile + "」吗？\n" +
      "该操作会同时删除文件本身，并从侧边栏与分类索引中移除对应链接，且不可恢复。"
    );
    if (!ok) return;
    try {
      await apiFetch("/api/files/" + encodeURIComponent(currentFile), {
        method: "DELETE",
      });
      toast("删除成功 ✅", "success");
      // 删除后跳转到该分类索引页（或首页），避免停留在已不存在的页面
      var targetHash = currentCategory
        ? "#/docs/" + currentCategory + "/README.md"
        : "#/";
      setTimeout(function () {
        window.location.hash = targetHash;
      }, 300);
      setTimeout(refreshPage, 600);
    } catch (err) {
      toast("删除失败：" + err.message, "error");
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
    var delBtn = document.getElementById("wiki-del-btn");
    var newBtn = document.getElementById("wiki-new-btn");

    if (routeInfo.mode === "doc") {
      // 文档页：显示「编辑此页」+「删除」按钮（右下角浮动）
      if (!editBtn || !editBtn.isConnected) {
        editBtn = ensureButton("wiki-edit-btn", "✏️ 编辑此页", "wiki-edit-btn");
        if (editBtn) {
          editBtn.addEventListener("click", function () {
            if (currentFile) openModal("edit", currentFile, routeInfo.category);
          });
        }
      }
      if (!delBtn || !delBtn.isConnected) {
        delBtn = ensureButton("wiki-del-btn", "🗑️ 删除", "wiki-del-btn");
        if (delBtn) {
          delBtn.addEventListener("click", function () {
            deleteCurrentFile();
          });
        }
      }
      if (editBtn) editBtn.style.display = "inline-block";
      if (delBtn) delBtn.style.display = "inline-block";
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
      if (delBtn) delBtn.style.display = "none";
    } else {
      // 首页 / docsify 下其它只读页面：不显示任何按钮
      if (editBtn) editBtn.style.display = "none";
      if (delBtn) delBtn.style.display = "none";
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
