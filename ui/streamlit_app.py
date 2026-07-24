import os

import requests
import streamlit as st


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


st.set_page_config(page_title="AI Knowledge Base", page_icon="📚", layout="wide")

st.title("AI Knowledge Base")
st.caption("Search your own notes and ask grounded questions with citations.")

with st.sidebar:
    st.subheader("API")
    st.code(API_BASE_URL)
    health_clicked = st.button("Check Health")
    if health_clicked:
        try:
            health = requests.get(f"{API_BASE_URL}/health", timeout=10)
            st.json(health.json())
        except requests.RequestException as exc:
            st.error(str(exc))

tab_search, tab_ingest = st.tabs(["Ask", "Ingest"])

with tab_search:
    question = st.text_area("Question", placeholder="例如：我之前关于 RAG 分块策略记录了什么？", height=120)
    top_k = st.slider("Top K", min_value=3, max_value=10, value=6)
    tag_filter = st.text_input("Tag filter", placeholder="例如：pdf 或 raw")
    if st.button("Ask Knowledge Base", type="primary"):
        payload = {
            "question": question,
            "top_k": top_k,
            "tag_filter": tag_filter or None,
        }
        try:
            response = requests.post(f"{API_BASE_URL}/api/query", json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            st.subheader("Answer")
            st.write(result["answer"])
            st.subheader("Citations")
            for citation in result["citations"]:
                st.markdown(
                    f"**{citation['title']}** | `{citation['chunk_id']}` | score `{citation['score']}`"
                )
                st.caption(citation["file_path"])
                st.write(citation["excerpt"])
        except requests.RequestException as exc:
            st.error(str(exc))

with tab_ingest:
    uploaded_file = st.file_uploader("Upload a document", type=["md", "markdown", "txt", "pdf"])
    if st.button("Upload and Ingest"):
        if uploaded_file is None:
            st.warning("Please choose a file first.")
        else:
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type or "application/octet-stream")}
                response = requests.post(f"{API_BASE_URL}/api/documents/upload", files=files, timeout=120)
                response.raise_for_status()
                st.success("Document ingested.")
                st.json(response.json())
            except requests.RequestException as exc:
                st.error(str(exc))

