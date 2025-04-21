from langchain_community.vectorstores import FAISS
from langflow.base.vectorstores.model import LCVectorStoreComponent, check_cached_vector_store
from langflow.helpers.data import docs_to_data
from langflow.io import BoolInput, HandleInput, IntInput, StrInput, Output
from langflow.schema import Data
import os


class FaissVectorStoreComponent(LCVectorStoreComponent):
    """FAISS Vector Store with conditional update logic."""

    display_name: str = "FAISS"
    description: str = "FAISS Vector Store with conditional indexing"
    name = "FAISS"
    icon = "FAISS"

    inputs = [
        StrInput(name="index_name", display_name="Index Name", value="langflow_index"),
        StrInput(name="persist_directory", display_name="Persist Directory", info="Path to save the FAISS index."),
        IntInput(name="vector_dim", display_name="Vector Dimension", info="Dimension of embedding vectors.", value=768),
        *LCVectorStoreComponent.inputs,
        BoolInput(name="allow_dangerous_deserialization", display_name="Allow Dangerous Deserialization",
                  info="Set to True to allow loading pickle files from untrusted sources.", advanced=True, value=True),
        HandleInput(name="embedding", display_name="Embedding", input_types=["Embeddings"]),
        IntInput(name="number_of_results", display_name="Number of Results", info="Number of results to return.",
                 advanced=True, value=4),
        BoolInput(name="force_rebuild", display_name="Force Rebuild", info="If set to True, rebuilds the FAISS index.",
                  value=False),
    ]

    outputs = LCVectorStoreComponent.outputs + [
        Output(display_name="Vector Store", name="vector_store", method="build_vector_store")
    ]

    @check_cached_vector_store
    def build_vector_store(self) -> FAISS:
        """Conditional index building with search-aware updates"""
        if not self.persist_directory:
            raise ValueError("Persist directory is required")

        path = self.resolve_path(self.persist_directory)
        os.makedirs(path, exist_ok=True)
        index_path = os.path.join(path, f"{self.index_name}.faiss")

        # Existing index handling
        if os.path.exists(index_path) and not self.force_rebuild:
            vector_store = FAISS.load_local(
                folder_path=path,
                embeddings=self.embedding,
                index_name=self.index_name,
                allow_dangerous_deserialization=self.allow_dangerous_deserialization
            )
            
            # Update only when no search query present
            if self.ingest_data and not self.search_query.strip():
                self._update_index(vector_store, path)
            
            return vector_store

        # New index creation (required for search if missing)
        return self._create_new_index(path)

    def _update_index(self, vector_store: FAISS, path: str):
        """Update index with new documents"""
        docs = [d.to_lc_document() if isinstance(d, Data) else d for d in self.ingest_data]
        vector_store.add_documents(docs)
        vector_store.save_local(path, self.index_name)
        self.log(f"Index updated with {len(docs)} new documents")

    def _create_new_index(self, path: str) -> FAISS:
        """Create new index from scratch"""
        if not self.ingest_data:
            raise ValueError("No data provided for index creation")

        docs = [d.to_lc_document() if isinstance(d, Data) else d for d in self.ingest_data]
        vector_store = FAISS.from_documents(docs, self.embedding)
        vector_store.save_local(path, self.index_name)
        self.log("New FAISS index created")
        return vector_store

    def search_documents(self) -> list[Data]:
        """Search-only execution flow"""
        if not self.search_query.strip():
            return []

        vector_store = self.build_vector_store()
        docs = vector_store.similarity_search(
            query=self.search_query,
            k=self.number_of_results
        )
        return docs_to_data(docs)