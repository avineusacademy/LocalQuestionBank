import streamlit as st
import os
import tempfile
from io import BytesIO
from PIL import Image
import ocrmypdf
from fpdf import FPDF
from pdfminer.high_level import extract_text
from langchain.schema.document import Document

from populate_database import split_documents, add_to_chroma, clear_chroma, count_documents
from query_data import query_rag

# --- Utilities ---
def get_pdf_text_with_layout(pdf_path):
    try:
        return extract_text(pdf_path)
    except Exception as e:
        st.error(f"Error extracting text: {e}")
        return ""

def create_response_pdf(query, response_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, f"Query:\n{query}\n\nResponse:\n{response_text}")
    return BytesIO(pdf.output(dest='S').encode('latin-1'))

def images_to_pdf_file(images):
    pdf_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
    pil_images = [Image.open(img).convert("RGB") for img in images]
    pil_images[0].save(pdf_path, save_all=True, append_images=pil_images[1:])
    return pdf_path

def ocr_pdf_file(input_pdf_path, lang_code):
    output_pdf_path = input_pdf_path.replace(".pdf", "_ocr.pdf")
    ocrmypdf.ocr(input_pdf_path, output_pdf_path, deskew=True, force_ocr=True, language=lang_code)
    return output_pdf_path

# --- App Config ---
st.set_page_config(page_title="OCR + RAG", layout="centered")
st.title("📄 OCR + RAG: Searchable PDF Knowledge Base")

# --- Session State ---
if "ocr_saved" not in st.session_state:
    st.session_state.ocr_saved = False
if "text_to_save" not in st.session_state:
    st.session_state.text_to_save = None

# --- Sidebar Settings ---
st.sidebar.header("⚙️ Options")

lang_map = {
    "English (eng)": "eng",
    "Hindi (hin)": "hin",
    "Tamil (tam)": "tam"
}
ocr_lang_display = st.sidebar.selectbox("🗣️ OCR Language", options=list(lang_map.keys()))
ocr_lang = lang_map[ocr_lang_display]

if st.sidebar.button("🔁 Reset DB & Clear Session"):
    clear_chroma()
    st.session_state.ocr_saved = False
    st.session_state.text_to_save = None
    st.sidebar.success("✅ Vector DB cleared and session reset.")

doc_count = count_documents()
st.sidebar.markdown(f"📦 Documents in DB: **{doc_count}**")

# --- Upload Files ---
st.markdown("### 📤 Upload Files")
uploaded_files = st.file_uploader(
    "Upload PDF, TXT, or images (PNG, JPG)",
    type=["pdf", "txt", "png", "jpg", "jpeg"],
    accept_multiple_files=True
)

if uploaded_files:
    image_files = [f for f in uploaded_files if "image" in f.type]
    pdf_files = [f for f in uploaded_files if f.type == "application/pdf"]
    text_files = [f for f in uploaded_files if f.type == "text/plain"]

    if image_files:
        st.subheader("🖼️ Images → Searchable PDF with OCR")
        if st.button("📄 Convert Images and Extract Text"):
            with st.spinner("Running OCR..."):
                combined_pdf = images_to_pdf_file(image_files)
                ocr_pdf_path = ocr_pdf_file(combined_pdf, ocr_lang)
                text = get_pdf_text_with_layout(ocr_pdf_path)
                st.session_state.text_to_save = text
                st.session_state.ocr_saved = False

            st.success("✅ OCR complete. Preview below:")
            st.text_area("🔍 Extracted Text", st.session_state.text_to_save, height=300)

    elif pdf_files:
        st.subheader("📄 PDF OCR")
        for pdf in pdf_files:
            if st.button(f"🔍 OCR '{pdf.name}'"):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
                    temp_pdf.write(pdf.getbuffer())
                    ocr_pdf_path = ocr_pdf_file(temp_pdf.name, ocr_lang)
                text = get_pdf_text_with_layout(ocr_pdf_path)
                st.session_state.text_to_save = text
                st.session_state.ocr_saved = False

                st.success(f"✅ OCR complete for {pdf.name}")
                st.text_area("🔍 Extracted Text", st.session_state.text_to_save, height=300)

    elif text_files:
        st.subheader("📄 Add Text File to Knowledge Base")
        for txt in text_files:
            content = txt.read().decode("utf-8")
            st.text_area(f"🔍 Preview: {txt.name}", content, height=300)
            st.session_state.text_to_save = content
            st.session_state.ocr_saved = False

# --- Save Extracted Text ---
if st.session_state.text_to_save and not st.session_state.ocr_saved:
    if st.checkbox("✅ Save extracted text to Knowledge Base"):
        with st.spinner("Saving to DB..."):
            clear_chroma()
            chunks = split_documents([Document(page_content=st.session_state.text_to_save)])
            add_to_chroma(chunks)
        st.session_state.ocr_saved = True
        st.success("✅ Text saved to vector DB.")
elif st.session_state.ocr_saved:
    st.info("ℹ️ Text already saved to DB.")

# --- Query Section ---
st.markdown("---")
st.header("🔍 Ask a Question from Knowledge Base")

user_query = st.text_input("Enter your question here")

if st.button("Submit Query"):
    if not user_query.strip():
        st.warning("⚠️ Please enter a valid question.")
    else:
        with st.spinner("Querying..."):
            response = query_rag(user_query)
            st.success("✅ Response:")
            st.write(response)

            pdf_file = create_response_pdf(user_query, response)
            st.download_button(
                label="📥 Download Response as PDF",
                data=pdf_file,
                file_name="query_response.pdf",
                mime="application/pdf"
            )
