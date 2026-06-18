import logging
import uuid
import numpy as np
from app.config import settings
from app.rag.embedder import embedder

logger = logging.getLogger(__name__)

class ChromaVectorStore:
    def __init__(self):
        self.persist_directory = settings.CHROMA_PERSIST_DIRECTORY
        self.collection_name = "bangla_knowledge_base"
        self.client = None
        self.collection = None
        self.memory_db = []  # Fallback in-memory database structure
        
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings
            logger.info(f"Connecting to ChromaDB at {self.persist_directory}...")
            self.client = chromadb.PersistentClient(path=self.persist_directory)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}  # Use cosine similarity
            )
            logger.info("ChromaDB persistent client loaded.")
        except Exception as e:
            logger.warning(
                f"Failed to initialize ChromaDB native client: {e}. "
                f"Falling back to high-fidelity, thread-safe in-memory vector store."
            )
            self.client = None
            self.collection = None
            # In-memory database backup structure
            self.memory_db = []  # List of dicts containing: id, text, metadata, embedding

    def add_documents(self, texts: list[str], metadatas: list[dict] = None, ids: list[str] = None):
        """Add documents to the vector database."""
        if not texts:
            return
        
        if metadatas is None:
            metadatas = [{} for _ in texts]
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in texts]
            
        embeddings = embedder.embed_documents(texts)
        
        if self.collection:
            try:
                self.collection.add(
                    documents=texts,
                    embeddings=embeddings,
                    metadatas=metadatas,
                    ids=ids
                )
                logger.info(f"Successfully added {len(texts)} documents to ChromaDB.")
                return
            except Exception as e:
                logger.error(f"Error writing to ChromaDB: {e}. Writing to memory fallback.")
                
        # In-memory store fallback logic
        for i in range(len(texts)):
            self.memory_db.append({
                "id": ids[i],
                "text": texts[i],
                "metadata": metadatas[i],
                "embedding": embeddings[i]
            })
        logger.info(f"Successfully added {len(texts)} documents to in-memory fallback store.")

    def query_documents(self, query_text: str, n_results: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Query semantic matches for query_text.
        Returns:
            List of dicts containing: content, metadata, id, and confidence_score (0.0 to 1.0)
        """
        query_vector = embedder.embed_text(query_text)
        results = []
        
        if self.collection:
            try:
                # Query Chroma
                chroma_results = self.collection.query(
                    query_embeddings=[query_vector],
                    n_results=n_results,
                    where=metadata_filter
                )
                
                if chroma_results and chroma_results["documents"] and chroma_results["documents"][0]:
                    docs = chroma_results["documents"][0]
                    metas = chroma_results["metadatas"][0] if chroma_results["metadatas"] else [{}] * len(docs)
                    distances = chroma_results["distances"][0] if chroma_results["distances"] else [0.0] * len(docs)
                    ids = chroma_results["ids"][0] if chroma_results["ids"] else [str(uuid.uuid4())] * len(docs)
                    
                    for idx in range(len(docs)):
                        # In Chroma cosine space, distance is (1.0 - cosine_similarity).
                        # Hence similarity is 1.0 - distance. We cap confidence at [0.0, 1.0].
                        distance = distances[idx]
                        confidence = float(max(0.0, min(1.0, 1.0 - distance)))
                        
                        results.append({
                            "id": ids[idx],
                            "content": docs[idx],
                            "metadata": metas[idx],
                            "confidence_score": confidence
                        })
                    return results
            except Exception as e:
                logger.error(f"Error querying ChromaDB: {e}. Querying in-memory database.")
                
        # In-memory fallback lookup logic
        if not self.memory_db:
            return []
            
        candidate_scores = []
        q_vec = np.array(query_vector)
        q_norm = np.linalg.norm(q_vec)
        
        for doc in self.memory_db:
            # Filter metadata if requested
            if metadata_filter:
                match = True
                for k, v in metadata_filter.items():
                    if doc["metadata"].get(k) != v:
                        match = False
                        break
                if not match:
                    continue
            
            d_vec = np.array(doc["embedding"])
            d_norm = np.linalg.norm(d_vec)
            
            if q_norm == 0 or d_norm == 0:
                similarity = 0.0
            else:
                similarity = float(np.dot(q_vec, d_vec) / (q_norm * d_norm))
                
            confidence = max(0.0, min(1.0, (similarity + 1.0) / 2.0)) # Normalize cosine [-1,1] to [0,1]
            candidate_scores.append((confidence, doc))
            
        # Sort candidates descending by confidence score
        candidate_scores.sort(key=lambda x: x[0], reverse=True)
        top_candidates = candidate_scores[:n_results]
        
        for confidence, doc in top_candidates:
            results.append({
                "id": doc["id"],
                "content": doc["text"],
                "metadata": doc["metadata"],
                "confidence_score": confidence
            })
            
        return results

# Instantiate singleton
vector_store = ChromaVectorStore()
