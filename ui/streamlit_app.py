import os
from collections import Counter

import requests
import streamlit as st


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
REQUEST_TIMEOUT = 30
TOP_K_OPTIONS = [3, 4, 5, 6, 8, 10, 12]
STATUS_LABELS = {
    "indexed": "已索引",
    "pending_index": "待索引",
    "orphaned_index": "孤立索引",
    "external_index": "外部索引",
}


st.set_page_config(page_title="AI Knowledge Base", page_icon=":books:", layout="wide")


if "documents_cache" not in st.session_state:
    st.session_state["documents_cache"] = []
if "documents_loaded" not in st.session_state:
    st.session_state["documents_loaded"] = False
if "top_k" not in st.session_state:
    st.session_state["top_k"] = 6
if "query_history" not in st.session_state:
    st.session_state["query_history"] = []


def fetch_documents(force_refresh: bool = False) -> list[dict]:
    if st.session_state["documents_loaded"] and not force_refresh:
        return st.session_state["documents_cache"]

    response = requests.get(f"{API_BASE_URL}/api/documents", timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    documents = response.json()["documents"]
    st.session_state["documents_cache"] = documents
    st.session_state["documents_loaded"] = True
    return documents


def fetch_overview() -> dict:
    response = requests.get(f"{API_BASE_URL}/api/documents/overview", timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.json()


def fetch_filter_options() -> dict:
    response = requests.get(f"{API_BASE_URL}/api/documents/filters", timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.json()


def format_file_size(size_bytes: int | None) -> str:
    if size_bytes is None:
        return "-"
    size = float(size_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size_bytes} B"


def format_datetime(value: str | None) -> str:
    if not value:
        return "-"
    return value.replace("T", " ")[:19]


def mark_documents_stale() -> None:
    st.session_state["documents_loaded"] = False


def summarize_readiness(overview: dict | None) -> tuple[str, str]:
    if not overview:
        return "不可用", "无法读取系统概览。"
    issues = []
    if not overview["openai_configured"]:
        issues.append("未配置 OpenAI API Key")
    if not overview["qdrant_reachable"]:
        issues.append("Qdrant 不可达")
    if issues:
        return "需处理", "；".join(issues)
    return "就绪", "API、模型配置和向量库均可用。"


def render_status_caption(doc: dict) -> str:
    return STATUS_LABELS.get(doc["status"], doc["status"])


st.title("AI Knowledge Base")
st.caption("面向个人长期维护的知识工作台：导入、检索、核对、清理都放在一个地方完成。")

overview = None
filter_options = None
documents: list[dict] = []
overview_error = None
documents_error = None
filters_error = None

try:
    overview = fetch_overview()
except requests.RequestException as exc:
    overview_error = exc

try:
    filter_options = fetch_filter_options()
except requests.RequestException as exc:
    filters_error = exc

try:
    documents = fetch_documents()
except requests.RequestException as exc:
    documents_error = exc

with st.sidebar:
    st.subheader("连接信息")
    st.code(API_BASE_URL)
    readiness_label, readiness_detail = summarize_readiness(overview)
    st.metric("系统状态", readiness_label)
    st.caption(readiness_detail)
    st.markdown("**工作建议**")
    st.write("1. 先同步或上传资料")
    st.write("2. 再用问答验证召回效果")
    st.write("3. 最后清理孤立索引与旧文件")
    if st.button("查看健康检查", use_container_width=True):
        try:
            health = requests.get(f"{API_BASE_URL}/health", timeout=10)
            health.raise_for_status()
            st.json(health.json())
        except requests.RequestException as exc:
            st.error(str(exc))

if overview_error:
    st.error(f"读取系统概览失败：{overview_error}")
if documents_error:
    st.error(f"读取文档列表失败：{documents_error}")
if filters_error:
    st.warning(f"读取过滤选项失败，将退回到本地推断：{filters_error}")

metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
if overview and not overview_error:
    metric_col1.metric("文档总数", overview["total_documents"])
    metric_col2.metric("已索引", overview["indexed_documents"])
    metric_col3.metric("待索引", overview["pending_documents"])
    metric_col4.metric("孤立索引", overview["orphaned_documents"] + overview["external_indexed_documents"])

hero_left, hero_right = st.columns([2, 1])
with hero_left:
    st.subheader("当前工作区")
    if overview and not overview_error:
        st.write(
            f"当前共管理 **{overview['total_documents']}** 份文档，已索引 **{overview['indexed_documents']}** 份，"
            f"累计片段 **{overview['total_chunks']}** 个。"
        )
        st.caption(
            "支持的文件类型："
            + " / ".join(overview.get("supported_file_types", []))
            + f" | Collection：`{overview['collection']}`"
        )
        if not overview["openai_configured"]:
            st.warning("尚未配置 `OPENAI_API_KEY`，检索可以继续，但问答生成不可用。")
        if not overview["qdrant_reachable"]:
            st.warning("Qdrant 当前不可达，导入和检索能力会受影响。")
with hero_right:
    if overview and not overview_error:
        st.metric("外部索引", overview["external_indexed_documents"])
        st.metric("存储区域", len(overview["storage_areas"]))
        st.metric("分类数", len(overview["categories"]))


tab_search, tab_ingest, tab_manage = st.tabs(["问答工作台", "导入与同步", "文档总览"])

with tab_search:
    st.subheader("知识库问答")
    st.caption("通过分类、来源和文件类型缩小范围，用引用片段核对回答质量。")

    categories = ["全部"] + (
        filter_options["categories"] if filter_options else sorted({doc["category"] for doc in documents})
    )
    sources = ["全部"] + (
        filter_options["source_labels"] if filter_options else sorted({doc["source_label"] for doc in documents})
    )
    file_types = ["全部"] + (
        filter_options["file_types"] if filter_options else sorted({doc["file_type"] for doc in documents})
    )

    with st.form("search_form"):
        question = st.text_area(
            "你的问题",
            placeholder="例如：总结我关于 RAG 分块策略和文档治理的笔记。",
            height=140,
        )
        filter_col1, filter_col2, filter_col3 = st.columns(3)
        with filter_col1:
            selected_category = st.selectbox("分类过滤", categories)
        with filter_col2:
            selected_source = st.selectbox("来源过滤", sources)
        with filter_col3:
            selected_file_type = st.selectbox("文件类型过滤", file_types)
        top_k = st.select_slider("引用数量上限", options=TOP_K_OPTIONS, value=int(st.session_state["top_k"]))
        submitted = st.form_submit_button("开始问答", type="primary", use_container_width=True)

    if submitted:
        payload = {
            "question": question.strip(),
            "top_k": int(top_k),
            "category_filter": None if selected_category == "全部" else selected_category,
            "source_filter": None if selected_source == "全部" else selected_source,
            "file_type_filter": None if selected_file_type == "全部" else selected_file_type,
            "tag_filter": None,
        }

        try:
            with st.spinner("正在检索并生成回答..."):
                response = requests.post(f"{API_BASE_URL}/api/query", json=payload, timeout=60)
                response.raise_for_status()
                result = response.json()

            st.session_state["top_k"] = int(top_k)
            st.session_state["query_history"] = [question.strip(), *st.session_state["query_history"][:4]]

            st.markdown("### 回答")
            st.write(result.get("answer", "没有返回回答内容。"))

            debug = result.get("debug", {}) if isinstance(result.get("debug", {}), dict) else {}
            metric_col1, metric_col2, metric_col3 = st.columns(3)
            metric_col1.metric("召回候选", debug.get("retrieved_candidates", 0))
            metric_col2.metric("返回引用", debug.get("returned_citations", 0))
            active_filters = ", ".join(
                str(value)
                for value in [
                    debug.get("category_filter"),
                    debug.get("source_filter"),
                    debug.get("file_type_filter"),
                ]
                if value
            )
            metric_col3.metric("当前过滤", active_filters or "无")

            citations = result.get("citations", [])
            if citations:
                st.markdown("### 引用片段")
                for citation in citations:
                    label = (
                        f"{citation.get('filename', citation.get('title', '未知标题'))}"
                        f" | {citation.get('chunk_id', '-')}"
                        f" | 分数 {citation.get('score', '-')}"
                    )
                    with st.expander(label):
                        st.caption(citation.get("file_path", ""))
                        st.write(citation.get("excerpt", ""))
            else:
                st.info("本次没有返回可引用片段。")
        except requests.HTTPError as exc:
            detail = exc.response.text if exc.response is not None else str(exc)
            st.error(f"问答请求失败：{detail}")
        except requests.RequestException as exc:
            st.error(f"问答请求失败：{exc}")
        except Exception as exc:
            st.error(f"问答执行异常：{exc}")
            st.code(repr(payload), language="python")
            st.exception(exc)

    if st.session_state["query_history"]:
        st.caption("最近问题：" + " | ".join(st.session_state["query_history"]))

with tab_ingest:
    st.subheader("导入与同步")
    st.caption("推荐先用 `data/raw/` 维护长期资料，再通过上传补充临时或零散文件。")

    sync_col, upload_col = st.columns(2)
    with sync_col:
        st.markdown("### 批量同步 `data/raw/`")
        st.write("适合导入长期沉淀资料。重复执行会按文件路径覆盖旧索引。")
        if st.button("同步原始目录", type="primary", use_container_width=True):
            try:
                with st.spinner("正在同步原始目录..."):
                    response = requests.post(f"{API_BASE_URL}/api/documents/ingest/raw", timeout=180)
                    response.raise_for_status()
                    result = response.json()
                mark_documents_stale()
                st.success(f"本次处理了 {result['ingested_count']} 个文件。")
                if result["summaries"]:
                    st.dataframe(result["summaries"], use_container_width=True, hide_index=True)
            except requests.RequestException as exc:
                st.error(f"同步失败：{exc}")

    with upload_col:
        st.markdown("### 上传单个文件")
        st.write("适合快速补充单篇文档。支持 `md / markdown / txt / pdf`。")
        with st.form("upload_form", clear_on_submit=True):
            uploaded_file = st.file_uploader("选择文档", type=["md", "markdown", "txt", "pdf"])
            source_label = st.text_input("来源标签", value="upload")
            category = st.text_input("文档分类", value="general")
            upload_submitted = st.form_submit_button("上传并索引", use_container_width=True)

        if upload_submitted:
            if uploaded_file is None:
                st.warning("请先选择文件。")
            else:
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type or "application/octet-stream")}
                    data = {"source_label": source_label, "category": category}
                    response = requests.post(f"{API_BASE_URL}/api/documents/upload", files=files, data=data, timeout=180)
                    response.raise_for_status()
                    mark_documents_stale()
                    st.success("文档已完成上传并写入索引。")
                    st.json(response.json())
                except requests.RequestException as exc:
                    st.error(f"上传失败：{exc}")

with tab_manage:
    st.subheader("文档总览")
    st.caption("把磁盘文件、索引状态和删除操作放在同一视图里管理。")

    refresh_col, summary_col = st.columns([1, 3])
    with refresh_col:
        refresh_clicked = st.button("刷新列表", use_container_width=True)
    with summary_col:
        st.caption("同步、上传或删除后建议刷新，避免看到过期缓存。")

    if refresh_clicked:
        try:
            documents = fetch_documents(force_refresh=True)
            filter_options = fetch_filter_options()
        except requests.RequestException as exc:
            st.error(f"刷新失败：{exc}")
            documents = []

    if not documents:
        st.info("当前还没有文档。先去“导入与同步”页建立你的第一批资料。")
    else:
        categories = Counter(doc["category"] for doc in documents)
        status_options = ["全部"] + [STATUS_LABELS.get(status, status) for status in (filter_options or {}).get("statuses", [])]
        status_reverse = {STATUS_LABELS.get(key, key): key for key in (filter_options or {}).get("statuses", [])}

        search_term = st.text_input("按文件名搜索", placeholder="例如：rag、产品、架构")
        filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)
        with filter_col1:
            selected_category = st.selectbox("分类", ["全部"] + sorted(categories))
        with filter_col2:
            selected_storage = st.selectbox("存储区域", ["全部"] + sorted({doc["storage_area"] for doc in documents}))
        with filter_col3:
            selected_status = st.selectbox("状态", status_options)
        with filter_col4:
            selected_source = st.selectbox("来源", ["全部"] + sorted({doc["source_label"] for doc in documents}))

        filtered_documents = []
        for doc in documents:
            if search_term.strip() and search_term.strip().lower() not in doc["filename"].lower():
                continue
            if selected_category != "全部" and doc["category"] != selected_category:
                continue
            if selected_storage != "全部" and doc["storage_area"] != selected_storage:
                continue
            if selected_source != "全部" and doc["source_label"] != selected_source:
                continue
            if selected_status != "全部" and doc["status"] != status_reverse[selected_status]:
                continue
            filtered_documents.append(doc)

        stat_col1, stat_col2, stat_col3 = st.columns(3)
        stat_col1.metric("当前列表", len(filtered_documents))
        stat_col2.metric("已索引", sum(1 for doc in filtered_documents if doc["indexed"]))
        stat_col3.metric("孤立索引", sum(1 for doc in filtered_documents if doc["status"] in {"orphaned_index", "external_index"}))

        st.caption("分类分布：" + " | ".join(f"{name}: {count}" for name, count in categories.most_common()))

        table_rows = [
            {
                "文件名": doc["filename"],
                "状态": render_status_caption(doc),
                "分类": doc["category"],
                "来源": doc["source_label"],
                "文件类型": doc["file_type"],
                "区域": doc["storage_area"],
                "大小": format_file_size(doc["size_bytes"]),
                "片段数": doc["chunk_count"],
                "更新时间": format_datetime(doc["updated_at"]),
                "相对路径": doc["relative_path"],
            }
            for doc in filtered_documents
        ]
        st.dataframe(table_rows, use_container_width=True, hide_index=True)

        doc_options = {
            (
                f"{doc['filename']} | {render_status_caption(doc)} | "
                f"{doc['storage_area']} | {doc['category']}"
            ): doc
            for doc in filtered_documents
            if doc["storage_area"] in {"raw", "upload"}
        }

        if doc_options:
            st.markdown("### 删除文档或索引")
            st.warning("删除文件和删除向量索引是两件独立操作，请确认勾选项。")
            with st.form("delete_form"):
                selected_label = st.selectbox("选择要删除的文档", list(doc_options.keys()))
                delete_file = st.checkbox("删除原文件", value=True)
                delete_index = st.checkbox("删除向量索引", value=True)
                delete_submitted = st.form_submit_button("执行删除", use_container_width=True)

            if delete_submitted:
                try:
                    chosen = doc_options[selected_label]
                    payload = {
                        "storage_area": chosen["storage_area"],
                        "relative_path": chosen["relative_path"],
                        "delete_file": delete_file,
                        "delete_index": delete_index,
                    }
                    response = requests.post(f"{API_BASE_URL}/api/documents/delete", json=payload, timeout=60)
                    response.raise_for_status()
                    mark_documents_stale()
                    st.success("删除完成。")
                    st.json(response.json())
                except requests.RequestException as exc:
                    st.error(f"删除失败：{exc}")
