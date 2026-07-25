const state = {
  documents: [],
  filterOptions: null,
};

const statusLabels = {
  indexed: "文件+索引",
  pending_index: "仅文件",
  orphaned_index: "仅索引",
  external_index: "外部索引",
};

const deleteWarnings = {
  "delete-index": "将删除向量索引，文档文件会保留。删除后该文档暂时不可被问答检索，可重新同步恢复索引。",
  "delete-file": "将删除磁盘上的文档文件，当前索引会保留。之后仍可能检索到旧片段，建议只在需要保留检索历史时使用。",
  "delete-both": "将同时删除文档文件和向量索引。该操作不可撤销，删除后需要重新上传或恢复文件。",
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
  citationTemplate: document.getElementById("citationTemplate"),
};

async function apiRequest(path, options = {}) {
  const response = await fetch(path, options);
  const contentType = response.headers.get("content-type") || "";
  const body = contentType.includes("application/json") ? await response.json() : await response.text();

  if (!response.ok) {
    const detail = typeof body === "string" ? body : body.detail || JSON.stringify(body);
    throw new Error(`${response.status} ${detail}`);
  }

  return body;
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

function fillSelect(select, items, includeAll = true, placeholder = "全部") {
  select.innerHTML = "";
  if (includeAll) {
    const option = document.createElement("option");
    option.value = "";
    option.textContent = placeholder;
    select.appendChild(option);
  }

  items.forEach((item) => {
    const option = document.createElement("option");
    option.value = item;
    option.textContent = statusLabels[item] || item;
    select.appendChild(option);
  });
}

async function loadOverview() {
  const overview = await apiRequest("/api/documents/overview");
  elements.systemStatus.textContent = overview.qdrant_reachable ? "运行正常" : "服务降级";
  elements.systemStatus.classList.toggle("degraded", !overview.qdrant_reachable);
  elements.systemDetail.textContent = overview.qdrant_reachable
    ? `API 与向量库可用，当前 collection：${overview.collection}`
    : "Qdrant 当前不可达，请优先检查向量库状态。";
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
    if (keyword && !`${doc.filename} ${doc.relative_path}`.toLowerCase().includes(keyword)) {
      return false;
    }
    if (category && doc.category !== category) {
      return false;
    }
    if (source && doc.source_label !== source) {
      return false;
    }
    if (status && doc.status !== status) {
      return false;
    }
    return true;
  });

  elements.documentsSummary.textContent = `当前显示 ${filtered.length} / ${state.documents.length} 份文档`;

  if (!filtered.length) {
    elements.documentsTable.innerHTML = `<tr><td colspan="8" class="empty-row">没有符合当前筛选条件的文档。</td></tr>`;
    return;
  }

  elements.documentsTable.innerHTML = filtered.map(renderDocumentRow).join("");
}

function renderDocumentRow(doc) {
  const removable = doc.storage_area === "raw" || doc.storage_area === "upload";
  return `
    <tr>
      <td>
        <div class="doc-name">
          <strong>${escapeHtml(doc.filename)}</strong>
          <span class="doc-path">${escapeHtml(doc.relative_path)}</span>
        </div>
      </td>
      <td><span class="status-badge status-${escapeHtml(doc.status)}">${escapeHtml(statusLabels[doc.status] || doc.status)}</span></td>
      <td>${escapeHtml(doc.category)}</td>
      <td>${escapeHtml(doc.source_label)}</td>
      <td>${escapeHtml(doc.file_type)}</td>
      <td>${escapeHtml(doc.storage_area)}</td>
      <td>${doc.chunk_count}</td>
      <td>
        ${
          removable
            ? `
          <div class="doc-actions">
            <button class="action-button" title="删除索引，保留文件" data-action="delete-index" data-storage="${escapeHtml(doc.storage_area)}" data-path="${escapeHtml(doc.relative_path)}">删索引</button>
            <button class="action-button" title="删除文件，保留索引" data-action="delete-file" data-storage="${escapeHtml(doc.storage_area)}" data-path="${escapeHtml(doc.relative_path)}">删文件</button>
            <button class="action-button danger" data-action="delete-both" data-storage="${escapeHtml(doc.storage_area)}" data-path="${escapeHtml(doc.relative_path)}">全部删除</button>
          </div>
        `
            : `<span class="doc-path">仅可查看</span>`
        }
      </td>
    </tr>
  `;
}

async function initialize() {
  try {
    await Promise.all([loadOverview(), loadFilters(), loadDocuments()]);
  } catch (error) {
    elements.systemStatus.textContent = "加载失败";
    elements.systemStatus.classList.add("degraded");
    elements.systemDetail.textContent = error.message;
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
  elements.answerBox.classList.remove("empty");
  elements.answerBox.textContent = "正在整理回答...";
  elements.citationsBox.classList.remove("empty");
  elements.citationsBox.textContent = "正在检索引用片段...";

  try {
    const payload = {
      question,
      top_k: Number(elements.topK.value),
      category_filter: elements.categoryFilter.value || null,
      source_filter: elements.sourceFilter.value || null,
      file_type_filter: elements.fileTypeFilter.value || null,
      tag_filter: null,
    };

    const result = await apiRequest("/api/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const citations = result.citations || [];
    elements.queryStatus.textContent = `回答完成，返回 ${citations.length} 条引用。`;
    elements.answerBox.textContent = result.answer || "没有返回回答内容。";
    renderCitations(citations);
  } catch (error) {
    elements.queryStatus.textContent = `请求失败：${error.message}`;
    elements.answerBox.textContent = `请求失败：${error.message}`;
    elements.citationsBox.classList.add("empty");
    elements.citationsBox.textContent = "本次没有可用引用片段。";
  }
}

function renderCitations(citations) {
  if (!citations.length) {
    elements.citationsBox.classList.add("empty");
    elements.citationsBox.textContent = "本次没有返回引用片段。";
    return;
  }

  elements.citationsBox.classList.remove("empty");
  elements.citationsBox.innerHTML = "";

  citations.forEach((citation, index) => {
    const node = elements.citationTemplate.content.firstElementChild.cloneNode(true);
    const title = node.querySelector(".citation-title");
    const score = node.querySelector(".citation-score");
    const preview = node.querySelector(".citation-preview");
    const meta = node.querySelector(".citation-meta");
    const content = node.querySelector(".citation-content");

    title.textContent = `${citation.filename} · ${citation.chunk_id}`;
    score.textContent = `相关度 ${Number(citation.score).toFixed(3)}`;
    preview.textContent = citation.excerpt || "无摘要";
    meta.textContent = citation.file_path || citation.title || "";
    content.textContent = citation.excerpt || "无内容";

    if (index === 0) {
      node.open = true;
    }

    elements.citationsBox.appendChild(node);
  });
}

async function syncRawDirectory() {
  elements.syncStatus.textContent = "同步中...";
  elements.syncResult.classList.add("hidden");

  try {
    const result = await apiRequest("/api/documents/ingest/raw", { method: "POST" });
    elements.syncStatus.textContent = `同步完成，本次处理 ${result.ingested_count} 个文件。`;
    elements.syncResult.textContent = JSON.stringify(result, null, 2);
    elements.syncResult.classList.remove("hidden");
    await initialize();
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
    const result = await apiRequest("/api/documents/upload", {
      method: "POST",
      body: formData,
    });
    elements.uploadStatus.textContent = `上传完成：${result.filename}`;
    elements.uploadFile.value = "";
    await initialize();
  } catch (error) {
    elements.uploadStatus.textContent = `上传失败：${error.message}`;
  }
}

async function handleTableAction(event) {
  const button = event.target.closest("[data-action]");
  if (!button) {
    return;
  }

  const action = button.dataset.action;
  const storage = button.dataset.storage;
  const relativePath = button.dataset.path;

  const options = {
    "delete-index": { delete_file: false, delete_index: true, label: "删除索引" },
    "delete-file": { delete_file: true, delete_index: false, label: "删除原文件" },
    "delete-both": { delete_file: true, delete_index: true, label: "同时删除文件和索引" },
  }[action];

  if (!options) {
    return;
  }

  const confirmed = window.confirm(`${options.label}：${relativePath}\n\n${deleteWarnings[action]}\n\n确认继续？`);
  if (!confirmed) {
    return;
  }

  try {
    await apiRequest("/api/documents/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        storage_area: storage,
        relative_path: relativePath,
        delete_file: options.delete_file,
        delete_index: options.delete_index,
      }),
    });
    await initialize();
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
  document.getElementById("refreshAllBtn").addEventListener("click", initialize);
  document.getElementById("refreshDocsBtn").addEventListener("click", loadDocuments);
  document.getElementById("clearQueryBtn").addEventListener("click", () => {
    elements.questionInput.value = "";
    elements.queryStatus.textContent = "";
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
initialize();
