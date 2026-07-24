import os

import requests
import streamlit as st


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
REQUEST_TIMEOUT = 30


st.set_page_config(page_title="AI知识库", page_icon=":books:", layout="wide")

st.title("AI知识库")
st.caption("上传、整理并问答你的个人资料库。")


if "documents_cache" not in st.session_state:
    st.session_state["documents_cache"] = []
if "documents_loaded" not in st.session_state:
    st.session_state["documents_loaded"] = False


def fetch_documents(force_refresh: bool = False) -> list[dict]:
    if st.session_state["documents_loaded"] and not force_refresh:
        return st.session_state["documents_cache"]

    response = requests.get(f"{API_BASE_URL}/api/documents", timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    documents = response.json()["documents"]
    st.session_state["documents_cache"] = documents
    st.session_state["documents_loaded"] = True
    return documents


with st.sidebar:
    st.subheader("服务状态")
    st.code(API_BASE_URL)
    if st.button("检查健康状态"):
        try:
            health = requests.get(f"{API_BASE_URL}/health", timeout=10)
            health.raise_for_status()
            st.json(health.json())
        except requests.RequestException as exc:
            st.error(str(exc))


tab_search, tab_ingest, tab_manage = st.tabs(["智能问答", "上传资料", "文档管理"])

with tab_search:
    st.subheader("基于知识库提问")
    with st.form("search_form"):
        question = st.text_area(
            "你的问题",
            placeholder="例如：我之前记录过哪些关于 RAG 分块策略的要点？",
            height=120,
        )
        top_k = st.number_input("召回数量", min_value=3, max_value=10, value=6, step=1)
        tag_filter = st.text_input("标签过滤", placeholder="例如：pdf、工作、rag")
        submitted = st.form_submit_button("开始问答", type="primary")

    if submitted:
        payload = {
            "question": question,
            "top_k": int(top_k),
            "tag_filter": tag_filter or None,
        }
        try:
            response = requests.post(f"{API_BASE_URL}/api/query", json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            st.subheader("回答")
            st.write(result["answer"])
            st.subheader("引用片段")
            for citation in result["citations"]:
                st.markdown(f"**{citation['title']}** | `{citation['chunk_id']}` | 分数 `{citation['score']}`")
                st.caption(citation["file_path"])
                st.write(citation["excerpt"])
        except requests.RequestException as exc:
            st.error(f"问答失败：{exc}")

with tab_ingest:
    st.subheader("上传并入库")
    st.write("上传文件后会立即写入知识库，同时保留分类和来源标签。")
    with st.form("upload_form", clear_on_submit=True):
        uploaded_file = st.file_uploader("选择文档", type=["md", "markdown", "txt", "pdf"])
        source_label = st.text_input("来源标签", value="upload", help="例如：upload、obsidian、notion、manual")
        category = st.text_input("文档分类", value="general", help="例如：工作、学习、rag、项目")
        upload_submitted = st.form_submit_button("上传并索引")

    if upload_submitted:
        if uploaded_file is None:
            st.warning("请先选择一个文件。")
        else:
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type or "application/octet-stream")}
                data = {"source_label": source_label, "category": category}
                response = requests.post(f"{API_BASE_URL}/api/documents/upload", files=files, data=data, timeout=120)
                response.raise_for_status()
                st.session_state["documents_loaded"] = False
                st.success("文档已经成功入库。")
                st.json(response.json())
            except requests.RequestException as exc:
                st.error(f"上传失败：{exc}")

with tab_manage:
    st.subheader("文档管理")
    st.write("查看当前资料、分类、索引状态，并删除不需要的文档。")

    refresh_col, info_col = st.columns([1, 3])
    with refresh_col:
        refresh_clicked = st.button("刷新文档列表")
    with info_col:
        st.caption("上传或删除文档后，点击刷新可同步最新状态。")

    try:
        documents = fetch_documents(force_refresh=refresh_clicked)
    except requests.RequestException as exc:
        documents = []
        st.error(f"获取文档列表失败：{exc}")

    if not documents:
        st.info("当前还没有可管理的文档。")
    else:
        st.metric("当前文档数", len(documents))
        category_options = ["全部"] + sorted({doc["category"] for doc in documents})
        storage_options = ["全部"] + sorted({doc["storage_area"] for doc in documents})
        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            selected_category = st.selectbox("按分类筛选", category_options)
        with filter_col2:
            selected_storage = st.selectbox("按存储区域筛选", storage_options)

        filtered_documents = [
            doc
            for doc in documents
            if (selected_category == "全部" or doc["category"] == selected_category)
            and (selected_storage == "全部" or doc["storage_area"] == selected_storage)
        ]

        if not filtered_documents:
            st.info("当前筛选条件下没有文档。")
        else:
            st.dataframe(filtered_documents, use_container_width=True)
            doc_options = {
                f"{doc['filename']} | {doc['category']} | {doc['storage_area']} | 已索引:{'是' if doc['indexed'] else '否'}": doc
                for doc in filtered_documents
            }

            with st.form("delete_form"):
                selected_label = st.selectbox("选择要删除的文档", list(doc_options.keys()))
                delete_file = st.checkbox("删除原文件", value=True)
                delete_index = st.checkbox("删除向量索引", value=True)
                delete_submitted = st.form_submit_button("删除选中文档")

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
                    st.session_state["documents_loaded"] = False
                    st.success("删除完成，请点击刷新文档列表确认最新状态。")
                    st.json(response.json())
                except requests.RequestException as exc:
                    st.error(f"删除失败：{exc}")
