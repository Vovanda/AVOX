import json
import logging
import time
from collections import defaultdict
from datetime import datetime
from typing import Dict, Any

import numpy as np
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from numpy import ndarray
from sentence_transformers import SentenceTransformer
from sqlalchemy import and_, or_, text
from sqlalchemy.orm import Session

from avox_shared.knowledge_service.rag import RAGResponse
from knowledge_service.app.llm.base_provider import BaseLLMProvider
from knowledge_service.app.llm.dto import *
from knowledge_service.app.llm.rag_system_prompt import SYSTEM_PROMPT_TEMPLATE
from knowledge_service.app.models import AccessGrant
from knowledge_service.app.models.core.company import User
from knowledge_service.app.models.core.document import Document
from knowledge_service.app.models.enums import DocAccessLevel, UserType

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def cosine_distance(vec1: ndarray, vec2: ndarray) -> float:
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 1.0
    cosine_sim = np.dot(vec1, vec2) / (norm1 * norm2)
    return 1 - cosine_sim


class KnowledgeRAGPipeline:
    HISTORY_LIMIT = 20
    SUMMARIZE_OLD_MESSAGES = 10
    TOP_K = 20

    def __init__(self, db_session: Session, llm_provider: BaseLLMProvider):
        self.db = db_session
        self.llm = llm_provider
        self.prompt_template = PromptTemplate(input_variables=["request_json"], template=SYSTEM_PROMPT_TEMPLATE.strip())
        self.memory: Dict[str, List[Dict[str, str]]] = {}
        self.embedder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')


    def _get_accessible_docs(self, user: Optional[User]) -> List[Document]:
        query = self.db.query(Document)

        public_docs = and_(
            Document.access_level == DocAccessLevel.PUBLIC,
            Document.is_approved == True,
            Document.company_id == (user.company_id if user else None)
        )
        owner_docs = (user is not None) and (Document.owner_id == user.id)
        internal_docs = and_(
            user is not None,
            Document.access_level == DocAccessLevel.INTERNAL,
            user.user_type == UserType.INTERNAL,
            Document.company_id == user.company_id
        )
        access_granted_docs = Document.access_grants.any(
            and_(
                AccessGrant.user_id == user.id,
                AccessGrant.is_revoked == False,
                or_(
                    AccessGrant.expires_at == None,
                    AccessGrant.expires_at >= datetime.now()
                )
            )
        ) if user else False

        access_filter = or_(
            public_docs,
            owner_docs,
            internal_docs,
            access_granted_docs
        )
        return query.filter(access_filter).all()

    def _get_similar_chunks(
            self,
            question: str,
            user: Optional[User],
            top_k: int = 20,
            subchunk_top_k: int = 3,
            score_threshold: float = 0.25
    ) -> List[Dict[str, Any]]:
        start_time = time.time()
        accessible_docs = self._get_accessible_docs(user)
        doc_ids = [str(doc.id) for doc in accessible_docs]
        if not doc_ids:
            return []

        query_vector_np = self.embedder.encode([question])[0]
        query_vector = query_vector_np.tolist()

        sql = """
        WITH best_subchunks AS (
            SELECT DISTINCT ON (dc.id)
                dc.id AS chunk_id,
                dc.document_id,
                dc.chunk_text,
                dc.chunk_idx,
                (emb.vector <=> CAST(:query_vector AS vector)) AS best_distance
            FROM document_chunks dc
            JOIN chunk_embeddings_384 emb ON emb.chunk_id = dc.id
            WHERE dc.document_id = ANY(CAST(:doc_ids AS uuid[]))
              AND emb.status = 'COMPLETED'
            ORDER BY dc.id, best_distance ASC
        ),
        top_subchunks AS (
            SELECT
                dc.id AS chunk_id,
                (emb.vector <=> CAST(:query_vector AS vector)) AS dist,
                ROW_NUMBER() OVER (PARTITION BY dc.id ORDER BY (emb.vector <=> CAST(:query_vector AS vector))) AS subchunk_rank
            FROM document_chunks dc
            JOIN chunk_embeddings_384 emb ON emb.chunk_id = dc.id
            WHERE dc.document_id = ANY(CAST(:doc_ids AS uuid[]))
              AND emb.status = 'COMPLETED'
        )
        SELECT
            b.chunk_id,
            b.document_id,
            b.chunk_idx,
            b.chunk_text,
            b.best_distance,
            AVG(t.dist) FILTER (WHERE t.subchunk_rank <= :subchunk_top_k) AS avg_distance,
            SUM((t.subchunk_rank <= :subchunk_top_k)::int) AS match_count
        FROM best_subchunks b
        JOIN top_subchunks t ON t.chunk_id = b.chunk_id
        GROUP BY b.chunk_id, b.document_id, b.chunk_text, b.chunk_idx, b.best_distance
        ORDER BY b.best_distance ASC
        LIMIT :top_k;
        """
        result = self.db.execute(
            text(sql),
            {"query_vector": query_vector, "doc_ids": doc_ids, "top_k": top_k, "subchunk_top_k": subchunk_top_k}
        ).mappings().all()

        chunks = []
        for row in result:
            best_distance = float(row["best_distance"])
            avg_distance = float(row["avg_distance"]) if row["avg_distance"] is not None else best_distance
            match_count = int(row["match_count"])

            norm_best = 1 - best_distance
            norm_avg = 1 - avg_distance
            norm_match = match_count / subchunk_top_k
            score = 0.6 * norm_best + 0.3 * norm_avg + 0.1 * norm_match

            if score >= score_threshold:
                chunks.append({
                    "chunk_id": row["chunk_id"],
                    "document_id": row["document_id"],
                    "chunk_idx": row["chunk_idx"],
                    "chunk_text": row["chunk_text"],
                    "best_distance": best_distance,
                    "avg_distance": avg_distance,
                    "match_count": match_count,
                    "score": score
                })

        elapsed = time.time() - start_time
        logger.debug(f"Retrieved {len(chunks)} chunks in {elapsed:.3f}s for user {user.id if user else 'anon'}")
        return chunks

    def _parse_response(self, response: str) -> LLMDocumentResponse:
        """
        Извлекает JSON-ответ из LLM и конвертирует в LLMDocumentResponse.
        Если JSON некорректен — возвращает пустой ответ.
        """
        try:
            # Ищем первый JSON в тексте
            start = response.find("{")
            end = response.rfind("}") + 1
            json_str = response[start:end]
            data = json.loads(json_str)

            # Приводим поля new_facts/updated_facts к FactCertainty
            def parse_facts(facts_list):
                result = []
                for f in facts_list:
                    result.append(Fact(
                        id=f.get("id"),
                        fact=f["fact"],
                        certainty=FactCertainty(f["certainty"].lower()),
                        reasoning=f.get("reasoning", "")
                    ))
                return result

            return LLMDocumentResponse(
                answer=data.get("answer", ""),
                reasoning=data.get("reasoning", ""),
                new_facts=parse_facts(data.get("new_facts", [])),
                updated_facts=parse_facts(data.get("updated_facts", [])),
                can_answer=data.get("can_answer", False)
            )
        except Exception as e:
            logger.error(f"Failed to parse LLM JSON response: {str(e)}")
            return LLMDocumentResponse(answer="", reasoning="", new_facts=[], updated_facts=[], can_answer=False)

    def _process_document(
            self,
            chunks: List[dict],
            question: str,
            previous_facts: List[Fact],
            previous_answer: str,
            dialog_history: str
    ) -> LLMDocumentResponse:
        """
        Формирует запрос к LLM, передаёт контекст, предыдущие факты и историю диалога.
        Возвращает LLMDocumentResponse.
        """
        try:
            if not chunks:
                return LLMDocumentResponse(answer="", reasoning="", new_facts=[], updated_facts=[], can_answer=False)

            # Подготовка контекста
            document_id = chunks[0]["document_id"]
            document_context = [
                {"chunk_id": c["chunk_id"], "chunk_text": c["chunk_text"]} for c in chunks
            ]

            # Формируем DTO запроса
            request_dto: LLMDocumentRequest = {
                "task": "Analyze document for relevant information",
                "question": question,
                "document_context": document_context,
                "previous_facts": previous_facts,
                "previous_answer": previous_answer,
                "dialog_history": dialog_history
            }

            request_json = json.dumps(request_dto, ensure_ascii=False)

            chain = LLMChain(llm=self.llm, prompt=self.prompt_template)
            response_text = chain.run({"request_json": request_json})

            return self._parse_response(response_text)

        except Exception as e:
            logger.error(f"Document processing failed: {str(e)}")
            return LLMDocumentResponse(answer="", reasoning="", new_facts=[], updated_facts=[], can_answer=False)

    def _format_history(self, history: List[Dict[str, str]]) -> str:
        return "\n".join([f"{m['role']}: {m['text']}" for m in history])

    def iterative_answer(self, user: User, question: str, doc_ids: Optional[List[str]] = None) -> RAGResponse:
        start_time = time.time()
        logger.info(f"Starting RAG processing for user {user.id}, question: {question}")

        try:
            # Получаем релевантные чанки
            chunk_dicts = self._get_similar_chunks(question, user, score_threshold=0.3)

            # Группировка по документу
            grouped_chunks: dict[str, list[dict]] = defaultdict(list)
            for chunk in chunk_dicts:
                grouped_chunks[chunk["document_id"]].append(chunk)

            # Сортировка чанков внутри документа
            for chunks in grouped_chunks.values():
                chunks.sort(key=lambda ch: ch.get("chunk_idx", 0))

            # Инициализация глобального списка фактов, ответа и истории
            facts: Dict[str, Fact] = {}
            fact_counter = 0
            answer = ""
            user_id = str(user.id)
            history = self.memory.get(user_id, [])
            history.append({"role": "user", "text": question})
            dialog_history = self._format_history(history)

            for doc_id, chunks in grouped_chunks.items():
                # Формируем previous_facts для LLM
                previous_facts_list = [
                    {
                        "id": fact_id,
                        "fact": fact.text,
                        "certainty": fact.certainty,
                        "reasoning": fact.reasoning
                    }
                    for fact_id, fact in facts.items()
                ]

                # Обработка документа
                result: LLMDocumentResponse = self._process_document(
                    chunks,
                    question,
                    previous_facts_list,
                    previous_answer=answer,
                    dialog_history=dialog_history
                )

                # Обновляем previous_answer
                answer = result.answer

                # Добавляем новые факты и обновляем существующие
                for new_fact in result.new_facts:
                    if new_fact["certainty"] == "contradicts":
                        continue

                    fact_counter += 1
                    fact_id = str(fact_counter)

                    facts[fact_id] = Fact(
                        id=fact_id,
                        fact=new_fact["fact"],
                        certainty=new_fact["certainty"],
                        reasoning=new_fact.get("reasoning", "")
                    )

                for updated_fact in result.updated_facts:
                    fact_id = updated_fact.id
                    if not fact_id or fact_id not in facts:
                        continue
                    if updated_fact.certainty == FactCertainty.CONTRADICTS:
                        del facts[fact_id]
                    else:
                        facts[fact_id].fact = updated_fact.text or facts[fact_id].fact
                        facts[fact_id].certainty = updated_fact.certainty or facts[fact_id].certainty
                        facts[fact_id].reasoning = updated_fact.reasoning or facts[fact_id].reasoning

            # Обновляем историю
            history.append({"role": "system", "text": answer})
            self.memory[user_id] = history
            processing_time_ms = int((time.time() - start_time) * 1000)

            used_doc_ids = list(grouped_chunks.keys())
            used_chunk_ids = [str(chunk["chunk_id"]) for chunks in grouped_chunks.values() for chunk in chunks]

            return RAGResponse(
                final_result=self._synthesize_answer(list(facts.values())),
                facts=list(facts.values()),
                reasoning="\n".join(f.reasoning for f in facts.values()),
                used_documents=used_doc_ids,
                used_doc_chunks=used_chunk_ids,
                confidence=min(1.0, len(facts) * 0.2),
                llm_provider=self.llm.__class__.__name__,
                processing_time_ms=processing_time_ms
            )

        except Exception as e:
            logger.error(f"Pipeline execution failed: {str(e)}")
            return RAGResponse(
                final_result="Error processing request",
                facts=[],
                reasoning=str(e),
                used_documents=[],
                used_doc_chunks=[],
                confidence=0.0,
                llm_provider=self.llm.__class__.__name__,
                processing_time_ms=int((time.time() - start_time) * 1000)
            )

