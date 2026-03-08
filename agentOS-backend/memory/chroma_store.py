import chromadb
from chromadb.config import Settings as ChromaSettings
from memory.embedder import embedder
from config import settings
from typing import List


class ChromaStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name="agentOS_memory",
            metadata={"hnsw:space": "cosine"},
        )
        print(f"ChromaDB ready. {self.collection.count()} memories stored.")

    async def add(self, doc_id: str, document: str, metadata: dict):
        embedding = embedder.embed(document)
        try:
            self.collection.add(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[document],
                metadatas=[metadata],
            )
        except Exception:
            # doc_id already exists — update instead
            self.collection.update(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[document],
                metadatas=[metadata],
            )

    async def query(self, query_text: str, n_results: int = 3) -> List[dict]:
        if self.collection.count() == 0:
            return []
        embedding = embedder.embed(query_text)
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=min(n_results, self.collection.count()),
            include=["documents", "metadatas", "distances"],
        )
        output = []
        for i, doc in enumerate(results["documents"][0]):
            output.append({
                "chunk": doc,
                "score": round(1 - results["distances"][0][i], 3),
                "task_id": results["metadatas"][0][i].get("task_id", ""),
                "task_description": results["metadatas"][0][i].get("task_description", ""),
                "timestamp": results["metadatas"][0][i].get("timestamp", ""),
            })
        return output

    async def search_by_text(self, query: str, n_results: int = 10) -> List[dict]:
        return await self.query(query, n_results)

    def count(self) -> int:
        return self.collection.count()

    # ── Legacy sync-style aliases (used by existing route stubs) ─────
    def get_all(self, limit: int = 50) -> List[dict]:
        count = self.collection.count()
        if count == 0:
            return []
        raw = self.collection.get(
            limit=min(limit, count),
            include=["documents", "metadatas"],
        )
        out = []
        for i, doc_id in enumerate(raw.get("ids", [])):
            meta = raw["metadatas"][i] if i < len(raw.get("metadatas", [])) else {}
            task_id = meta.get("task_id", doc_id)  # Fallback to doc_id if no task_id
            
            # Skip test entries
            if doc_id.startswith("test-") or doc_id.startswith("test_"):
                continue
                
            out.append({
                "id": doc_id,
                "task_id": task_id,
                "task_description": meta.get("task_description", ""),
                "content": raw["documents"][i] if i < len(raw.get("documents", [])) else "",
                "score": 1.0,
                "created_at": meta.get("timestamp", meta.get("created_at", "")),
            })
        return out

    def search(self, query_text: str, k: int = 10) -> List[dict]:
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            results = loop.run_until_complete(self.query(query_text, k))
            return [
                {**r, "content": r.get("chunk", ""), "created_at": r.get("timestamp", "")}
                for r in results
            ]
        finally:
            loop.close()

    def delete(self, mem_id: str) -> bool:
        try:
            self.collection.delete(ids=[mem_id])
            return True
        except Exception:
            return False


# Single shared instance — import this everywhere
chroma_store = ChromaStore()
