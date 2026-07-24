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


st.title("AI Knowledge Base")
st.caption("把分散的笔记、文档和 PDF 收进一个可搜索、可追溯、可持续维护的知识库。")


with st.sidebar:
    st.subheader("工作台信息")
    st.code(API_BASE_URL)
    st.caption("推荐流程：先同步原始目录，再上传临时资料，最后用问答验证召回效果。")
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
    st.subheader("系统总览")
    if overview_error:
        st.error(f"系统概览读取失败：{overview_error}")
    elif overview:
        status_text = "运行正常" if overview["status"] == "ok" else "需要检查"
        st.write(
            f"当前状态：**{status_text}**，已收录 **{overview['indexed_documents']} / {overview['total_documents']}** 份文档，"
            f"共 **{overview['total_chunks']}** 个索引片段。"
        )
        if not overview["openai_configured"]:
            st.warning("尚未配置 `OPENAI_API_KEY`，问答和向量化会失败。")
        if not overview["qdrant_reachable"]:
            st.warning("Qdrant 当前不可达，请先检查容器或连接地址。")
with hero_right:
    if overview and not overview_error:
        st.metric("文档总数", overview["total_documents"])
        st.metric("已索引", overview["indexed_documents"])
        st.metric("索引片段", overview["total_chunks"])


if documents_error:
    st.error(f"文档列表加载失败：{documents_error}")


tab_search, tab_ingest, tab_manage = st.tabs(["智能问答", "同步与上传", "文档管理"])

with tab_search:
    st.subheader("基于知识库提问")
    st.caption("建议问题尽量具体，最好带上主题、时间范围或资料类型。")

    quick_questions = [
        "我记录过哪些关于 RAG 分块策略的要点？",
        "把最近和部署相关的知识点整理成执行步骤。",
        "这个知识库里有哪些和 API 设计有关的材料？",
    ]
    selected_quick_question = st.segmented_control("快捷问题", options=quick_questions, selection_mode="single")

    with st.form("search_form"):
        question = st.text_area(
            "你的问题",
            value=selected_quick_question or "",
            placeholder="例如：请总结我记录过的 RAG 分块策略，并说明各自适用场景。",
            height=140,
        )
        form_col1, form_col2 = st.columns(2)
        with form_col1:
            top_k = st.select_slider("召回数量", options=TOP_K_OPTIONS, value=int(st.session_state["top_k"]))
        with form_col2:
            category_options = ["不限"] + sorted({doc["category"] for doc in documents})
            selected_category = st.selectbox("按分类过滤", category_options)
        tag_filter = st.text_input("附加标签过滤", placeholder="例如：rag、project、pdf")
        submitted = st.form_submit_button("开始问答", type="primary", use_container_width=True)

    if submitted:
        if not question.strip():
            st.warning("先输入一个问题，我们再开始检索。")
        else:
            st.session_state["top_k"] = int(top_k)
            payload = {
                "question": question.strip(),
                "top_k": int(top_k),
                "tag_filter": None if selected_category == "不限" else selected_category,
            }
            if tag_filter.strip():
                payload["tag_filter"] = tag_filter.strip()

            try:
                with st.spinner("正在召回片段并生成回答..."):
                    response = requests.post(f"{API_BASE_URL}/api/query", json=payload, timeout=60)
                    response.raise_for_status()
                    result = response.json()

                st.session_state["query_history"] = [question.strip(), *st.session_state["query_history"][:4]]
                st.success("问答完成。")
                st.subheader("回答")
                st.write(result["answer"])

                debug = result.get("debug", {})
                metric_col1, metric_col2, metric_col3 = st.columns(3)
                metric_col1.metric("召回候选", debug.get("retrieved_candidates", 0))
                metric_col2.metric("返回引用", debug.get("returned_citations", 0))
                metric_col3.metric("过滤标签", debug.get("tag_filter") or "无")

                st.subheader("引用片段")
                for citation in result["citations"]:
                    with st.expander(f"{citation['title']} | {citation['chunk_id']} | 分数 {citation['score']}"):
                        st.caption(citation["file_path"])
                        st.write(citation["excerpt"])
            except requests.RequestException as exc:
                st.error(f"问答失败：{exc}")

    if st.session_state["query_history"]:
        st.caption("最近问题：" + " | ".join(st.session_state["query_history"]))

with tab_ingest:
    st.subheader("同步与上传")
    st.write("这里负责把资料真正变成可检索知识。原始目录适合批量同步，上传入口适合零散补充。")

    sync_col, upload_col = st.columns(2)
    with sync_col:
        st.markdown("### 同步 `data/raw/`")
        st.caption("适合 Obsidian 导出、手工整理的长期资料。重复同步会自动覆盖旧索引，避免重复片段。")
        if st.button("一键同步原始目录", type="primary", use_container_width=True):
            try:
                with st.spinner("正在同步原始目录..."):
                    response = requests.post(f"{API_BASE_URL}/api/documents/ingest/raw", timeout=120)
                    response.raise_for_status()
                    result = response.json()
                mark_documents_stale()
                st.success(f"同步完成，本次处理 {result['ingested_count']} 个文件。")
                if result["summaries"]:
                    st.dataframe(result["summaries"], use_container_width=True)
            except requests.RequestException as exc:
                st.error(f"目录同步失败：{exc}")

    with upload_col:
        st.markdown("### 上传单个文件")
        with st.form("upload_form", clear_on_submit=True):
            uploaded_file = st.file_uploader("选择文档", type=["md", "markdown", "txt", "pdf"])
            source_label = st.text_input("来源标签", value="upload", help="例如：upload、obsidian、notion、manual")
            category = st.text_input("文档分类", value="general", help="例如：工作、学习、rag、项目")
            upload_submitted = st.form_submit_button("上传并索引", use_container_width=True)

        if upload_submitted:
            if uploaded_file is None:
                st.warning("请先选择一个文件。")
            else:
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type or "application/octet-stream")}
                    data = {"source_label": source_label, "category": category}
                    response = requests.post(f"{API_BASE_URL}/api/documents/upload", files=files, data=data, timeout=120)
                    response.raise_for_status()
                    mark_documents_stale()
                    st.success("文档已经成功入库。")
                    st.json(response.json())
                except requests.RequestException as exc:
                    st.error(f"上传失败：{exc}")

with tab_manage:
    st.subheader("文档管理")
    st.write("这里可以看索引覆盖情况、分类分布和待清理文档。")

    refresh_col, summary_col = st.columns([1, 3])
    with refresh_col:
        refresh_clicked = st.button("刷新列表", use_container_width=True)
    with summary_col:
        st.caption("上传、同步或删除后点一次刷新，就能看到最新状态。")

    if refresh_clicked:
        try:
            documents = fetch_documents(force_refresh=True)
        except requests.RequestException as exc:
            st.error(f"刷新失败：{exc}")
            documents = []

    if not documents:
        st.info("当前还没有可管理的文档。")
    else:
        indexed_count = sum(1 for doc in documents if doc["indexed"])
        orphaned_count = sum(1 for doc in documents if doc["indexed"] and not doc["exists_on_disk"])
        stat_col1, stat_col2, stat_col3 = st.columns(3)
        stat_col1.metric("文档总数", len(documents))
        stat_col2.metric("已索引文档", indexed_count)
        stat_col3.metric("孤立索引", orphaned_count)

        categories = Counter(doc["category"] for doc in documents)
        st.caption("分类分布：" + " | ".join(f"{name}: {count}" for name, count in categories.most_common()))

        filter_col1, filter_col2, filter_col3 = st.columns(3)
        with filter_col1:
            selected_category = st.selectbox("分类", ["全部"] + sorted(categories))
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
            f"{doc['filename']} | {doc['category']} | {doc['storage_area']} | 索引:{'是' if doc['indexed'] else '否'}": doc
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
                    st.success("删除完成，点击刷新列表可确认最新状态。")
                    st.json(response.json())
                except requests.RequestException as exc:
                    st.error(f"删除失败：{exc}")
