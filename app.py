import streamlit as st
import os
from io import BytesIO
from fpdf import FPDF  # <-- NEW
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

def create_pdf(query, response_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, f"Query:\n{query}\n\nResponse:\n{response_text}")
    
    # Output PDF as a string
    pdf_output = pdf.output(dest='S').encode('latin-1')  # Return as bytes (latin-1 is required)
    buffer = BytesIO(pdf_output)
    return buffer

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

            # Generate PDF and add download button
            pdf_file = create_pdf(user_query, response)
            st.download_button(
                label="📥 Download Response as PDF",
                data=pdf_file,
                file_name="query_response.pdf",
                mime="application/pdf"
            )
