import uuid
from typing import List

from nltk.tokenize import sent_tokenize
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session
from transformers import AutoTokenizer

from knowledge_service.app.api.schemas.document import DocumentIngestResponse
from knowledge_service.app.models.core.document import Document, DocumentChunk, ChunkEmbedding384
from knowledge_service.app.models.enums import DocAccessLevel, SourceType, EmbeddingStatus


class DocumentIngestor:
    def __init__(self, db: Session):
        self.db = db
        self.model_name = "sentence-transformers/all-MiniLM-L6-v2"
        self.model = SentenceTransformer(self.model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)

        self.max_embedding_tokens = 256
        self.subchunk_overlap_tokens = 32

        self.chunk_size_sentences = 5
        self.chunk_overlap_sentences = 2

    def _split_text_into_subchunks(self, text: str) -> List[str]:
        encoding = self.tokenizer(
            text,
            max_length=self.max_embedding_tokens,
            stride=self.subchunk_overlap_tokens,
            truncation=True,
            return_overflowing_tokens=True,
            return_offsets_mapping=True
        )
        subchunks = []
        for i, input_ids in enumerate(encoding['input_ids']):
            offsets = encoding['offset_mapping'][i]
            start_char = offsets[0][0]
            end_char = offsets[-1][1]
            subchunk_text = text[start_char:end_char]
            subchunks.append(subchunk_text)
        return subchunks

    def _split_into_chunks_with_overlap(self, sentences: List[str], chunk_size: int, overlap: int) -> List[List[str]]:
        chunks = []
        i = 0
        while i < len(sentences):
            chunk = sentences[i:i + chunk_size]
            chunks.append(chunk)
            i += chunk_size - overlap
        return chunks

    def ingest(
        self,
        text: str,
        title: str,
        company_id: uuid.UUID,
        owner_id: uuid.UUID,
        source_type: SourceType,
        access_level: DocAccessLevel,
    ) -> Document:

        sentences = sent_tokenize(text)

        chunks_sentences = self._split_into_chunks_with_overlap(
            sentences,
            chunk_size=self.chunk_size_sentences,
            overlap=self.chunk_overlap_sentences
        )

        doc = Document(
            title=title,
            company_id=company_id,
            owner_id=owner_id,
            source_type=source_type,
            access_level=access_level,
            is_approved=(access_level == DocAccessLevel.RESTRICTED),
        )
        self.db.add(doc)
        self.db.flush()

        for chunk_idx, chunk_sents in enumerate(chunks_sentences):
            chunk_text = " ".join(chunk_sents)

            chunk = DocumentChunk(
                document_id=doc.id,
                chunk_text=chunk_text,
                chunk_idx=chunk_idx,
                chunk_scope = "sentence",
                is_hot=False,
            )
            self.db.add(chunk)
            self.db.flush()

            subchunks = self._split_text_into_subchunks(chunk_text)

            # Кодируем все subchunks одной партией — оптимально
            embeddings = self.model.encode(subchunks, convert_to_numpy=True)

            for subchunk_idx, (subchunk_text, embedding_vector) in enumerate(zip(subchunks, embeddings)):
                embedding = ChunkEmbedding384(
                    chunk_id=chunk.id,
                    vector=embedding_vector.tolist(),
                    embedding_model=self.model_name,
                    embedding_scope="subchunk",
                    subchunk_idx=subchunk_idx,
                    chunk_scope="sentence_chunk",
                    overlap = self.subchunk_overlap_tokens,
                    status=EmbeddingStatus.COMPLETED
                )
                self.db.add(embedding)

        self.db.commit()

        return DocumentIngestResponse(
                document_id=doc.id,
                title=doc.title,
                status="success"
            )
