const state = {
  documents: [],
  filterOptions: null,
};

const API_BASE_URL = resolveApiBaseUrl();

const statusLabels = {
  indexed: "文件和索引",
  pending_index: "仅文件",
  orphaned_index: "仅索引",
  external_index: "外部索引",
};

const statusDescriptions = {
  indexed: "文件与向量索引均存在",
  pending_index: "文件存在，但还没有向量索引",
  orphaned_index: "向量索引存在，但文件已不在磁盘",
  external_index: "索引来自工作区外部路径",
};

const deleteWarnings = {
  "delete-index": "删除向量索引，保留原文件。删除后文档暂时不可检索，可重新同步恢复。",
  "delete-file": "删除磁盘上的原文件，保留已有索引。之后仍可能检索到旧片段。",
  "delete-both": "同时删除原文件和向量索引，此操作不可撤销。",
};

const elements = {
  systemStatus: document.getElementById("systemStatus"),
  systemDetail: document.getElementById("systemDetail"),
  totalDocuments: document.getElementById("totalDocuments"),
  indexedDocuments: document.getElementById("indexedDocuments"),
  totalChunks: document.getElementById("totalChunks"),
  categoryFilter: document.getElementById("categoryFilter"),
  sourceFilter: document.getElementById("sourceFilter"),
  fileTypeFilter: document.getElementById("fileTypeFilter"),
  manageCategoryFilter: document.getElementById("manageCategoryFilter"),
  manageSourceFilter: document.getElementById("manageSourceFilter"),
  manageStatusFilter: document.getElementById("manageStatusFilter"),
  topK: document.getElementById("topK"),
  questionInput: document.getElementById("questionInput"),
  queryStatus: document.getElementById("queryStatus"),
  answerBox: document.getElementById("answerBox"),
  citationsBox: document.getElementById("citationsBox"),
  documentsTable: document.getElementById("documentsTable"),
  documentsSummary: document.getElementById("documentsSummary"),
  syncStatus: document.getElementById("syncStatus"),
  syncResult: document.getElementById("syncResult"),
  uploadStatus: document.getElementById("uploadStatus"),
  uploadFile: document.getElementById("uploadFile"),
  uploadSource: document.getElementById("uploadSource"),
  uploadCategory: document.getElementById("uploadCategory"),
  docSearchInput: document.getElementById("docSearchInput"),
};

async function apiRequest(path, options = {}) {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 10000);
  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { ...options, signal: controller.signal });
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error("API 请求超时，请确认后端服务已启动。");
    }
    throw error;
  } finally {
    window.clearTimeout(timeout);
  }
  const contentType = response.headers.get("content-type") || "";
  const body = contentType.includes("application/json") ? await response.json() : await response.text();

  if (!response.ok) {
    const detail = typeof body === "string" ? body : body.detail || JSON.stringify(body);
    throw new Error(`${response.status} ${detail}`);
  }

  return body;
}

function resolveApiBaseUrl() {
  const { protocol, hostname, port } = window.location;
  if ((hostname === "localhost" || hostname === "127.0.0.1") && port && port !== "8000") {
    return `${protocol}//${hostname}:8000`;
  }
  return "";
}

function setupTabs() {
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach((node) => node.classList.remove("active"));
      document.querySelectorAll(".panel").forEach((node) => node.classList.remove("active"));
      tab.classList.add("active");
      document.getElementById(`tab-${tab.dataset.tab}`).classList.add("active");
    });
  });
}

function fillSelect(select, items, placeholder = "全部") {
  const values = Array.isArray(items) ? items : [];
  select.innerHTML = "";
  select.disabled = false;

  const option = document.createElement("option");
  option.value = "";
  option.textContent = values.length ? placeholder : "暂无可用选项";
  select.appendChild(option);

  values.forEach((item) => {
    const itemOption = document.createElement("option");
    itemOption.value = item;
    itemOption.textContent = statusLabels[item] || item;
    if (statusDescriptions[item]) {
      itemOption.title = statusDescriptions[item];
    }
    select.appendChild(itemOption);
  });

  select.disabled = values.length === 0;
  select.title = values.length ? "" : "当前没有可供筛选的数据";
}

async function loadOverview() {
  const overview = await apiRequest("/api/documents/overview");
  elements.systemStatus.textContent = overview.qdrant_reachable ? "运行正常" : "服务降级";
  elements.systemStatus.classList.toggle("degraded", !overview.qdrant_reachable);
  elements.systemDetail.textContent = overview.qdrant_reachable
    ? `API 与向量库可用，collection：${overview.collection}`
    : "Qdrant 当前不可达，请检查向量库服务。";
  elements.totalDocuments.textContent = overview.total_documents;
  elements.indexedDocuments.textContent = overview.indexed_documents;
  elements.totalChunks.textContent = overview.total_chunks;
}

async function loadFilters() {
  state.filterOptions = await apiRequest("/api/documents/filters");
  fillSelect(elements.categoryFilter, state.filterOptions.categories);
  fillSelect(elements.sourceFilter, state.filterOptions.source_labels);
  fillSelect(elements.fileTypeFilter, state.filterOptions.file_types);
  fillSelect(elements.manageCategoryFilter, state.filterOptions.categories);
  fillSelect(elements.manageSourceFilter, state.filterOptions.source_labels);
  fillSelect(elements.manageStatusFilter, state.filterOptions.statuses);
}

async function loadDocuments() {
  const result = await apiRequest("/api/documents");
  state.documents = result.documents;
  renderDocuments();
}

function renderDocuments() {
  const keyword = elements.docSearchInput.value.trim().toLowerCase();
  const category = elements.manageCategoryFilter.value;
  const source = elements.manageSourceFilter.value;
  const status = elements.manageStatusFilter.value;

  const filtered = state.documents.filter((doc) => {
    if (keyword && !`${doc.filename} ${doc.relative_path}`.toLowerCase().includes(keyword)) return false;
    if (category && doc.category !== category) return false;
    if (source && doc.source_label !== source) return false;
    if (status && doc.status !== status) return false;
    return true;
  });

  elements.documentsSummary.textContent = `显示 ${filtered.length} / ${state.documents.length} 份文档`;

  if (!filtered.length) {
    elements.documentsTable.innerHTML = `<tr><td colspan="8" class="empty-row">没有符合条件的文档。可以清空筛选，或先导入资料。</td></tr>`;
    return;
  }

  elements.documentsTable.innerHTML = filtered.map(renderDocumentRow).join("");
}

function renderDocumentRow(doc) {
  const removable = doc.storage_area === "raw" || doc.storage_area === "upload";
  return `
    <tr>
      <td><div class="doc-name"><strong>${escapeHtml(doc.filename)}</strong><span class="doc-path">${escapeHtml(doc.relative_path)}</span></div></td>
      <td><span class="status-badge status-${escapeHtml(doc.status)}" title="${escapeHtml(statusDescriptions[doc.status] || "")}">${escapeHtml(statusLabels[doc.status] || doc.status)}</span></td>
      <td>${escapeHtml(doc.category)}</td>
      <td>${escapeHtml(doc.source_label)}</td>
      <td>${escapeHtml(doc.file_type)}</td>
      <td>${escapeHtml(doc.storage_area)}</td>
      <td>${doc.chunk_count}</td>
      <td>
        ${
          removable
            ? `<div class="doc-actions">
                <button class="action-button" title="删除索引，保留文件" data-action="delete-index" data-storage="${escapeHtml(doc.storage_area)}" data-path="${escapeHtml(doc.relative_path)}">删索引</button>
                <button class="action-button" title="删除文件，保留索引" data-action="delete-file" data-storage="${escapeHtml(doc.storage_area)}" data-path="${escapeHtml(doc.relative_path)}">删文件</button>
                <button class="action-button danger" title="删除文件和索引" data-action="delete-both" data-storage="${escapeHtml(doc.storage_area)}" data-path="${escapeHtml(doc.relative_path)}">全部删除</button>
              </div>`
            : `<span class="doc-path">仅可查看</span>`
        }
      </td>
    </tr>
  `;
}

async function refreshWorkspace() {
  const button = document.getElementById("refreshAllBtn");
  button.disabled = true;
  button.textContent = "检查中...";
  try {
    await Promise.all([loadOverview(), loadFilters(), loadDocuments()]);
  } catch (error) {
    elements.systemStatus.textContent = "检查失败";
    elements.systemStatus.classList.add("degraded");
    elements.systemDetail.textContent = error.message;
  } finally {
    button.disabled = false;
    button.textContent = "重新检查";
  }
}

async function askQuestion(event) {
  event.preventDefault();
  const question = elements.questionInput.value.trim();
  if (!question) {
    elements.queryStatus.textContent = "请输入问题。";
    elements.questionInput.focus();
    return;
  }

  elements.queryStatus.textContent = "正在生成回答...";
  setTextbox(elements.answerBox, "正在整理回答...", false);
  setTextbox(elements.citationsBox, "正在检索引用片段...", false);

  try {
    const result = await apiRequest("/api/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question,
        top_k: Number(elements.topK.value),
        category_filter: elements.categoryFilter.value || null,
        source_filter: elements.sourceFilter.value || null,
        file_type_filter: elements.fileTypeFilter.value || null,
        tag_filter: null,
      }),
    });

    const citations = result.citations || [];
    elements.queryStatus.textContent = `回答完成，返回 ${citations.length} 条引用。`;
    setTextbox(elements.answerBox, result.answer || "没有返回回答内容。", false);
    renderCitations(citations);
  } catch (error) {
    elements.queryStatus.textContent = `请求失败：${error.message}`;
    setTextbox(elements.answerBox, `请求失败：${error.message}`, false);
    setTextbox(elements.citationsBox, "本次没有可用引用片段。", true);
  }
}

function setTextbox(node, text, empty) {
  node.classList.toggle("empty", empty);
  node.textContent = text;
}

function renderCitations(citations) {
  if (!citations.length) {
    setTextbox(elements.citationsBox, "本次没有返回引用片段。", true);
    return;
  }

  elements.citationsBox.classList.remove("empty");
  elements.citationsBox.innerHTML = citations
    .map((citation, index) => {
      const title = `${index + 1}. ${citation.filename || "未命名文件"} · ${citation.chunk_id || "片段"}`;
      const meta = `${citation.file_path || citation.title || "未知路径"} · 相关度 ${Number(citation.score || 0).toFixed(3)}`;
      return `<article class="citation-entry">
        <div class="citation-entry-head"><strong>${escapeHtml(title)}</strong><span>${escapeHtml(meta)}</span></div>
        <pre>${escapeHtml(citation.excerpt || "无引用内容")}</pre>
      </article>`;
    })
    .join("");
}

async function syncRawDirectory() {
  elements.syncStatus.textContent = "同步中...";
  elements.syncResult.classList.add("hidden");
  try {
    const result = await apiRequest("/api/documents/ingest/raw", { method: "POST" });
    elements.syncStatus.textContent = `同步完成，处理 ${result.ingested_count} 个文件。`;
    elements.syncResult.textContent = JSON.stringify(result, null, 2);
    elements.syncResult.classList.remove("hidden");
    await refreshWorkspace();
  } catch (error) {
    elements.syncStatus.textContent = `同步失败：${error.message}`;
  }
}

async function uploadSingleDocument(event) {
  event.preventDefault();
  if (!elements.uploadFile.files.length) {
    elements.uploadStatus.textContent = "请先选择要上传的文档。";
    return;
  }

  const formData = new FormData();
  formData.append("file", elements.uploadFile.files[0]);
  formData.append("source_label", elements.uploadSource.value.trim() || "upload");
  formData.append("category", elements.uploadCategory.value.trim() || "general");
  elements.uploadStatus.textContent = "上传中...";

  try {
    const result = await apiRequest("/api/documents/upload", { method: "POST", body: formData });
    elements.uploadStatus.textContent = `上传完成：${result.filename}`;
    elements.uploadFile.value = "";
    await refreshWorkspace();
  } catch (error) {
    elements.uploadStatus.textContent = `上传失败：${error.message}`;
  }
}

async function handleTableAction(event) {
  const button = event.target.closest("[data-action]");
  if (!button) return;

  const action = button.dataset.action;
  const options = {
    "delete-index": { delete_file: false, delete_index: true, label: "删除索引" },
    "delete-file": { delete_file: true, delete_index: false, label: "删除文件" },
    "delete-both": { delete_file: true, delete_index: true, label: "全部删除" },
  }[action];
  if (!options) return;

  const path = button.dataset.path;
  if (!window.confirm(`${options.label}：${path}\n\n${deleteWarnings[action]}\n\n确认继续？`)) return;

  try {
    await apiRequest("/api/documents/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        storage_area: button.dataset.storage,
        relative_path: path,
        delete_file: options.delete_file,
        delete_index: options.delete_index,
      }),
    });
    await refreshWorkspace();
  } catch (error) {
    window.alert(`删除失败：${error.message}`);
  }
}

function resetDocumentFilters() {
  elements.docSearchInput.value = "";
  elements.manageCategoryFilter.value = "";
  elements.manageSourceFilter.value = "";
  elements.manageStatusFilter.value = "";
  renderDocuments();
}

function bindEvents() {
  setupTabs();
  document.getElementById("refreshAllBtn").addEventListener("click", refreshWorkspace);
  document.getElementById("refreshDocsBtn").addEventListener("click", loadDocuments);
  document.getElementById("clearQueryBtn").addEventListener("click", () => {
    elements.questionInput.value = "";
    elements.queryStatus.textContent = "";
    setTextbox(elements.answerBox, "还没有回答，请先输入问题。", true);
    setTextbox(elements.citationsBox, "回答完成后，引用片段会显示在这里。", true);
    elements.questionInput.focus();
  });
  document.getElementById("syncBtn").addEventListener("click", syncRawDirectory);
  document.getElementById("queryForm").addEventListener("submit", askQuestion);
  document.getElementById("uploadForm").addEventListener("submit", uploadSingleDocument);
  document.getElementById("documentsTable").addEventListener("click", handleTableAction);
  document.getElementById("resetDocFiltersBtn").addEventListener("click", resetDocumentFilters);

  [elements.docSearchInput, elements.manageCategoryFilter, elements.manageSourceFilter, elements.manageStatusFilter].forEach((node) => {
    node.addEventListener("input", renderDocuments);
    node.addEventListener("change", renderDocuments);
  });
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

bindEvents();
refreshWorkspace();
