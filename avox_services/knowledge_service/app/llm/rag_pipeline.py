import logging
import re
import time
from datetime import datetime
from typing import List, Dict, Optional

from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from sentence_transformers import SentenceTransformer
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session

from knowledge_service.app.api.schemas.rag import Fact, RAGResponse
from knowledge_service.app.llm.base_provider import BaseLLMProvider
from knowledge_service.app.models import AccessGrant
from knowledge_service.app.models.core.company import User
from knowledge_service.app.models.core.document import Document, DocumentChunk, ChunkEmbedding384
from knowledge_service.app.models.enums import DocAccessLevel, UserType, EmbeddingStatus

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
class KnowledgeRAGPipeline:
    HISTORY_LIMIT = 20
    SUMMARIZE_OLD_MESSAGES = 10
    TOP_K = 20

    def __init__(self, db_session: Session, llm_provider: BaseLLMProvider):
        self.db = db_session
        self.llm = llm_provider
        self.prompt_template = self._create_prompt_template()
        self.memory: Dict[str, List[Dict[str, str]]] = {}
        self.embedder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    def _create_prompt_template(self) -> PromptTemplate:
        return PromptTemplate(
            input_variables=["task", "question", "context", "previous_facts"],
            template="""
Task: {task}
Role: AVOX Knowledge Assistant

Question: {question}
Context Documents: {context}
Previous Facts: {previous_facts}

Response Format:
Reasoning: <step-by-step analysis>
New Facts: <list of facts with certainty levels: confirmed|likely|contradicts>
Answer: <final synthesized response>
Confidence: <0.0-1.0>
Source Documents: <list of doc IDs>
""".strip()
        )

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
        query = query.filter(access_filter)
        return query.all()

    def _get_similar_chunks(self, question: str, user: Optional[User]) -> List[DocumentChunk]:
        accessible_docs = self._get_accessible_docs(user)
        accessible_doc_ids = [doc.id for doc in accessible_docs]

        if not accessible_doc_ids:
            return []

        query_vector = self.embedder.encode([question])[0].tolist()

        # Быстрый поиск по ivfflat
        top_chunks = (
            self.db.query(DocumentChunk, ChunkEmbedding384.vector)
            .join(ChunkEmbedding384, ChunkEmbedding384.chunk_id == DocumentChunk.id)
            .filter(
                DocumentChunk.document_id.in_(accessible_doc_ids),
                ChunkEmbedding384.status == EmbeddingStatus.COMPLETED
            )
            .order_by(ChunkEmbedding384.vector.cosine_distance(query_vector))
            .limit(self.TOP_K)
            .all()
        )

        # Фильтрация по расстоянию в Python
        return [
            chunk for chunk, vector in top_chunks
            if vector.cosine_distance(query_vector) < 0.6
        ]

    def _process_document(self, doc: Document, question: str, facts: List[Fact], previous_context: str = "") -> Dict:
        try:
            context = f"Document {doc.id} ({doc.title}):\n" + "\n".join(
                [f"Chunk {idx}: {chunk.chunk_text}" for idx, chunk in enumerate(doc.chunks, 1)]
            )
            chain = LLMChain(llm=self.llm, prompt=self.prompt_template)
            response = chain.run({
                "task": "Analyze document for relevant information",
                "question": question,
                "context": context,
                "previous_facts": previous_context
            })
            return self._parse_response(response)
        except Exception as e:
            logger.error(f"Document processing failed: {str(e)}")
            return {"answer": "", "new_facts": []}

    def iterative_answer(self, user: User, question: str, doc_ids: Optional[List[str]] = None) -> RAGResponse:
        start_time = time.time()
        logger.info(f"Starting RAG processing for user {user.id}, question: {question}")

        try:
            docs_chunks = self._get_similar_chunks(question, user)
            facts: List[Fact] = []
            user_id = str(user.id)
            history = self.memory.get(user_id, [])
            history.append({"role": "user", "text": question})

            for i, chunk in enumerate(docs_chunks):
                is_last = i == len(docs_chunks) - 1
                previous_context = self._format_history(history) if is_last else ""
                result = self._process_document(chunk, question, facts, previous_context)

                history.append({"role": "system", "text": result.get("answer", "")})
                facts.extend([
                    Fact(
                        text=fact["text"],
                        certainty=fact["certainty"],
                        reasoning=fact["reasoning"],
                        source_doc_id=str(chunk.document_id),
                        source_doc_chuk_id=str(chunk.id),
                        timestamp=datetime.now()
                    )
                    for fact in result.get("new_facts", [])
                    if fact.get("certainty") != "contradicts"
                ])

                if len(history) > self.HISTORY_LIMIT:
                    history = self._summarize_old_messages(history)

            self.memory[user_id] = history
            processing_time_ms = int((time.time() - start_time) * 1000)

            return RAGResponse(
                final_result=self._synthesize_answer(facts),
                facts=facts,
                reasoning="\n".join(f.reasoning for f in facts),
                used_documents=[str(ch.document_id) for ch in docs_chunks],
                used_doc_chunks=[str(ch.id) for ch in docs_chunks],
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

    def _summarize_old_messages(self, history: List[Dict[str, str]]) -> List[Dict[str, str]]:
        to_summarize = history[:self.SUMMARIZE_OLD_MESSAGES]
        remaining = history[self.SUMMARIZE_OLD_MESSAGES:]

        combined_text = "\n".join([f"{m['role']}: {m['text']}" for m in to_summarize])
        prompt_text = (
            "Суммируй кратко следующую историю переписки между пользователем и системой, "
            "выделяя ключевые моменты и факты:\n\n"
            f"{combined_text}\n\nКраткое резюме:"
        )

        chain = LLMChain(llm=self.llm, prompt=PromptTemplate(
            input_variables=["text"],
            template="{text}"
        ))
        summary_text = chain.run({"text": prompt_text}).strip()
        summary = {"role": "system", "text": f"[History Summary]: {summary_text}"}
        return [summary] + remaining

    def _format_history(self, history: List[Dict[str, str]]) -> str:
        return "\n".join([f"{m['role']}: {m['text']}" for m in history])

    def _parse_response(self, response: str) -> Dict:
        try:
            def extract_block(label: str) -> str:
                pattern = re.compile(rf"{label}\s*(.*?)(?=\n\\S|$)", re.DOTALL | re.IGNORECASE)
                match = pattern.search(response)
                return match.group(1).strip() if match else ""

            reasoning = extract_block("Reasoning:")
            facts_block = extract_block("New Facts:")
            answer = extract_block("Answer:")
            confidence_str = extract_block("Confidence:")
            docs_str = extract_block("Source Documents:")

            new_facts = []
            for line in facts_block.split("\n"):
                line = line.strip()
                if not line:
                    continue
                m = re.match(r"-\s*(.+?)\s*\((confirmed|likely|contradicts)\):\s*(.+)", line, re.IGNORECASE)
                if m:
                    new_facts.append({
                        "text": m.group(1),
                        "certainty": m.group(2).lower(),
                        "reasoning": m.group(3)
                    })

            return {
                "reasoning": reasoning,
                "answer": answer,
                "confidence": float(confidence_str) if confidence_str else 0.0,
                "source_documents": [doc.strip() for doc in docs_str.split(",") if doc.strip()],
                "new_facts": new_facts
            }
        except Exception as e:
            logger.error(f"Failed to parse response: {str(e)}")
            return {"answer": "", "new_facts": []}

    def _synthesize_answer(self, facts: List[Fact]) -> str:
        return "\n".join([f"- {f.text}" for f in facts])
