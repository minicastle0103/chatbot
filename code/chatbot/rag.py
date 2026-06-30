from pathlib import Path
from typing import List

import chromadb
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage
from llama_index.core import VectorStoreIndex
from llama_index.core.embeddings import BaseEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from openai import OpenAI

from .prompts import SYSTEM_PROMPT, build_user_prompt

CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent.parent
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

embed_model = LMStudioEmbedding()
db = chromadb.PersistentClient(path=DB_PATH)
chroma_collection = db.get_or_create_collection(COLLECTION_NAME)
vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

index = VectorStoreIndex.from_vector_store(
    vector_store,
    embed_model=embed_model
)

custom_profile = {
    "max_input_tokens": 100_000,
}

def ask_truss_bot(question: str, model_id: str = "qwen2.5", top_k: int = 3):
    retriever = index.as_retriever(similarity_top_k=top_k)
    raw_nodes = retriever.retrieve(question)

    if not raw_nodes:
        return "문서를 찾을 수 없습니다.", ["참고 문서가 없습니다."], None

    contexts = [node.get_content() for node in raw_nodes]
    sources = list(set([
        node.metadata.get('file_name', 'Unknown') for node in raw_nodes
    ]))

    best_context = "\n\n---\n\n".join(contexts)
    user_prompt = build_user_prompt(question, best_context)

    try:
        if model_id == "qwen2.5":
            llm = init_chat_model(
                model="qwen2.5-7b-instruct-uncensored",
                model_provider="openai",
                api_key="lm-studio",
                base_url="http://localhost:1234/v1",
                temperature=0.0
            )
        elif model_id == "llama-3.1":
            llm = init_chat_model(
                model="llama-3.1-korean-8b-instruct-law",
                model_provider="openai",
                api_key="lm-studio",
                base_url="http://127.0.0.1:1234/v1",
                temperature=0.0
            )
        else:
            raise ValueError(f"알 수 없는 모델 선택입니다: {model_id}")

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_prompt)
        ]

        res = llm.invoke(messages)
        answer = res.content
        clean_sources = [f"참고 문서명: {file}" for file in sources]

        return answer, clean_sources, None

    except Exception as e:
        return f"LLM 오류: {e}", ["에러 발생으로 읽지 못함"], None