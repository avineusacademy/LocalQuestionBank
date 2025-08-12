import os
import shutil
from langchain.document_loaders import DirectoryLoader, TextLoader
from langchain.document_loaders.pdf import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema.document import Document
from langchain.vectorstores.chroma import Chroma

from get_embedding_function import get_embedding_function

CHROMA_PATH = "chroma"
DATA_PATH = "data"


def process_documents(reset: bool = False):
    if reset:
        print("✨ Clearing database...")
        clear_database()

    documents = load_documents()
    chunks = split_documents(documents)
    add_to_chroma(chunks)


def load_documents() -> list[Document]:
    # Dynamically handle both PDFs and text files
    if any(fname.endswith(".pdf") for fname in os.listdir(DATA_PATH)):
        document_loader = PyPDFDirectoryLoader(DATA_PATH)
    else:
        document_loader = DirectoryLoader(DATA_PATH, loader_cls=TextLoader)
    return document_loader.load()


def split_documents(documents: list[Document]) -> list[Document]:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=80,
        length_function=len,
        is_separator_regex=False,
    )
    return text_splitter.split_documents(documents)


def add_to_chroma(chunks: list[Document]):
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=get_embedding_function())

    chunks_with_ids = calculate_chunk_ids(chunks)

    existing_items = db.get(include=[])  # IDs are included by default
    existing_ids = set(existing_items["ids"])
    print(f"Number of existing documents in DB: {len(existing_ids)}")

    new_chunks = [chunk for chunk in chunks_with_ids if chunk.metadata["id"] not in existing_ids]

    if new_chunks:
        print(f"👉 Adding new documents: {len(new_chunks)}")
        new_chunk_ids = [chunk.metadata["id"] for chunk in new_chunks]
        db.add_documents(new_chunks, ids=new_chunk_ids)
        db.persist()
    else:
        print("✅ No new documents to add")


def calculate_chunk_ids(chunks: list[Document]) -> list[Document]:
    last_page_id = None
    current_chunk_index = 0

    for chunk in chunks:
        source = chunk.metadata.get("source")
        page = chunk.metadata.get("page")
        current_page_id = f"{source}:{page}"

        if current_page_id == last_page_id:
            current_chunk_index += 1
        else:
            current_chunk_index = 0

        chunk_id = f"{current_page_id}:{current_chunk_index}"
        last_page_id = current_page_id
        chunk.metadata["id"] = chunk_id

    return chunks


def clear_database():
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Reset the database.")
    args = parser.parse_args()

    process_documents(reset=args.reset)
