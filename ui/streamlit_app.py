import os
from collections import Counter

import requests
import streamlit as st


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
REQUEST_TIMEOUT = 30
TOP_K_OPTIONS = [3, 4, 5, 6, 8, 10]


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


def format_file_size(size_bytes: int | None) -> str:
    if size_bytes is None:
        return "-"
    size = float(size_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size_bytes} B"


def mark_documents_stale() -> None:
    st.session_state["documents_loaded"] = False


def get_file_type_options(documents: list[dict]) -> list[str]:
    file_types = set()
    for doc in documents:
        parts = doc["filename"].rsplit(".", 1)
        if len(parts) == 2 and parts[1]:
            file_types.add(parts[1].lower())
    return sorted(file_types)


st.title("AI 知识库")
st.caption("在一个地方搜索你的笔记、PDF 和上传资料。")

with st.sidebar:
    st.subheader("工作台")
    st.code(API_BASE_URL)
    if st.button("检查系统状态", use_container_width=True):
        try:
            health = requests.get(f"{API_BASE_URL}/health", timeout=10)
            health.raise_for_status()
            st.json(health.json())
        except requests.RequestException as exc:
            st.error(str(exc))


overview = None
documents: list[dict] = []
overview_error = None
documents_error = None

try:
    overview = fetch_overview()
except requests.RequestException as exc:
    overview_error = exc

try:
    documents = fetch_documents()
except requests.RequestException as exc:
    documents_error = exc


hero_left, hero_right = st.columns([2, 1])
with hero_left:
    st.subheader("系统概览")
    if overview_error:
        st.error(f"读取系统概览失败：{overview_error}")
    elif overview:
        st.write(
            f"当前已索引 **{overview['indexed_documents']} / {overview['total_documents']}** 份文档，"
            f"共 **{overview['total_chunks']}** 个片段。"
        )
        if not overview["openai_configured"]:
            st.warning("尚未配置 `OPENAI_API_KEY`。")
        if not overview["qdrant_reachable"]:
            st.warning("Qdrant 当前不可达。")
with hero_right:
    if overview and not overview_error:
        st.metric("文档数", overview["total_documents"])
        st.metric("已索引", overview["indexed_documents"])
        st.metric("片段数", overview["total_chunks"])


if documents_error:
    st.error(f"读取文档列表失败：{documents_error}")


tab_search, tab_ingest, tab_manage = st.tabs(["智能问答", "同步与上传", "文档管理"])

with tab_search:
    st.subheader("基于知识库提问")
    st.caption("说明：当前可稳定过滤的维度是分类、来源和文件类型。之前的自由标签过滤设计不准确，已经移除。")

    category_options = ["全部"] + sorted({doc["category"] for doc in documents})
    source_options = ["全部"] + sorted({doc["source_label"] for doc in documents})
    file_type_options = ["全部"] + get_file_type_options(documents)

    with st.form("search_form"):
        question = st.text_area(
            "你的问题",
            placeholder="例如：总结我关于 RAG 分块策略的笔记。",
            height=140,
        )
        filter_col1, filter_col2, filter_col3 = st.columns(3)
        with filter_col1:
            selected_category = st.selectbox("分类过滤", category_options)
        with filter_col2:
            selected_source = st.selectbox("来源过滤", source_options)
        with filter_col3:
            selected_file_type = st.selectbox("文件类型过滤", file_type_options)
        top_k = st.select_slider("召回数量", options=TOP_K_OPTIONS, value=int(st.session_state["top_k"]))
        submitted = st.form_submit_button("开始问答", type="primary", use_container_width=True)

    if submitted:
        if not question.strip():
            st.warning("请先输入问题。")
        else:
            st.session_state["top_k"] = int(top_k)
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

                if not isinstance(result, dict):
                    raise ValueError(f"API 返回了非预期结果：{type(result)}")

                st.session_state["query_history"] = [question.strip(), *st.session_state["query_history"][:4]]
                st.subheader("回答")
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

                st.subheader("引用片段")
                for citation in result.get("citations", []):
                    with st.expander(f"{citation.get('title', '未知标题')} | {citation.get('chunk_id', '-')} | 分数 {citation.get('score', '-') }"):
                        st.caption(citation["file_path"])
                        st.write(citation["excerpt"])
            except requests.RequestException as exc:
                st.error(f"问答请求失败：{exc}")
            except Exception as exc:
                st.error(f"问答执行异常：{exc}")
                st.code(repr(payload), language="python")
                st.exception(exc)

    if st.session_state["query_history"]:
        st.caption("最近问题：" + " | ".join(st.session_state["query_history"]))

with tab_ingest:
    st.subheader("同步与上传")

    sync_col, upload_col = st.columns(2)
    with sync_col:
        st.markdown("### 同步 `data/raw/`")
        if st.button("同步原始目录", type="primary", use_container_width=True):
            try:
                with st.spinner("正在同步原始目录..."):
                    response = requests.post(f"{API_BASE_URL}/api/documents/ingest/raw", timeout=120)
                    response.raise_for_status()
                    result = response.json()
                mark_documents_stale()
                st.success(f"本次已同步 {result['ingested_count']} 个文件。")
                if result["summaries"]:
                    st.dataframe(result["summaries"], use_container_width=True)
            except requests.RequestException as exc:
                st.error(f"同步失败：{exc}")

    with upload_col:
        st.markdown("### 上传单个文件")
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
                    response = requests.post(f"{API_BASE_URL}/api/documents/upload", files=files, data=data, timeout=120)
                    response.raise_for_status()
                    mark_documents_stale()
                    st.success("文档入库成功。")
                    st.json(response.json())
                except requests.RequestException as exc:
                    st.error(f"上传失败：{exc}")

with tab_manage:
    st.subheader("文档管理")

    refresh_col, summary_col = st.columns([1, 3])
    with refresh_col:
        refresh_clicked = st.button("刷新", use_container_width=True)
    with summary_col:
        st.caption("同步、上传或删除后可以刷新列表。")

    if refresh_clicked:
        try:
            documents = fetch_documents(force_refresh=True)
        except requests.RequestException as exc:
            st.error(f"刷新失败：{exc}")
            documents = []

    if not documents:
        st.info("当前还没有文档。")
    else:
        indexed_count = sum(1 for doc in documents if doc["indexed"])
        orphaned_count = sum(1 for doc in documents if doc["indexed"] and not doc["exists_on_disk"])
        stat_col1, stat_col2, stat_col3 = st.columns(3)
        stat_col1.metric("文档数", len(documents))
        stat_col2.metric("已索引", indexed_count)
        stat_col3.metric("孤立索引", orphaned_count)

        categories = Counter(doc["category"] for doc in documents)
        st.caption("分类分布：" + " | ".join(f"{name}: {count}" for name, count in categories.most_common()))

        filter_col1, filter_col2, filter_col3 = st.columns(3)
        with filter_col1:
            selected_category = st.selectbox("分类过滤", ["全部"] + sorted(categories))
        with filter_col2:
            selected_storage = st.selectbox("存储区域", ["全部"] + sorted({doc["storage_area"] for doc in documents}))
        with filter_col3:
            selected_index_status = st.selectbox("索引状态", ["全部", "仅已索引", "仅未索引"])

        filtered_documents = []
        for doc in documents:
            if selected_category != "全部" and doc["category"] != selected_category:
                continue
            if selected_storage != "全部" and doc["storage_area"] != selected_storage:
                continue
            if selected_index_status == "仅已索引" and not doc["indexed"]:
                continue
            if selected_index_status == "仅未索引" and doc["indexed"]:
                continue
            filtered_documents.append(doc)

        table_rows = [
            {
                "文件名": doc["filename"],
                "分类": doc["category"],
                "来源": doc["source_label"],
                "区域": doc["storage_area"],
                "大小": format_file_size(doc["size_bytes"]),
                "片段数": doc["chunk_count"],
                "已索引": "是" if doc["indexed"] else "否",
                "磁盘存在": "是" if doc["exists_on_disk"] else "否",
                "相对路径": doc["relative_path"],
            }
            for doc in filtered_documents
        ]
        st.dataframe(table_rows, use_container_width=True, hide_index=True)

        doc_options = {
            f"{doc['filename']} | {doc['category']} | {doc['storage_area']} | 已索引:{'是' if doc['indexed'] else '否'}": doc
            for doc in filtered_documents
            if doc["storage_area"] in {"raw", "upload"}
        }

        if doc_options:
            with st.form("delete_form"):
                selected_label = st.selectbox("选择要删除的文档", list(doc_options.keys()))
                delete_file = st.checkbox("删除原文件", value=True)
                delete_index = st.checkbox("删除向量索引", value=True)
                delete_submitted = st.form_submit_button("删除选中文档", use_container_width=True)

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
