import streamlit as st
import os
from io import BytesIO
from langchain.schema.document import Document
from populate_database import load_documents, split_documents, add_to_chroma
from query_data import query_rag, CHROMA_PATH
from get_embedding_function import get_embedding_function

# Ensure required directories exist
DATA_PATH = "data"
os.makedirs(DATA_PATH, exist_ok=True)


def save_uploaded_file(uploaded_file):
    file_path = os.path.join(DATA_PATH, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path


st.title("📄 PDF Knowledge Base with RAG (Streamlit + LangChain)")

# --- File Upload Section ---
uploaded_file = st.file_uploader("Upload a PDF or Text File", type=["pdf", "txt"])
if uploaded_file is not None:
    file_path = save_uploaded_file(uploaded_file)
    st.success(f"Uploaded and saved file: {uploaded_file.name}")

    with st.spinner("Processing document and populating vector database..."):
        documents = load_documents()
        chunks = split_documents(documents)
        add_to_chroma(chunks)
    st.success("✅ Document processed and added to the database!")


# --- Query Section ---
st.markdown("---")
st.header("🔍 Ask a Question")
user_query = st.text_input("Enter your question")

if st.button("Submit Query"):
    if not user_query.strip():
        st.warning("Please enter a valid query.")
    else:
        with st.spinner("Querying database..."):
            response = query_rag(user_query)
            st.success("✅ Response generated:")
            st.write(response)
