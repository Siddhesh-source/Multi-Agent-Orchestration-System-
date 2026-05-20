"""
3-Tier Memory Architecture - USP #2
Episodic + Semantic + Procedural memory system.

Tier 1 - Episodic Memory: Timestamped task episodes with emotional valence tagging
Tier 2 - Semantic Memory: Entity graph built from extracted knowledge (networkx)
Tier 3 - Procedural Memory: Reusable agent workflows from successful task patterns

Novel: No existing open-source agent system implements all three simultaneously.
Enables: forgetting curves, cross-task knowledge transfer, workflow templating.
"""
import json
import math
import asyncio
from datetime import datetime, timezone, timedelta
from typing import List, Optional, TypedDict
from memory.chroma_store import ChromaStore
from memory.embedder import embedder
from config import settings


class EpisodicEntry(TypedDict):
    """A timestamped task episode with emotional valence."""
    id: str
    task_id: str
    task_description: str
    content: str
    timestamp: str
    valence: float          # -1.0 (negative) to 1.0 (positive) outcome
    decay_weight: float     # current memory strength (0-1, decreases over time)
    access_count: int       # how many times retrieved
    last_accessed: str


class SemanticEntity(TypedDict):
    """An entity node in the semantic knowledge graph."""
    id: str
    entity: str             # e.g. "Python", "machine learning", "Tesla"
    entity_type: str        # "concept", "person", "technology", "place", "organization"
    description: str        # extracted description
    related_entities: List[str]  # entity names this is connected to
    occurrence_count: int   # how often this entity appears
    first_seen: str
    last_seen: str


class ProceduralWorkflow(TypedDict):
    """A reusable workflow template extracted from successful tasks."""
    id: str
    name: str               # e.g. "research_paper_workflow"
    description: str
    task_patterns: List[str]  # task descriptions that triggered this workflow
    subtask_sequence: List[dict]  # the ordered steps + agent hints
    success_count: int      # times used successfully
    avg_duration_seconds: float
    created_at: str
    last_used: str


class TrieMemorySystem:
    """
    3-Tier Memory System combining Episodic, Semantic, and Procedural memory.
    
    Architecture:
    - Tier 1 (Episodic): ChromaDB with decay-weighted embeddings
    - Tier 2 (Semantic): ChromaDB for entity search
    - Tier 3 (Procedural): ChromaDB-backed workflow templates
    """
    
    # Ebbinghaus forgetting curve parameters
    MEMORY_DECAY_RATE = 0.1      # decay per day
    MEMORY_BOOST_ON_ACCESS = 0.2  # strength boost when memory is accessed
    
    def __init__(self):
        import chromadb
        from chromadb.config import Settings as ChromaSettings
        self._chroma_client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        
        # Create separate collections for each memory tier
        self._episodic_collection = self._chroma_client.get_or_create_collection(
            name="episodic_memory",
            metadata={"hnsw:space": "cosine"},
        )
        self._semantic_collection = self._chroma_client.get_or_create_collection(
            name="semantic_memory",
            metadata={"hnsw:space": "cosine"},
        )
        self._procedural_collection = self._chroma_client.get_or_create_collection(
            name="procedural_memory",
            metadata={"hnsw:space": "cosine"},
        )
        
        print(f"[TrieMemory] Episodic: {self._episodic_collection.count()}, "
              f"Semantic: {self._semantic_collection.count()}, "
              f"Procedural: {self._procedural_collection.count()}")
    
    # ─── TIER 1: EPISODIC MEMORY ──────────────────────────────────────
    
    async def store_episode(
        self, 
        task_id: str, 
        task_description: str, 
        content: str,
        valence: float = 0.5  # 0.5 = neutral outcome
    ) -> str:
        """
        Store a task episode with timestamp and valence (outcome quality).
        
        Args:
            valence: -1.0 (failed) to 1.0 (excellent) - emotional outcome tag
        """
        episode_id = f"ep_{task_id}"
        now = datetime.now(timezone.utc).isoformat()
        
        document = f"Task: {task_description}\nOutcome: {content}"
        embedding = embedder.embed(document)
        
        metadata = {
            "task_id": task_id,
            "task_description": task_description,
            "timestamp": now,
            "valence": valence,
            "decay_weight": 1.0,  # Fresh memory starts at full strength
            "access_count": 0,
            "last_accessed": now,
            "memory_type": "episodic",
        }
        
        try:
            self._episodic_collection.add(
                ids=[episode_id],
                embeddings=[embedding],
                documents=[document],
                metadatas=[metadata],
            )
        except Exception:
            # Update if exists
            metadata["decay_weight"] = 1.0  # Refresh on re-store
            self._episodic_collection.update(
                ids=[episode_id],
                embeddings=[embedding],
                documents=[document],
                metadatas=[metadata],
            )
        
        return episode_id
    
    async def retrieve_episodes(
        self, 
        query: str, 
        n_results: int = 3,
        min_valence: float = -1.0,
        recency_bias: float = 0.3  # 0 = pure semantic, 1 = pure recency
    ) -> List[EpisodicEntry]:
        """
        Retrieve episodic memories with decay weighting and recency bias.
        
        Uses Ebbinghaus forgetting curve: strength = e^(-decay_rate * days_since)
        """
        if self._episodic_collection.count() == 0:
            return []
        
        embedding = embedder.embed(query)
        n = min(n_results * 3, self._episodic_collection.count())  # Over-fetch for reranking
        
        results = self._episodic_collection.query(
            query_embeddings=[embedding],
            n_results=n,
            include=["documents", "metadatas", "distances"],
        )
        
        episodes = []
        now = datetime.now(timezone.utc)
        
        for i, doc in enumerate(results["documents"][0]):
            meta = results["metadatas"][0][i]
            semantic_score = 1 - results["distances"][0][i]
            
            # Apply valence filter
            valence = float(meta.get("valence", 0.5))
            if valence < min_valence:
                continue
            
            # Compute forgetting curve decay
            last_accessed = meta.get("last_accessed", meta.get("timestamp", ""))
            try:
                last_dt = datetime.fromisoformat(last_accessed)
                days_since = (now - last_dt).total_seconds() / 86400
                decay = math.exp(-self.MEMORY_DECAY_RATE * days_since)
            except Exception:
                decay = 0.5
            
            # Recency score (normalized days)
            timestamp = meta.get("timestamp", "")
            try:
                ts_dt = datetime.fromisoformat(timestamp)
                days_old = (now - ts_dt).total_seconds() / 86400
                recency_score = math.exp(-0.05 * days_old)
            except Exception:
                recency_score = 0.5
            
            # Final composite score
            final_score = (
                (1 - recency_bias) * semantic_score * decay +
                recency_bias * recency_score +
                valence * 0.1  # Slight boost for positive outcomes
            )
            
            episodes.append({
                "entry": {
                    "id": results["ids"][0][i] if "ids" in results else "",
                    "task_id": meta.get("task_id", ""),
                    "task_description": meta.get("task_description", ""),
                    "content": doc,
                    "timestamp": meta.get("timestamp", ""),
                    "valence": valence,
                    "decay_weight": decay,
                    "access_count": int(meta.get("access_count", 0)),
                    "last_accessed": last_accessed,
                },
                "score": final_score,
            })
        
        # Sort by composite score and return top n
        episodes.sort(key=lambda x: x["score"], reverse=True)
        return [e["entry"] for e in episodes[:n_results]]
    
    # ─── TIER 2: SEMANTIC MEMORY ──────────────────────────────────────
    
    async def store_entities(self, task_id: str, content: str, llm_client) -> List[str]:
        """
        Extract and store entities from content into the semantic knowledge graph.
        
        Uses LLM to extract entities and their relationships.
        """
        from core.llm import rate_limit_delay
        
        extraction_prompt = f"""Extract key entities from this text. Return ONLY JSON.

Text: {content[:2000]}

JSON format:
{{
  "entities": [
    {{"entity": "name", "type": "concept|person|technology|place|organization", "description": "brief description"}},
    ...
  ],
  "relationships": [
    {{"from": "entity1", "to": "entity2", "relationship": "relates_to|uses|part_of|causes|contrasts_with"}},
    ...
  ]
}}

No markdown, no extra text."""
        
        try:
            response = llm_client.invoke(extraction_prompt)
            await rate_limit_delay()
            result = self._parse_entities(response.content)
        except Exception as e:
            print(f"[TrieMemory] Entity extraction failed: {e}")
            return []
        
        if not result:
            return []
        
        stored_ids = []
        for entity in result.get("entities", []):
            entity_id = f"entity_{entity['entity'].lower().replace(' ', '_')}"
            doc = f"Entity: {entity['entity']}\nType: {entity['type']}\nDescription: {entity['description']}"
            embedding = embedder.embed(doc)
            
            now = datetime.now(timezone.utc).isoformat()
            
            # Build related entities from relationships
            related = [
                r["to"] for r in result.get("relationships", []) if r["from"] == entity["entity"]
            ] + [
                r["from"] for r in result.get("relationships", []) if r["to"] == entity["entity"]
            ]
            
            try:
                self._semantic_collection.add(
                    ids=[entity_id],
                    embeddings=[embedding],
                    documents=[doc],
                    metadatas={
                        "entity": entity["entity"],
                        "entity_type": entity["type"],
                        "description": entity["description"],
                        "related_entities": json.dumps(related),
                        "task_id": task_id,
                        "occurrence_count": 1,
                        "first_seen": now,
                        "last_seen": now,
                        "memory_type": "semantic",
                    },
                )
            except Exception:
                # Entity exists - update occurrence count and last_seen
                try:
                    existing = self._semantic_collection.get(ids=[entity_id])
                    existing_meta = existing["metadatas"][0] if existing["metadatas"] else {}
                    count = int(existing_meta.get("occurrence_count", 0)) + 1
                    self._semantic_collection.update(
                        ids=[entity_id],
                        metadatas={
                            **existing_meta,
                            "occurrence_count": count,
                            "last_seen": datetime.now(timezone.utc).isoformat(),
                        },
                    )
                except Exception as e:
                    print(f"[TrieMemory] Semantic update error: {e}")
            
            stored_ids.append(entity_id)
        
        print(f"[TrieMemory] Stored {len(stored_ids)} semantic entities")
        return stored_ids
    
    async def query_semantic(self, query: str, n_results: int = 5) -> List[dict]:
        """Retrieve semantically related entities from the knowledge graph."""
        if self._semantic_collection.count() == 0:
            return []
        
        embedding = embedder.embed(query)
        n = min(n_results, self._semantic_collection.count())
        results = self._semantic_collection.query(
            query_embeddings=[embedding],
            n_results=n,
            include=["documents", "metadatas", "distances"],
        )
        
        entities = []
        for i, doc in enumerate(results["documents"][0]):
            meta = results["metadatas"][0][i]
            entities.append({
                "entity": meta.get("entity", ""),
                "type": meta.get("entity_type", ""),
                "description": meta.get("description", ""),
                "related": json.loads(meta.get("related_entities", "[]")),
                "relevance": round(1 - results["distances"][0][i], 3),
                "occurrence_count": int(meta.get("occurrence_count", 1)),
            })
        
        return entities
    
    # ─── TIER 3: PROCEDURAL MEMORY ────────────────────────────────────
    
    async def store_workflow(
        self,
        task_id: str,
        task_description: str,
        dag_nodes: List[dict],
        duration_seconds: float,
        success: bool
    ) -> str:
        """
        Store a successful workflow as a reusable procedural template.
        
        Extracts the pattern from the DAG and stores it for future retrieval.
        """
        if not success:
            return ""  # Only store successful workflows
        
        workflow_id = f"proc_{task_id}"
        
        # Build simplified template from DAG nodes
        template_steps = [
            {
                "step": i + 1,
                "task_pattern": node.get("task", ""),
                "agent_hint": node.get("agent_hint", "executor"),
                "complexity": node.get("estimated_complexity", "medium"),
                "depends_on": node.get("depends_on", []),
            }
            for i, node in enumerate(dag_nodes)
        ]
        
        doc = (
            f"Workflow for: {task_description}\n"
            f"Steps: {json.dumps([s['task_pattern'] for s in template_steps])}"
        )
        embedding = embedder.embed(doc)
        
        now = datetime.now(timezone.utc).isoformat()
        metadata = {
            "task_id": task_id,
            "task_description": task_description,
            "subtask_sequence": json.dumps(template_steps),
            "success_count": 1,
            "avg_duration_seconds": duration_seconds,
            "created_at": now,
            "last_used": now,
            "memory_type": "procedural",
        }
        
        try:
            self._procedural_collection.add(
                ids=[workflow_id],
                embeddings=[embedding],
                documents=[doc],
                metadatas=[metadata],
            )
        except Exception:
            # Update success count
            try:
                existing = self._procedural_collection.get(ids=[workflow_id])
                existing_meta = existing["metadatas"][0] if existing["metadatas"] else {}
                count = int(existing_meta.get("success_count", 0)) + 1
                avg_dur = (
                    float(existing_meta.get("avg_duration_seconds", duration_seconds)) + duration_seconds
                ) / 2
                self._procedural_collection.update(
                    ids=[workflow_id],
                    metadatas={**existing_meta, "success_count": count, "avg_duration_seconds": avg_dur, "last_used": now},
                )
            except Exception as e:
                print(f"[TrieMemory] Procedural update error: {e}")
        
        print(f"[TrieMemory] Stored workflow template for: '{task_description[:50]}'")
        return workflow_id
    
    async def retrieve_workflow(self, task_description: str, n_results: int = 2) -> List[dict]:
        """
        Find similar past workflows to reuse as templates.
        """
        if self._procedural_collection.count() == 0:
            return []
        
        embedding = embedder.embed(task_description)
        n = min(n_results, self._procedural_collection.count())
        results = self._procedural_collection.query(
            query_embeddings=[embedding],
            n_results=n,
            include=["documents", "metadatas", "distances"],
        )
        
        workflows = []
        for i, doc in enumerate(results["documents"][0]):
            meta = results["metadatas"][0][i]
            similarity = 1 - results["distances"][0][i]
            
            # Only return highly similar workflows (> 0.7 similarity)
            if similarity < 0.7:
                continue
            
            steps_raw = meta.get("subtask_sequence", "[]")
            try:
                steps = json.loads(steps_raw)
            except Exception:
                steps = []
            
            workflows.append({
                "task_description": meta.get("task_description", ""),
                "subtask_sequence": steps,
                "success_count": int(meta.get("success_count", 1)),
                "avg_duration_seconds": float(meta.get("avg_duration_seconds", 0)),
                "similarity": round(similarity, 3),
            })
        
        return workflows
    
    # ─── UNIFIED RETRIEVAL ────────────────────────────────────────────
    
    async def retrieve_all_context(self, query: str) -> dict:
        """
        Retrieve relevant context from all 3 memory tiers simultaneously.
        Returns a unified context dict for enriching new tasks.
        """
        results = await asyncio.gather(
            self.retrieve_episodes(query, n_results=2),
            self.query_semantic(query, n_results=5),
            self.retrieve_workflow(query, n_results=1),
            return_exceptions=True,
        )
        
        episodes = results[0] if not isinstance(results[0], Exception) else []
        entities = results[1] if not isinstance(results[1], Exception) else []
        workflows = results[2] if not isinstance(results[2], Exception) else []
        
        return {
            "episodic": episodes,
            "semantic": entities,
            "procedural": workflows,
        }
    
    def count(self) -> dict:
        """Return count of entries in each memory tier."""
        return {
            "episodic": self._episodic_collection.count(),
            "semantic": self._semantic_collection.count(),
            "procedural": self._procedural_collection.count(),
            "total": (
                self._episodic_collection.count() +
                self._semantic_collection.count() +
                self._procedural_collection.count()
            ),
        }
    
    def _parse_entities(self, text: str) -> dict | None:
        """Parse entity extraction JSON from LLM."""
        cleaned = text.strip()
        for fence in ("```json", "```"):
            if cleaned.startswith(fence):
                cleaned = cleaned[len(fence):]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        
        try:
            return json.loads(cleaned)
        except (json.JSONDecodeError, ValueError):
            return None


# Singleton instance
trie_memory = TrieMemorySystem()
