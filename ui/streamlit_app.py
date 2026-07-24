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


st.title("AI Knowledge Base")
st.caption("Search your notes, PDFs, and uploaded documents in one place.")

with st.sidebar:
    st.subheader("Workspace")
    st.code(API_BASE_URL)
    if st.button("Check system status", use_container_width=True):
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
    st.subheader("Overview")
    if overview_error:
        st.error(f"Failed to load overview: {overview_error}")
    elif overview:
        st.write(
            f"Indexed **{overview['indexed_documents']} / {overview['total_documents']}** documents "
            f"with **{overview['total_chunks']}** chunks."
        )
        if not overview["openai_configured"]:
            st.warning("`OPENAI_API_KEY` is not configured.")
        if not overview["qdrant_reachable"]:
            st.warning("Qdrant is not reachable.")
with hero_right:
    if overview and not overview_error:
        st.metric("Documents", overview["total_documents"])
        st.metric("Indexed", overview["indexed_documents"])
        st.metric("Chunks", overview["total_chunks"])


if documents_error:
    st.error(f"Failed to load documents: {documents_error}")


tab_search, tab_ingest, tab_manage = st.tabs(["Ask", "Sync & Upload", "Manage"])

with tab_search:
    st.subheader("Ask the knowledge base")

    category_options = ["All"] + sorted({doc["category"] for doc in documents})
    source_options = ["All"] + sorted({doc["source_label"] for doc in documents})
    file_type_options = ["All"] + get_file_type_options(documents)

    with st.form("search_form"):
        question = st.text_area(
            "Question",
            placeholder="Example: Summarize my notes about RAG chunking strategies.",
            height=140,
        )
        filter_col1, filter_col2, filter_col3 = st.columns(3)
        with filter_col1:
            selected_category = st.selectbox("Category", category_options)
        with filter_col2:
            selected_source = st.selectbox("Source", source_options)
        with filter_col3:
            selected_file_type = st.selectbox("File type", file_type_options)
        top_k = st.select_slider("Recall size", options=TOP_K_OPTIONS, value=int(st.session_state["top_k"]))
        submitted = st.form_submit_button("Ask", type="primary", use_container_width=True)

    if submitted:
        if not question.strip():
            st.warning("Enter a question first.")
        else:
            st.session_state["top_k"] = int(top_k)
            payload = {
                "question": question.strip(),
                "top_k": int(top_k),
                "category_filter": None if selected_category == "All" else selected_category,
                "source_filter": None if selected_source == "All" else selected_source,
                "file_type_filter": None if selected_file_type == "All" else selected_file_type,
                "tag_filter": None,
            }
            try:
                with st.spinner("Searching and generating answer..."):
                    response = requests.post(f"{API_BASE_URL}/api/query", json=payload, timeout=60)
                    response.raise_for_status()
                    result = response.json()
                st.session_state["query_history"] = [question.strip(), *st.session_state["query_history"][:4]]
                st.subheader("Answer")
                st.write(result["answer"])

                debug = result.get("debug", {})
                metric_col1, metric_col2, metric_col3 = st.columns(3)
                metric_col1.metric("Candidates", debug.get("retrieved_candidates", 0))
                metric_col2.metric("Citations", debug.get("returned_citations", 0))
                active_filters = ", ".join(
                    value
                    for value in [
                        debug.get("category_filter"),
                        debug.get("source_filter"),
                        debug.get("file_type_filter"),
                    ]
                    if value
                )
                metric_col3.metric("Filters", active_filters or "None")

                st.subheader("Citations")
                for citation in result["citations"]:
                    with st.expander(f"{citation['title']} | {citation['chunk_id']} | score {citation['score']}"):
                        st.caption(citation["file_path"])
                        st.write(citation["excerpt"])
            except requests.RequestException as exc:
                st.error(f"Query failed: {exc}")

    if st.session_state["query_history"]:
        st.caption("Recent questions: " + " | ".join(st.session_state["query_history"]))

with tab_ingest:
    st.subheader("Sync and upload")

    sync_col, upload_col = st.columns(2)
    with sync_col:
        st.markdown("### Sync `data/raw/`")
        if st.button("Sync raw directory", type="primary", use_container_width=True):
            try:
                with st.spinner("Syncing raw directory..."):
                    response = requests.post(f"{API_BASE_URL}/api/documents/ingest/raw", timeout=120)
                    response.raise_for_status()
                    result = response.json()
                mark_documents_stale()
                st.success(f"Synced {result['ingested_count']} files.")
                if result["summaries"]:
                    st.dataframe(result["summaries"], use_container_width=True)
            except requests.RequestException as exc:
                st.error(f"Sync failed: {exc}")

    with upload_col:
        st.markdown("### Upload a file")
        with st.form("upload_form", clear_on_submit=True):
            uploaded_file = st.file_uploader("Select a document", type=["md", "markdown", "txt", "pdf"])
            source_label = st.text_input("Source label", value="upload")
            category = st.text_input("Category", value="general")
            upload_submitted = st.form_submit_button("Upload and index", use_container_width=True)

        if upload_submitted:
            if uploaded_file is None:
                st.warning("Choose a file first.")
            else:
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type or "application/octet-stream")}
                    data = {"source_label": source_label, "category": category}
                    response = requests.post(f"{API_BASE_URL}/api/documents/upload", files=files, data=data, timeout=120)
                    response.raise_for_status()
                    mark_documents_stale()
                    st.success("File indexed successfully.")
                    st.json(response.json())
                except requests.RequestException as exc:
                    st.error(f"Upload failed: {exc}")

with tab_manage:
    st.subheader("Manage documents")

    refresh_col, summary_col = st.columns([1, 3])
    with refresh_col:
        refresh_clicked = st.button("Refresh", use_container_width=True)
    with summary_col:
        st.caption("Refresh after sync, upload, or delete.")

    if refresh_clicked:
        try:
            documents = fetch_documents(force_refresh=True)
        except requests.RequestException as exc:
            st.error(f"Refresh failed: {exc}")
            documents = []

    if not documents:
        st.info("No documents available yet.")
    else:
        indexed_count = sum(1 for doc in documents if doc["indexed"])
        orphaned_count = sum(1 for doc in documents if doc["indexed"] and not doc["exists_on_disk"])
        stat_col1, stat_col2, stat_col3 = st.columns(3)
        stat_col1.metric("Documents", len(documents))
        stat_col2.metric("Indexed", indexed_count)
        stat_col3.metric("Orphaned indexes", orphaned_count)

        categories = Counter(doc["category"] for doc in documents)
        st.caption("Categories: " + " | ".join(f"{name}: {count}" for name, count in categories.most_common()))

        filter_col1, filter_col2, filter_col3 = st.columns(3)
        with filter_col1:
            selected_category = st.selectbox("Category filter", ["All"] + sorted(categories))
        with filter_col2:
            selected_storage = st.selectbox("Storage area", ["All"] + sorted({doc["storage_area"] for doc in documents}))
        with filter_col3:
            selected_index_status = st.selectbox("Index status", ["All", "Indexed only", "Unindexed only"])

        filtered_documents = []
        for doc in documents:
            if selected_category != "All" and doc["category"] != selected_category:
                continue
            if selected_storage != "All" and doc["storage_area"] != selected_storage:
                continue
            if selected_index_status == "Indexed only" and not doc["indexed"]:
                continue
            if selected_index_status == "Unindexed only" and doc["indexed"]:
                continue
            filtered_documents.append(doc)

        table_rows = [
            {
                "Filename": doc["filename"],
                "Category": doc["category"],
                "Source": doc["source_label"],
                "Area": doc["storage_area"],
                "Size": format_file_size(doc["size_bytes"]),
                "Chunks": doc["chunk_count"],
                "Indexed": "Yes" if doc["indexed"] else "No",
                "On disk": "Yes" if doc["exists_on_disk"] else "No",
                "Relative path": doc["relative_path"],
            }
            for doc in filtered_documents
        ]
        st.dataframe(table_rows, use_container_width=True, hide_index=True)

        doc_options = {
            f"{doc['filename']} | {doc['category']} | {doc['storage_area']} | indexed:{'yes' if doc['indexed'] else 'no'}": doc
            for doc in filtered_documents
            if doc["storage_area"] in {"raw", "upload"}
        }

        if doc_options:
            with st.form("delete_form"):
                selected_label = st.selectbox("Document to delete", list(doc_options.keys()))
                delete_file = st.checkbox("Delete source file", value=True)
                delete_index = st.checkbox("Delete vector index", value=True)
                delete_submitted = st.form_submit_button("Delete selected document", use_container_width=True)

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
                    st.success("Delete completed.")
                    st.json(response.json())
                except requests.RequestException as exc:
                    st.error(f"Delete failed: {exc}")
