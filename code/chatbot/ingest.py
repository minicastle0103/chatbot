import os
import re
from pathlib import Path
from typing import List

import chromadb
from markitdown import MarkItDown
from openai import OpenAI

from llama_index.core import (
    Document,
    VectorStoreIndex,
    StorageContext,
    SimpleDirectoryReader
)
from llama_index.core.node_parser import MarkdownNodeParser
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.embeddings import BaseEmbedding

CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent.parent

RAW_DOCS_DIR = ROOT_DIR / "data" / "docs"
MD_OUTPUT_DIR = ROOT_DIR / "data" / "parsed_md"
DB_PATH = str(ROOT_DIR / "chroma_local_db")
COLLECTION_NAME = "truss_docs"

LM_STUDIO_URL = "http://127.0.0.1:1234/v1"
EMBED_MODEL_NAME = "text-embedding-bge-m3"

class LMStudioEmbedding(BaseEmbedding):
    model_name: str = EMBED_MODEL_NAME
    api_base: str = LM_STUDIO_URL
    api_key: str = "lm-studio"

    def _get_client(self) -> OpenAI:
        return OpenAI(base_url=self.api_base, api_key=self.api_key)

    def _get_query_embedding(self, query: str) -> List[float]:
        client = self._get_client()
        res = client.embeddings.create(model=self.model_name, input=query)
        return res.data[0].embedding

    def _get_text_embedding(self, text: str) -> List[float]:
        client = self._get_client()
        res = client.embeddings.create(model=self.model_name, input=text)
        return res.data[0].embedding

    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        client = self._get_client()
        res = client.embeddings.create(model=self.model_name, input=texts)
        return [data.embedding for data in res.data]

    async def _aget_query_embedding(self, query: str) -> List[float]:
        return self._get_query_embedding(query)

    async def _aget_text_embedding(self, text: str) -> List[float]:
        return self._get_text_embedding(text)

def parse_documents(files_to_process: set):
    MD_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DOCS_DIR.mkdir(parents=True, exist_ok=True)

    md_converter = MarkItDown()
    parsed_docs = []

    for filename in os.listdir(RAW_DOCS_DIR):
        if filename not in files_to_process:
            continue

        file_path = RAW_DOCS_DIR / filename
        base_name, ext = os.path.splitext(filename)
        ext = ext.lower()
        md_text = ""

        try:
            if ext == '.pdf':
                pdf_docs = SimpleDirectoryReader(
                    input_files=[str(file_path)]
                ).load_data()
                texts = [d.get_content() for d in pdf_docs]
                md_text = "\n\n".join(texts)

            elif ext in ['.docx', '.xlsx', '.pptx', '.html']:
                result = md_converter.convert(str(file_path))
                md_text = result.text_content
                md_text = re.sub(
                    r'!\[.*?\]\(.*?\)', '', md_text, flags=re.DOTALL
                )

            elif ext == '.txt':
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        md_text = f.read()
                except UnicodeDecodeError:
                    with open(file_path, 'r', encoding='cp949') as f:
                        md_text = f.read()
            else:
                continue

            out_path = MD_OUTPUT_DIR / f"{base_name}.md"
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(md_text)

            parsed_docs.append(
                Document(text=md_text, metadata={"file_name": filename})
            )
        except Exception as e:
            print(f"Error parsing {filename}: {e}")

    return parsed_docs

def build_vector_db():
    db = chromadb.PersistentClient(path=DB_PATH)
    chroma_collection = db.get_or_create_collection(COLLECTION_NAME)

    RAW_DOCS_DIR.mkdir(parents=True, exist_ok=True)
    folder_files = set(os.listdir(RAW_DOCS_DIR))

    existing_data = chroma_collection.get(include=["metadatas"])
    existing_metadatas = existing_data.get("metadatas", [])

    db_files = set()
    if existing_metadatas:
        for meta in existing_metadatas:
            if meta and "file_name" in meta:
                db_files.add(meta["file_name"])

    files_to_remove = db_files - folder_files
    if files_to_remove:
        for f_name in files_to_remove:
            chroma_collection.delete(where={"file_name": f_name})

    files_to_add = folder_files - db_files

    if not files_to_add:
        return

    documents = parse_documents(files_to_add)

    if not documents:
        return

    parser = MarkdownNodeParser()
    nodes = parser.get_nodes_from_documents(documents)

    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(
        vector_store=vector_store
    )
    embed_model = LMStudioEmbedding()

    VectorStoreIndex(
        nodes,
        storage_context=storage_context,
        embed_model=embed_model
    )