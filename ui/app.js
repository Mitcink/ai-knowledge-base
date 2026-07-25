const apiBase = "";

const state = {
  documents: [],
  filters: null,
};

const el = {
  systemStatus: document.getElementById("systemStatus"),
  systemDetail: document.getElementById("systemDetail"),
  totalDocuments: document.getElementById("totalDocuments"),
  indexedDocuments: document.getElementById("indexedDocuments"),
  totalChunks: document.getElementById("totalChunks"),
  categoryFilter: document.getElementById("categoryFilter"),
  sourceFilter: document.getElementById("sourceFilter"),
  fileTypeFilter: document.getElementById("fileTypeFilter"),
  topK: document.getElementById("topK"),
  questionInput: document.getElementById("questionInput"),
  queryStatus: document.getElementById("queryStatus"),
  answerBox: document.getElementById("answerBox"),
  citationsBox: document.getElementById("citationsBox"),
  documentsTable: document.getElementById("documentsTable"),
  syncStatus: document.getElementById("syncStatus"),
  syncResult: document.getElementById("syncResult"),
};

async function request(path, options = {}) {
  const response = await fetch(`${apiBase}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  const contentType = response.headers.get("content-type") || "";
  const body = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const detail = typeof body === "object" ? JSON.stringify(body) : body;
    throw new Error(`status ${response.status}: ${detail}`);
  }
  return body;
}

function setTabs() {
  document.querySelectorAll(".tab").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach((node) => node.classList.remove("active"));
      document.querySelectorAll(".panel").forEach((node) => node.classList.remove("active"));
      button.classList.add("active");
      document.getElementById(`tab-${button.dataset.tab}`).classList.add("active");
    });
  });
}

function fillSelect(select, items) {
  select.innerHTML = "";
  const all = document.createElement("option");
  all.value = "";
  all.textContent = "全部";
  select.appendChild(all);
  items.forEach((item) => {
    const option = document.createElement("option");
    option.value = item;
    option.textContent = item;
    select.appendChild(option);
  });
}

function renderDocuments(documents) {
  if (!documents.length) {
    el.documentsTable.innerHTML = `<tr><td colspan="8" class="empty-row">当前还没有文档</td></tr>`;
    return;
  }

  el.documentsTable.innerHTML = documents
    .map(
      (doc) => `
        <tr>
          <td>${escapeHtml(doc.filename)}</td>
          <td>${escapeHtml(doc.status)}</td>
          <td>${escapeHtml(doc.category)}</td>
          <td>${escapeHtml(doc.source_label)}</td>
          <td>${escapeHtml(doc.file_type)}</td>
          <td>${escapeHtml(doc.storage_area)}</td>
          <td>${doc.chunk_count}</td>
          <td>${escapeHtml(doc.relative_path)}</td>
        </tr>
      `,
    )
    .join("");
}

function renderCitations(citations) {
  if (!citations.length) {
    el.citationsBox.className = "citations-box empty";
    el.citationsBox.textContent = "没有返回引用片段。";
    return;
  }

  el.citationsBox.className = "citations-box";
  el.citationsBox.innerHTML = citations
    .map(
      (citation) => `
        <article class="citation-item">
          <div class="citation-meta">
            <strong>${escapeHtml(citation.filename)}</strong>
            <span> | ${escapeHtml(citation.chunk_id)}</span>
            <span> | score ${citation.score}</span>
          </div>
          <div>${escapeHtml(citation.excerpt)}</div>
        </article>
      `,
    )
    .join("");
}

async function loadOverview() {
  const overview = await request("/api/documents/overview");
  el.systemStatus.textContent = overview.qdrant_reachable ? "就绪" : "降级";
  el.systemDetail.textContent = overview.qdrant_reachable
    ? `API 与向量库可用，当前 collection: ${overview.collection}`
    : "Qdrant 当前不可达，请检查向量库状态。";
  el.totalDocuments.textContent = overview.total_documents;
  el.indexedDocuments.textContent = overview.indexed_documents;
  el.totalChunks.textContent = overview.total_chunks;
}

async function loadFilters() {
  state.filters = await request("/api/documents/filters");
  fillSelect(el.categoryFilter, state.filters.categories);
  fillSelect(el.sourceFilter, state.filters.source_labels);
  fillSelect(el.fileTypeFilter, state.filters.file_types);
}

async function loadDocuments() {
  const data = await request("/api/documents");
  state.documents = data.documents;
  renderDocuments(state.documents);
}

async function bootstrap() {
  setTabs();

  document.getElementById("refreshAllBtn").addEventListener("click", initialize);
  document.getElementById("refreshDocsBtn").addEventListener("click", loadDocuments);
  document.getElementById("syncBtn").addEventListener("click", syncRawDirectory);
  document.getElementById("queryForm").addEventListener("submit", askQuestion);

  await initialize();
}

async function initialize() {
  try {
    await Promise.all([loadOverview(), loadFilters(), loadDocuments()]);
  } catch (error) {
    el.systemStatus.textContent = "错误";
    el.systemDetail.textContent = error.message;
  }
}

async function askQuestion(event) {
  event.preventDefault();
  const question = el.questionInput.value.trim();
  if (!question) {
    el.queryStatus.textContent = "请输入问题。";
    return;
  }

  el.queryStatus.textContent = "正在回答...";
  el.answerBox.className = "answer-box";
  el.answerBox.textContent = "";

  try {
    const result = await request("/api/query", {
      method: "POST",
      body: JSON.stringify({
        question,
        top_k: Number(el.topK.value),
        category_filter: el.categoryFilter.value || null,
        source_filter: el.sourceFilter.value || null,
        file_type_filter: el.fileTypeFilter.value || null,
        tag_filter: null,
      }),
    });
    el.queryStatus.textContent = "回答完成。";
    el.answerBox.className = "answer-box";
    el.answerBox.textContent = result.answer || "";
    renderCitations(result.citations || []);
  } catch (error) {
    el.queryStatus.textContent = "请求失败。";
    el.answerBox.className = "answer-box";
    el.answerBox.textContent = `请求失败：${error.message}`;
    renderCitations([]);
  }
}

async function syncRawDirectory() {
  el.syncStatus.textContent = "同步中...";
  el.syncResult.classList.add("hidden");
  try {
    const result = await request("/api/documents/ingest/raw", { method: "POST", headers: {} });
    el.syncStatus.textContent = `同步完成，处理了 ${result.ingested_count} 个文件。`;
    el.syncResult.textContent = JSON.stringify(result, null, 2);
    el.syncResult.classList.remove("hidden");
    await initialize();
  } catch (error) {
    el.syncStatus.textContent = `同步失败：${error.message}`;
  }
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

bootstrap();
